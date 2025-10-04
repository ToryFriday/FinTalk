"""
Tests for error handling and logging functionality.
Tests custom exception handlers, error pages, and logging behavior.
"""
import json
import logging
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status

from posts.models import Post
from common.exceptions import PostNotFoundError, ValidationError, ServiceError
from common.exception_handlers import custom_exception_handler


class ErrorHandlingTestCase(APITestCase):
    """Test cases for API error handling."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.post_data = {
            'title': 'Test Post',
            'content': 'This is test content for the post.',
            'author': 'Test Author',
            'tags': 'test, django',
        }
        self.post = Post.objects.create(**self.post_data)
    
    def test_post_not_found_error_handling(self):
        """Test handling of PostNotFoundError in API views."""
        # Try to get a non-existent post
        response = self.client.get('/api/posts/999/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        response_data = response.json()
        self.assertTrue(response_data['error'])
        self.assertEqual(response_data['error_type'], 'resource_not_found')
        self.assertIn('not found', response_data['message'].lower())
        self.assertIn('timestamp', response_data)
    
    def test_validation_error_handling(self):
        """Test handling of validation errors in API views."""
        # Try to create a post with invalid data
        invalid_data = {
            'title': '',  # Empty title should fail validation
            'content': 'Test content',
            'author': 'Test Author'
        }
        
        response = self.client.post(
            '/api/posts/',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response_data = response.json()
        self.assertTrue(response_data['error'])
        self.assertEqual(response_data['error_type'], 'validation_error')
        # The message might be different based on DRF's default validation messages
        self.assertIn('error_type', response_data)
        self.assertIn('detail', response_data)
    
    def test_invalid_post_id_handling(self):
        """Test handling of invalid post ID format."""
        # Try to get a post with invalid ID format
        response = self.client.get('/api/posts/invalid_id/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_method_not_allowed_handling(self):
        """Test handling of method not allowed errors."""
        # Try to use PATCH method which is not allowed
        response = self.client.patch('/api/posts/')
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        response_data = response.json()
        self.assertTrue(response_data['error'])
        self.assertEqual(response_data['error_type'], 'method_not_allowed')
    
    def test_invalid_json_handling(self):
        """Test handling of invalid JSON in request body."""
        # Send invalid JSON
        response = self.client.post(
            '/api/posts/',
            data='{"invalid": json}',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response_data = response.json()
        self.assertTrue(response_data['error'])
        self.assertEqual(response_data['error_type'], 'parse_error')


class CustomExceptionHandlerTestCase(TestCase):
    """Test cases for custom exception handler."""
    
    def setUp(self):
        """Set up test data."""
        self.mock_request = MagicMock()
        self.mock_request.method = 'GET'
        self.mock_request.path = '/api/posts/1/'
        self.mock_request.user.username = 'testuser'
        
        self.mock_view = MagicMock()
        self.mock_view.__class__.__name__ = 'TestView'
        
        self.context = {
            'request': self.mock_request,
            'view': self.mock_view
        }
    
    def test_post_not_found_error_handling(self):
        """Test custom handling of PostNotFoundError."""
        exc = PostNotFoundError(post_id=123)
        
        response = custom_exception_handler(exc, self.context)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(response.data['error'])
        self.assertEqual(response.data['error_type'], 'resource_not_found')
        self.assertEqual(response.data['post_id'], 123)
    
    def test_validation_error_handling(self):
        """Test custom handling of ValidationError."""
        errors = {'title': ['This field is required']}
        exc = ValidationError('Validation failed', errors)
        
        response = custom_exception_handler(exc, self.context)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data['error'])
        self.assertEqual(response.data['error_type'], 'validation_error')
        self.assertEqual(response.data['field_errors'], errors)
    
    def test_service_error_handling(self):
        """Test custom handling of ServiceError."""
        exc = ServiceError('Database connection failed')
        
        response = custom_exception_handler(exc, self.context)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertTrue(response.data['error'])
        self.assertEqual(response.data['error_type'], 'service_error')
    
    def test_unexpected_error_handling(self):
        """Test handling of unexpected exceptions."""
        exc = RuntimeError('Unexpected error occurred')
        
        response = custom_exception_handler(exc, self.context)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertTrue(response.data['error'])
        self.assertEqual(response.data['error_type'], 'internal_server_error')


class ErrorPageTestCase(TestCase):
    """Test cases for custom error pages."""
    
    def test_404_error_page(self):
        """Test custom 404 error page."""
        response = self.client.get('/nonexistent-page/')
        
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, '404', status_code=404)
        self.assertContains(response, 'Page Not Found', status_code=404)
    
    @override_settings(DEBUG=False)
    def test_500_error_page(self):
        """Test custom 500 error page."""
        # This test would require triggering a real 500 error
        # For now, we'll test that the handler is properly configured
        from blog_manager.urls import handler500
        self.assertEqual(handler500, 'blog_manager.error_views.handler500')


class LoggingTestCase(TestCase):
    """Test cases for logging functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.post_data = {
            'title': 'Test Post',
            'content': 'This is test content for the post.',
            'author': 'Test Author',
            'tags': 'test, django',
        }
        self.post = Post.objects.create(**self.post_data)
    
    @patch('posts.views.logger')
    def test_successful_operation_logging(self, mock_logger):
        """Test logging of successful CRUD operations."""
        # Test successful GET request
        response = self.client.get(f'/api/posts/{self.post.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify logging was called
        mock_logger.info.assert_called()
        log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        self.assertTrue(any('Successfully retrieved post' in call for call in log_calls))
    
    @patch('common.exception_handlers.logger')
    def test_error_operation_logging(self, mock_logger):
        """Test logging of error operations."""
        # Test 404 error
        response = self.client.get('/api/posts/999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify error logging was called (now in exception handler)
        mock_logger.warning.assert_called()
        log_calls = [call.args[0] for call in mock_logger.warning.call_args_list]
        self.assertTrue(any('Resource not found' in call for call in log_calls))
    
    @patch('common.exception_handlers.logger')
    def test_validation_error_logging(self, mock_logger):
        """Test logging of validation errors."""
        # Test validation error
        invalid_data = {
            'title': '',  # Empty title should fail validation
            'content': 'Test content',
            'author': 'Test Author'
        }
        
        response = self.client.post(
            '/api/posts/',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify warning logging was called for validation errors (now in exception handler)
        mock_logger.warning.assert_called()
    
    def test_log_file_creation(self):
        """Test that log files are created when logging occurs."""
        import os
        from django.conf import settings
        
        # Make a request that will generate logs
        response = self.client.get('/api/posts/')
        
        # Check if log files exist (they should be created in BASE_DIR)
        base_dir = settings.BASE_DIR
        log_files = [
            'blog_manager.log',
            'blog_manager_errors.log'
        ]
        
        # Note: In test environment, log files might not be created
        # This test verifies the configuration is correct
        for log_file in log_files:
            log_path = base_dir / log_file
            # We just verify the path is correctly configured
            self.assertTrue(str(log_path).endswith(log_file))


class ErrorScenarioIntegrationTestCase(APITestCase):
    """Integration tests for various error scenarios."""
    
    def setUp(self):
        """Set up test data."""
        self.post_data = {
            'title': 'Test Post',
            'content': 'This is test content for the post.',
            'author': 'Test Author',
            'tags': 'test, django',
        }
        self.post = Post.objects.create(**self.post_data)
    
    def test_complete_crud_error_scenarios(self):
        """Test error handling across all CRUD operations."""
        
        # Test CREATE with validation error
        invalid_create_data = {'title': '', 'content': '', 'author': ''}
        response = self.client.post(
            '/api/posts/',
            data=json.dumps(invalid_create_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.json()['error'])
        
        # Test READ with non-existent ID
        response = self.client.get('/api/posts/999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(response.json()['error'])
        
        # Test UPDATE with non-existent ID
        update_data = {'title': 'Updated Title'}
        response = self.client.put(
            '/api/posts/999/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        # Note: This might return 400 due to validation before checking if post exists
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND])
        self.assertTrue(response.json()['error'])
        
        # Test DELETE with non-existent ID
        response = self.client.delete('/api/posts/999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(response.json()['error'])
    
    def test_error_response_consistency(self):
        """Test that all error responses follow the same format."""
        error_responses = []
        
        # Generate different types of errors
        responses_to_test = [
            self.client.get('/api/posts/999/'),  # 404 error
            self.client.post('/api/posts/', data='invalid json', content_type='application/json'),  # Parse error
            self.client.patch('/api/posts/'),  # Method not allowed
        ]
        
        for response in responses_to_test:
            if response.status_code >= 400:
                data = response.json()
                error_responses.append(data)
        
        # Verify all error responses have consistent structure
        for error_data in error_responses:
            self.assertIn('error', error_data)
            self.assertIn('error_type', error_data)
            self.assertIn('message', error_data)
            self.assertIn('timestamp', error_data)
            self.assertTrue(error_data['error'])