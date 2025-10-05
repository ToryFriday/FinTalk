"""
Comprehensive tests for content moderation and flagging system.
"""

import json
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User, Permission
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

from posts.models import Post
from accounts.models import Role, UserRole
from .models import ContentFlag, ModerationAction, ModerationSettings
from .tasks import send_flag_notification, send_moderation_notification


class ContentFlagModelTest(TestCase):
    """
    Test cases for ContentFlag model.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        self.moderator = User.objects.create_user(
            username='moderator',
            email='moderator@example.com',
            password='testpass123',
            is_staff=True
        )
        
        self.post = Post.objects.create(
            title='Test Post',
            content='This is a test post content.',
            author='Test Author',
            author_user=self.user1
        )
    
    def test_create_content_flag(self):
        """Test creating a content flag."""
        flag = ContentFlag.objects.create(
            post=self.post,
            flagged_by=self.user2,
            reason='spam',
            description='This looks like spam content.'
        )
        
        self.assertEqual(flag.post, self.post)
        self.assertEqual(flag.flagged_by, self.user2)
        self.assertEqual(flag.reason, 'spam')
        self.assertEqual(flag.status, 'pending')
        self.assertIsNone(flag.reviewed_by)
        self.assertIsNone(flag.reviewed_at)
    
    def test_flag_validation_prevents_self_flagging(self):
        """Test that users cannot flag their own content."""
        with self.assertRaises(Exception):
            flag = ContentFlag(
                post=self.post,
                flagged_by=self.user1,  # Same as post author
                reason='spam',
                description='Trying to flag own content.'
            )
            flag.full_clean()
    
    def test_flag_validation_prevents_duplicate_flags(self):
        """Test that users cannot flag the same content twice."""
        # Create first flag
        ContentFlag.objects.create(
            post=self.post,
            flagged_by=self.user2,
            reason='spam',
            description='First flag.'
        )
        
        # Try to create duplicate flag
        with self.assertRaises(Exception):
            ContentFlag.objects.create(
                post=self.post,
                flagged_by=self.user2,  # Same user
                reason='inappropriate',
                description='Second flag.'
            )
    
    def test_flag_status_methods(self):
        """Test flag status checking methods."""
        flag = ContentFlag.objects.create(
            post=self.post,
            flagged_by=self.user2,
            reason='spam'
        )
        
        # Test pending status
        self.assertTrue(flag.is_pending())
        self.assertFalse(flag.is_under_review())
        self.assertFalse(flag.is_resolved())
        
        # Change to under review
        flag.status = 'under_review'
        flag.save()
        
        self.assertFalse(flag.is_pending())
        self.assertTrue(flag.is_under_review())
        self.assertFalse(flag.is_resolved())
        
        # Change to resolved
        flag.status = 'resolved_valid'
        flag.save()
        
        self.assertFalse(flag.is_pending())
        self.assertFalse(flag.is_under_review())
        self.assertTrue(flag.is_resolved())
        self.assertTrue(flag.is_valid_flag())
    
    def test_flag_resolution_methods(self):
        """Test flag resolution methods."""
        flag = ContentFlag.objects.create(
            post=self.post,
            flagged_by=self.user2,
            reason='spam'
        )
        
        # Test resolving as valid
        flag.resolve_as_valid(
            reviewer=self.moderator,
            resolution_notes='Content removed for spam.',
            action_taken='content_removed'
        )
        
        self.assertEqual(flag.status, 'resolved_valid')
        self.assertEqual(flag.reviewed_by, self.moderator)
        self.assertEqual(flag.action_taken, 'content_removed')
        self.assertIsNotNone(flag.reviewed_at)
    
    def test_get_flag_count_for_post(self):
        """Test getting flag count for a post."""
        # Create multiple flags for the same post
        ContentFlag.objects.create(
            post=self.post,
            flagged_by=self.user2,
            reason='spam'
        )
        
        user3 = User.objects.create_user(
            username='testuser3',
            email='test3@example.com',
            password='testpass123'
        )
        ContentFlag.objects.create(
            post=self.post,
            flagged_by=user3,
            reason='inappropriate'
        )
        
        flag = ContentFlag.objects.first()
        self.assertEqual(flag.get_flag_count_for_post(), 2)


class ModerationSettingsModelTest(TestCase):
    """
    Test cases for ModerationSettings model.
    """
    
    def test_get_settings_singleton(self):
        """Test that ModerationSettings works as singleton."""
        settings1 = ModerationSettings.get_settings()
        settings2 = ModerationSettings.get_settings()
        
        self.assertEqual(settings1.id, settings2.id)
        self.assertEqual(ModerationSettings.objects.count(), 1)
    
    def test_auto_moderation_thresholds(self):
        """Test auto-moderation threshold methods."""
        settings = ModerationSettings.get_settings()
        settings.auto_flag_threshold = 3
        settings.auto_hide_threshold = 5
        settings.save()
        
        self.assertFalse(settings.should_auto_flag(2))
        self.assertTrue(settings.should_auto_flag(3))
        self.assertTrue(settings.should_auto_flag(4))
        
        self.assertFalse(settings.should_auto_hide(4))
        self.assertTrue(settings.should_auto_hide(5))
        self.assertTrue(settings.should_auto_hide(6))


class FlagPostViewTest(APITestCase):
    """
    Test cases for FlagPostView API endpoint.
    """
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        self.user1 = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='flagger',
            email='flagger@example.com',
            password='testpass123'
        )
        
        self.post = Post.objects.create(
            title='Test Post',
            content='This is a test post content.',
            author='Test Author',
            author_user=self.user1
        )
        
        self.flag_url = reverse('moderation:flag-post', kwargs={'pk': self.post.id})
    
    def test_flag_post_success(self):
        """Test successfully flagging a post."""
        self.client.force_authenticate(user=self.user2)
        
        data = {
            'reason': 'spam',
            'description': 'This looks like spam content.'
        }
        
        with patch('moderation.views.send_flag_notification.delay') as mock_task:
            response = self.client.post(self.flag_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ContentFlag.objects.count(), 1)
        
        flag = ContentFlag.objects.first()
        self.assertEqual(flag.post, self.post)
        self.assertEqual(flag.flagged_by, self.user2)
        self.assertEqual(flag.reason, 'spam')
        self.assertEqual(flag.status, 'pending')
        
        # Check that notification task was called
        mock_task.assert_called_once_with(flag.id)
    
    def test_flag_post_unauthenticated(self):
        """Test flagging post without authentication."""
        data = {
            'reason': 'spam',
            'description': 'This looks like spam content.'
        }
        
        response = self.client.post(self.flag_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_flag_own_post_forbidden(self):
        """Test that users cannot flag their own posts."""
        self.client.force_authenticate(user=self.user1)  # Post author
        
        data = {
            'reason': 'spam',
            'description': 'Trying to flag own content.'
        }
        
        response = self.client.post(self.flag_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('cannot flag your own content', response.data['error'])
    
    def test_duplicate_flag_forbidden(self):
        """Test that users cannot flag the same post twice."""
        # Create first flag
        ContentFlag.objects.create(
            post=self.post,
            flagged_by=self.user2,
            reason='spam'
        )
        
        self.client.force_authenticate(user=self.user2)
        
        data = {
            'reason': 'inappropriate',
            'description': 'Second flag attempt.'
        }
        
        response = self.client.post(self.flag_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already flagged', response.data['error'])
    
    def test_flag_nonexistent_post(self):
        """Test flagging a non-existent post."""
        self.client.force_authenticate(user=self.user2)
        
        nonexistent_url = reverse('moderation:flag-post', kwargs={'pk': 99999})
        data = {
            'reason': 'spam',
            'description': 'Flagging non-existent post.'
        }
        
        response = self.client.post(nonexistent_url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ContentFlagListViewTest(APITestCase):
    """
    Test cases for ContentFlagListView API endpoint.
    """
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create users
        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='testpass123'
        )
        self.moderator = User.objects.create_user(
            username='moderator',
            email='moderator@example.com',
            password='testpass123',
            is_staff=True
        )
        
        # Add moderation permission to moderator
        permission = Permission.objects.get(codename='can_view_flags')
        self.moderator.user_permissions.add(permission)
        
        # Create test post and flags
        self.post = Post.objects.create(
            title='Test Post',
            content='Test content',
            author='Test Author',
            author_user=self.user
        )
        
        self.flag1 = ContentFlag.objects.create(
            post=self.post,
            flagged_by=self.user,
            reason='spam',
            description='Spam content'
        )
        
        self.flag2 = ContentFlag.objects.create(
            post=self.post,
            flagged_by=self.user,
            reason='inappropriate',
            status='resolved_valid'
        )
        
        self.flags_url = reverse('moderation:content-flags')
    
    def test_list_flags_as_moderator(self):
        """Test listing flags as a moderator."""
        self.client.force_authenticate(user=self.moderator)
        
        response = self.client.get(self.flags_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertIn('summary', response.data)
    
    def test_list_flags_unauthorized(self):
        """Test listing flags without proper permissions."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(self.flags_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_filter_flags_by_status(self):
        """Test filtering flags by status."""
        self.client.force_authenticate(user=self.moderator)
        
        response = self.client.get(self.flags_url, {'status': 'pending'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['status'], 'pending')
    
    def test_filter_flags_by_reason(self):
        """Test filtering flags by reason."""
        self.client.force_authenticate(user=self.moderator)
        
        response = self.client.get(self.flags_url, {'reason': 'spam'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['reason'], 'spam')


class ContentFlagDetailViewTest(APITestCase):
    """
    Test cases for ContentFlagDetailView API endpoint.
    """
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='testpass123'
        )
        self.moderator = User.objects.create_user(
            username='moderator',
            email='moderator@example.com',
            password='testpass123',
            is_staff=True
        )
        
        # Add moderation permissions
        permissions = Permission.objects.filter(
            codename__in=['can_moderate_content', 'can_view_flags']
        )
        self.moderator.user_permissions.add(*permissions)
        
        self.post = Post.objects.create(
            title='Test Post',
            content='Test content',
            author='Test Author',
            author_user=self.user
        )
        
        self.flag = ContentFlag.objects.create(
            post=self.post,
            flagged_by=self.user,
            reason='spam',
            description='Spam content'
        )
        
        self.flag_detail_url = reverse('moderation:flag-detail', kwargs={'pk': self.flag.id})
    
    def test_retrieve_flag_as_moderator(self):
        """Test retrieving flag details as moderator."""
        self.client.force_authenticate(user=self.moderator)
        
        response = self.client.get(self.flag_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.flag.id)
        self.assertEqual(response.data['reason'], 'spam')
    
    def test_update_flag_status(self):
        """Test updating flag status."""
        self.client.force_authenticate(user=self.moderator)
        
        data = {
            'status': 'resolved_valid',
            'resolution_notes': 'Content removed for spam.',
            'action_taken': 'content_removed'
        }
        
        with patch('moderation.views.send_moderation_notification.delay') as mock_task:
            response = self.client.put(self.flag_detail_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh flag from database
        self.flag.refresh_from_db()
        self.assertEqual(self.flag.status, 'resolved_valid')
        self.assertEqual(self.flag.reviewed_by, self.moderator)
        self.assertEqual(self.flag.resolution_notes, 'Content removed for spam.')
        
        # Check that notification task was called
        mock_task.assert_called_once_with(self.flag.id)
    
    def test_invalid_status_transition(self):
        """Test invalid status transition."""
        # Set flag to resolved first
        self.flag.status = 'resolved_valid'
        self.flag.save()
        
        self.client.force_authenticate(user=self.moderator)
        
        data = {
            'status': 'pending',  # Invalid transition from resolved
            'resolution_notes': 'Trying invalid transition.'
        }
        
        response = self.client.put(self.flag_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ModerationTasksTest(TransactionTestCase):
    """
    Test cases for moderation Celery tasks.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='testpass123'
        )
        self.moderator = User.objects.create_user(
            username='moderator',
            email='moderator@example.com',
            password='testpass123',
            is_staff=True
        )
        
        self.post = Post.objects.create(
            title='Test Post',
            content='Test content',
            author='Test Author',
            author_user=self.user
        )
        
        self.flag = ContentFlag.objects.create(
            post=self.post,
            flagged_by=self.user,
            reason='spam',
            description='Spam content'
        )
    
    @patch('moderation.tasks.send_mail')
    @patch('moderation.tasks.render_to_string')
    def test_send_flag_notification_task(self, mock_render, mock_send_mail):
        """Test send_flag_notification task."""
        mock_render.return_value = 'Test email content'
        
        # Mock settings
        with patch('django.conf.settings.DEFAULT_FROM_EMAIL', 'test@example.com'):
            with patch('django.conf.settings.FRONTEND_URL', 'http://localhost:3000'):
                result = send_flag_notification(self.flag.id)
        
        # Check that email rendering was called
        self.assertEqual(mock_render.call_count, 2)  # HTML and text templates
        
        # Check that send_mail was called
        mock_send_mail.assert_called_once()
    
    @patch('moderation.tasks.send_mail')
    @patch('moderation.tasks.render_to_string')
    def test_send_moderation_notification_task(self, mock_render, mock_send_mail):
        """Test send_moderation_notification task."""
        # Set up flag as resolved
        self.flag.status = 'resolved_valid'
        self.flag.reviewed_by = self.moderator
        self.flag.resolution_notes = 'Content removed'
        self.flag.action_taken = 'content_removed'
        self.flag.save()
        
        mock_render.return_value = 'Test email content'
        
        with patch('django.conf.settings.DEFAULT_FROM_EMAIL', 'test@example.com'):
            with patch('django.conf.settings.FRONTEND_URL', 'http://localhost:3000'):
                result = send_moderation_notification(self.flag.id)
        
        # Check that email rendering was called
        self.assertEqual(mock_render.call_count, 2)  # HTML and text templates
        
        # Check that send_mail was called
        mock_send_mail.assert_called_once()


class ModerationIntegrationTest(APITestCase):
    """
    Integration tests for complete moderation workflows.
    """
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create users
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='testpass123'
        )
        self.flagger = User.objects.create_user(
            username='flagger',
            email='flagger@example.com',
            password='testpass123'
        )
        self.moderator = User.objects.create_user(
            username='moderator',
            email='moderator@example.com',
            password='testpass123',
            is_staff=True
        )
        
        # Add permissions to moderator
        permissions = Permission.objects.filter(
            codename__in=['can_moderate_content', 'can_view_flags', 'can_resolve_flags']
        )
        self.moderator.user_permissions.add(*permissions)
        
        # Create test post
        self.post = Post.objects.create(
            title='Test Post',
            content='This is test content that might be inappropriate.',
            author='Test Author',
            author_user=self.author
        )
    
    def test_complete_flag_and_resolution_workflow(self):
        """Test complete workflow from flagging to resolution."""
        # Step 1: User flags content
        self.client.force_authenticate(user=self.flagger)
        flag_url = reverse('moderation:flag-post', kwargs={'pk': self.post.id})
        
        flag_data = {
            'reason': 'inappropriate',
            'description': 'This content is inappropriate for the platform.'
        }
        
        with patch('moderation.views.send_flag_notification.delay'):
            flag_response = self.client.post(flag_url, flag_data)
        
        self.assertEqual(flag_response.status_code, status.HTTP_201_CREATED)
        flag_id = flag_response.data['id']
        
        # Step 2: Moderator reviews flags
        self.client.force_authenticate(user=self.moderator)
        flags_url = reverse('moderation:content-flags')
        
        flags_response = self.client.get(flags_url)
        self.assertEqual(flags_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(flags_response.data['results']), 1)
        
        # Step 3: Moderator resolves flag
        flag_detail_url = reverse('moderation:flag-detail', kwargs={'pk': flag_id})
        
        resolution_data = {
            'status': 'resolved_valid',
            'resolution_notes': 'Content violates community guidelines.',
            'action_taken': 'content_removed'
        }
        
        with patch('moderation.views.send_moderation_notification.delay'):
            resolution_response = self.client.put(flag_detail_url, resolution_data)
        
        self.assertEqual(resolution_response.status_code, status.HTTP_200_OK)
        
        # Step 4: Verify flag is resolved
        flag = ContentFlag.objects.get(id=flag_id)
        self.assertEqual(flag.status, 'resolved_valid')
        self.assertEqual(flag.reviewed_by, self.moderator)
        self.assertIsNotNone(flag.reviewed_at)
        
        # Step 5: Verify moderation action was created
        moderation_actions = ModerationAction.objects.filter(flag=flag)
        self.assertEqual(moderation_actions.count(), 1)
        
        action = moderation_actions.first()
        self.assertEqual(action.moderator, self.moderator)
        self.assertEqual(action.affected_user, self.author)
    
    def test_auto_moderation_threshold(self):
        """Test auto-moderation when threshold is reached."""
        # Set up moderation settings
        settings = ModerationSettings.get_settings()
        settings.auto_flag_threshold = 2
        settings.save()
        
        # Create multiple flags for the same post
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )
        
        # First flag
        self.client.force_authenticate(user=self.flagger)
        flag_url = reverse('moderation:flag-post', kwargs={'pk': self.post.id})
        
        with patch('moderation.views.send_flag_notification.delay'):
            self.client.post(flag_url, {'reason': 'spam', 'description': 'Spam'})
        
        # Second flag (should trigger auto-moderation)
        self.client.force_authenticate(user=user2)
        
        with patch('moderation.views.send_flag_notification.delay'):
            response = self.client.post(flag_url, {'reason': 'inappropriate', 'description': 'Bad'})
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that flags were auto-flagged for review
        pending_flags = ContentFlag.objects.filter(post=self.post, status='pending').count()
        under_review_flags = ContentFlag.objects.filter(post=self.post, status='under_review').count()
        
        # Should have auto-flagged some for review
        self.assertGreaterEqual(under_review_flags, 1)
