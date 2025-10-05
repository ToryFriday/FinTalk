"""
Tests for social features in the accounts app.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from unittest.mock import patch

from .models import UserProfile, UserFollow
from .tasks import send_new_follower_notification


class UserFollowModelTest(TestCase):
    """Test cases for UserFollow model."""
    
    def setUp(self):
        """Set up test data."""
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
        self.user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )
    
    def test_create_follow_relationship(self):
        """Test creating a follow relationship."""
        follow = UserFollow.objects.create(
            follower=self.user1,
            following=self.user2
        )
        
        self.assertEqual(follow.follower, self.user1)
        self.assertEqual(follow.following, self.user2)
        self.assertIsNotNone(follow.created_at)
        self.assertEqual(str(follow), f"{self.user1.username} follows {self.user2.username}")
    
    def test_unique_follow_relationship(self):
        """Test that follow relationships are unique."""
        UserFollow.objects.create(
            follower=self.user1,
            following=self.user2
        )
        
        # Attempting to create duplicate should raise IntegrityError
        with self.assertRaises(IntegrityError):
            UserFollow.objects.create(
                follower=self.user1,
                following=self.user2
            )
    
    def test_cannot_follow_self(self):
        """Test that users cannot follow themselves."""
        with self.assertRaises(ValidationError):
            follow = UserFollow(
                follower=self.user1,
                following=self.user1
            )
            follow.full_clean()
    
    def test_follow_relationship_ordering(self):
        """Test that follow relationships are ordered by creation date."""
        follow1 = UserFollow.objects.create(
            follower=self.user1,
            following=self.user2
        )
        follow2 = UserFollow.objects.create(
            follower=self.user1,
            following=self.user3
        )
        
        follows = UserFollow.objects.all()
        self.assertEqual(follows[0], follow2)  # Most recent first
        self.assertEqual(follows[1], follow1)


class UserSocialMethodsTest(TestCase):
    """Test cases for User model social methods."""
    
    def setUp(self):
        """Set up test data."""
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
        self.user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )
        self.user4 = User.objects.create_user(
            username='user4',
            email='user4@example.com',
            password='testpass123'
        )
    
    def test_follow_user(self):
        """Test following a user."""
        result = self.user1.follow(self.user2)
        
        self.assertTrue(result)
        self.assertTrue(self.user1.is_following(self.user2))
        self.assertTrue(self.user2.is_followed_by(self.user1))
        self.assertEqual(self.user1.get_following_count(), 1)
        self.assertEqual(self.user2.get_followers_count(), 1)
    
    def test_follow_user_twice(self):
        """Test that following the same user twice returns False."""
        self.user1.follow(self.user2)
        result = self.user1.follow(self.user2)
        
        self.assertFalse(result)
        self.assertEqual(self.user1.get_following_count(), 1)
    
    def test_follow_self(self):
        """Test that users cannot follow themselves."""
        result = self.user1.follow(self.user1)
        
        self.assertFalse(result)
        self.assertEqual(self.user1.get_following_count(), 0)
    
    def test_unfollow_user(self):
        """Test unfollowing a user."""
        self.user1.follow(self.user2)
        result = self.user1.unfollow(self.user2)
        
        self.assertTrue(result)
        self.assertFalse(self.user1.is_following(self.user2))
        self.assertFalse(self.user2.is_followed_by(self.user1))
        self.assertEqual(self.user1.get_following_count(), 0)
        self.assertEqual(self.user2.get_followers_count(), 0)
    
    def test_unfollow_not_following(self):
        """Test unfollowing a user that is not being followed."""
        result = self.user1.unfollow(self.user2)
        
        self.assertFalse(result)
    
    def test_get_followers(self):
        """Test getting followers."""
        self.user1.follow(self.user2)
        self.user3.follow(self.user2)
        
        followers = self.user2.get_followers()
        
        self.assertEqual(followers.count(), 2)
        self.assertIn(self.user1, followers)
        self.assertIn(self.user3, followers)
    
    def test_get_following(self):
        """Test getting following."""
        self.user1.follow(self.user2)
        self.user1.follow(self.user3)
        
        following = self.user1.get_following()
        
        self.assertEqual(following.count(), 2)
        self.assertIn(self.user2, following)
        self.assertIn(self.user3, following)
    
    def test_get_mutual_followers(self):
        """Test getting mutual followers."""
        # user4 follows both user1 and user2
        self.user4.follow(self.user1)
        self.user4.follow(self.user2)
        
        # user3 follows only user1
        self.user3.follow(self.user1)
        
        mutual = self.user1.get_mutual_followers(self.user2)
        
        self.assertEqual(mutual.count(), 1)
        self.assertIn(self.user4, mutual)
        self.assertNotIn(self.user3, mutual)
    
    def test_get_suggested_users_to_follow(self):
        """Test getting suggested users to follow."""
        # user1 follows user2
        self.user1.follow(self.user2)
        
        # user2 follows user3 and user4
        self.user2.follow(self.user3)
        self.user2.follow(self.user4)
        
        # user1 should get user3 and user4 as suggestions
        suggested = self.user1.get_suggested_users_to_follow()
        
        self.assertIn(self.user3, suggested)
        self.assertIn(self.user4, suggested)
        self.assertNotIn(self.user2, suggested)  # Already following
        self.assertNotIn(self.user1, suggested)  # Self


class SocialAPIViewsTest(APITestCase):
    """Test cases for social API views."""
    
    def setUp(self):
        """Set up test data."""
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
        self.user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )
        
        # Create profiles
        UserProfile.objects.get_or_create(user=self.user1)
        UserProfile.objects.get_or_create(user=self.user2)
        UserProfile.objects.get_or_create(user=self.user3)
    
    def test_follow_user_authenticated(self):
        """Test following a user when authenticated."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('accounts:follow-user', kwargs={'pk': self.user2.id})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['action'], 'followed')
        self.assertTrue(response.data['is_following'])
        self.assertTrue(self.user1.is_following(self.user2))
    
    def test_unfollow_user_authenticated(self):
        """Test unfollowing a user when authenticated."""
        self.user1.follow(self.user2)
        self.client.force_authenticate(user=self.user1)
        url = reverse('accounts:follow-user', kwargs={'pk': self.user2.id})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['action'], 'unfollowed')
        self.assertFalse(response.data['is_following'])
        self.assertFalse(self.user1.is_following(self.user2))
    
    def test_follow_user_unauthenticated(self):
        """Test following a user when not authenticated."""
        url = reverse('accounts:follow-user', kwargs={'pk': self.user2.id})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_follow_self(self):
        """Test that users cannot follow themselves via API."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('accounts:follow-user', kwargs={'pk': self.user1.id})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('cannot follow themselves', response.data['error'])
    
    def test_follow_nonexistent_user(self):
        """Test following a non-existent user."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('accounts:follow-user', kwargs={'pk': 9999})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_user_followers(self):
        """Test getting user's followers."""
        self.user1.follow(self.user2)
        self.user3.follow(self.user2)
        
        url = reverse('accounts:user-followers', kwargs={'pk': self.user2.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['metadata']['total_followers'], 2)
    
    def test_get_user_following(self):
        """Test getting users that a user is following."""
        self.user1.follow(self.user2)
        self.user1.follow(self.user3)
        
        url = reverse('accounts:user-following', kwargs={'pk': self.user1.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['metadata']['total_following'], 2)
    
    def test_get_user_social_profile(self):
        """Test getting user's social profile."""
        self.user1.follow(self.user2)
        self.user3.follow(self.user2)
        
        url = reverse('accounts:user-social-profile', kwargs={'pk': self.user2.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_id'], self.user2.id)
        self.assertEqual(response.data['username'], self.user2.username)
        self.assertEqual(response.data['followers_count'], 2)
        self.assertEqual(response.data['following_count'], 0)
    
    def test_check_follow_status_authenticated(self):
        """Test checking follow status when authenticated."""
        self.user1.follow(self.user2)
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('accounts:check-follow-status', kwargs={'pk': self.user2.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_following'])
        self.assertFalse(response.data['is_followed_by'])
        self.assertEqual(response.data['followers_count'], 1)
    
    def test_check_follow_status_unauthenticated(self):
        """Test checking follow status when not authenticated."""
        url = reverse('accounts:check-follow-status', kwargs={'pk': self.user2.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_suggested_users_authenticated(self):
        """Test getting suggested users when authenticated."""
        # Set up follow relationships for suggestions
        self.user1.follow(self.user2)
        self.user2.follow(self.user3)
        
        self.client.force_authenticate(user=self.user1)
        url = reverse('accounts:suggested-users')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data['results'], list)
        self.assertIn('metadata', response.data)
    
    def test_get_suggested_users_unauthenticated(self):
        """Test getting suggested users when not authenticated."""
        url = reverse('accounts:suggested-users')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_mutual_followers(self):
        """Test getting mutual followers."""
        # user3 follows both user1 and user2
        self.user3.follow(self.user1)
        self.user3.follow(self.user2)
        
        self.client.force_authenticate(user=self.user1)
        url = reverse('accounts:mutual-followers', kwargs={'pk': self.user2.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['mutual_followers_count'], 1)
        self.assertEqual(len(response.data['mutual_followers']), 1)
        self.assertEqual(response.data['mutual_followers'][0]['username'], self.user3.username)


class SocialTasksTest(TestCase):
    """Test cases for social-related Celery tasks."""
    
    def setUp(self):
        """Set up test data."""
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
        
        # Create profiles
        UserProfile.objects.get_or_create(user=self.user1)
        UserProfile.objects.get_or_create(user=self.user2)
    
    @patch('accounts.tasks.send_mail')
    def test_send_new_follower_notification(self, mock_send_mail):
        """Test sending new follower notification email."""
        mock_send_mail.return_value = True
        
        result = send_new_follower_notification(self.user1.id, self.user2.id)
        
        self.assertIn('notification sent', result.lower())
        mock_send_mail.assert_called_once()
        
        # Check email parameters
        call_args = mock_send_mail.call_args
        self.assertIn(self.user1.profile.get_full_name(), call_args[1]['subject'])
        self.assertEqual(call_args[1]['recipient_list'], [self.user2.email])
    
    @patch('accounts.tasks.send_mail')
    def test_send_new_follower_notification_user_not_found(self, mock_send_mail):
        """Test sending notification when user doesn't exist."""
        result = send_new_follower_notification(9999, self.user2.id)
        
        self.assertEqual(result, 'User not found')
        mock_send_mail.assert_not_called()


class SocialIntegrationTest(APITestCase):
    """Integration tests for social features."""
    
    def setUp(self):
        """Set up test data."""
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
        self.user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )
        
        # Create profiles with some data
        profile1 = UserProfile.objects.get_or_create(user=self.user1)[0]
        profile1.bio = "I'm user1, a test user"
        profile1.save()
        
        profile2 = UserProfile.objects.get_or_create(user=self.user2)[0]
        profile2.bio = "I'm user2, another test user"
        profile2.save()
    
    @patch('accounts.tasks.send_new_follower_notification.delay')
    def test_complete_follow_workflow(self, mock_notification_task):
        """Test complete follow workflow with notifications."""
        self.client.force_authenticate(user=self.user1)
        
        # 1. Follow user2
        follow_url = reverse('accounts:follow-user', kwargs={'pk': self.user2.id})
        response = self.client.post(follow_url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['is_following'])
        
        # Check that notification task was called
        mock_notification_task.assert_called_once_with(self.user1.id, self.user2.id)
        
        # 2. Check follow status
        status_url = reverse('accounts:check-follow-status', kwargs={'pk': self.user2.id})
        response = self.client.get(status_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_following'])
        self.assertEqual(response.data['followers_count'], 1)
        
        # 3. Get user2's followers (should include user1)
        followers_url = reverse('accounts:user-followers', kwargs={'pk': self.user2.id})
        response = self.client.get(followers_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['username'], self.user1.username)
        
        # 4. Get user1's following (should include user2)
        following_url = reverse('accounts:user-following', kwargs={'pk': self.user1.id})
        response = self.client.get(following_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['username'], self.user2.username)
        
        # 5. Unfollow user2
        response = self.client.post(follow_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_following'])
        
        # 6. Verify unfollow
        response = self.client.get(status_url)
        self.assertFalse(response.data['is_following'])
        self.assertEqual(response.data['followers_count'], 0)
    
    def test_social_profile_with_stats(self):
        """Test social profile endpoint with various stats."""
        # Set up relationships
        self.user1.follow(self.user2)
        self.user3.follow(self.user2)
        self.user2.follow(self.user3)
        
        self.client.force_authenticate(user=self.user1)
        
        # Get user2's social profile
        url = reverse('accounts:user-social-profile', kwargs={'pk': self.user2.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertEqual(data['user_id'], self.user2.id)
        self.assertEqual(data['username'], self.user2.username)
        self.assertEqual(data['followers_count'], 2)  # user1 and user3
        self.assertEqual(data['following_count'], 1)  # user3
        self.assertTrue(data['is_following'])  # user1 is following user2
        self.assertFalse(data['is_followed_by'])  # user2 is not following user1
        self.assertEqual(data['bio'], "I'm user2, another test user")
    
    def test_pagination_in_followers_list(self):
        """Test pagination in followers list."""
        # Create multiple followers
        followers = []
        for i in range(15):
            user = User.objects.create_user(
                username=f'follower{i}',
                email=f'follower{i}@example.com',
                password='testpass123'
            )
            user.follow(self.user1)
            followers.append(user)
        
        url = reverse('accounts:user-followers', kwargs={'pk': self.user1.id})
        
        # Test first page
        response = self.client.get(url, {'page': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 15)
        self.assertIsNotNone(response.data.get('next'))
        
        # Test second page
        response = self.client.get(url, {'page': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data.get('next'))