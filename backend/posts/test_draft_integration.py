"""
Integration tests for draft management and scheduled publishing workflow.
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
from accounts.models import Role, UserRole


class DraftWorkflowIntegrationTestCase(APITestCase):
    """Integration test for complete draft management workflow."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create users with different roles
        self.writer = User.objects.create_user(
            username='writer',
            email='writer@example.com',
            password='testpass123'
        )
        
        self.editor = User.objects.create_user(
            username='editor',
            email='editor@example.com',
            password='testpass123'
        )
        
        # Create roles
        self.writer_role, _ = Role.objects.get_or_create(
            name='writer',
            defaults={
                'display_name': 'Writer',
                'description': 'Can create and edit posts'
            }
        )
        
        self.editor_role, _ = Role.objects.get_or_create(
            name='editor',
            defaults={
                'display_name': 'Editor',
                'description': 'Can edit, schedule and publish posts'
            }
        )
        
        # Assign roles
        UserRole.objects.create(user=self.writer, role=self.writer_role)
        UserRole.objects.create(user=self.editor, role=self.editor_role)
    
    def test_complete_draft_to_published_workflow(self):
        """Test the complete workflow from draft creation to publishing."""
        
        # Step 1: Writer creates a draft post
        self.client.force_authenticate(user=self.writer)
        create_url = reverse('posts:post-list-create')
        
        draft_data = {
            'title': 'My Draft Article',
            'content': 'This is the content of my draft article.',
            'author': 'Writer User',
            'author_user': self.writer.id,
            'tags': 'finance, draft',
            'status': 'draft'
        }
        
        response = self.client.post(create_url, draft_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post_id = response.data['id']
        self.assertEqual(response.data['status'], 'draft')
        
        # Step 2: Writer views their drafts
        drafts_url = reverse('posts:draft-posts')
        response = self.client.get(drafts_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        
        # Filter to only our test post
        our_drafts = [r for r in results if r['id'] == post_id]
        self.assertEqual(len(our_drafts), 1)
        self.assertEqual(our_drafts[0]['id'], post_id)
        
        # Step 3: Writer edits the draft
        edit_url = reverse('posts:post-detail', kwargs={'pk': post_id})
        updated_data = {
            'title': 'My Updated Draft Article',
            'content': 'This is the updated content of my draft article.',
            'author': 'Writer User',
            'author_user': self.writer.id,
            'tags': 'finance, updated',
            'status': 'draft'
        }
        
        response = self.client.put(edit_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'My Updated Draft Article')
        
        # Step 4: Editor schedules the post for future publication
        self.client.force_authenticate(user=self.editor)
        schedule_url = reverse('posts:schedule-post', kwargs={'pk': post_id})
        
        future_date = timezone.now() + timedelta(hours=1)
        schedule_data = {
            'scheduled_publish_date': future_date.isoformat()
        }
        
        response = self.client.post(schedule_url, schedule_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'scheduled')
        
        # Step 5: Verify post appears in scheduled posts filter
        list_url = reverse('posts:post-list-create')
        response = self.client.get(list_url, {'status': 'scheduled'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        scheduled_posts = [p for p in results if p['id'] == post_id]
        self.assertEqual(len(scheduled_posts), 1)
        
        # Step 6: Editor publishes the post immediately
        publish_url = reverse('posts:publish-post', kwargs={'pk': post_id})
        response = self.client.post(publish_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'published')
        self.assertIsNone(response.data['scheduled_publish_date'])
        
        # Step 7: Verify post is now visible to anonymous users
        self.client.force_authenticate(user=None)
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        published_posts = [p for p in results if p['id'] == post_id and p['status'] == 'published']
        self.assertEqual(len(published_posts), 1)
    
    def test_scheduled_publishing_workflow(self):
        """Test the scheduled publishing workflow with Celery task."""
        
        # Create a draft post
        self.client.force_authenticate(user=self.editor)
        create_url = reverse('posts:post-list-create')
        
        draft_data = {
            'title': 'Scheduled Article',
            'content': 'This article will be published automatically.',
            'author': 'Editor User',
            'author_user': self.editor.id,
            'tags': 'finance, scheduled',
            'status': 'draft'
        }
        
        response = self.client.post(create_url, draft_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post_id = response.data['id']
        
        # Schedule the post for publication
        schedule_url = reverse('posts:schedule-post', kwargs={'pk': post_id})
        future_date = timezone.now() + timedelta(minutes=5)
        schedule_data = {
            'scheduled_publish_date': future_date.isoformat()
        }
        
        response = self.client.post(schedule_url, schedule_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'scheduled')
        
        # Simulate time passing by updating the scheduled date to the past
        post = Post.objects.get(id=post_id)
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE blog_posts SET scheduled_publish_date = %s WHERE id = %s",
                [timezone.now() - timedelta(minutes=1), post_id]
            )
        
        # Run the scheduled publishing task
        with patch('posts.tasks.send_new_post_notification.delay') as mock_notification:
            result = publish_scheduled_posts()
        
        # Verify the post was published
        post.refresh_from_db()
        self.assertEqual(post.status, 'published')
        self.assertIsNone(post.scheduled_publish_date)
        
        # Verify notification was queued
        mock_notification.assert_called_once_with(post_id)
        
        # Verify task result
        self.assertIn('Published 1 scheduled posts', result)
        
        # Verify post is now visible to anonymous users
        self.client.force_authenticate(user=None)
        list_url = reverse('posts:post-list-create')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        published_posts = [p for p in results if p['id'] == post_id and p['status'] == 'published']
        self.assertEqual(len(published_posts), 1)
    
    def test_permission_enforcement(self):
        """Test that permissions are properly enforced throughout the workflow."""
        
        # Create a draft post as writer
        self.client.force_authenticate(user=self.writer)
        create_url = reverse('posts:post-list-create')
        
        draft_data = {
            'title': 'Writer Draft',
            'content': 'This is a writer\'s draft.',
            'author': 'Writer User',
            'author_user': self.writer.id,
            'status': 'draft'
        }
        
        response = self.client.post(create_url, draft_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post_id = response.data['id']
        
        # Writer should NOT be able to schedule posts
        schedule_url = reverse('posts:schedule-post', kwargs={'pk': post_id})
        future_date = timezone.now() + timedelta(hours=1)
        schedule_data = {
            'scheduled_publish_date': future_date.isoformat()
        }
        
        response = self.client.post(schedule_url, schedule_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Writer should NOT be able to publish posts directly
        publish_url = reverse('posts:publish-post', kwargs={'pk': post_id})
        response = self.client.post(publish_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Editor should be able to schedule and publish
        self.client.force_authenticate(user=self.editor)
        
        # Editor can schedule
        response = self.client.post(schedule_url, schedule_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Editor can publish
        response = self.client.post(publish_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'published')