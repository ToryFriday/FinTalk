"""
Tests specifically targeting missing code coverage areas.
Based on coverage report, targeting specific uncovered lines.
"""
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.paginator import EmptyPage, PageNotAnInteger
from rest_framework.test import APITestCase
from rest_framework import status

from posts.models import Post
from posts.services import PostService
from posts.views import PostListCreateView
from common.exceptions import ServiceError


class ServiceMissingCoverageTestCase(TestCase):
    """Tests targeting missing coverage in services.py."""
    
    def setUp(self):
        """Set up test data."""
        self.valid_post_data = {
            'title': 'Test Post Title',
            'content': 'This is test content for the blog post.',
            'author': 'Test Author',
            'tags': 'test, django, python'
        }
    
    @patch('posts.services.Paginator')
    def test_get_all_posts_page_not_integer_exception(self, mock_paginator_class):
        """Test get_all_posts when PageNotAnInteger is raised."""
        # Create a real post first
        Post.objects.create(**self.valid_post_data)
        
        # Mock paginator to raise PageNotAnInteger
        mock_paginator = MagicMock()
        mock_paginator.page.side_effect = [PageNotAnInteger(), MagicMock()]
        mock_paginator.num_pages = 1
        mock_paginator.count = 1
        mock_paginator_class.return_value = mock_paginator
        
        # Mock the page object that gets returned
        mock_page = MagicMock()
        mock_page.object_list = []
        mock_page.number = 1
        mock_page.has_next.return_value = False
        mock_page.has_previous.return_value = False
        mock_paginator.page.return_value = mock_page
        
        result = PostService.get_all_posts(page=1, page_size=10)
        
        # Should fall back to page 1
        self.assertIn('posts', result)
        self.assertIn('pagination', result)
    
    @patch('posts.services.Paginator')
    def test_get_all_posts_empty_page_exception(self, mock_paginator_class):
        """Test get_all_posts when EmptyPage is raised."""
        # Create a real post first
        Post.objects.create(**self.valid_post_data)
        
        # Mock paginator to raise EmptyPage
        mock_paginator = MagicMock()
        mock_paginator.page.side_effect = [EmptyPage(), MagicMock()]
        mock_paginator.num_pages = 1
        mock_paginator.count = 1
        mock_paginator_class.return_value = mock_paginator
        
        # Mock the page object that gets returned
        mock_page = MagicMock()
        mock_page.object_list = []
        mock_page.number = 1
        mock_page.has_next.return_value = False
        mock_page.has_previous.return_value = False
        mock_paginator.page.return_value = mock_page
        
        result = PostService.get_all_posts(page=999, page_size=10)
        
        # Should fall back to last page
        self.assertIn('posts', result)
        self.assertIn('pagination', result)
    
    @patch('posts.services.Paginator')
    def test_search_posts_page_not_integer_exception(self, mock_paginator_class):
        """Test search_posts when PageNotAnInteger is raised."""
        # Create a real post first
        Post.objects.create(**self.valid_post_data)
        
        # Mock paginator to raise PageNotAnInteger
        mock_paginator = MagicMock()
        mock_paginator.page.side_effect = [PageNotAnInteger(), MagicMock()]
        mock_paginator.num_pages = 1
        mock_paginator.count = 1
        mock_paginator_class.return_value = mock_paginator
        
        # Mock the page object that gets returned
        mock_page = MagicMock()
        mock_page.object_list = []
        mock_page.number = 1
        mock_page.has_next.return_value = False
        mock_page.has_previous.return_value = False
        mock_paginator.page.return_value = mock_page
        
        result = PostService.search_posts('test', page=1, page_size=10)
        
        # Should fall back to page 1
        self.assertIn('posts', result)
        self.assertIn('query', result)
        self.assertIn('pagination', result)
    
    @patch('posts.services.Paginator')
    def test_search_posts_empty_page_exception(self, mock_paginator_class):
        """Test search_posts when EmptyPage is raised."""
        # Create a real post first
        Post.objects.create(**self.valid_post_data)
        
        # Mock paginator to raise EmptyPage
        mock_paginator = MagicMock()
        mock_paginator.page.side_effect = [EmptyPage(), MagicMock()]
        mock_paginator.num_pages = 1
        mock_paginator.count = 1
        mock_paginator_class.return_value = mock_paginator
        
        # Mock the page object that gets returned
        mock_page = MagicMock()
        mock_page.object_list = []
        mock_page.number = 1
        mock_page.has_next.return_value = False
        mock_page.has_previous.return_value = False
        mock_paginator.page.return_value = mock_page
        
        result = PostService.search_posts('test', page=999, page_size=10)
        
        # Should fall back to last page
        self.assertIn('posts', result)
        self.assertIn('query', result)
        self.assertIn('pagination', result)
    
    def test_create_post_with_image_url_none(self):
        """Test create_post when image_url is explicitly None."""
        post_data = self.valid_post_data.copy()
        post_data['image_url'] = None
        
        post = PostService.create_post(post_data)
        
        self.assertIsNone(post.image_url)
        self.assertEqual(post.title, post_data['title'])
    
    def test_update_post_with_image_url_update(self):
        """Test update_post when image_url is updated."""
        post = Post.objects.create(**self.valid_post_data)
        
        update_data = {
            'image_url': 'https://example.com/new-image.jpg'
        }
        
        updated_post = PostService.update_post(post.id, update_data)
        
        self.assertEqual(updated_post.image_url, update_data['image_url'])


class ViewMissingCoverageTestCase(APITestCase):
    """Tests targeting missing coverage in views.py."""
    
    def setUp(self):
        """Set up test data."""
        self.valid_post_data = {
            'title': 'Test Post Title',
            'content': 'This is test content for the blog post.',
            'author': 'Test Author',
            'tags': 'test, django, python'
        }
        
        self.post = Post.objects.create(**self.valid_post_data)
    
    def test_list_view_pagination_links_edge_cases(self):
        """Test pagination link generation edge cases."""
        # Test when there's no next page
        response = self.client.get('/api/posts/?page=1&page_size=100')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIsNone(data['next'])  # No next page
        self.assertIsNone(data['previous'])  # No previous page
    
    def test_list_view_with_custom_page_size(self):
        """Test list view with custom page size parameter."""
        # Create more posts
        for i in range(5):
            Post.objects.create(
                title=f'Test Post {i}',
                content=f'Content for test post {i}',
                author='Test Author'
            )
        
        response = self.client.get('/api/posts/?page=1&page_size=3')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertEqual(data['page_size'], 3)
        self.assertEqual(len(data['results']), 3)
        self.assertIsNotNone(data['next'])
    
    def test_retrieve_view_with_valid_post(self):
        """Test retrieve view to ensure all code paths are covered."""
        response = self.client.get(f'/api/posts/{self.post.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.post.id)
        self.assertEqual(response.data['title'], self.post.title)
    
    def test_update_view_with_all_fields(self):
        """Test update view with all fields to cover all update paths."""
        update_data = {
            'title': 'Completely Updated Title',
            'content': 'Completely updated content for the post.',
            'author': 'Updated Author',
            'tags': 'updated, tags, test',
            'image_url': 'https://example.com/updated-image.jpg'
        }
        
        response = self.client.put(
            f'/api/posts/{self.post.id}/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify all fields were updated
        for field, value in update_data.items():
            self.assertEqual(response.data[field], value)
    
    def test_delete_view_success_path(self):
        """Test delete view success path to ensure coverage."""
        post_id = self.post.id
        
        response = self.client.delete(f'/api/posts/{post_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify post was deleted
        with self.assertRaises(Post.DoesNotExist):
            Post.objects.get(id=post_id)


class SerializerMissingCoverageTestCase(TestCase):
    """Tests targeting missing coverage in serializers.py."""
    
    def setUp(self):
        """Set up test data."""
        self.valid_post_data = {
            'title': 'Test Blog Post Title',
            'content': 'This is a test blog post content that is long enough to pass validation.',
            'author': 'Test Author',
            'tags': 'python, django, testing',
            'image_url': 'https://example.com/image.jpg'
        }
    
    def test_validate_image_url_with_whitespace_url(self):
        """Test validate_image_url with URL containing whitespace."""
        from posts.serializers import PostSerializer
        
        serializer = PostSerializer()
        
        # Test with URL that has whitespace
        url_with_whitespace = '  https://example.com/image.jpg  '
        result = serializer.validate_image_url(url_with_whitespace)
        
        self.assertEqual(result, 'https://example.com/image.jpg')
    
    def test_validate_tags_with_whitespace_only(self):
        """Test validate_tags with whitespace-only string."""
        from posts.serializers import PostSerializer
        
        serializer = PostSerializer()
        
        # Test with whitespace-only string
        result = serializer.validate_tags('   ')
        self.assertEqual(result, '')
    
    def test_create_method_coverage(self):
        """Test serializer create method."""
        from posts.serializers import PostSerializer
        
        serializer = PostSerializer(data=self.valid_post_data)
        self.assertTrue(serializer.is_valid())
        
        post = serializer.create(serializer.validated_data)
        
        self.assertIsInstance(post, Post)
        self.assertEqual(post.title, self.valid_post_data['title'])
    
    def test_update_method_coverage(self):
        """Test serializer update method."""
        from posts.serializers import PostSerializer
        
        # Create initial post
        post = Post.objects.create(**self.valid_post_data)
        
        # Update data
        update_data = {
            'title': 'Updated Title',
            'content': 'Updated content for the post.'
        }
        
        serializer = PostSerializer(post, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_post = serializer.update(post, serializer.validated_data)
        
        self.assertEqual(updated_post.title, update_data['title'])
        self.assertEqual(updated_post.content, update_data['content'])


class ExceptionHandlerMissingCoverageTestCase(TestCase):
    """Tests targeting missing coverage in exception handlers."""
    
    def test_get_error_message_with_different_exception_types(self):
        """Test _get_error_message with different exception types."""
        from common.exception_handlers import _get_error_message
        from rest_framework.exceptions import ValidationError as DRFValidationError
        
        # Test with exception having default_detail
        exc_with_default = DRFValidationError()
        message = _get_error_message(exc_with_default)
        self.assertIsInstance(message, str)
        
        # Test with exception having dict detail
        exc_with_dict = DRFValidationError({'field': ['error message']})
        message = _get_error_message(exc_with_dict)
        self.assertIn('Validation failed', message.lower())
        
        # Test with exception having list detail
        exc_with_list = DRFValidationError(['error1', 'error2'])
        message = _get_error_message(exc_with_list)
        self.assertEqual(message, 'error1; error2')
        
        # Test with exception having string detail
        exc_with_string = DRFValidationError('string error')
        message = _get_error_message(exc_with_string)
        self.assertEqual(message, 'string error')
        
        # Test with exception having no detail or default_detail
        exc_basic = Exception('basic error')
        message = _get_error_message(exc_basic)
        self.assertEqual(message, 'basic error')
    
    def test_handle_drf_exception_with_throttled(self):
        """Test DRF exception handler with Throttled exception."""
        from common.exception_handlers import _handle_drf_exception
        from rest_framework.exceptions import Throttled
        
        exc = Throttled(wait=60)
        response = _handle_drf_exception(exc, None)
        
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertTrue(response.data['error'])
        self.assertEqual(response.data['error_type'], 'throttled')
        self.assertIn('retry_after', response.data)
    
    def test_handle_drf_exception_with_method_not_allowed(self):
        """Test DRF exception handler with MethodNotAllowed exception."""
        from common.exception_handlers import _handle_drf_exception
        from rest_framework.exceptions import MethodNotAllowed
        
        exc = MethodNotAllowed('POST')
        exc.allowed_methods = ['GET', 'PUT']  # Set allowed methods as attribute
        response = _handle_drf_exception(exc, None)
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(response.data['error'])
        self.assertEqual(response.data['error_type'], 'method_not_allowed')
        self.assertIn('allowed_methods', response.data)
    
    def test_django_validation_error_with_messages(self):
        """Test Django ValidationError with messages attribute."""
        from common.exception_handlers import _handle_django_validation_error
        from django.core.exceptions import ValidationError as DjangoValidationError
        
        exc = DjangoValidationError(['Error message 1', 'Error message 2'])
        response = _handle_django_validation_error(exc, None)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data['error'])
        self.assertEqual(response.data['error_type'], 'validation_error')
        self.assertIn('field_errors', response.data)
        self.assertIn('non_field_errors', response.data['field_errors'])
    
    def test_django_validation_error_with_string(self):
        """Test Django ValidationError with simple string."""
        from common.exception_handlers import _handle_django_validation_error
        from django.core.exceptions import ValidationError as DjangoValidationError
        
        exc = DjangoValidationError('Simple error message')
        response = _handle_django_validation_error(exc, None)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data['error'])
        self.assertEqual(response.data['error_type'], 'validation_error')
        self.assertIn('field_errors', response.data)
        self.assertIn('non_field_errors', response.data['field_errors'])