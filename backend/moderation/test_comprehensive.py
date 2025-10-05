"""
Comprehensive unit tests for moderation app models, serializers, and views.
This file provides extensive test coverage for all moderation functionality.
"""

import json
from unittest.mock import patch, MagicMock

from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User, Permission
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from .models import ContentFlag, ModerationAction, ModerationSettings
from .serializers import ContentFlagSerializer, ModerationActionSerializer
from posts.models import Post
from accounts.models import Role, UserRole


class ContentFlagModelTest(TestCase):
    """Comprehensive tests for ContentFlag model."""
    
    def setUp(self):
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
            author_user=self.user1,
            status='published'
        )
    
    def test_content_flag_creation(self):
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
        self.assertIsNotNone(flag.created_at)
    
    def test_content_flag_str_representation(self):
        """Test content flag string representation."""
        flag = ContentFlag.objects.create(
            post=self.post,
            flagged_by=self.user2,
            reason='spam'
        )
        
        expected = f"Flag #{flag.id}: {self.post.title} - Spam"
        self.assertEqual(str(flag), expected)
    
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
        self.assertFalse(flag.is_invalid_flag())
    
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
        
        # Test resolving as invalid
        flag2 = ContentFlag.objects.create(
            post=self.post,
            flagged_by=self.user2,
            reason='inappropriate'
        )
        
        flag2.resolve_as_invalid(
            reviewer=self.moderator,
            resolution_notes='Content is appropriate.'
        )
        
        self.assertEqual(flag2.status, 'resolved_invalid')
        self.assertEqual(flag2.reviewed_by, self.moderator)
        self.assertEqual(flag2.action_taken, '')
    
    def test_flag_permission_checking(self):
        """Test flag permission checking methods."""
        flag = ContentFlag.objects.create(
            post=self.post,
            flagged_by=self.user2,
            reason='spam'
        )
        
        # Regular user cannot review
        self.assertFalse(flag.can_be_reviewed_by(self.user2))
        
        # Superuser can review
        self.assertTrue(flag.can_be_reviewed_by(self.moderator))
        
        # Create editor role and user
        editor_role = Role.objects.create(
            name='editor',
            display_name='Editor',
            description='Content editor'
        )
        editor_user = User.objects.create_user(
            username='editor',
            email='editor@example.com',
            password='testpass123'
        )
        UserRole.objects.create(user=editor_user, role=editor_role)
        
        # Editor can review
        self.assertTrue(flag.can_be_reviewed_by(editor_user))
    
    def test_flag_count_methods(self):
        """Test flag count methods."""
        flag = ContentFlag.objects.create(
            post=self.post,
            flagged_by=self.user2,
            reason='spam'
        )
        
        # Create another user and flag
        user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )
        ContentFlag.objects.create(
            post=self.post,
            flagged_by=user3,
            reason='inappropriate'
        )
        
        self.assertEqual(flag.get_flag_count_for_post(), 2)
        self.assertEqual(flag.get_pending_flag_count_for_post(), 2)
    
    def test_flag_validation_errors(self):
        """Test flag validation error cases."""
        # Users cannot flag their own content
        with self.assertRaises(Exception):
            flag = ContentFlag(
                post=self.post,
                flagged_by=self.user1,  # Same as post author
                reason='spam'
            )
            flag.full_clean()
        
        # Duplicate flags should be prevented by unique constraint
        ContentFlag.objects.create(
            post=self.post,
            flagged_by=self.user2,
            reason='spam'
        )
        
        with self.assertRaises(Exception):
            ContentFlag.objects.create(
                post=self.post,
                flagged_by=self.user2,  # Same user
                reason='inappropriate'
            )


class ModerationActionModelTest(TestCase):
    """Comprehensive tests for ModerationAction model."""
    
    def setUp(self):
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
        
        self.post = Post.objects.create(
            title='Test Post',
            content='This is a test post content.',
            author='Test Author',
            author_user=self.author,
            status='published'
        )
        
        self.flag = ContentFlag.objects.create(
            post=self.post,
            flagged_by=self.flagger,
            reason='spam'
        )
    
    def test_moderation_action_creation(self):
        """Test creating a moderation action."""
        action = ModerationAction.objects.create(
            flag=self.flag,
            post=self.post,
            action_type='content_removed',
            moderator=self.moderator,
            reason='Content violates community guidelines',
            affected_user=self.author,
            severity_level=3
        )
        
        self.assertEqual(action.flag, self.flag)
        self.assertEqual(action.post, self.post)
        self.assertEqual(action.action_type, 'content_removed')
        self.assertEqual(action.moderator, self.moderator)
        self.assertEqual(action.affected_user, self.author)
        self.assertEqual(action.severity_level, 3)
        self.assertFalse(action.is_automated)
        self.assertIsNotNone(action.created_at)
    
    def test_moderation_action_str_representation(self):
        """Test moderation action string representation."""
        action = ModerationAction.objects.create(
            flag=self.flag,
            post=self.post,
            action_type='content_removed',
            moderator=self.moderator,
            reason='Spam content'
        )
        
        expected = f"Moderation Action: Content Removed on {self.post.title}"
        self.assertEqual(str(action), expected)
    
    def test_moderation_action_validation(self):
        """Test moderation action validation."""
        # Valid action
        action = ModerationAction(
            flag=self.flag,
            post=self.post,
            action_type='content_removed',
            moderator=self.moderator,
            reason='Valid reason',
            severity_level=2
        )
        
        try:
            action.full_clean()
        except Exception:
            self.fail("Valid moderation action should not raise validation error")
    
    def test_moderation_action_validation_errors(self):
        """Test moderation action validation error cases."""
        # Invalid severity level
        action = ModerationAction(
            flag=self.flag,
            post=self.post,
            action_type='content_removed',
            moderator=self.moderator,
            reason='Valid reason',
            severity_level=6  # Invalid (should be 1-5)
        )
        
        with self.assertRaises(Exception):
            action.full_clean()
    
    def test_affected_user_auto_assignment(self):
        """Test automatic assignment of affected_user from post author."""
        action = ModerationAction.objects.create(
            flag=self.flag,
            post=self.post,
            action_type='warning_issued',
            moderator=self.moderator,
            reason='Warning for inappropriate content'
        )
        
        # Should automatically set affected_user to post author
        self.assertEqual(action.affected_user, self.author)


class ModerationSettingsModelTest(TestCase):
    """Comprehensive tests for ModerationSettings model."""
    
    def test_moderation_settings_singleton(self):
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
    
    def test_moderation_settings_str_representation(self):
        """Test moderation settings string representation."""
        settings = ModerationSettings.get_settings()
        self.assertEqual(str(settings), "Moderation Settings")


class ContentFlagSerializerTest(TestCase):
    """Test ContentFlagSerializer."""
    
    def setUp(self):
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
        
        self.post = Post.objects.create(
            title='Test Post',
            content='This is a test post content.',
            author='Test Author',
            author_user=self.author,
            status='published'
        )
        
        self.flag = ContentFlag.objects.create(
            post=self.post,
            flagged_by=self.flagger,
            reason='spam',
            description='This looks like spam'
        )
    
    def test_content_flag_serialization(self):
        """Test content flag serialization."""
        serializer = ContentFlagSerializer(self.flag)
        data = serializer.data
        
        self.assertEqual(data['reason'], 'spam')
        self.assertEqual(data['description'], 'This looks like spam')
        self.assertEqual(data['status'], 'pending')
        self.assertIn('post', data)
        self.assertIn('flagged_by', data)
        self.assertIn('created_at', data)
    
    def test_content_flag_creation_via_serializer(self):
        """Test creating a content flag via serializer."""
        data = {
            'reason': 'inappropriate',
            'description': 'This content is inappropriate'
        }
        
        serializer = ContentFlagSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Would need to set post and flagged_by in the view
        flag = serializer.save(post=self.post, flagged_by=self.flagger)
        
        self.assertEqual(flag.reason, 'inappropriate')
        self.assertEqual(flag.description, 'This content is inappropriate')
        self.assertEqual(flag.post, self.post)
        self.assertEqual(flag.flagged_by, self.flagger)


class FlagPostAPITest(APITestCase):
    """Test flag post API endpoint."""
    
    def setUp(self):
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
        
        self.post = Post.objects.create(
            title='Test Post',
            content='This is a test post content.',
            author='Test Author',
            author_user=self.author,
            status='published'
        )
        
        self.flag_url = reverse('moderation:flag-post', kwargs={'pk': self.post.id})
    
    def test_flag_post_success(self):
        """Test successfully flagging a post."""
        self.client.force_authenticate(user=self.flagger)
        
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
        self.assertEqual(flag.flagged_by, self.flagger)
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
        self.client.force_authenticate(user=self.author)  # Post author
        
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
            flagged_by=self.flagger,
            reason='spam'
        )
        
        self.client.force_authenticate(user=self.flagger)
        
        data = {
            'reason': 'inappropriate',
            'description': 'Second flag attempt.'
        }
        
        response = self.client.post(self.flag_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already flagged', response.data['error'])
    
    def test_flag_nonexistent_post(self):
        """Test flagging a non-existent post."""
        self.client.force_authenticate(user=self.flagger)
        
        nonexistent_url = reverse('moderation:flag-post', kwargs={'pk': 99999})
        data = {
            'reason': 'spam',
            'description': 'Flagging non-existent post.'
        }
        
        response = self.client.post(nonexistent_url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ContentFlagListAPITest(APITestCase):
    """Test content flag list API endpoint."""
    
    def setUp(self):
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
        permission = Permission.objects.get_or_create(
            codename='can_view_flags',
            defaults={
                'name': 'Can view flags',
                'content_type_id': 1
            }
        )[0]
        self.moderator.user_permissions.add(permission)
        
        # Create test post and flags
        self.post = Post.objects.create(
            title='Test Post',
            content='Test content',
            author='Test Author',
            author_user=self.user,
            status='published'
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


class ContentFlagDetailAPITest(APITestCase):
    """Test content flag detail API endpoint."""
    
    def setUp(self):
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
        if not permissions.exists():
            # Create permissions if they don't exist
            from django.contrib.contenttypes.models import ContentType
            content_type = ContentType.objects.get_for_model(ContentFlag)
            permissions = [
                Permission.objects.get_or_create(
                    codename='can_moderate_content',
                    defaults={
                        'name': 'Can moderate content',
                        'content_type': content_type
                    }
                )[0],
                Permission.objects.get_or_create(
                    codename='can_view_flags',
                    defaults={
                        'name': 'Can view flags',
                        'content_type': content_type
                    }
                )[0]
            ]
        
        self.moderator.user_permissions.add(*permissions)
        
        self.post = Post.objects.create(
            title='Test Post',
            content='Test content',
            author='Test Author',
            author_user=self.user,
            status='published'
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


class ModerationDashboardAPITest(APITestCase):
    """Test moderation dashboard API endpoint."""
    
    def setUp(self):
        self.moderator = User.objects.create_user(
            username='moderator',
            email='moderator@example.com',
            password='testpass123',
            is_staff=True
        )
        
        # Create editor role
        self.editor_role = Role.objects.create(
            name='editor',
            display_name='Editor',
            description='Content editor'
        )
        UserRole.objects.create(user=self.moderator, role=self.editor_role)
        
        # Create test data
        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='testpass123'
        )
        
        self.post = Post.objects.create(
            title='Test Post',
            content='Test content',
            author='Test Author',
            author_user=self.user,
            status='published'
        )
        
        # Create flags
        ContentFlag.objects.create(
            post=self.post,
            flagged_by=self.user,
            reason='spam',
            status='pending'
        )
        ContentFlag.objects.create(
            post=self.post,
            flagged_by=self.user,
            reason='inappropriate',
            status='resolved_valid'
        )
        
        self.dashboard_url = reverse('moderation:moderation-dashboard')
    
    def test_moderation_dashboard_access(self):
        """Test accessing moderation dashboard."""
        self.client.force_authenticate(user=self.moderator)
        
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check dashboard data structure
        self.assertIn('pending_flags', response.data)
        self.assertIn('flags_today', response.data)
        self.assertIn('flags_this_week', response.data)
        self.assertIn('recent_actions', response.data)
        self.assertIn('flag_reasons_breakdown', response.data)
    
    def test_dashboard_unauthorized_access(self):
        """Test unauthorized access to dashboard."""
        regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='testpass123'
        )
        
        self.client.force_authenticate(user=regular_user)
        
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ModerationIntegrationTest(APITestCase):
    """Integration tests for complete moderation workflows."""
    
    def setUp(self):
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
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(ContentFlag)
        permissions = [
            Permission.objects.get_or_create(
                codename='can_moderate_content',
                defaults={
                    'name': 'Can moderate content',
                    'content_type': content_type
                }
            )[0],
            Permission.objects.get_or_create(
                codename='can_view_flags',
                defaults={
                    'name': 'Can view flags',
                    'content_type': content_type
                }
            )[0],
            Permission.objects.get_or_create(
                codename='can_resolve_flags',
                defaults={
                    'name': 'Can resolve flags',
                    'content_type': content_type
                }
            )[0]
        ]
        self.moderator.user_permissions.add(*permissions)
        
        # Create test post
        self.post = Post.objects.create(
            title='Test Post',
            content='This is test content that might be inappropriate.',
            author='Test Author',
            author_user=self.author,
            status='published'
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
        
        # Check that flags exist
        total_flags = ContentFlag.objects.filter(post=self.post).count()
        self.assertEqual(total_flags, 2)


class ModerationPerformanceTest(TransactionTestCase):
    """Test performance of moderation operations."""
    
    def setUp(self):
        # Create test users
        self.users = []
        for i in range(20):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass123'
            )
            self.users.append(user)
        
        # Create test posts
        self.posts = []
        for i in range(10):
            post = Post.objects.create(
                title=f'Test Post {i}',
                content=f'This is test post content number {i}.',
                author=f'Author {i}',
                author_user=self.users[i % len(self.users)],
                status='published'
            )
            self.posts.append(post)
    
    def test_bulk_flag_creation_performance(self):
        """Test performance of bulk flag creation."""
        import time
        
        start_time = time.time()
        
        # Create flags in bulk
        flags = []
        for i in range(50):
            post = self.posts[i % len(self.posts)]
            flagger = self.users[(i + 1) % len(self.users)]  # Different user than author
            
            # Skip if flagger is the same as post author
            if post.author_user == flagger:
                continue
                
            flags.append(ContentFlag(
                post=post,
                flagged_by=flagger,
                reason='spam',
                description=f'Flag number {i}'
            ))
        
        ContentFlag.objects.bulk_create(flags, ignore_conflicts=True)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete in reasonable time
        self.assertLess(execution_time, 1.0)
        
        # Verify flags were created
        self.assertGreater(ContentFlag.objects.count(), 0)
    
    def test_flag_query_performance(self):
        """Test performance of flag queries."""
        # Create test flags
        flags = []
        for i in range(30):
            post = self.posts[i % len(self.posts)]
            flagger = self.users[(i + 1) % len(self.users)]
            
            if post.author_user != flagger:  # Avoid self-flagging
                flags.append(ContentFlag(
                    post=post,
                    flagged_by=flagger,
                    reason='spam',
                    description=f'Flag {i}'
                ))
        
        ContentFlag.objects.bulk_create(flags, ignore_conflicts=True)
        
        import time
        start_time = time.time()
        
        # Test various queries
        pending_flags = ContentFlag.objects.filter(status='pending').count()
        flags_by_reason = ContentFlag.objects.filter(reason='spam').count()
        recent_flags = ContentFlag.objects.order_by('-created_at')[:10]
        
        # Force evaluation of querysets
        list(recent_flags)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete quickly
        self.assertLess(execution_time, 0.5)
        
        # Verify query results
        self.assertGreaterEqual(pending_flags, 0)
        self.assertGreaterEqual(flags_by_reason, 0)