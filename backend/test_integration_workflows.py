"""
Integration tests for complete user workflows.
Tests end-to-end functionality across multiple apps and features.
"""

import tempfile
import os
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase, TransactionTestCase, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from PIL import Image

from accounts.models import UserProfile, Role, UserRole, SavedArticle, UserFollow
from posts.models import Post, MediaFile, PostMedia
from moderation.models import ContentFlag, ModerationAction
from notifications.models import EmailSubscription


class UserRegistrationWorkflowTest(APITestCase):
    """Test complete user registration and verification workflow."""
    
    def test_complete_registration_workflow(self):
        """Test complete user registration, verification, and profile setup."""
        # Step 1: Register new user
        registration_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'strongpassword123',
            'password_confirm': 'strongpassword123',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        register_url = reverse('accounts:register')
        response = self.client.post(register_url, registration_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user_id', response.data)
        
        # Verify user was created but not verified
        user = User.objects.get(username='newuser')
        self.assertFalse(user.profile.is_email_verified)
        self.assertIsNotNone(user.profile.email_verification_token)
        
        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Verify your email', mail.outbox[0].subject)
        
        # Step 2: Verify email
        token = user.profile.email_verification_token
        verify_url = reverse('accounts:verify-email', kwargs={'token': token})
        response = self.client.get(verify_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify user is now verified
        user.refresh_from_db()
        self.assertTrue(user.profile.is_email_verified)
        
        # Step 3: Login
        login_data = {
            'username': 'newuser',
            'password': 'strongpassword123'
        }
        
        login_url = reverse('accounts:login')
        response = self.client.post(login_url, login_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertTrue(response.data['user']['is_email_verified'])
        
        # Step 4: Update profile
        profile_data = {
            'bio': 'I am a new user interested in financial topics.',
            'website': 'https://newuser.com',
            'location': 'New York, NY'
        }
        
        profile_url = reverse('accounts:user-profile')
        response = self.client.patch(profile_url, profile_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bio'], profile_data['bio'])
        
        # Verify profile was updated
        user.refresh_from_db()
        self.assertEqual(user.profile.bio, profile_data['bio'])
        self.assertEqual(user.profile.website, profile_data['website'])


class ContentCreationWorkflowTest(APITestCase):
    """Test complete content creation and publishing workflow."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='writer',
            email='writer@example.com',
            password='testpass123'
        )
        self.user.profile.is_email_verified = True
        self.user.profile.save()
        
        # Assign writer role
        self.writer_role = Role.objects.create(
            name='writer',
            display_name='Writer',
            description='Can create and edit posts'
        )
        UserRole.objects.create(user=self.user, role=self.writer_role)
        
        self.client.force_authenticate(user=self.user)
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_complete_content_creation_workflow(self):
        """Test complete workflow from draft creation to publishing with media."""
        # Step 1: Upload media file
        test_image = Image.new('RGB', (100, 100), color='red')
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        test_image.save(temp_file, 'JPEG')
        temp_file.seek(0)
        
        try:
            with open(temp_file.name, 'rb') as f:
                upload_data = {
                    'file': SimpleUploadedFile(
                        name='test_image.jpg',
                        content=f.read(),
                        content_type='image/jpeg'
                    ),
                    'alt_text': 'Test financial chart'
                }
                
                upload_url = reverse('posts:media-upload')
                response = self.client.post(upload_url, upload_data, format='multipart')
                
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                media_file_id = response.data['id']
            
            # Step 2: Create draft post
            post_data = {
                'title': 'Understanding Market Volatility',
                'content': 'Market volatility is a key concept in finance that every investor should understand. This comprehensive guide will walk you through the fundamentals.',
                'tags': 'finance, markets, volatility, investing',
                'status': 'draft'
            }
            
            posts_url = reverse('posts:post-list-create')
            response = self.client.post(posts_url, post_data)
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            post_id = response.data['id']
            self.assertEqual(response.data['status'], 'draft')
            
            # Step 3: Attach media to post
            media_data = {
                'media_files': [
                    {
                        'media_file_id': media_file_id,
                        'order': 0,
                        'caption': 'Market volatility visualization'
                    }
                ]
            }
            
            attach_url = reverse('posts:post-media', kwargs={'pk': post_id})
            response = self.client.post(attach_url, media_data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
            # Verify media was attached
            post_media = PostMedia.objects.get(post_id=post_id)
            self.assertEqual(post_media.media_file_id, media_file_id)
            self.assertEqual(post_media.caption, 'Market volatility visualization')
            
            # Step 4: Schedule post for future publication
            future_date = timezone.now() + timedelta(hours=2)
            schedule_data = {
                'scheduled_publish_date': future_date.isoformat()
            }
            
            schedule_url = reverse('posts:schedule-post', kwargs={'pk': post_id})
            response = self.client.post(schedule_url, schedule_data)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Verify post was scheduled
            post = Post.objects.get(id=post_id)
            self.assertEqual(post.status, 'scheduled')
            self.assertIsNotNone(post.scheduled_publish_date)
            
            # Step 5: Publish post immediately
            publish_url = reverse('posts:publish-post', kwargs={'pk': post_id})
            response = self.client.post(publish_url)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Verify post was published
            post.refresh_from_db()
            self.assertEqual(post.status, 'published')
            self.assertIsNone(post.scheduled_publish_date)
            
            # Step 6: Verify post appears in public list
            response = self.client.get(posts_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data['results']), 1)
            self.assertEqual(response.data['results'][0]['status'], 'published')
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)


class SocialInteractionWorkflowTest(APITestCase):
    """Test complete social interaction workflows."""
    
    def setUp(self):
        # Create users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        # Verify both users
        for user in [self.user1, self.user2]:
            user.profile.is_email_verified = True
            user.profile.save()
        
        # Create writer role and assign to user1
        self.writer_role = Role.objects.create(
            name='writer',
            display_name='Writer',
            description='Can create posts'
        )
        UserRole.objects.create(user=self.user1, role=self.writer_role)
        
        # Create a published post by user1
        self.post = Post.objects.create(
            title='Investment Strategies for Beginners',
            content='This comprehensive guide covers basic investment strategies that every beginner should know.',
            author='User One',
            author_user=self.user1,
            status='published',
            tags='investing, beginners, strategies'
        )
    
    def test_complete_social_interaction_workflow(self):
        """Test following users, saving posts, and email subscriptions."""
        # Step 1: User2 follows User1
        self.client.force_authenticate(user=self.user2)
        
        follow_url = reverse('accounts:follow-user', kwargs={'pk': self.user1.id})
        response = self.client.post(follow_url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['following'])
        
        # Verify follow relationship was created
        follow = UserFollow.objects.get(follower=self.user2, following=self.user1)
        self.assertIsNotNone(follow)
        
        # Step 2: User2 saves User1's post
        save_url = reverse('posts:save-post', kwargs={'pk': self.post.id})
        response = self.client.post(save_url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify post was saved
        saved_article = SavedArticle.objects.get(user=self.user2, post=self.post)
        self.assertIsNotNone(saved_article)
        
        # Step 3: User2 subscribes to email notifications
        subscribe_data = {
            'subscription_type': 'all_posts'
        }
        
        subscribe_url = reverse('notifications:subscribe')
        response = self.client.post(subscribe_url, subscribe_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify subscription was created
        subscription = EmailSubscription.objects.get(user=self.user2)
        self.assertEqual(subscription.subscription_type, 'all_posts')
        self.assertTrue(subscription.is_active)
        
        # Step 4: Check user2's saved posts
        saved_url = reverse('posts:saved-posts')
        response = self.client.get(saved_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['post']['id'], self.post.id)
        
        # Step 5: Check user1's followers
        followers_url = reverse('accounts:user-followers', kwargs={'pk': self.user1.id})
        response = self.client.get(followers_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['username'], 'user2')
        
        # Step 6: User2 unfollows User1
        response = self.client.delete(follow_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify follow relationship was removed
        self.assertFalse(UserFollow.objects.filter(
            follower=self.user2, following=self.user1
        ).exists())


class ContentModerationWorkflowTest(APITestCase):
    """Test complete content moderation workflow."""
    
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
        
        # Create editor role and assign to moderator
        self.editor_role = Role.objects.create(
            name='editor',
            display_name='Editor',
            description='Can moderate content'
        )
        UserRole.objects.create(user=self.moderator, role=self.editor_role)
        
        # Create writer role and assign to author
        self.writer_role = Role.objects.create(
            name='writer',
            display_name='Writer',
            description='Can create posts'
        )
        UserRole.objects.create(user=self.author, role=self.writer_role)
        
        # Create a published post
        self.post = Post.objects.create(
            title='Controversial Investment Advice',
            content='This post contains some controversial investment advice that might be flagged.',
            author='Author User',
            author_user=self.author,
            status='published'
        )
    
    @patch('moderation.tasks.send_flag_notification.delay')
    @patch('moderation.tasks.send_moderation_notification.delay')
    def test_complete_moderation_workflow(self, mock_moderation_task, mock_flag_task):
        """Test complete workflow from flagging to resolution."""
        # Step 1: User flags content
        self.client.force_authenticate(user=self.flagger)
        
        flag_data = {
            'reason': 'inappropriate',
            'description': 'This content promotes risky investment strategies without proper disclaimers.'
        }
        
        flag_url = reverse('moderation:flag-post', kwargs={'pk': self.post.id})
        response = self.client.post(flag_url, flag_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        flag_id = response.data['id']
        
        # Verify flag was created
        flag = ContentFlag.objects.get(id=flag_id)
        self.assertEqual(flag.post, self.post)
        self.assertEqual(flag.flagged_by, self.flagger)
        self.assertEqual(flag.status, 'pending')
        
        # Verify notification task was called
        mock_flag_task.assert_called_once_with(flag_id)
        
        # Step 2: Moderator views moderation dashboard
        self.client.force_authenticate(user=self.moderator)
        
        dashboard_url = reverse('moderation:moderation-dashboard')
        response = self.client.get(dashboard_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['pending_flags'], 1)
        self.assertIn('inappropriate', response.data['flag_reasons_breakdown'])
        
        # Step 3: Moderator views flag details
        flag_detail_url = reverse('moderation:flag-detail', kwargs={'pk': flag_id})
        response = self.client.get(flag_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['reason'], 'inappropriate')
        self.assertEqual(response.data['status'], 'pending')
        
        # Step 4: Moderator resolves flag as valid
        resolution_data = {
            'status': 'resolved_valid',
            'resolution_notes': 'Content requires disclaimer. Author contacted.',
            'action_taken': 'warning_issued'
        }
        
        response = self.client.put(flag_detail_url, resolution_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify flag was resolved
        flag.refresh_from_db()
        self.assertEqual(flag.status, 'resolved_valid')
        self.assertEqual(flag.reviewed_by, self.moderator)
        self.assertEqual(flag.action_taken, 'warning_issued')
        self.assertIsNotNone(flag.reviewed_at)
        
        # Verify moderation notification task was called
        mock_moderation_task.assert_called_once_with(flag_id)
        
        # Step 5: Verify moderation action was created
        moderation_action = ModerationAction.objects.get(flag=flag)
        self.assertEqual(moderation_action.action_type, 'warning_issued')
        self.assertEqual(moderation_action.moderator, self.moderator)
        self.assertEqual(moderation_action.affected_user, self.author)
        
        # Step 6: Check updated dashboard statistics
        response = self.client.get(dashboard_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['pending_flags'], 0)
        self.assertEqual(len(response.data['recent_actions']), 1)


class EmailNotificationWorkflowTest(APITestCase):
    """Test email notification workflows."""
    
    def setUp(self):
        # Create users
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='testpass123'
        )
        self.subscriber = User.objects.create_user(
            username='subscriber',
            email='subscriber@example.com',
            password='testpass123'
        )
        
        # Create writer role
        self.writer_role = Role.objects.create(
            name='writer',
            display_name='Writer',
            description='Can create posts'
        )
        UserRole.objects.create(user=self.author, role=self.writer_role)
        
        # Create email subscription
        self.subscription = EmailSubscription.objects.create(
            user=self.subscriber,
            email=self.subscriber.email,
            subscription_type='all_posts',
            is_active=True
        )
    
    @patch('notifications.tasks.send_new_post_notification.delay')
    def test_email_notification_workflow(self, mock_notification_task):
        """Test email notification when new post is published."""
        self.client.force_authenticate(user=self.author)
        
        # Create and publish a post
        post_data = {
            'title': 'New Market Analysis',
            'content': 'This is a comprehensive analysis of current market conditions and future predictions.',
            'tags': 'market, analysis, predictions',
            'status': 'published'
        }
        
        posts_url = reverse('posts:post-list-create')
        response = self.client.post(posts_url, post_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post_id = response.data['id']
        
        # Verify notification task was triggered
        mock_notification_task.assert_called_once_with(post_id)
        
        # Test unsubscribe workflow
        unsubscribe_token = self.subscription.unsubscribe_token
        unsubscribe_url = reverse('notifications:unsubscribe', kwargs={'token': unsubscribe_token})
        
        response = self.client.get(unsubscribe_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify subscription was deactivated
        self.subscription.refresh_from_db()
        self.assertFalse(self.subscription.is_active)


class APIErrorHandlingTest(APITestCase):
    """Test API error handling across different scenarios."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_authentication_errors(self):
        """Test various authentication error scenarios."""
        # Test accessing protected endpoint without authentication
        profile_url = reverse('accounts:user-profile')
        response = self.client.get(profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test login with invalid credentials
        login_url = reverse('accounts:login')
        invalid_data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(login_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_permission_errors(self):
        """Test permission-related error scenarios."""
        self.client.force_authenticate(user=self.user)
        
        # Test accessing moderation endpoint without proper role
        dashboard_url = reverse('moderation:moderation-dashboard')
        response = self.client.get(dashboard_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_validation_errors(self):
        """Test validation error scenarios."""
        self.client.force_authenticate(user=self.user)
        
        # Test creating post with invalid data
        posts_url = reverse('posts:post-list-create')
        invalid_data = {
            'title': 'Hi',  # Too short
            'content': 'Short',  # Too short
            'status': 'invalid_status'  # Invalid choice
        }
        
        response = self.client.post(posts_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)
        self.assertIn('content', response.data)
    
    def test_not_found_errors(self):
        """Test 404 error scenarios."""
        self.client.force_authenticate(user=self.user)
        
        # Test accessing non-existent post
        post_url = reverse('posts:post-detail', kwargs={'pk': 99999})
        response = self.client.get(post_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class APIPerformanceTest(APITestCase):
    """Basic performance tests for API endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create writer role
        self.writer_role = Role.objects.create(
            name='writer',
            display_name='Writer',
            description='Can create posts'
        )
        UserRole.objects.create(user=self.user, role=self.writer_role)
        
        self.client.force_authenticate(user=self.user)
        
        # Create multiple posts for testing
        for i in range(50):
            Post.objects.create(
                title=f'Test Post {i}',
                content=f'This is test post content number {i}. ' * 10,
                author=f'Author {i}',
                author_user=self.user,
                status='published',
                tags=f'tag{i}, test, performance'
            )
    
    def test_post_list_performance(self):
        """Test performance of post list endpoint with pagination."""
        import time
        
        posts_url = reverse('posts:post-list-create')
        
        # Test with different page sizes
        for page_size in [10, 25, 50]:
            start_time = time.time()
            response = self.client.get(posts_url, {'page_size': page_size})
            end_time = time.time()
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertLessEqual(len(response.data['results']), page_size)
            
            # Response should be under 1 second
            response_time = end_time - start_time
            self.assertLess(response_time, 1.0, 
                          f"Response time {response_time:.2f}s too slow for page_size={page_size}")
    
    def test_search_performance(self):
        """Test performance of search functionality."""
        import time
        
        posts_url = reverse('posts:post-list-create')
        
        start_time = time.time()
        response = self.client.get(posts_url, {'search': 'test'})
        end_time = time.time()
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Search should be under 2 seconds
        response_time = end_time - start_time
        self.assertLess(response_time, 2.0, 
                      f"Search response time {response_time:.2f}s too slow")
    
    def test_database_query_optimization(self):
        """Test that endpoints use optimized database queries."""
        from django.test.utils import override_settings
        from django.db import connection
        
        posts_url = reverse('posts:post-list-create')
        
        with override_settings(DEBUG=True):
            # Reset query count
            connection.queries_log.clear()
            
            response = self.client.get(posts_url, {'page_size': 10})
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Should not have excessive queries (N+1 problem)
            query_count = len(connection.queries)
            self.assertLess(query_count, 10, 
                          f"Too many database queries: {query_count}")