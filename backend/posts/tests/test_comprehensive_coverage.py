"""
Additional comprehensive tests to achieve 80%+ code coverage.
Tests edge cases, error scenarios, and missing functionality.
"""
import time
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from rest_framework.test import APITestCase
from rest_framework import status

from posts.models import Post
from posts.services import PostService
from posts.serializers import PostSerializer
from posts.views import PostListCreateView, PostRetrieveUpdateDestroyView
from common.exceptions import PostNotFoundError, ValidationError, ServiceError


class PostModelComprehensiveTestCase(TestCase):
    """Additional comprehensive tests for Post model."""
    
    def setUp(self):
        """Set up test data."""
        self.valid_post_data = {
            'title': 'Test Blog Post Title',
            'content': 'This is a test blog post content that is long enough to pass validation.',
            'author': 'Test Author',
            'tags': 'django, python, testing',
            'image_url': 'https://example.com/image.jpg'
        }
    
    def test_timestamps_auto_populated_with_delay(self):
        """Test that updated_at changes on save with proper delay."""
        post = Post.objects.create(**self.valid_post_data)
        
        self.assertIsNotNone(post.created_at)
        self.assertIsNotNone(post.updated_at)
        
        # Add a small delay to ensure timestamp difference
        time.sleep(0.01)
        
        # Test that updated_at changes on save
        original_updated_at = post.updated_at
        post.title = 'Updated Title'
        post.save()
        
        # Refresh from database to get updated timestamp
        post.refresh_from_db()
        self.assertGreater(post.updated_at, original_updated_at)
    
    def test_model_meta_attributes(self):
        """Test model Meta attributes."""
        self.assertEqual(Post._meta.db_table, 'blog_posts')
        self.assertEqual(Post._meta.ordering, ['-created_at'])
        
        # Check indexes exist
        index_names = [index.name for index in Post._meta.indexes]
        self.assertIn('posts_created_at_idx', index_names)
        self.assertIn('posts_author_idx', index_names)
        self.assertIn('posts_title_idx', index_names)
    
    def test_get_tags_list_with_various_formats(self):
        """Test get_tags_list with various tag formats."""
        test_cases = [
            ('tag1, tag2, tag3', ['tag1', 'tag2', 'tag3']),
            ('tag1,tag2,tag3', ['tag1', 'tag2', 'tag3']),
            ('  tag1  ,  tag2  ,  tag3  ', ['tag1', 'tag2', 'tag3']),
            ('single-tag', ['single-tag']),
            ('tag1, , tag2', ['tag1', 'tag2']),  # Empty tag filtered out
            ('', []),
            (None, []),
        ]
        
        for tags_input, expected_output in test_cases:
            post = Post(**self.valid_post_data)
            post.tags = tags_input or ''
            self.assertEqual(post.get_tags_list(), expected_output)
    
    def test_set_tags_from_list_with_various_inputs(self):
        """Test set_tags_from_list with various input types."""
        post = Post(**self.valid_post_data)
        
        # Test with strings
        post.set_tags_from_list(['tag1', 'tag2', 'tag3'])
        self.assertEqual(post.tags, 'tag1, tag2, tag3')
        
        # Test with mixed types
        post.set_tags_from_list(['tag1', 123, 'tag3'])
        self.assertEqual(post.tags, 'tag1, 123, tag3')
        
        # Test with empty strings in list
        post.set_tags_from_list(['tag1', '', 'tag3'])
        self.assertEqual(post.tags, 'tag1, tag3')
        
        # Test with None
        post.set_tags_from_list(None)
        self.assertEqual(post.tags, '')
    
    def test_clean_method_edge_cases(self):
        """Test clean method with edge cases."""
        # Test with None values
        post = Post()
        post.title = None
        post.content = None
        post.author = None
        
        with self.assertRaises(DjangoValidationError) as context:
            post.clean()
        
        errors = context.exception.error_dict
        self.assertIn('title', errors)
        self.assertIn('content', errors)
        self.assertIn('author', errors)
    
    def test_save_method_validation_bypass(self):
        """Test that save method calls full_clean."""
        post = Post(**self.valid_post_data)
        post.title = 'Hi'  # Too short
        
        with self.assertRaises(DjangoValidationError):
            post.save()


class PostSerializerComprehensiveTestCase(TestCase):
    """Additional comprehensive tests for PostSerializer."""
    
    def setUp(self):
        """Set up test data."""
        self.valid_post_data = {
            'title': 'Test Blog Post Title',
            'content': 'This is a test blog post content that is long enough to pass validation.',
            'author': 'Test Author',
            'tags': 'python, django, testing',
            'image_url': 'https://example.com/image.jpg'
        }
    
    def test_validate_methods_with_none_values(self):
        """Test individual validate methods with None values."""
        from rest_framework.exceptions import ValidationError as DRFValidationError
        serializer = PostSerializer()
        
        # Test validate_title with None
        with self.assertRaises(DRFValidationError):
            serializer.validate_title(None)
        
        # Test validate_content with None
        with self.assertRaises(DRFValidationError):
            serializer.validate_content(None)
        
        # Test validate_author with None
        with self.assertRaises(DRFValidationError):
            serializer.validate_author(None)
    
    def test_validate_image_url_edge_cases(self):
        """Test image_url validation with edge cases."""
        serializer = PostSerializer()
        
        # Test with empty string
        result = serializer.validate_image_url('')
        self.assertEqual(result, '')
        
        # Test with None
        result = serializer.validate_image_url(None)
        self.assertIsNone(result)
        
        # Test with whitespace
        result = serializer.validate_image_url('  https://example.com/image.jpg  ')
        self.assertEqual(result, 'https://example.com/image.jpg')
    
    def test_validate_tags_edge_cases(self):
        """Test tags validation with edge cases."""
        serializer = PostSerializer()
        
        # Test with None
        result = serializer.validate_tags(None)
        self.assertIsNone(result)
        
        # Test with empty string
        result = serializer.validate_tags('')
        self.assertEqual(result, '')
        
        # Test with whitespace only
        result = serializer.validate_tags('   ')
        self.assertEqual(result, '')
    
    def test_to_representation_edge_cases(self):
        """Test to_representation with edge cases."""
        # Create post with empty tags
        post = Post.objects.create(
            title='Test Post',
            content='Test content for representation.',
            author='Test Author',
            tags=''
        )
        
        serializer = PostSerializer(post)
        data = serializer.data
        
        self.assertIn('tags_list', data)
        self.assertEqual(data['tags_list'], [])
        
        # Test with None tags
        post.tags = None
        serializer = PostSerializer(post)
        data = serializer.data
        
        self.assertEqual(data['tags_list'], [])


class PostServiceComprehensiveTestCase(TestCase):
    """Additional comprehensive tests for PostService."""
    
    def setUp(self):
        """Set up test data."""
        self.valid_post_data = {
            'title': 'Test Post Title',
            'content': 'This is test content for the blog post.',
            'author': 'Test Author',
            'tags': 'test, django, python',
            'image_url': 'https://example.com/image.jpg'
        }
    
    def test_get_post_by_id_with_string_id(self):
        """Test get_post_by_id with string ID that can be converted."""
        post = Post.objects.create(**self.valid_post_data)
        
        # This should raise ServiceError for invalid ID type
        with self.assertRaises(ServiceError):
            PostService.get_post_by_id("not_a_number")
    
    def test_search_posts_case_insensitive(self):
        """Test that search is case insensitive."""
        Post.objects.create(
            title='Django Tutorial',
            content='Learn Django framework basics.',
            author='Tutorial Author'
        )
        
        # Search with different cases
        result1 = PostService.search_posts('django')
        result2 = PostService.search_posts('DJANGO')
        result3 = PostService.search_posts('Django')
        
        self.assertEqual(len(result1['posts']), 1)
        self.assertEqual(len(result2['posts']), 1)
        self.assertEqual(len(result3['posts']), 1)
    
    def test_search_posts_pagination_edge_cases(self):
        """Test search posts pagination with edge cases."""
        # Create test posts
        for i in range(5):
            Post.objects.create(
                title=f'Search Test Post {i}',
                content=f'Content for search test post {i}',
                author='Search Author'
            )
        
        # Test page beyond available pages
        result = PostService.search_posts('Search', page=10, page_size=2)
        
        # Should return last available page
        self.assertEqual(result['pagination']['current_page'], 3)  # Last page
        self.assertGreater(len(result['posts']), 0)
    
    def test_get_all_posts_pagination_edge_cases(self):
        """Test get_all_posts pagination with edge cases."""
        # Create test posts
        for i in range(3):
            Post.objects.create(
                title=f'Pagination Test Post {i}',
                content=f'Content for pagination test post {i}',
                author='Pagination Author'
            )
        
        # Test page beyond available pages
        result = PostService.get_all_posts(page=10, page_size=2)
        
        # Should return last available page
        self.assertEqual(result['pagination']['current_page'], 2)  # Last page
        self.assertGreater(len(result['posts']), 0)
    
    @patch('posts.services.logger')
    def test_service_methods_logging_coverage(self, mock_logger):
        """Test logging coverage for all service methods."""
        post = Post.objects.create(**self.valid_post_data)
        
        # Test all methods to ensure logging is called
        PostService.get_all_posts()
        mock_logger.info.assert_called()
        
        PostService.get_post_by_id(post.id)
        mock_logger.info.assert_called()
        
        PostService.create_post({
            'title': 'Logging Test',
            'content': 'Content for logging test.',
            'author': 'Logging Author'
        })
        mock_logger.info.assert_called()
        
        PostService.update_post(post.id, {'title': 'Updated for Logging'})
        mock_logger.info.assert_called()
        
        PostService.delete_post(post.id)
        mock_logger.info.assert_called()
        
        PostService.search_posts('test')
        mock_logger.info.assert_called()


class PostViewsComprehensiveTestCase(APITestCase):
    """Additional comprehensive tests for API views."""
    
    def setUp(self):
        """Set up test data."""
        self.valid_post_data = {
            'title': 'Test Post Title',
            'content': 'This is test content for the blog post.',
            'author': 'Test Author',
            'tags': 'test, django, python',
            'image_url': 'https://example.com/image.jpg'
        }
        
        self.post = Post.objects.create(**self.valid_post_data)
    
    def test_list_view_pagination_links(self):
        """Test pagination links in list view."""
        # Create more posts for pagination
        for i in range(15):
            Post.objects.create(
                title=f'Pagination Test Post {i}',
                content=f'Content for pagination test post {i}',
                author='Pagination Author'
            )
        
        # Test first page
        response = self.client.get('/api/posts/?page=1&page_size=5')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['current_page'], 1)
        self.assertEqual(data['page_size'], 5)
        
        # Test middle page
        response = self.client.get('/api/posts/?page=2&page_size=5')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIsNotNone(data['next'])
        self.assertIsNotNone(data['previous'])
        self.assertEqual(data['current_page'], 2)
    
    def test_create_view_with_partial_data(self):
        """Test create view with only required fields."""
        minimal_data = {
            'title': 'Minimal Test Post',
            'content': 'This is minimal content for testing.',
            'author': 'Minimal Author'
        }
        
        response = self.client.post(
            '/api/posts/',
            data=json.dumps(minimal_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], minimal_data['title'])
        self.assertEqual(response.data['tags'], '')
        self.assertIsNone(response.data['image_url'])
    
    def test_update_view_partial_update(self):
        """Test partial update functionality."""
        # For PUT requests, DRF requires all required fields, so we need to include them
        update_data = {
            'title': 'Partially Updated Title',
            'content': self.post.content,  # Keep existing content
            'author': self.post.author,    # Keep existing author
            'tags': 'updated, tags'        # Only change tags
        }
        
        response = self.client.put(
            f'/api/posts/{self.post.id}/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], update_data['title'])
        self.assertEqual(response.data['content'], self.post.content)  # Unchanged
        self.assertEqual(response.data['author'], self.post.author)  # Unchanged
        self.assertEqual(response.data['tags'], update_data['tags'])  # Changed
    
    def test_view_error_handling_with_invalid_json(self):
        """Test view error handling with malformed JSON."""
        response = self.client.post(
            '/api/posts/',
            data='{"invalid": json}',  # Malformed JSON
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data['error'])
        self.assertEqual(response.data['error_type'], 'parse_error')
    
    def test_view_method_not_allowed(self):
        """Test method not allowed error handling."""
        response = self.client.patch('/api/posts/')  # PATCH not allowed on list view
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(response.data['error'])
        self.assertEqual(response.data['error_type'], 'method_not_allowed')


class ExceptionHandlerComprehensiveTestCase(TestCase):
    """Additional tests for exception handler coverage."""
    
    def setUp(self):
        """Set up test data."""
        self.post = Post.objects.create(
            title='Exception Test Post',
            content='Content for exception testing.',
            author='Exception Author'
        )
    
    def test_integrity_error_handling(self):
        """Test IntegrityError handling in exception handler."""
        from common.exception_handlers import custom_exception_handler
        from django.db import IntegrityError
        
        exc = IntegrityError("Database constraint violation")
        context = {'request': None, 'view': None}
        
        response = custom_exception_handler(exc, context)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data['error'])
        self.assertEqual(response.data['error_type'], 'database_error')
    
    def test_django_validation_error_handling(self):
        """Test Django ValidationError handling."""
        from common.exception_handlers import custom_exception_handler
        from django.core.exceptions import ValidationError as DjangoValidationError
        
        exc = DjangoValidationError({'title': ['This field is required']})
        context = {'request': None, 'view': None}
        
        response = custom_exception_handler(exc, context)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data['error'])
        self.assertEqual(response.data['error_type'], 'validation_error')
        self.assertIn('field_errors', response.data)
    
    def test_exception_handler_logging_failure(self):
        """Test exception handler when logging fails."""
        from common.exception_handlers import _log_exception
        
        # Create a mock request that will cause logging to fail
        mock_request = MagicMock()
        mock_request.method = None  # This might cause issues in logging
        
        # This should not raise an exception even if logging fails
        try:
            _log_exception(Exception("Test exception"), mock_request, None)
        except Exception:
            self.fail("_log_exception should handle logging failures gracefully")


class ModelValidationComprehensiveTestCase(TestCase):
    """Comprehensive tests for model validation edge cases."""
    
    def test_model_validation_with_boundary_values(self):
        """Test model validation with boundary values."""
        # Test minimum valid lengths
        post_data = {
            'title': 'Valid',  # Exactly 5 characters
            'content': '1234567890',  # Exactly 10 characters
            'author': 'AB',  # Exactly 2 characters
            'tags': '',  # Empty is allowed
            'image_url': None  # None is allowed
        }
        
        post = Post(**post_data)
        post.full_clean()  # Should not raise ValidationError
        post.save()
        
        self.assertEqual(post.title, 'Valid')
        self.assertEqual(post.content, '1234567890')
        self.assertEqual(post.author, 'AB')
    
    def test_model_validation_with_maximum_lengths(self):
        """Test model validation with maximum allowed lengths."""
        post_data = {
            'title': 'A' * 200,  # Maximum title length
            'content': 'This is a very long content that should still be valid.',
            'author': 'B' * 100,  # Maximum author length
            'tags': 'C' * 500,  # Maximum tags length
        }
        
        post = Post(**post_data)
        post.full_clean()  # Should not raise ValidationError
        post.save()
        
        self.assertEqual(len(post.title), 200)
        self.assertEqual(len(post.author), 100)
        self.assertEqual(len(post.tags), 500)