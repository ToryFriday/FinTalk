"""
Integration tests to verify PostService works correctly with serializers.
"""
from django.test import TestCase
from posts.models import Post
from posts.services import PostService
from posts.serializers import PostSerializer
from common.exceptions import PostNotFoundError, ValidationError


class ServiceSerializerIntegrationTestCase(TestCase):
    """Test integration between PostService and PostSerializer."""
    
    def test_service_create_with_serializer_data(self):
        """Test that service can create posts with serializer-validated data."""
        # Simulate data coming from a serializer
        serializer_data = {
            'title': 'Integration Test Post',
            'content': 'This is content for integration testing.',
            'author': 'Integration Author',
            'tags': 'integration, test, django'
        }
        
        # Validate with serializer first
        serializer = PostSerializer(data=serializer_data)
        self.assertTrue(serializer.is_valid())
        
        # Create post using service with validated data
        post = PostService.create_post(serializer.validated_data)
        
        # Verify post was created correctly
        self.assertIsInstance(post, Post)
        self.assertEqual(post.title, serializer_data['title'])
        self.assertEqual(post.content, serializer_data['content'])
        self.assertEqual(post.author, serializer_data['author'])
        self.assertEqual(post.tags, serializer_data['tags'])
    
    def test_service_update_with_serializer_data(self):
        """Test that service can update posts with serializer-validated data."""
        # Create initial post
        post = PostService.create_post({
            'title': 'Original Title',
            'content': 'Original content for testing.',
            'author': 'Original Author'
        })
        
        # Update data through serializer
        update_data = {
            'title': 'Updated Integration Title',
            'content': 'Updated content for integration testing.'
        }
        
        serializer = PostSerializer(post, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        # Update using service
        updated_post = PostService.update_post(post.id, serializer.validated_data)
        
        # Verify update
        self.assertEqual(updated_post.title, update_data['title'])
        self.assertEqual(updated_post.content, update_data['content'])
        self.assertEqual(updated_post.author, 'Original Author')  # Unchanged
    
    def test_service_handles_serializer_validation_errors(self):
        """Test that service properly handles validation errors from serializer data."""
        # Invalid data that would fail serializer validation
        invalid_data = {
            'title': 'A',  # Too short
            'content': 'Short',  # Too short
            'author': ''  # Empty
        }
        
        # Service should handle this gracefully
        with self.assertRaises(ValidationError):
            PostService.create_post(invalid_data)
    
    def test_serializer_with_service_created_post(self):
        """Test that serializer works correctly with service-created posts."""
        # Create post using service
        post = PostService.create_post({
            'title': 'Service Created Post',
            'content': 'This post was created by the service layer.',
            'author': 'Service Author',
            'tags': 'service, test'
        })
        
        # Serialize the post
        serializer = PostSerializer(post)
        data = serializer.data
        
        # Verify serialized data
        self.assertEqual(data['title'], post.title)
        self.assertEqual(data['content'], post.content)
        self.assertEqual(data['author'], post.author)
        self.assertEqual(data['tags'], post.tags)
        self.assertIn('tags_list', data)
        self.assertEqual(data['tags_list'], ['service', 'test'])
        self.assertIn('id', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)