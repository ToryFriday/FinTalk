"""
Django REST Framework API views for blog posts.
Provides CRUD operations with proper HTTP status codes and error handling.
"""
import logging
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.http import Http404
from django.views.decorators.cache import cache_control
from django.utils.decorators import method_decorator
from django.views.decorators.vary import vary_on_headers

from .models import Post
from .serializers import PostSerializer
from .services import PostService
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
    
    GET /api/posts/ - Returns paginated list of all posts
    POST /api/posts/ - Creates a new post
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    pagination_class = PostPagination
    
    def get_queryset(self):
        """
        Override to use service layer for data retrieval.
        """
        return Post.objects.all().order_by('-created_at')
    
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
        serializer.is_valid(raise_exception=True)  # Let DRF handle validation errors
        
        # Use service layer to create the post - let exceptions bubble up to custom handler
        post = PostService.create_post(serializer.validated_data)
        
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
    
    GET /api/posts/{id}/ - Returns a specific post
    PUT /api/posts/{id}/ - Updates a specific post
    DELETE /api/posts/{id}/ - Deletes a specific post
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    lookup_field = 'pk'
    
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
        
        # Validate the request data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # Let DRF handle validation errors
        
        # Use service layer to update the post - let exceptions bubble up to custom handler
        post = PostService.update_post(post_id, serializer.validated_data)
        
        # Serialize the updated post
        response_serializer = self.get_serializer(post)
        
        logger.info(f"Successfully updated post: {post.title}")
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK
        )
    
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
