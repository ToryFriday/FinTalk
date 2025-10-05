"""
Tests for saved articles functionality.
"""

import json
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from posts.models import Post
from accounts.models import SavedArticle, UserProfile, Role, UserRole


class SavedArticleModelTest(TestCase):
    """Test cases for SavedArticle model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Test Post',
            content='This is a test post content.',
            author='Test Author',
            author_user=self.user,
            status='published'
        )
    
    def test_create_saved_article(self):
        """Test creating a saved article."""
        saved_article = SavedArticle.objects.create(
            user=self.user,
            post=self.post,
            notes='Interesting article'
        )
        
        self.assertEqual(saved_article.user, self.user)
        self.assertEqual(saved_article.post, self.post)
        self.assertEqual(saved_article.notes, 'Interesting article')
        self.assertIsNotNone(saved_article.saved_at)
    
    def test_saved_article_str_representation(self):
        """Test string representation of SavedArticle."""
        saved_article = SavedArticle.objects.create(
            user=self.user,
            post=self.post
        )
        
        expected_str = f"{self.user.username} saved '{self.post.title}'"
        self.assertEqual(str(saved_article), expected_str)
    
    def test_unique_constraint(self):
        """Test that user cannot save the same post twice."""
        SavedArticle.objects.create(user=self.user, post=self.post)
        
        with self.assertRaises(Exception):
            SavedArticle.objects.create(user=self.user, post=self.post)
    
    def test_notes_validation(self):
        """Test notes field validation."""
        # Test with valid notes
        saved_article = SavedArticle(
            user=self.user,
            post=self.post,
            notes='A' * 500  # Max length
        )
        saved_article.full_clean()  # Should not raise
        
        # Test with notes too long
        saved_article.notes = 'A' * 501
        with self.assertRaises(Exception):
            saved_article.full_clean()
    
    def test_cascade_delete_user(self):
        """Test that saved articles are deleted when user is deleted."""
        saved_article = SavedArticle.objects.create(user=self.user, post=self.post)
        
        self.user.delete()
        
        self.assertFalse(SavedArticle.objects.filter(id=saved_article.id).exists())
    
    def test_cascade_delete_post(self):
        """Test that saved articles are deleted when post is deleted."""
        saved_article = SavedArticle.objects.create(user=self.user, post=self.post)
        
        self.post.delete()
        
        self.assertFalse(SavedArticle.objects.filter(id=saved_article.id).exists())


class SavePostViewTest(APITestCase):
    """Test cases for SavePostView API endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Test Post',
            content='This is a test post content.',
            author='Test Author',
            author_user=self.user,
            status='published'
        )
        self.draft_post = Post.objects.create(
            title='Draft Post',
            content='This is a draft post content.',
            author='Test Author',
            author_user=self.user,
            status='draft'
        )
        
        # Create reader role and assign to user
        reader_role, _ = Role.objects.get_or_create(
            name='reader',
            defaults={'display_name': 'Reader', 'description': 'Can read posts'}
        )
        UserRole.objects.create(user=self.user, role=reader_role)
        UserRole.objects.create(user=self.other_user, role=reader_role)
    
    def test_save_post_success(self):
        """Test successfully saving a post."""
        self.client.force_authenticate(user=self.user)
        url = reverse('posts:save-post', kwargs={'pk': self.post.pk})
        
        response = self.client.post(url, {'notes': 'Great article!'})
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('saved_article', response.data)
        
        # Verify saved article was created
        saved_article = SavedArticle.objects.get(user=self.user, post=self.post)
        self.assertEqual(saved_article.notes, 'Great article!')
    
    def test_save_post_already_saved(self):
        """Test saving a post that is already saved."""
        SavedArticle.objects.create(user=self.user, post=self.post)
        
        self.client.force_authenticate(user=self.user)
        url = reverse('posts:save-post', kwargs={'pk': self.post.pk})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Article is already saved', response.data['message'])
    
    def test_save_draft_post_fails(self):
        """Test that draft posts cannot be saved."""
        self.client.force_authenticate(user=self.user)
        url = reverse('posts:save-post', kwargs={'pk': self.draft_post.pk})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Only published posts can be saved', response.data['error'])
    
    def test_save_post_unauthenticated(self):
        """Test that unauthenticated users cannot save posts."""
        url = reverse('posts:save-post', kwargs={'pk': self.post.pk})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_save_nonexistent_post(self):
        """Test saving a non-existent post."""
        self.client.force_authenticate(user=self.user)
        url = reverse('posts:save-post', kwargs={'pk': 9999})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_unsave_post_success(self):
        """Test successfully unsaving a post."""
        SavedArticle.objects.create(user=self.user, post=self.post)
        
        self.client.force_authenticate(user=self.user)
        url = reverse('posts:save-post', kwargs={'pk': self.post.pk})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Article unsaved successfully', response.data['message'])
        
        # Verify saved article was deleted
        self.assertFalse(SavedArticle.objects.filter(user=self.user, post=self.post).exists())
    
    def test_unsave_post_not_saved(self):
        """Test unsaving a post that is not saved."""
        self.client.force_authenticate(user=self.user)
        url = reverse('posts:save-post', kwargs={'pk': self.post.pk})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Article is not saved', response.data['error'])


class CheckArticleSavedViewTest(APITestCase):
    """Test cases for check_article_saved API endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Test Post',
            content='This is a test post content.',
            author='Test Author',
            author_user=self.user,
            status='published'
        )
        
        # Create reader role and assign to user
        reader_role, _ = Role.objects.get_or_create(
            name='reader',
            defaults={'display_name': 'Reader', 'description': 'Can read posts'}
        )
        UserRole.objects.create(user=self.user, role=reader_role)
    
    def test_check_saved_post(self):
        """Test checking if a saved post is saved."""
        saved_article = SavedArticle.objects.create(
            user=self.user, 
            post=self.post,
            notes='Test notes'
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('posts:check-article-saved', kwargs={'pk': self.post.pk})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['post_id'], self.post.pk)
        self.assertTrue(response.data['is_saved'])
        self.assertIsNotNone(response.data['saved_article'])
        self.assertEqual(response.data['saved_article']['id'], saved_article.id)
        self.assertEqual(response.data['saved_article']['notes'], 'Test notes')
    
    def test_check_unsaved_post(self):
        """Test checking if an unsaved post is saved."""
        self.client.force_authenticate(user=self.user)
        url = reverse('posts:check-article-saved', kwargs={'pk': self.post.pk})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['post_id'], self.post.pk)
        self.assertFalse(response.data['is_saved'])
        self.assertIsNone(response.data['saved_article'])
    
    def test_check_saved_unauthenticated(self):
        """Test that unauthenticated users cannot check saved status."""
        url = reverse('posts:check-article-saved', kwargs={'pk': self.post.pk})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SavedPostsViewTest(APITestCase):
    """Test cases for SavedPostsView API endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        # Create posts
        self.post1 = Post.objects.create(
            title='First Post',
            content='Content of first post.',
            author='Author One',
            author_user=self.user,
            status='published',
            tags='tech, programming'
        )
        self.post2 = Post.objects.create(
            title='Second Post',
            content='Content of second post.',
            author='Author Two',
            author_user=self.other_user,
            status='published',
            tags='design, ui'
        )
        
        # Create saved articles
        self.saved1 = SavedArticle.objects.create(
            user=self.user,
            post=self.post1,
            notes='Interesting tech article'
        )
        self.saved2 = SavedArticle.objects.create(
            user=self.user,
            post=self.post2,
            notes='Good design tips'
        )
        
        # Create saved article for other user (should not appear in results)
        SavedArticle.objects.create(user=self.other_user, post=self.post1)
        
        # Create reader role and assign to users
        reader_role, _ = Role.objects.get_or_create(
            name='reader',
            defaults={'display_name': 'Reader', 'description': 'Can read posts'}
        )
        UserRole.objects.create(user=self.user, role=reader_role)
        UserRole.objects.create(user=self.other_user, role=reader_role)
    
    def test_get_saved_posts(self):
        """Test getting saved posts for authenticated user."""
        self.client.force_authenticate(user=self.user)
        url = reverse('posts:saved-posts')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)
        
        # Check that only user's saved articles are returned
        post_ids = [item['post'] for item in response.data['results']]
        self.assertIn(self.post1.id, post_ids)
        self.assertIn(self.post2.id, post_ids)
        
        # Check metadata
        self.assertEqual(response.data['metadata']['total_saved'], 2)
    
    def test_search_saved_posts(self):
        """Test searching saved posts."""
        self.client.force_authenticate(user=self.user)
        url = reverse('posts:saved-posts')
        
        response = self.client.get(url, {'search': 'tech'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['post_title'], 'First Post')
    
    def test_filter_by_tag(self):
        """Test filtering saved posts by tag."""
        self.client.force_authenticate(user=self.user)
        url = reverse('posts:saved-posts')
        
        response = self.client.get(url, {'tag': 'design'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['post_title'], 'Second Post')
    
    def test_filter_by_author(self):
        """Test filtering saved posts by author."""
        self.client.force_authenticate(user=self.user)
        url = reverse('posts:saved-posts')
        
        response = self.client.get(url, {'author': 'Author One'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['post_title'], 'First Post')
    
    def test_ordering_saved_posts(self):
        """Test ordering saved posts."""
        self.client.force_authenticate(user=self.user)
        url = reverse('posts:saved-posts')
        
        response = self.client.get(url, {'ordering': 'post__title'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [item['post_title'] for item in response.data['results']]
        self.assertEqual(titles, ['First Post', 'Second Post'])
    
    def test_saved_posts_unauthenticated(self):
        """Test that unauthenticated users cannot access saved posts."""
        url = reverse('posts:saved-posts')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_empty_saved_posts(self):
        """Test getting saved posts when user has none."""
        # Create new user with no saved articles
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='testpass123'
        )
        
        self.client.force_authenticate(user=new_user)
        url = reverse('posts:saved-posts')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(len(response.data['results']), 0)
        self.assertEqual(response.data['metadata']['total_saved'], 0)


class SavedArticleIntegrationTest(APITestCase):
    """Integration tests for saved articles functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Integration Test Post',
            content='This is an integration test post.',
            author='Test Author',
            author_user=self.user,
            status='published'
        )
        
        # Create reader role and assign to user
        reader_role, _ = Role.objects.get_or_create(
            name='reader',
            defaults={'display_name': 'Reader', 'description': 'Can read posts'}
        )
        UserRole.objects.create(user=self.user, role=reader_role)
    
    def test_complete_save_workflow(self):
        """Test complete workflow: save, check, list, unsave."""
        self.client.force_authenticate(user=self.user)
        
        # 1. Check initial state (not saved)
        check_url = reverse('posts:check-article-saved', kwargs={'pk': self.post.pk})
        response = self.client.get(check_url)
        self.assertFalse(response.data['is_saved'])
        
        # 2. Save the post
        save_url = reverse('posts:save-post', kwargs={'pk': self.post.pk})
        response = self.client.post(save_url, {'notes': 'Test workflow'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 3. Check saved state
        response = self.client.get(check_url)
        self.assertTrue(response.data['is_saved'])
        self.assertEqual(response.data['saved_article']['notes'], 'Test workflow')
        
        # 4. List saved posts
        list_url = reverse('posts:saved-posts')
        response = self.client.get(list_url)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['post_title'], 'Integration Test Post')
        
        # 5. Unsave the post
        response = self.client.delete(save_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 6. Check final state (not saved)
        response = self.client.get(check_url)
        self.assertFalse(response.data['is_saved'])
        
        # 7. List saved posts (should be empty)
        response = self.client.get(list_url)
        self.assertEqual(response.data['count'], 0)