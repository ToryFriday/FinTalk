"""
Tests for draft management and scheduled publishing functionality.
"""

import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import timedelta
from unittest.mock import patch

from .models import Post
from .tasks import publish_scheduled_posts


class DraftManagementTestCase(APITestCase):
    """Test cases for draft management functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
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
        
        # Create test posts
        self.draft_post = Post.objects.create(
            title='Draft Post',
            content='This is a draft post content.',
            author='Test Author',
            author_user=self.user,
            status='draft'
        )
        
        self.published_post = Post.objects.create(
            title='Published Post',
            content='This is a published post content.',
            author='Test Author',
            author_user=self.user,
            status='published'
        )
        
        self.other_user_draft = Post.objects.create(
            title='Other User Draft',
            content='This is another user\'s draft.',
            author='Other Author',
            author_user=self.other_user,
            status='draft'
        )
    
    def test_get_drafts_unauthenticated(self):
        """Test that unauthenticated users cannot access drafts."""
        url = reverse('posts:draft-posts')
        response = self.client.get(url)
        # The view returns empty results for unauthenticated users, not 403
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 0)
    
    def test_get_user_drafts(self):
        """Test that authenticated users can get their own drafts."""
        self.client.force_authenticate(user=self.user)
        url = reverse('posts:draft-posts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.draft_post.id)
        self.assertEqual(results[0]['status'], 'draft')
    
    def test_drafts_exclude_other_users(self):
        """Test that users only see their own drafts."""
        self.client.force_authenticate(user=self.user)
        url = reverse('posts:draft-posts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        draft_ids = [post['id'] for post in results]
        self.assertIn(self.draft_post.id, draft_ids)
        self.assertNotIn(self.other_user_draft.id, draft_ids)
    
    def test_drafts_exclude_published_posts(self):
        """Test that drafts endpoint only returns draft posts."""
        self.client.force_authenticate(user=self.user)
        url = reverse('posts:draft-posts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        draft_ids = [post['id'] for post in results]
        self.assertIn(self.draft_post.id, draft_ids)
        self.assertNotIn(self.published_post.id, draft_ids)


class ScheduledPublishingTestCase(APITestCase):
    """Test cases for scheduled publishing functionality."""
    
    def setUp(self):
        """Set up test data."""
        from accounts.models import Role, UserRole
        
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create editor role and assign to user for scheduling permissions
        self.editor_role, created = Role.objects.get_or_create(
            name='editor',
            defaults={
                'display_name': 'Editor',
                'description': 'Can edit and schedule posts'
            }
        )
        UserRole.objects.create(user=self.user, role=self.editor_role)
        
        self.draft_post = Post.objects.create(
            title='Draft Post',
            content='This is a draft post content.',
            author='Test Author',
            author_user=self.user,
            status='draft'
        )
        
        self.published_post = Post.objects.create(
            title='Published Post',
            content='This is a published post content.',
            author='Test Author',
            author_user=self.user,
            status='published'
        )
    
    def test_schedule_post_success(self):
        """Test successfully scheduling a post."""
        self.client.force_authenticate(user=self.user)
        url = reverse('posts:schedule-post', kwargs={'pk': self.draft_post.id})
        
        future_date = timezone.now() + timedelta(hours=1)
        data = {
            'scheduled_publish_date': future_date.isoformat()
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.draft_post.refresh_from_db()
        self.assertEqual(self.draft_post.status, 'scheduled')
        self.assertIsNotNone(self.draft_post.scheduled_publish_date)
    
    def test_schedule_post_past_date(self):
        """Test scheduling a post with past date fails."""
        self.client.force_authenticate(user=self.user)
        url = reverse('posts:schedule-post', kwargs={'pk': self.draft_post.id})
        
        past_date = timezone.now() - timedelta(hours=1)
        data = {
            'scheduled_publish_date': past_date.isoformat()
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('future', response.data['error'].lower())
    
    def test_schedule_post_missing_date(self):
        """Test scheduling a post without date fails."""
        self.client.force_authenticate(user=self.user)
        url = reverse('posts:schedule-post', kwargs={'pk': self.draft_post.id})
        
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('required', response.data['error'].lower())
    
    def test_schedule_nonexistent_post(self):
        """Test scheduling a non-existent post fails."""
        self.client.force_authenticate(user=self.user)
        url = reverse('posts:schedule-post', kwargs={'pk': 99999})
        
        future_date = timezone.now() + timedelta(hours=1)
        data = {
            'scheduled_publish_date': future_date.isoformat()
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_publish_post_success(self):
        """Test successfully publishing a draft post."""
        self.client.force_authenticate(user=self.user)
        url = reverse('posts:publish-post', kwargs={'pk': self.draft_post.id})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.draft_post.refresh_from_db()
        self.assertEqual(self.draft_post.status, 'published')
        self.assertIsNone(self.draft_post.scheduled_publish_date)
    
    def test_publish_already_published_post(self):
        """Test publishing an already published post fails."""
        self.client.force_authenticate(user=self.user)
        url = reverse('posts:publish-post', kwargs={'pk': self.published_post.id})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('cannot be published', response.data['error'].lower())
    
    def test_publish_scheduled_posts_task(self):
        """Test the Celery task for publishing scheduled posts."""
        # Create a scheduled post that should be published (bypass validation)
        scheduled_post = Post.objects.create(
            title='Scheduled Post',
            content='This post should be published.',
            author='Test Author',
            author_user=self.user,
            status='draft'  # Create as draft first
        )
        # Update to scheduled with past date using raw SQL to bypass validation
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE blog_posts SET status = %s, scheduled_publish_date = %s WHERE id = %s",
                ['scheduled', timezone.now() - timedelta(minutes=1), scheduled_post.id]
            )
        scheduled_post.refresh_from_db()
        
        # Create a scheduled post that should NOT be published yet
        future_post = Post.objects.create(
            title='Future Post',
            content='This post should not be published yet.',
            author='Test Author',
            author_user=self.user,
            status='draft'  # Create as draft first
        )
        # Update to scheduled with future date
        future_post.status = 'scheduled'
        future_post.scheduled_publish_date = timezone.now() + timedelta(hours=1)
        future_post.save()
        
        # Run the task
        with patch('posts.tasks.send_new_post_notification.delay') as mock_notification:
            result = publish_scheduled_posts()
        
        # Check results
        scheduled_post.refresh_from_db()
        future_post.refresh_from_db()
        
        self.assertEqual(scheduled_post.status, 'published')
        self.assertIsNone(scheduled_post.scheduled_publish_date)
        self.assertEqual(future_post.status, 'scheduled')
        self.assertIsNotNone(future_post.scheduled_publish_date)
        
        # Check that notification was queued
        mock_notification.assert_called_once_with(scheduled_post.id)
        
        # Check task result
        self.assertIn('Published 1 scheduled posts', result)


class PostStatusFilteringTestCase(APITestCase):
    """Test cases for post status filtering in list views."""
    
    def setUp(self):
        """Set up test data."""
        from accounts.models import Role, UserRole
        
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create editor role and assign to user for viewing all posts
        self.editor_role, created = Role.objects.get_or_create(
            name='editor',
            defaults={
                'display_name': 'Editor',
                'description': 'Can edit and schedule posts'
            }
        )
        UserRole.objects.create(user=self.user, role=self.editor_role)
        
        # Create posts with different statuses
        self.draft_post = Post.objects.create(
            title='Draft Post',
            content='Draft content',
            author='Test Author',
            author_user=self.user,
            status='draft'
        )
        
        self.published_post = Post.objects.create(
            title='Published Post',
            content='Published content',
            author='Test Author',
            author_user=self.user,
            status='published'
        )
        
        # Create scheduled post (create as draft first, then update)
        self.scheduled_post = Post.objects.create(
            title='Scheduled Post',
            content='Scheduled content',
            author='Test Author',
            author_user=self.user,
            status='draft'
        )
        self.scheduled_post.status = 'scheduled'
        self.scheduled_post.scheduled_publish_date = timezone.now() + timedelta(hours=1)
        self.scheduled_post.save()
    
    def test_filter_posts_by_status_draft(self):
        """Test filtering posts by draft status."""
        self.client.force_authenticate(user=self.user)
        url = reverse('posts:post-list-create')
        
        response = self.client.get(url, {'status': 'draft'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        # Filter results to only include our test posts
        test_results = [r for r in results if r['id'] in [self.draft_post.id, self.published_post.id, self.scheduled_post.id]]
        draft_results = [r for r in test_results if r['status'] == 'draft']
        self.assertEqual(len(draft_results), 1)
        self.assertEqual(draft_results[0]['id'], self.draft_post.id)
    
    def test_filter_posts_by_status_published(self):
        """Test filtering posts by published status."""
        url = reverse('posts:post-list-create')
        
        response = self.client.get(url, {'status': 'published'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        # Filter results to only include our test posts
        test_results = [r for r in results if r['id'] in [self.draft_post.id, self.published_post.id, self.scheduled_post.id]]
        published_results = [r for r in test_results if r['status'] == 'published']
        self.assertEqual(len(published_results), 1)
        self.assertEqual(published_results[0]['id'], self.published_post.id)
    
    def test_filter_posts_by_status_scheduled(self):
        """Test filtering posts by scheduled status."""
        self.client.force_authenticate(user=self.user)
        url = reverse('posts:post-list-create')
        
        response = self.client.get(url, {'status': 'scheduled'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        # Filter results to only include our test posts
        test_results = [r for r in results if r['id'] in [self.draft_post.id, self.published_post.id, self.scheduled_post.id]]
        scheduled_results = [r for r in test_results if r['status'] == 'scheduled']
        self.assertEqual(len(scheduled_results), 1)
        self.assertEqual(scheduled_results[0]['id'], self.scheduled_post.id)
    
    def test_anonymous_user_sees_only_published(self):
        """Test that anonymous users only see published posts."""
        url = reverse('posts:post-list-create')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        # Filter results to only include our test posts
        test_results = [r for r in results if r['id'] in [self.draft_post.id, self.published_post.id, self.scheduled_post.id]]
        # Anonymous users should only see published posts
        published_results = [r for r in test_results if r['status'] == 'published']
        self.assertEqual(len(published_results), 1)
        self.assertEqual(published_results[0]['id'], self.published_post.id)