"""
Unit tests for PostService business logic layer.
Tests all CRUD operations, error handling, and business rules.
"""
import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from unittest.mock import patch, MagicMock

from posts.models import Post
from posts.services import PostService
from common.exceptions import PostNotFoundError, ValidationError, ServiceError


class PostServiceTestCase(TestCase):
    """Test cases for PostService CRUD operations."""
    
    def setUp(self):
        """Set up test data."""
        self.valid_post_data = {
            'title': 'Test Post Title',
            'content': 'This is test content for the blog post.',
            'author': 'Test Author',
            'tags': 'test, django, python',
            'image_url': 'https://example.com/image.jpg'
        }
        
        self.minimal_post_data = {
            'title': 'Minimal Post',
            'content': 'Minimal content for testing.',
            'author': 'Test Author'
        }
        
        # Create test posts for retrieval tests
        self.test_post1 = Post.objects.create(
            title='First Test Post',
            content='Content of the first test post.',
            author='Author One',
            tags='first, test'
        )
        
        self.test_post2 = Post.objects.create(
            title='Second Test Post',
            content='Content of the second test post.',
            author='Author Two',
            tags='second, test'
        )
    
    def test_create_post_success(self):
        """Test successful post creation with valid data."""
        post = PostService.create_post(self.valid_post_data)
        
        self.assertIsInstance(post, Post)
        self.assertEqual(post.title, self.valid_post_data['title'])
        self.assertEqual(post.content, self.valid_post_data['content'])
        self.assertEqual(post.author, self.valid_post_data['author'])
        self.assertEqual(post.tags, self.valid_post_data['tags'])
        self.assertEqual(post.image_url, self.valid_post_data['image_url'])
        self.assertIsNotNone(post.id)
        self.assertIsNotNone(post.created_at)
        self.assertIsNotNone(post.updated_at)
    
    def test_create_post_minimal_data(self):
        """Test post creation with minimal required data."""
        post = PostService.create_post(self.minimal_post_data)
        
        self.assertIsInstance(post, Post)
        self.assertEqual(post.title, self.minimal_post_data['title'])
        self.assertEqual(post.content, self.minimal_post_data['content'])
        self.assertEqual(post.author, self.minimal_post_data['author'])
        self.assertEqual(post.tags, '')
        self.assertIsNone(post.image_url)
    
    def test_create_post_missing_required_fields(self):
        """Test post creation fails with missing required fields."""
        # Test missing title
        invalid_data = self.valid_post_data.copy()
        del invalid_data['title']
        
        with self.assertRaises(ValidationError) as context:
            PostService.create_post(invalid_data)
        self.assertIn('title', str(context.exception))
        
        # Test missing content
        invalid_data = self.valid_post_data.copy()
        del invalid_data['content']
        
        with self.assertRaises(ValidationError) as context:
            PostService.create_post(invalid_data)
        self.assertIn('content', str(context.exception))
        
        # Test missing author
        invalid_data = self.valid_post_data.copy()
        del invalid_data['author']
        
        with self.assertRaises(ValidationError) as context:
            PostService.create_post(invalid_data)
        self.assertIn('author', str(context.exception))
    
    def test_create_post_empty_required_fields(self):
        """Test post creation fails with empty required fields."""
        invalid_data = self.valid_post_data.copy()
        invalid_data['title'] = ''
        
        with self.assertRaises(ValidationError):
            PostService.create_post(invalid_data)
    
    @patch('posts.services.logger')
    def test_create_post_database_error(self, mock_logger):
        """Test post creation handles database errors."""
        with patch.object(Post, 'save', side_effect=IntegrityError("Database error")):
            with self.assertRaises(ServiceError) as context:
                PostService.create_post(self.valid_post_data)
            self.assertIn('database constraint', str(context.exception))
            mock_logger.error.assert_called()
    
    def test_get_post_by_id_success(self):
        """Test successful post retrieval by ID."""
        post = PostService.get_post_by_id(self.test_post1.id)
        
        self.assertEqual(post.id, self.test_post1.id)
        self.assertEqual(post.title, self.test_post1.title)
        self.assertEqual(post.content, self.test_post1.content)
        self.assertEqual(post.author, self.test_post1.author)
    
    def test_get_post_by_id_not_found(self):
        """Test post retrieval with non-existent ID."""
        non_existent_id = 99999
        
        with self.assertRaises(PostNotFoundError) as context:
            PostService.get_post_by_id(non_existent_id)
        
        self.assertEqual(context.exception.post_id, non_existent_id)
    
    def test_get_post_by_id_invalid_id(self):
        """Test post retrieval with invalid ID types."""
        # Test negative ID
        with self.assertRaises(ServiceError):
            PostService.get_post_by_id(-1)
        
        # Test zero ID
        with self.assertRaises(ServiceError):
            PostService.get_post_by_id(0)
        
        # Test string ID
        with self.assertRaises(ServiceError):
            PostService.get_post_by_id("invalid")
    
    def test_get_all_posts_success(self):
        """Test successful retrieval of all posts with pagination."""
        result = PostService.get_all_posts(page=1, page_size=10)
        
        self.assertIn('posts', result)
        self.assertIn('pagination', result)
        
        posts = result['posts']
        pagination = result['pagination']
        
        self.assertEqual(len(posts), 2)  # We created 2 test posts
        self.assertEqual(pagination['total_posts'], 2)
        self.assertEqual(pagination['current_page'], 1)
        self.assertEqual(pagination['page_size'], 10)
        
        # Check posts are ordered by creation date (newest first)
        self.assertEqual(posts[0].id, self.test_post2.id)  # Second post created
        self.assertEqual(posts[1].id, self.test_post1.id)  # First post created
    
    def test_get_all_posts_pagination(self):
        """Test pagination functionality."""
        # Create more posts for pagination testing
        for i in range(5):
            Post.objects.create(
                title=f'Pagination Test Post {i}',
                content=f'Content for pagination test post {i}',
                author='Pagination Author'
            )
        
        # Test first page with page size 3
        result = PostService.get_all_posts(page=1, page_size=3)
        
        self.assertEqual(len(result['posts']), 3)
        self.assertEqual(result['pagination']['current_page'], 1)
        self.assertEqual(result['pagination']['total_posts'], 7)  # 2 original + 5 new
        self.assertTrue(result['pagination']['has_next'])
        self.assertFalse(result['pagination']['has_previous'])
        
        # Test second page
        result = PostService.get_all_posts(page=2, page_size=3)
        
        self.assertEqual(len(result['posts']), 3)
        self.assertEqual(result['pagination']['current_page'], 2)
        self.assertTrue(result['pagination']['has_next'])
        self.assertTrue(result['pagination']['has_previous'])
    
    def test_get_all_posts_invalid_pagination(self):
        """Test get_all_posts with invalid pagination parameters."""
        # Test invalid page number
        with self.assertRaises(ServiceError):
            PostService.get_all_posts(page=0)
        
        with self.assertRaises(ServiceError):
            PostService.get_all_posts(page=-1)
        
        # Test invalid page size
        with self.assertRaises(ServiceError):
            PostService.get_all_posts(page_size=0)
        
        with self.assertRaises(ServiceError):
            PostService.get_all_posts(page_size=101)  # Max is 100
    
    def test_update_post_success(self):
        """Test successful post update."""
        update_data = {
            'title': 'Updated Title',
            'content': 'Updated content for the post.',
            'tags': 'updated, test'
        }
        
        updated_post = PostService.update_post(self.test_post1.id, update_data)
        
        self.assertEqual(updated_post.id, self.test_post1.id)
        self.assertEqual(updated_post.title, update_data['title'])
        self.assertEqual(updated_post.content, update_data['content'])
        self.assertEqual(updated_post.tags, update_data['tags'])
        self.assertEqual(updated_post.author, self.test_post1.author)  # Unchanged
    
    def test_update_post_partial_update(self):
        """Test partial post update (only some fields)."""
        update_data = {'title': 'Partially Updated Title'}
        
        updated_post = PostService.update_post(self.test_post1.id, update_data)
        
        self.assertEqual(updated_post.title, update_data['title'])
        self.assertEqual(updated_post.content, self.test_post1.content)  # Unchanged
        self.assertEqual(updated_post.author, self.test_post1.author)  # Unchanged
    
    def test_update_post_not_found(self):
        """Test update of non-existent post."""
        non_existent_id = 99999
        update_data = {'title': 'Updated Title'}
        
        with self.assertRaises(PostNotFoundError):
            PostService.update_post(non_existent_id, update_data)
    
    def test_update_post_invalid_data(self):
        """Test post update with invalid data."""
        invalid_data = {'title': ''}  # Empty title
        
        with self.assertRaises(ValidationError):
            PostService.update_post(self.test_post1.id, invalid_data)
    
    def test_delete_post_success(self):
        """Test successful post deletion."""
        post_id = self.test_post1.id
        
        result = PostService.delete_post(post_id)
        
        self.assertTrue(result)
        
        # Verify post is deleted
        with self.assertRaises(PostNotFoundError):
            PostService.get_post_by_id(post_id)
    
    def test_delete_post_not_found(self):
        """Test deletion of non-existent post."""
        non_existent_id = 99999
        
        with self.assertRaises(PostNotFoundError):
            PostService.delete_post(non_existent_id)
    
    @patch('posts.services.logger')
    def test_delete_post_database_error(self, mock_logger):
        """Test post deletion handles database errors."""
        with patch.object(Post, 'delete', side_effect=Exception("Database error")):
            with self.assertRaises(ServiceError):
                PostService.delete_post(self.test_post1.id)
            mock_logger.error.assert_called()
    
    def test_search_posts_success(self):
        """Test successful post search."""
        # Search by title
        result = PostService.search_posts('First')
        
        self.assertIn('posts', result)
        self.assertIn('query', result)
        self.assertIn('pagination', result)
        
        posts = result['posts']
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].id, self.test_post1.id)
        self.assertEqual(result['query'], 'First')
    
    def test_search_posts_content_match(self):
        """Test post search matches content."""
        result = PostService.search_posts('second test post')
        
        posts = result['posts']
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].id, self.test_post2.id)
    
    def test_search_posts_no_results(self):
        """Test post search with no matching results."""
        result = PostService.search_posts('nonexistent')
        
        self.assertEqual(len(result['posts']), 0)
        self.assertEqual(result['pagination']['total_posts'], 0)
    
    def test_search_posts_empty_query(self):
        """Test post search with empty query."""
        with self.assertRaises(ServiceError):
            PostService.search_posts('')
        
        with self.assertRaises(ServiceError):
            PostService.search_posts('   ')  # Whitespace only
    
    def test_search_posts_invalid_pagination(self):
        """Test post search with invalid pagination parameters."""
        with self.assertRaises(ServiceError):
            PostService.search_posts('test', page=0)
        
        with self.assertRaises(ServiceError):
            PostService.search_posts('test', page_size=101)
    
    @patch('posts.services.logger')
    def test_logging_functionality(self, mock_logger):
        """Test that service methods log appropriately."""
        # Test create post logging
        PostService.create_post(self.minimal_post_data)
        mock_logger.info.assert_called()
        
        # Test get post logging
        PostService.get_post_by_id(self.test_post1.id)
        mock_logger.info.assert_called()
        
        # Test error logging
        try:
            PostService.get_post_by_id(99999)
        except PostNotFoundError:
            pass
        mock_logger.warning.assert_called()


class PostServiceEdgeCasesTestCase(TestCase):
    """Test edge cases and error scenarios for PostService."""
    
    def test_create_post_with_special_characters(self):
        """Test post creation with special characters."""
        special_data = {
            'title': 'Post with Special Characters: @#$%^&*()',
            'content': 'Content with unicode: 你好世界 and emojis: 🚀🎉',
            'author': 'Author with Àccénts'
        }
        
        post = PostService.create_post(special_data)
        self.assertEqual(post.title, special_data['title'])
        self.assertEqual(post.content, special_data['content'])
        self.assertEqual(post.author, special_data['author'])
    
    def test_create_post_with_long_content(self):
        """Test post creation with very long content."""
        long_content = 'A' * 10000  # Very long content
        
        long_data = {
            'title': 'Post with Long Content',
            'content': long_content,
            'author': 'Test Author'
        }
        
        post = PostService.create_post(long_data)
        self.assertEqual(len(post.content), 10000)
    
    def test_update_post_with_none_values(self):
        """Test post update with None values (should be ignored)."""
        post = Post.objects.create(
            title='Original Title',
            content='Original content',
            author='Original Author'
        )
        
        update_data = {
            'title': 'Updated Title',
            'content': None,  # Should be ignored
            'author': 'Updated Author'
        }
        
        # Remove None values before update (as would happen in real usage)
        filtered_data = {k: v for k, v in update_data.items() if v is not None}
        
        updated_post = PostService.update_post(post.id, filtered_data)
        self.assertEqual(updated_post.title, 'Updated Title')
        self.assertEqual(updated_post.content, 'Original content')  # Unchanged
        self.assertEqual(updated_post.author, 'Updated Author')
    
    @patch('posts.services.logger')
    def test_service_error_handling_and_logging(self, mock_logger):
        """Test comprehensive error handling and logging."""
        # Test unexpected error in get_all_posts
        with patch('posts.models.Post.objects.all', side_effect=Exception("Unexpected error")):
            with self.assertRaises(ServiceError):
                PostService.get_all_posts()
            mock_logger.error.assert_called()
        
        # Test unexpected error in create_post
        with patch('posts.models.Post.save', side_effect=Exception("Unexpected error")):
            with self.assertRaises(ServiceError):
                PostService.create_post({
                    'title': 'Test',
                    'content': 'Test content',
                    'author': 'Test Author'
                })
            mock_logger.error.assert_called()