"""
Django REST Framework API views for blog posts.
Provides CRUD operations with proper HTTP status codes and error handling.
Enhanced with role-based permissions and status management.
"""
import logging
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.http import Http404
from django.views.decorators.cache import cache_control
from django.utils.decorators import method_decorator
from django.views.decorators.vary import vary_on_headers
from django.db.models import Q
from django.utils import timezone

from .models import Post, MediaFile, PostMedia
from .serializers import PostSerializer, MediaFileSerializer, PostMediaSerializer
from .services import PostService
from .permissions import PostPermission, can_user_view_post, can_user_modify_post_status
from common.exceptions import PostNotFoundError, ValidationError, ServiceError

logger = logging.getLogger(__name__)


class PostPagination(PageNumberPagination):
    """
    Custom pagination class for post listing.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        """
        Return a paginated style Response object with additional metadata.
        """
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'page_size': self.page.paginator.per_page,
            'results': data
        })


@method_decorator(vary_on_headers('Accept', 'Accept-Language'), name='dispatch')
class PostListCreateView(generics.ListCreateAPIView):
    """
    API view for listing all posts (GET) and creating new posts (POST).
    
    GET /api/posts/ - Returns paginated list of posts (filtered by status and permissions)
    POST /api/posts/ - Creates a new post
    """
    serializer_class = PostSerializer
    pagination_class = PostPagination
    permission_classes = [PostPermission]
    
    def get_queryset(self):
        """
        Override to filter posts based on user permissions and status.
        """
        user = self.request.user
        
        # Base queryset
        queryset = Post.objects.all().order_by('-created_at')
        
        # Filter based on user permissions
        if not user or not user.is_authenticated:
            # Anonymous users can only see published posts
            queryset = queryset.filter(status='published')
        elif user.is_superuser or user.has_any_role(['admin', 'editor']):
            # Admins and editors can see all posts
            pass
        else:
            # Other authenticated users can see:
            # - Published posts
            # - Their own drafts and scheduled posts
            queryset = queryset.filter(
                Q(status='published') |
                Q(author_user=user, status__in=['draft', 'scheduled'])
            )
        
        # Apply additional filters from query parameters
        status_filter = self.request.query_params.get('status')
        if status_filter and status_filter in dict(Post.STATUS_CHOICES):
            queryset = queryset.filter(status=status_filter)
        
        author_filter = self.request.query_params.get('author')
        if author_filter:
            queryset = queryset.filter(
                Q(author__icontains=author_filter) |
                Q(author_user__username__icontains=author_filter) |
                Q(author_user__first_name__icontains=author_filter) |
                Q(author_user__last_name__icontains=author_filter)
            )
        
        return queryset
    
    @method_decorator(cache_control(max_age=300, public=True))  # Cache for 5 minutes
    def list(self, request, *args, **kwargs):
        """
        Handle GET request to list all posts with pagination.
        Cached for 5 minutes to improve performance.
        """
        logger.info("Handling GET request for post list")
        
        # Get pagination parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        # Use service layer to get posts - let exceptions bubble up to custom handler
        posts_data = PostService.get_all_posts(page=page, page_size=page_size)
        
        # Serialize the posts
        serializer = self.get_serializer(posts_data['posts'], many=True)
        
        # Return paginated response
        paginated_response = {
            'count': posts_data['pagination']['total_posts'],
            'next': self._get_next_link(request, posts_data['pagination']),
            'previous': self._get_previous_link(request, posts_data['pagination']),
            'total_pages': posts_data['pagination']['total_pages'],
            'current_page': posts_data['pagination']['current_page'],
            'page_size': posts_data['pagination']['page_size'],
            'results': serializer.data
        }
        
        logger.info(f"Successfully returned {len(serializer.data)} posts")
        response = Response(paginated_response, status=status.HTTP_200_OK)
        
        # Add additional caching headers
        response['Cache-Control'] = 'public, max-age=300'
        response['ETag'] = f'posts-page-{page}-{page_size}-{posts_data["pagination"]["total_posts"]}'
        
        return response
    
    def create(self, request, *args, **kwargs):
        """
        Handle POST request to create a new post.
        """
        logger.info("Handling POST request to create new post")
        
        # Validate the request data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Set author_user to current user if not provided
        validated_data = serializer.validated_data
        if not validated_data.get('author_user') and request.user.is_authenticated:
            validated_data['author_user'] = request.user
        
        # Check if user can set the requested status
        requested_status = validated_data.get('status', 'draft')
        if requested_status in ['published', 'scheduled']:
            if not (request.user.is_superuser or request.user.has_any_role(['admin', 'editor'])):
                # Writers can only create drafts
                validated_data['status'] = 'draft'
                validated_data.pop('scheduled_publish_date', None)
        
        # Use service layer to create the post
        post = PostService.create_post(validated_data)
        
        # Serialize the created post
        response_serializer = self.get_serializer(post)
        
        logger.info(f"Successfully created post with ID: {post.id}")
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    def _get_next_link(self, request, pagination_info):
        """
        Generate next page link if available.
        """
        if not pagination_info['has_next']:
            return None
        
        next_page = pagination_info['current_page'] + 1
        return request.build_absolute_uri(f"?page={next_page}&page_size={pagination_info['page_size']}")
    
    def _get_previous_link(self, request, pagination_info):
        """
        Generate previous page link if available.
        """
        if not pagination_info['has_previous']:
            return None
        
        prev_page = pagination_info['current_page'] - 1
        return request.build_absolute_uri(f"?page={prev_page}&page_size={pagination_info['page_size']}")


@method_decorator(vary_on_headers('Accept', 'Accept-Language'), name='dispatch')
class PostRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting individual posts.
    
    GET /api/posts/{id}/ - Returns a specific post (if user has permission)
    PUT /api/posts/{id}/ - Updates a specific post (with permission checks)
    DELETE /api/posts/{id}/ - Deletes a specific post (editors and admins only)
    """
    serializer_class = PostSerializer
    lookup_field = 'pk'
    permission_classes = [PostPermission]
    
    def get_queryset(self):
        """
        Override to filter posts based on user permissions.
        """
        user = self.request.user
        queryset = Post.objects.all()
        
        # For retrieve operations, we'll handle permissions in get_object
        # For update/delete, the permission class will handle it
        return queryset
    
    def get_object(self):
        """
        Override to check view permissions and increment view count.
        """
        obj = super().get_object()
        
        # Check if user can view this post
        if not can_user_view_post(self.request.user, obj):
            raise Http404("Post not found or you don't have permission to view it.")
        
        # Increment view count for GET requests
        if self.request.method == 'GET':
            obj.increment_view_count()
        
        return obj
    
    @method_decorator(cache_control(max_age=600, public=True))  # Cache for 10 minutes
    def retrieve(self, request, *args, **kwargs):
        """
        Handle GET request to retrieve a specific post.
        Cached for 10 minutes to improve performance.
        """
        post_id = int(kwargs.get('pk'))
        logger.info(f"Handling GET request for post ID: {post_id}")
        
        # Use service layer to get the post - let exceptions bubble up to custom handler
        post = PostService.get_post_by_id(post_id)
        
        # Serialize the post
        serializer = self.get_serializer(post)
        
        logger.info(f"Successfully retrieved post: {post.title}")
        response = Response(serializer.data, status=status.HTTP_200_OK)
        
        # Add additional caching headers
        response['Cache-Control'] = 'public, max-age=600'
        response['ETag'] = f'post-{post_id}-{post.updated_at.isoformat()}'
        response['Last-Modified'] = post.updated_at.strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        return response
    
    def update(self, request, *args, **kwargs):
        """
        Handle PUT request to update a specific post.
        """
        post_id = int(kwargs.get('pk'))
        logger.info(f"Handling PUT request for post ID: {post_id}")
        
        instance = self.get_object()
        
        # Validate the request data
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)
        
        # Check status change permissions
        new_status = serializer.validated_data.get('status', instance.status)
        if new_status != instance.status:
            if not can_user_modify_post_status(request.user, instance, new_status):
                return Response(
                    {'error': f'You do not have permission to change post status to {new_status}.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Perform the update
        self.perform_update(serializer)
        
        logger.info(f"Successfully updated post: {instance.title}")
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        """
        Handle DELETE request to delete a specific post.
        """
        post_id = int(kwargs.get('pk'))
        logger.info(f"Handling DELETE request for post ID: {post_id}")
        
        # Use service layer to delete the post - let exceptions bubble up to custom handler
        PostService.delete_post(post_id)
        
        logger.info(f"Successfully deleted post with ID: {post_id}")
        return Response(status=status.HTTP_204_NO_CONTENT)


class DraftPostsView(generics.ListAPIView):
    """
    API view for listing draft posts for the authenticated user.
    
    GET /api/posts/drafts/ - Returns paginated list of user's draft posts
    """
    serializer_class = PostSerializer
    pagination_class = PostPagination
    permission_classes = [PostPermission]
    
    def get_queryset(self):
        """
        Return draft posts for the authenticated user.
        """
        user = self.request.user
        
        if not user or not user.is_authenticated:
            return Post.objects.none()
        
        # Users can see their own drafts
        # Admins and editors can see all drafts
        if user.is_superuser or user.has_any_role(['admin', 'editor']):
            queryset = Post.objects.filter(status='draft')
        else:
            queryset = Post.objects.filter(status='draft', author_user=user)
        
        return queryset.order_by('-updated_at')
    
    def list(self, request, *args, **kwargs):
        """
        Handle GET request to list draft posts.
        """
        logger.info(f"Handling GET request for draft posts by user: {request.user}")
        
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        logger.info(f"Successfully returned {len(serializer.data)} draft posts")
        return Response(serializer.data, status=status.HTTP_200_OK)


class SchedulePostView(APIView):
    """
    API view for scheduling posts for future publication.
    
    POST /api/posts/{id}/schedule/ - Schedule a post for future publication
    """
    permission_classes = [PostPermission]
    
    def post(self, request, pk):
        """
        Schedule a post for future publication.
        """
        logger.info(f"Handling POST request to schedule post ID: {pk}")
        
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response(
                {'error': 'Post not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permissions
        if not can_user_modify_post_status(request.user, post, 'scheduled'):
            return Response(
                {'error': 'You do not have permission to schedule this post.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate scheduled_publish_date
        scheduled_date = request.data.get('scheduled_publish_date')
        if not scheduled_date:
            return Response(
                {'error': 'scheduled_publish_date is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from django.utils.dateparse import parse_datetime
            parsed_date = parse_datetime(scheduled_date)
            if not parsed_date:
                return Response(
                    {'error': 'Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS).'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if parsed_date <= timezone.now():
                return Response(
                    {'error': 'Scheduled publish date must be in the future.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update post
            post.status = 'scheduled'
            post.scheduled_publish_date = parsed_date
            post.save()
            
            # Serialize and return updated post
            serializer = PostSerializer(post)
            logger.info(f"Successfully scheduled post: {post.title} for {parsed_date}")
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error scheduling post {pk}: {str(e)}")
            return Response(
                {'error': 'Failed to schedule post.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PublishPostView(APIView):
    """
    API view for publishing draft or scheduled posts.
    
    POST /api/posts/{id}/publish/ - Publish a draft or scheduled post immediately
    """
    permission_classes = [PostPermission]
    
    def post(self, request, pk):
        """
        Publish a post immediately.
        """
        logger.info(f"Handling POST request to publish post ID: {pk}")
        
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response(
                {'error': 'Post not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permissions
        if not can_user_modify_post_status(request.user, post, 'published'):
            return Response(
                {'error': 'You do not have permission to publish this post.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if post can be published
        if not post.can_be_published():
            return Response(
                {'error': f'Post with status "{post.status}" cannot be published.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Publish the post
            post.publish()
            
            # Serialize and return updated post
            serializer = PostSerializer(post)
            logger.info(f"Successfully published post: {post.title}")
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error publishing post {pk}: {str(e)}")
            return Response(
                {'error': 'Failed to publish post.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MediaFileUploadView(generics.CreateAPIView):
    """
    API view for uploading media files.
    
    POST /api/posts/media/upload/ - Upload a new media file
    """
    serializer_class = MediaFileSerializer
    permission_classes = [PostPermission]
    
    def create(self, request, *args, **kwargs):
        """
        Handle POST request to upload a media file.
        """
        logger.info(f"Handling media file upload request from user: {request.user}")
        
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required to upload files.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Validate the request data
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        try:
            # Create the media file
            media_file = serializer.save()
            
            logger.info(f"Successfully uploaded media file: {media_file.original_name}")
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.error(f"Error uploading media file: {str(e)}")
            return Response(
                {'error': 'Failed to upload file. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MediaFileListView(generics.ListAPIView):
    """
    API view for listing user's uploaded media files.
    
    GET /api/posts/media/ - Returns paginated list of user's media files
    """
    serializer_class = MediaFileSerializer
    pagination_class = PostPagination
    permission_classes = [PostPermission]
    
    def get_queryset(self):
        """
        Return media files for the authenticated user.
        """
        user = self.request.user
        
        if not user or not user.is_authenticated:
            return MediaFile.objects.none()
        
        # Users can see their own media files
        # Admins and editors can see all media files
        if user.is_superuser or user.has_any_role(['admin', 'editor']):
            queryset = MediaFile.objects.all()
        else:
            queryset = MediaFile.objects.filter(uploaded_by=user)
        
        # Apply filters from query parameters
        file_type_filter = self.request.query_params.get('file_type')
        if file_type_filter and file_type_filter in ['image', 'video']:
            queryset = queryset.filter(file_type=file_type_filter)
        
        return queryset.order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        """
        Handle GET request to list media files.
        """
        logger.info(f"Handling GET request for media files by user: {request.user}")
        
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        logger.info(f"Successfully returned {len(serializer.data)} media files")
        return Response(serializer.data, status=status.HTTP_200_OK)


class MediaFileDetailView(generics.RetrieveDestroyAPIView):
    """
    API view for retrieving and deleting individual media files.
    
    GET /api/posts/media/{id}/ - Returns a specific media file
    DELETE /api/posts/media/{id}/ - Deletes a specific media file
    """
    serializer_class = MediaFileSerializer
    lookup_field = 'pk'
    permission_classes = [PostPermission]
    
    def get_queryset(self):
        """
        Return media files based on user permissions.
        """
        user = self.request.user
        
        if not user or not user.is_authenticated:
            return MediaFile.objects.none()
        
        # Users can access their own media files
        # Admins and editors can access all media files
        if user.is_superuser or user.has_any_role(['admin', 'editor']):
            return MediaFile.objects.all()
        else:
            return MediaFile.objects.filter(uploaded_by=user)
    
    def retrieve(self, request, *args, **kwargs):
        """
        Handle GET request to retrieve a specific media file.
        """
        media_id = int(kwargs.get('pk'))
        logger.info(f"Handling GET request for media file ID: {media_id}")
        
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            logger.info(f"Successfully retrieved media file: {instance.original_name}")
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Http404:
            return Response(
                {'error': 'Media file not found or you do not have permission to access it.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def destroy(self, request, *args, **kwargs):
        """
        Handle DELETE request to delete a specific media file.
        """
        media_id = int(kwargs.get('pk'))
        logger.info(f"Handling DELETE request for media file ID: {media_id}")
        
        try:
            instance = self.get_object()
            
            # Check if media file is attached to any posts
            if instance.post_attachments.exists():
                return Response(
                    {'error': 'Cannot delete media file that is attached to posts. Remove from posts first.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Delete the media file
            instance.delete()
            
            logger.info(f"Successfully deleted media file: {instance.original_name}")
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Http404:
            return Response(
                {'error': 'Media file not found or you do not have permission to delete it.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error deleting media file {media_id}: {str(e)}")
            return Response(
                {'error': 'Failed to delete media file.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PostMediaView(APIView):
    """
    API view for managing media attachments to posts.
    
    GET /api/posts/{id}/media/ - List media files attached to a post
    POST /api/posts/{id}/media/ - Attach media files to a post
    DELETE /api/posts/{id}/media/{media_id}/ - Remove media file from a post
    """
    permission_classes = [PostPermission]
    
    def get(self, request, pk):
        """
        List media files attached to a post.
        """
        logger.info(f"Handling GET request for media files of post ID: {pk}")
        
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response(
                {'error': 'Post not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user can view this post
        if not can_user_view_post(request.user, post):
            return Response(
                {'error': 'You do not have permission to view this post.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get media files attached to the post
        post_media = post.media_files.all().order_by('order', 'created_at')
        serializer = PostMediaSerializer(post_media, many=True)
        
        logger.info(f"Successfully returned {len(serializer.data)} media files for post: {post.title}")
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request, pk):
        """
        Attach media files to a post.
        """
        logger.info(f"Handling POST request to attach media to post ID: {pk}")
        
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response(
                {'error': 'Post not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permissions to modify this post
        if not can_user_modify_post_status(request.user, post, post.status):
            return Response(
                {'error': 'You do not have permission to modify this post.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate request data
        media_file_ids = request.data.get('media_file_ids', [])
        if not media_file_ids or not isinstance(media_file_ids, list):
            return Response(
                {'error': 'media_file_ids is required and must be a list.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Validate that all media files exist and belong to the user
            media_files = MediaFile.objects.filter(id__in=media_file_ids)
            
            if len(media_files) != len(media_file_ids):
                return Response(
                    {'error': 'One or more media files not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if user can use these media files
            for media_file in media_files:
                if media_file.uploaded_by != request.user:
                    if not (request.user.is_superuser or request.user.has_any_role(['admin', 'editor'])):
                        return Response(
                            {'error': 'You can only attach your own media files.'},
                            status=status.HTTP_403_FORBIDDEN
                        )
            
            # Create PostMedia instances
            post_media_instances = []
            for i, media_file in enumerate(media_files):
                # Check if already attached
                if not PostMedia.objects.filter(post=post, media_file=media_file).exists():
                    post_media = PostMedia.objects.create(
                        post=post,
                        media_file=media_file,
                        order=i,
                        caption=request.data.get('captions', {}).get(str(media_file.id), '')
                    )
                    post_media_instances.append(post_media)
            
            # Serialize and return the attached media
            serializer = PostMediaSerializer(post_media_instances, many=True)
            
            logger.info(f"Successfully attached {len(post_media_instances)} media files to post: {post.title}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error attaching media to post {pk}: {str(e)}")
            return Response(
                {'error': 'Failed to attach media files to post.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, pk, media_id=None):
        """
        Remove media file from a post.
        """
        logger.info(f"Handling DELETE request to remove media from post ID: {pk}")
        
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response(
                {'error': 'Post not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permissions to modify this post
        if not can_user_modify_post_status(request.user, post, post.status):
            return Response(
                {'error': 'You do not have permission to modify this post.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get media_id from URL or request data
        if not media_id:
            media_id = request.data.get('media_id')
        
        if not media_id:
            return Response(
                {'error': 'media_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Find and delete the PostMedia instance
            post_media = PostMedia.objects.get(post=post, media_file_id=media_id)
            post_media.delete()
            
            logger.info(f"Successfully removed media file {media_id} from post: {post.title}")
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except PostMedia.DoesNotExist:
            return Response(
                {'error': 'Media file is not attached to this post.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error removing media from post {pk}: {str(e)}")
            return Response(
                {'error': 'Failed to remove media file from post.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )