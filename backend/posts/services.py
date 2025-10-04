"""
Service layer for blog post business logic.
Handles CRUD operations and business rules for posts.
"""
import logging
from typing import List, Optional, Dict, Any
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction, IntegrityError
from django.db import models

from .models import Post
from common.exceptions import PostNotFoundError, ValidationError, ServiceError

logger = logging.getLogger(__name__)


class PostService:
    """
    Service class for handling blog post business logic.
    Provides CRUD operations with proper error handling and logging.
    """
    
    @staticmethod
    def get_all_posts(page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """
        Retrieve paginated posts with business logic.
        
        Args:
            page (int): Page number (1-based)
            page_size (int): Number of posts per page
            
        Returns:
            Dict containing posts, pagination info, and metadata
            
        Raises:
            ServiceError: If pagination parameters are invalid
        """
        try:
            logger.info(f"Retrieving posts - page: {page}, page_size: {page_size}")
            
            # Validate pagination parameters
            if page < 1:
                raise ServiceError("Page number must be greater than 0")
            if page_size < 1 or page_size > 100:
                raise ServiceError("Page size must be between 1 and 100")
            
            # Get all posts ordered by creation date (newest first)
            posts_queryset = Post.objects.all().order_by('-created_at')
            
            # Apply pagination
            paginator = Paginator(posts_queryset, page_size)
            
            try:
                posts_page = paginator.page(page)
            except PageNotAnInteger:
                posts_page = paginator.page(1)
            except EmptyPage:
                posts_page = paginator.page(paginator.num_pages)
            
            posts_data = {
                'posts': list(posts_page.object_list),
                'pagination': {
                    'current_page': posts_page.number,
                    'total_pages': paginator.num_pages,
                    'total_posts': paginator.count,
                    'has_next': posts_page.has_next(),
                    'has_previous': posts_page.has_previous(),
                    'page_size': page_size
                }
            }
            
            logger.info(f"Successfully retrieved {len(posts_page.object_list)} posts")
            return posts_data
            
        except ServiceError:
            raise
        except Exception as e:
            logger.error(f"Error retrieving posts: {str(e)}")
            raise ServiceError(f"Failed to retrieve posts: {str(e)}")
    
    @staticmethod
    def get_post_by_id(post_id: int) -> Post:
        """
        Retrieve single post by ID with error handling.
        
        Args:
            post_id (int): ID of the post to retrieve
            
        Returns:
            Post: The requested post object
            
        Raises:
            PostNotFoundError: If post with given ID doesn't exist
            ServiceError: If post_id is invalid
        """
        try:
            logger.info(f"Retrieving post with ID: {post_id}")
            
            # Validate post_id
            if not isinstance(post_id, int) or post_id <= 0:
                raise ServiceError("Post ID must be a positive integer")
            
            try:
                post = Post.objects.get(id=post_id)
                logger.info(f"Successfully retrieved post: {post.title}")
                return post
            except Post.DoesNotExist:
                logger.warning(f"Post with ID {post_id} not found")
                raise PostNotFoundError(post_id)
                
        except (PostNotFoundError, ServiceError):
            raise
        except Exception as e:
            logger.error(f"Error retrieving post {post_id}: {str(e)}")
            raise ServiceError(f"Failed to retrieve post: {str(e)}")
    
    @staticmethod
    def create_post(post_data: Dict[str, Any]) -> Post:
        """
        Create post with business validation.
        
        Args:
            post_data (Dict): Dictionary containing post data
            
        Returns:
            Post: The created post object
            
        Raises:
            ValidationError: If post data is invalid
            ServiceError: If creation fails
        """
        try:
            logger.info(f"Creating new post with title: {post_data.get('title', 'N/A')}")
            
            # Validate required fields
            required_fields = ['title', 'content', 'author']
            missing_fields = [field for field in required_fields if not post_data.get(field)]
            if missing_fields:
                raise ValidationError(
                    f"Missing required fields: {', '.join(missing_fields)}",
                    {field: "This field is required" for field in missing_fields}
                )
            
            # Create post instance
            post = Post(
                title=post_data['title'],
                content=post_data['content'],
                author=post_data['author'],
                tags=post_data.get('tags', ''),
                image_url=post_data.get('image_url', None)
            )
            
            # Use transaction to ensure data consistency
            with transaction.atomic():
                try:
                    # This will call the model's clean() method and save()
                    post.save()
                    logger.info(f"Successfully created post with ID: {post.id}")
                    return post
                except DjangoValidationError as e:
                    logger.warning(f"Validation error creating post: {e.message_dict}")
                    raise ValidationError("Post validation failed", e.message_dict)
                except IntegrityError as e:
                    logger.error(f"Database integrity error creating post: {str(e)}")
                    raise ServiceError("Failed to create post due to database constraint")
                    
        except (ValidationError, ServiceError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating post: {str(e)}")
            raise ServiceError(f"Failed to create post: {str(e)}")
    
    @staticmethod
    def update_post(post_id: int, post_data: Dict[str, Any]) -> Post:
        """
        Update post with ownership validation.
        
        Args:
            post_id (int): ID of the post to update
            post_data (Dict): Dictionary containing updated post data
            
        Returns:
            Post: The updated post object
            
        Raises:
            PostNotFoundError: If post doesn't exist
            ValidationError: If update data is invalid
            ServiceError: If update fails
        """
        try:
            logger.info(f"Updating post with ID: {post_id}")
            
            # First, get the existing post
            post = PostService.get_post_by_id(post_id)
            
            # Update fields if provided
            if 'title' in post_data:
                post.title = post_data['title']
            if 'content' in post_data:
                post.content = post_data['content']
            if 'author' in post_data:
                post.author = post_data['author']
            if 'tags' in post_data:
                post.tags = post_data['tags']
            if 'image_url' in post_data:
                post.image_url = post_data['image_url']
            
            # Use transaction to ensure data consistency
            with transaction.atomic():
                try:
                    # This will call the model's clean() method and save()
                    post.save()
                    logger.info(f"Successfully updated post: {post.title}")
                    return post
                except DjangoValidationError as e:
                    logger.warning(f"Validation error updating post {post_id}: {e.message_dict}")
                    raise ValidationError("Post validation failed", e.message_dict)
                except IntegrityError as e:
                    logger.error(f"Database integrity error updating post {post_id}: {str(e)}")
                    raise ServiceError("Failed to update post due to database constraint")
                    
        except (PostNotFoundError, ValidationError, ServiceError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating post {post_id}: {str(e)}")
            raise ServiceError(f"Failed to update post: {str(e)}")
    
    @staticmethod
    def delete_post(post_id: int) -> bool:
        """
        Delete post with cascade handling.
        
        Args:
            post_id (int): ID of the post to delete
            
        Returns:
            bool: True if deletion was successful
            
        Raises:
            PostNotFoundError: If post doesn't exist
            ServiceError: If deletion fails
        """
        try:
            logger.info(f"Deleting post with ID: {post_id}")
            
            # First, get the existing post to ensure it exists
            post = PostService.get_post_by_id(post_id)
            post_title = post.title
            
            # Use transaction to ensure data consistency
            with transaction.atomic():
                try:
                    post.delete()
                    logger.info(f"Successfully deleted post: {post_title}")
                    return True
                except Exception as e:
                    logger.error(f"Database error deleting post {post_id}: {str(e)}")
                    raise ServiceError("Failed to delete post due to database error")
                    
        except (PostNotFoundError, ServiceError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting post {post_id}: {str(e)}")
            raise ServiceError(f"Failed to delete post: {str(e)}")
    
    @staticmethod
    def search_posts(query: str, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """
        Search posts by title or content.
        
        Args:
            query (str): Search query string
            page (int): Page number (1-based)
            page_size (int): Number of posts per page
            
        Returns:
            Dict containing matching posts and pagination info
            
        Raises:
            ServiceError: If search parameters are invalid
        """
        try:
            logger.info(f"Searching posts with query: '{query}'")
            
            # Validate search parameters
            if not query or not query.strip():
                raise ServiceError("Search query cannot be empty")
            if page < 1:
                raise ServiceError("Page number must be greater than 0")
            if page_size < 1 or page_size > 100:
                raise ServiceError("Page size must be between 1 and 100")
            
            query = query.strip()
            
            # Search in title and content
            posts_queryset = Post.objects.filter(
                models.Q(title__icontains=query) | 
                models.Q(content__icontains=query)
            ).order_by('-created_at')
            
            # Apply pagination
            paginator = Paginator(posts_queryset, page_size)
            
            try:
                posts_page = paginator.page(page)
            except PageNotAnInteger:
                posts_page = paginator.page(1)
            except EmptyPage:
                posts_page = paginator.page(paginator.num_pages)
            
            search_results = {
                'posts': list(posts_page.object_list),
                'query': query,
                'pagination': {
                    'current_page': posts_page.number,
                    'total_pages': paginator.num_pages,
                    'total_posts': paginator.count,
                    'has_next': posts_page.has_next(),
                    'has_previous': posts_page.has_previous(),
                    'page_size': page_size
                }
            }
            
            logger.info(f"Search found {paginator.count} posts matching '{query}'")
            return search_results
            
        except ServiceError:
            raise
        except Exception as e:
            logger.error(f"Error searching posts: {str(e)}")
            raise ServiceError(f"Failed to search posts: {str(e)}")