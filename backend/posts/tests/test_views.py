"""
Comprehensive tests for Django REST Framework API views.
Tests all CRUD operations with success and error scenarios.
"""
import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

from posts.models import Post
from posts.services import PostService
from common.exceptions import PostNotFoundError, ValidationError, ServiceError


class PostListCreateViewTestCase(APITestCase):
    """
    Test cases for PostListCreateView (GET /api/posts/ and POST /api/posts/).
    """
    
    def setUp(self):
        """Set up test data and client."""
        self.client = APIClient()
        self.list_create_url = reverse('posts:post-list-create')
        
        # Create test posts
        self.post1 = Post.objects.create(
            title='First Test Post',
            content='This is the content of the first test post.',
            author='Test Author 1',
            tags='test, first'
        )
        self.post2 = Post.objects.create(
            title='Second Test Post',
            content='This is the content of the second test post.',
            author='Test Author 2',
            tags='test, second'
        )
        
        # Valid post data for creation tests
        self.valid_post_data = {
            'title': 'New Test Post',
            'content': 'This is a new test post content.',
            'author': 'New Test Author',
            'tags': 'new, test',
            'image_url': 'https://example.com/image.jpg'
        }
        
        # Invalid post data for validation tests
        self.invalid_post_data = {
            'title': '',  # Empty title
            'content': 'Short',  # Too short content
            'author': '',  # Empty author
        }
    
    def test_get_posts_list_success(self):
        """Test successful retrieval of posts list."""
        response = self.client.get(self.list_create_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertIn('total_pages', response.data)
        self.assertIn('current_page', response.data)
        self.assertEqual(len(response.data['results']), 2)
        
        # Check that posts are ordered by creation date (newest first)
        results = response.data['results']
        self.assertEqual(results[0]['title'], 'Second Test Post')
        self.assertEqual(results[1]['title'], 'First Test Post')
    
    def test_get_posts_list_with_pagination(self):
        """Test posts list with pagination parameters."""
        response = self.client.get(self.list_create_url, {'page': 1, 'page_size': 1})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['total_pages'], 2)
        self.assertEqual(response.data['current_page'], 1)
        self.assertEqual(response.data['page_size'], 1)
    
    def test_get_posts_list_empty(self):
        """Test posts list when no posts exist."""
        Post.objects.all().delete()
        
        response = self.client.get(self.list_create_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
        self.assertEqual(response.data['count'], 0)
    
    @patch('posts.views.PostService.get_all_posts')
    def test_get_posts_list_service_error(self, mock_get_all_posts):
        """Test posts list when service layer raises an error."""
        mock_get_all_posts.side_effect = ServiceError("Database connection failed")
        
        response = self.client.get(self.list_create_url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Failed to retrieve posts')
    
    def test_create_post_success(self):
        """Test successful post creation."""
        initial_count = Post.objects.count()
        
        response = self.client.post(
            self.list_create_url,
            data=json.dumps(self.valid_post_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), initial_count + 1)
        
        # Verify response data
        self.assertEqual(response.data['title'], self.valid_post_data['title'])
        self.assertEqual(response.data['content'], self.valid_post_data['content'])
        self.assertEqual(response.data['author'], self.valid_post_data['author'])
        self.assertIn('id', response.data)
        self.assertIn('created_at', response.data)
        self.assertIn('updated_at', response.data)
    
    def test_create_post_validation_error(self):
        """Test post creation with invalid data."""
        initial_count = Post.objects.count()
        
        response = self.client.post(
            self.list_create_url,
            data=json.dumps(self.invalid_post_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Post.objects.count(), initial_count)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Validation failed')
        self.assertIn('details', response.data)
    
    def test_create_post_missing_required_fields(self):
        """Test post creation with missing required fields."""
        incomplete_data = {'title': 'Test Title'}
        
        response = self.client.post(
            self.list_create_url,
            data=json.dumps(incomplete_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('details', response.data)
    
    @patch('posts.views.PostService.create_post')
    def test_create_post_service_error(self, mock_create_post):
        """Test post creation when service layer raises an error."""
        mock_create_post.side_effect = ServiceError("Database error")
        
        response = self.client.post(
            self.list_create_url,
            data=json.dumps(self.valid_post_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Failed to create post')


class PostRetrieveUpdateDestroyViewTestCase(APITestCase):
    """
    Test cases for PostRetrieveUpdateDestroyView (GET/PUT/DELETE /api/posts/{id}/).
    """
    
    def setUp(self):
        """Set up test data and client."""
        self.client = APIClient()
        
        # Create test post
        self.post = Post.objects.create(
            title='Test Post for Detail View',
            content='This is the content of the test post for detail operations.',
            author='Detail Test Author',
            tags='detail, test'
        )
        
        self.detail_url = reverse('posts:post-detail', kwargs={'pk': self.post.id})
        self.nonexistent_url = reverse('posts:post-detail', kwargs={'pk': 99999})
        
        # Valid update data
        self.valid_update_data = {
            'title': 'Updated Test Post',
            'content': 'This is the updated content of the test post.',
            'author': 'Updated Test Author',
            'tags': 'updated, test'
        }
        
        # Invalid update data
        self.invalid_update_data = {
            'title': '',  # Empty title
            'content': 'Short',  # Too short content
            'author': '',  # Empty author
        }
    
    def test_retrieve_post_success(self):
        """Test successful retrieval of a specific post."""
        response = self.client.get(self.detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.post.id)
        self.assertEqual(response.data['title'], self.post.title)
        self.assertEqual(response.data['content'], self.post.content)
        self.assertEqual(response.data['author'], self.post.author)
        self.assertIn('created_at', response.data)
        self.assertIn('updated_at', response.data)
    
    def test_retrieve_post_not_found(self):
        """Test retrieval of non-existent post."""
        response = self.client.get(self.nonexistent_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Post not found')
    
    def test_retrieve_post_invalid_id(self):
        """Test retrieval with invalid post ID."""
        response = self.client.get('/api/posts/invalid/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    @patch('posts.views.PostService.get_post_by_id')
    def test_retrieve_post_service_error(self, mock_get_post):
        """Test post retrieval when service layer raises an error."""
        mock_get_post.side_effect = ServiceError("Database error")
        
        response = self.client.get(self.detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Failed to retrieve post')
    
    def test_update_post_success(self):
        """Test successful post update."""
        response = self.client.put(
            self.detail_url,
            data=json.dumps(self.valid_update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.valid_update_data['title'])
        self.assertEqual(response.data['content'], self.valid_update_data['content'])
        self.assertEqual(response.data['author'], self.valid_update_data['author'])
        
        # Verify database was updated
        updated_post = Post.objects.get(id=self.post.id)
        self.assertEqual(updated_post.title, self.valid_update_data['title'])
        self.assertEqual(updated_post.content, self.valid_update_data['content'])
    
    def test_update_post_validation_error(self):
        """Test post update with invalid data."""
        response = self.client.put(
            self.detail_url,
            data=json.dumps(self.invalid_update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Validation failed')
        self.assertIn('details', response.data)
    
    def test_update_post_not_found(self):
        """Test update of non-existent post."""
        response = self.client.put(
            self.nonexistent_url,
            data=json.dumps(self.valid_update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Post not found')
    
    @patch('posts.views.PostService.update_post')
    def test_update_post_service_error(self, mock_update_post):
        """Test post update when service layer raises an error."""
        mock_update_post.side_effect = ServiceError("Database error")
        
        response = self.client.put(
            self.detail_url,
            data=json.dumps(self.valid_update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Failed to update post')
    
    def test_delete_post_success(self):
        """Test successful post deletion."""
        initial_count = Post.objects.count()
        
        response = self.client.delete(self.detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Post.objects.count(), initial_count - 1)
        
        # Verify post was deleted
        with self.assertRaises(Post.DoesNotExist):
            Post.objects.get(id=self.post.id)
    
    def test_delete_post_not_found(self):
        """Test deletion of non-existent post."""
        response = self.client.delete(self.nonexistent_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Post not found')
    
    @patch('posts.views.PostService.delete_post')
    def test_delete_post_service_error(self, mock_delete_post):
        """Test post deletion when service layer raises an error."""
        mock_delete_post.side_effect = ServiceError("Database error")
        
        response = self.client.delete(self.detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Failed to delete post')


class PostAPIIntegrationTestCase(APITestCase):
    """
    Integration tests for complete CRUD workflows.
    """
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
        self.list_create_url = reverse('posts:post-list-create')
    
    def test_complete_crud_workflow(self):
        """Test complete CRUD workflow: Create -> Read -> Update -> Delete."""
        # 1. Create a post
        post_data = {
            'title': 'Integration Test Post',
            'content': 'This is an integration test post content.',
            'author': 'Integration Test Author',
            'tags': 'integration, test'
        }
        
        create_response = self.client.post(
            self.list_create_url,
            data=json.dumps(post_data),
            content_type='application/json'
        )
        
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        post_id = create_response.data['id']
        
        # 2. Read the created post
        detail_url = reverse('posts:post-detail', kwargs={'pk': post_id})
        read_response = self.client.get(detail_url)
        
        self.assertEqual(read_response.status_code, status.HTTP_200_OK)
        self.assertEqual(read_response.data['title'], post_data['title'])
        
        # 3. Update the post
        update_data = {
            'title': 'Updated Integration Test Post',
            'content': 'This is the updated integration test post content.',
            'author': 'Updated Integration Test Author',
            'tags': 'updated, integration, test'
        }
        
        update_response = self.client.put(
            detail_url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data['title'], update_data['title'])
        
        # 4. Delete the post
        delete_response = self.client.delete(detail_url)
        
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        
        # 5. Verify post is deleted
        final_read_response = self.client.get(detail_url)
        self.assertEqual(final_read_response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_list_posts_after_operations(self):
        """Test that list endpoint reflects CRUD operations correctly."""
        # Initial state
        initial_response = self.client.get(self.list_create_url)
        initial_count = initial_response.data['count']
        
        # Create two posts
        for i in range(2):
            post_data = {
                'title': f'Test Post {i+1}',
                'content': f'This is test post {i+1} content.',
                'author': f'Test Author {i+1}',
                'tags': f'test, post{i+1}'
            }
            
            create_response = self.client.post(
                self.list_create_url,
                data=json.dumps(post_data),
                content_type='application/json'
            )
            self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        
        # Verify list shows new posts
        after_create_response = self.client.get(self.list_create_url)
        self.assertEqual(after_create_response.data['count'], initial_count + 2)
        
        # Delete one post
        post_id = after_create_response.data['results'][0]['id']
        detail_url = reverse('posts:post-detail', kwargs={'pk': post_id})
        delete_response = self.client.delete(detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify list reflects deletion
        after_delete_response = self.client.get(self.list_create_url)
        self.assertEqual(after_delete_response.data['count'], initial_count + 1)