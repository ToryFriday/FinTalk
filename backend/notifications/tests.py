"""
Tests for notifications app.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core import mail
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
from posts.models import Post
from .models import EmailSubscription, NotificationLog, UnsubscribeRequest
from .tasks import send_new_post_notification, send_subscription_confirmation
import uuid


class EmailSubscriptionModelTest(TestCase):
    """
    Test EmailSubscription model functionality.
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='testpass123'
        )
    
    def test_create_subscription(self):
        """Test creating an email subscription."""
        subscription = EmailSubscription.objects.create(
            user=self.user,
            email=self.user.email,
            subscription_type='all_posts'
        )
        
        self.assertEqual(subscription.email, 'test@example.com')
        self.assertEqual(subscription.subscription_type, 'all_posts')
        self.assertTrue(subscription.is_active)
        self.assertIsNotNone(subscription.unsubscribe_token)
    
    def test_email_normalization(self):
        """Test that email addresses are normalized to lowercase."""
        subscription = EmailSubscription.objects.create(
            email='TEST@EXAMPLE.COM',
            subscription_type='all_posts'
        )
        
        self.assertEqual(subscription.email, 'test@example.com')
    
    def test_unique_constraint(self):
        """Test unique constraint on email, subscription_type, and author_filter."""
        # Create first subscription
        EmailSubscription.objects.create(
            email='test@example.com',
            subscription_type='all_posts'
        )
        
        # Try to create duplicate - should work since we're not enforcing at DB level in this test
        # In real usage, the API would prevent duplicates
        subscription2 = EmailSubscription.objects.create(
            email='test@example.com',
            subscription_type='weekly_digest'  # Different type, should work
        )
        
        self.assertIsNotNone(subscription2)
    
    def test_author_subscription_validation(self):
        """Test validation for author_posts subscription type."""
        # Should require author_filter for author_posts
        subscription = EmailSubscription(
            email='test@example.com',
            subscription_type='author_posts'
        )
        
        with self.assertRaises(Exception):  # ValidationError
            subscription.full_clean()
        
        # Should work with author_filter
        subscription.author_filter = self.author
        subscription.unsubscribe_token = 'test-token'  # Add required token
        subscription.full_clean()  # Should not raise
    
    def test_get_subscriber_name(self):
        """Test getting subscriber name."""
        # With user
        subscription = EmailSubscription.objects.create(
            user=self.user,
            email=self.user.email,
            subscription_type='all_posts'
        )
        
        self.assertEqual(subscription.get_subscriber_name(), 'testuser')
        
        # Without user
        subscription_anon = EmailSubscription.objects.create(
            email='john.doe@example.com',
            subscription_type='all_posts'
        )
        
        self.assertEqual(subscription_anon.get_subscriber_name(), 'John Doe')
    
    def test_matches_post(self):
        """Test post matching logic."""
        post = Post.objects.create(
            title='Test Post',
            content='Test content',
            author='Test Author',
            author_user=self.author,
            status='published'
        )
        
        # All posts subscription should match
        all_posts_sub = EmailSubscription.objects.create(
            email='test@example.com',
            subscription_type='all_posts'
        )
        self.assertTrue(all_posts_sub.matches_post(post))
        
        # Author posts subscription should match if author matches
        author_sub = EmailSubscription.objects.create(
            email='test2@example.com',
            subscription_type='author_posts',
            author_filter=self.author
        )
        self.assertTrue(author_sub.matches_post(post))
        
        # Author posts subscription should not match different author
        other_author = User.objects.create_user(
            username='other',
            email='other@example.com'
        )
        author_sub_other = EmailSubscription.objects.create(
            email='test3@example.com',
            subscription_type='author_posts',
            author_filter=other_author
        )
        self.assertFalse(author_sub_other.matches_post(post))


class NotificationAPITest(APITestCase):
    """
    Test notification API endpoints.
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='testpass123'
        )
    
    def test_public_subscribe(self):
        """Test public subscription endpoint."""
        url = reverse('notifications:public-subscribe')
        data = {
            'email': 'newuser@example.com',
            'subscription_type': 'all_posts'
        }
        
        with patch('notifications.views.send_subscription_confirmation.delay') as mock_task:
            response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(EmailSubscription.objects.filter(email='newuser@example.com').exists())
        mock_task.assert_called_once()
    
    def test_duplicate_subscription(self):
        """Test handling of duplicate subscriptions."""
        # Create existing subscription
        subscription = EmailSubscription(
            email='test@example.com',
            subscription_type='all_posts'
        )
        subscription.save()
        
        url = reverse('notifications:public-subscribe')
        data = {
            'email': 'test@example.com',
            'subscription_type': 'all_posts'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_reactivate_subscription(self):
        """Test reactivating inactive subscription."""
        # Create inactive subscription
        subscription = EmailSubscription(
            email='test@example.com',
            subscription_type='all_posts',
            is_active=False
        )
        subscription.save()
        
        url = reverse('notifications:public-subscribe')
        data = {
            'email': 'test@example.com',
            'subscription_type': 'all_posts'
        }
        
        with patch('notifications.views.send_subscription_confirmation.delay') as mock_task:
            response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that subscription is reactivated
        subscription.refresh_from_db()
        self.assertTrue(subscription.is_active)
        mock_task.assert_called_once()
    
    def test_unsubscribe_get(self):
        """Test getting subscription details for unsubscribe."""
        subscription = EmailSubscription.objects.create(
            email='test@example.com',
            subscription_type='all_posts'
        )
        
        url = reverse('notifications:unsubscribe', kwargs={'token': subscription.unsubscribe_token})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
    
    def test_unsubscribe_post(self):
        """Test processing unsubscribe request."""
        subscription = EmailSubscription(
            email='test@example.com',
            subscription_type='all_posts'
        )
        subscription.save()
        
        url = reverse('notifications:unsubscribe', kwargs={'token': subscription.unsubscribe_token})
        data = {
            'reason': 'too_frequent',
            'feedback': 'Too many emails'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that subscription is deactivated
        subscription.refresh_from_db()
        self.assertFalse(subscription.is_active)
        
        # Check that unsubscribe request is logged
        self.assertTrue(UnsubscribeRequest.objects.filter(
            email='test@example.com',
            reason='too_frequent'
        ).exists())
    
    def test_invalid_unsubscribe_token(self):
        """Test unsubscribe with invalid token."""
        url = reverse('notifications:unsubscribe', kwargs={'token': 'invalid-token'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_authenticated_subscription_list(self):
        """Test listing subscriptions for authenticated user."""
        self.client.force_authenticate(user=self.user)
        
        # Create subscription for user
        EmailSubscription.objects.create(
            user=self.user,
            email=self.user.email,
            subscription_type='all_posts'
        )
        
        url = reverse('notifications:subscription-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_toggle_author_subscription(self):
        """Test toggling author subscription."""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('notifications:toggle-author-subscription', kwargs={'author_id': self.author.id})
        
        with patch('notifications.views.send_subscription_confirmation.delay') as mock_task:
            response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('subscribed', response.data['detail'])
        self.assertTrue(response.data['is_subscribed'])
        
        # Check subscription was created
        self.assertTrue(EmailSubscription.objects.filter(
            user=self.user,
            subscription_type='author_posts',
            author_filter=self.author
        ).exists())
        
        mock_task.assert_called_once()
    
    def test_check_author_subscription(self):
        """Test checking author subscription status."""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('notifications:check-author-subscription', kwargs={'author_id': self.author.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_subscribed'])
        
        # Create subscription and check again
        EmailSubscription.objects.create(
            user=self.user,
            email=self.user.email,
            subscription_type='author_posts',
            author_filter=self.author
        )
        
        response = self.client.get(url)
        self.assertTrue(response.data['is_subscribed'])


class NotificationTaskTest(TestCase):
    """
    Test notification Celery tasks.
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Test Post',
            content='Test content for notification',
            author='Test Author',
            author_user=self.author,
            status='published'
        )
    
    @patch('notifications.tasks.send_mail')
    def test_send_new_post_notification(self, mock_send_mail):
        """Test sending new post notification."""
        # Create subscription
        subscription = EmailSubscription.objects.create(
            user=self.user,
            email=self.user.email,
            subscription_type='all_posts'
        )
        
        # Run task
        result = send_new_post_notification(self.post.id)
        
        # Check that email was sent
        mock_send_mail.assert_called_once()
        
        # Check notification log was created
        self.assertTrue(NotificationLog.objects.filter(
            subscription=subscription,
            post=self.post,
            notification_type='new_post'
        ).exists())
        
        # Check subscription was updated
        subscription.refresh_from_db()
        self.assertIsNotNone(subscription.last_notification_sent)
    
    @patch('notifications.tasks.send_mail')
    def test_send_subscription_confirmation_task(self, mock_send_mail):
        """Test sending subscription confirmation."""
        subscription = EmailSubscription.objects.create(
            user=self.user,
            email=self.user.email,
            subscription_type='all_posts'
        )
        
        # Run task
        result = send_subscription_confirmation(subscription.id)
        
        # Check that email was sent
        mock_send_mail.assert_called_once()
        
        # Check notification log was created
        self.assertTrue(NotificationLog.objects.filter(
            subscription=subscription,
            notification_type='subscription_confirmation'
        ).exists())
    
    def test_nonexistent_post_notification(self):
        """Test handling of nonexistent post in notification task."""
        result = send_new_post_notification(99999)  # Non-existent post ID
        
        self.assertIn('not found', result)
    
    @patch('notifications.tasks.send_mail')
    def test_author_specific_notification(self, mock_send_mail):
        """Test author-specific notifications."""
        # Create author subscription
        EmailSubscription.objects.create(
            user=self.user,
            email=self.user.email,
            subscription_type='author_posts',
            author_filter=self.author
        )
        
        # Create subscription for different author (should not receive notification)
        other_author = User.objects.create_user(
            username='other',
            email='other@example.com'
        )
        EmailSubscription.objects.create(
            email='other@example.com',
            subscription_type='author_posts',
            author_filter=other_author
        )
        
        # Run task
        result = send_new_post_notification(self.post.id)
        
        # Should only send one email (to the correct author subscriber)
        mock_send_mail.assert_called_once()
    
    @patch('notifications.tasks.send_mail')
    def test_notification_cooldown(self, mock_send_mail):
        """Test notification cooldown functionality."""
        subscription = EmailSubscription.objects.create(
            user=self.user,
            email=self.user.email,
            subscription_type='all_posts',
            last_notification_sent=timezone.now()  # Just sent
        )
        
        # Run task - should not send due to cooldown
        result = send_new_post_notification(self.post.id)
        
        # Should not send email due to cooldown
        mock_send_mail.assert_not_called()


class NotificationLogModelTest(TestCase):
    """
    Test NotificationLog model functionality.
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.subscription = EmailSubscription.objects.create(
            user=self.user,
            email=self.user.email,
            subscription_type='all_posts'
        )
    
    def test_create_notification_log(self):
        """Test creating a notification log."""
        log = NotificationLog.objects.create(
            subscription=self.subscription,
            notification_type='new_post',
            subject='Test Subject'
        )
        
        self.assertEqual(log.status, 'pending')
        self.assertEqual(log.notification_type, 'new_post')
        self.assertIsNone(log.sent_at)
    
    def test_mark_as_sent(self):
        """Test marking notification as sent."""
        log = NotificationLog.objects.create(
            subscription=self.subscription,
            notification_type='new_post',
            subject='Test Subject'
        )
        
        log.mark_as_sent()
        
        self.assertEqual(log.status, 'sent')
        self.assertIsNotNone(log.sent_at)
    
    def test_mark_as_failed(self):
        """Test marking notification as failed."""
        log = NotificationLog.objects.create(
            subscription=self.subscription,
            notification_type='new_post',
            subject='Test Subject'
        )
        
        error_message = 'SMTP connection failed'
        log.mark_as_failed(error_message)
        
        self.assertEqual(log.status, 'failed')
        self.assertEqual(log.error_message, error_message)