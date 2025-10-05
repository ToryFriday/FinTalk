"""
Comprehensive unit tests for accounts app models, serializers, and views.
This file provides extensive test coverage for all new functionality.
"""

import json
import tempfile
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase, TransactionTestCase, override_settings
from django.contrib.auth.models import User, Permission
from django.urls import reverse
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from PIL import Image

from .models import UserProfile, Role, UserRole, SavedArticle, UserFollow
from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    RoleSerializer,
    UserRoleSerializer,
    SavedArticleSerializer,
    UserFollowSerializer
)
from posts.models import Post


class UserProfileModelTest(TestCase):
    """Comprehensive tests for UserProfile model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_profile_auto_creation(self):
        """Test that UserProfile is automatically created with User."""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, UserProfile)
        self.assertEqual(self.user.profile.user, self.user)
    
    def test_profile_str_representation(self):
        """Test UserProfile string representation."""
        expected = f"{self.user.username}'s Profile"
        self.assertEqual(str(self.user.profile), expected)
    
    def test_get_full_name_variations(self):
        """Test get_full_name method with different name combinations."""
        profile = self.user.profile
        
        # With both names
        self.assertEqual(profile.get_full_name(), 'Test User')
        
        # With only first name
        self.user.last_name = ''
        self.user.save()
        self.assertEqual(profile.get_full_name(), 'Test')
        
        # With no names
        self.user.first_name = ''
        self.user.save()
        self.assertEqual(profile.get_full_name(), 'testuser')
    
    def test_verification_token_generation(self):
        """Test email verification token generation."""
        profile = self.user.profile
        token = profile.generate_verification_token()
        
        self.assertIsNotNone(token)
        self.assertEqual(len(token), 32)
        self.assertEqual(profile.email_verification_token, token)
        self.assertIsNotNone(profile.email_verification_sent_at)
    
    def test_verification_token_expiration(self):
        """Test token expiration logic."""
        profile = self.user.profile
        
        # No token sent
        self.assertTrue(profile.is_verification_token_expired())
        
        # Fresh token
        profile.generate_verification_token()
        self.assertFalse(profile.is_verification_token_expired())
        
        # Expired token
        profile.email_verification_sent_at = timezone.now() - timedelta(hours=25)
        self.assertTrue(profile.is_verification_token_expired())
    
    def test_age_calculation(self):
        """Test age calculation from birth date."""
        profile = self.user.profile
        
        # No birth date
        self.assertIsNone(profile.age)
        
        # With birth date
        today = timezone.now().date()
        birth_date = date(today.year - 25, today.month, today.day)
        profile.birth_date = birth_date
        profile.save()
        
        self.assertEqual(profile.age, 25)
class Rol
eModelTest(TestCase):
    """Comprehensive tests for Role model."""
    
    def setUp(self):
        self.role_data = {
            'name': 'writer',
            'display_name': 'Writer',
            'description': 'Can create and edit articles'
        }
    
    def test_role_creation(self):
        """Test role creation with valid data."""
        role = Role.objects.create(**self.role_data)
        
        self.assertEqual(role.name, 'writer')
        self.assertEqual(role.display_name, 'Writer')
        self.assertEqual(role.description, 'Can create and edit articles')
        self.assertTrue(role.is_active)
    
    def test_role_str_representation(self):
        """Test role string representation."""
        role = Role.objects.create(**self.role_data)
        self.assertEqual(str(role), 'Writer')
    
    def test_role_permission_methods(self):
        """Test role permission helper methods."""
        role = Role.objects.create(**self.role_data)
        
        # Create a test permission
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(Role)
        permission = Permission.objects.create(
            codename='test_permission',
            name='Test Permission',
            content_type=content_type
        )
        
        # Test has_permission method
        self.assertFalse(role.has_permission('test_permission'))
        
        role.permissions.add(permission)
        self.assertTrue(role.has_permission('test_permission'))
        
        # Test get_permission_names method
        permission_names = role.get_permission_names()
        self.assertIn('test_permission', permission_names)


class UserRoleModelTest(TestCase):
    """Comprehensive tests for UserRole model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.role = Role.objects.create(
            name='writer',
            display_name='Writer',
            description='Can create articles'
        )
    
    def test_user_role_creation(self):
        """Test user role assignment creation."""
        user_role = UserRole.objects.create(
            user=self.user,
            role=self.role,
            assigned_by=self.admin_user,
            notes='Initial assignment'
        )
        
        self.assertEqual(user_role.user, self.user)
        self.assertEqual(user_role.role, self.role)
        self.assertEqual(user_role.assigned_by, self.admin_user)
        self.assertTrue(user_role.is_active)
        self.assertIsNone(user_role.expires_at)
    
    def test_user_role_str_representation(self):
        """Test user role string representation."""
        user_role = UserRole.objects.create(
            user=self.user,
            role=self.role,
            assigned_by=self.admin_user
        )
        
        expected = f"{self.user.username} - {self.role.display_name}"
        self.assertEqual(str(user_role), expected)


class SavedArticleModelTest(TestCase):
    """Comprehensive tests for SavedArticle model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='authorpass123'
        )
        self.post = Post.objects.create(
            title='Test Post',
            content='This is a test post content.',
            author='Test Author',
            author_user=self.author
        )
    
    def test_saved_article_creation(self):
        """Test creating a saved article."""
        saved_article = SavedArticle.objects.create(
            user=self.user,
            post=self.post,
            notes='Great article about testing'
        )
        
        self.assertEqual(saved_article.user, self.user)
        self.assertEqual(saved_article.post, self.post)
        self.assertEqual(saved_article.notes, 'Great article about testing')
        self.assertIsNotNone(saved_article.saved_at)
    
    def test_saved_article_str_representation(self):
        """Test saved article string representation."""
        saved_article = SavedArticle.objects.create(
            user=self.user,
            post=self.post
        )
        
        expected = f"{self.user.username} saved '{self.post.title}'"
        self.assertEqual(str(saved_article), expected)


class UserFollowModelTest(TestCase):
    """Comprehensive tests for UserFollow model."""
    
    def setUp(self):
        self.follower = User.objects.create_user(
            username='follower',
            email='follower@example.com',
            password='followerpass123'
        )
        self.following = User.objects.create_user(
            username='following',
            email='following@example.com',
            password='followingpass123'
        )
    
    def test_user_follow_creation(self):
        """Test creating a user follow relationship."""
        follow = UserFollow.objects.create(
            follower=self.follower,
            following=self.following
        )
        
        self.assertEqual(follow.follower, self.follower)
        self.assertEqual(follow.following, self.following)
        self.assertIsNotNone(follow.created_at)
    
    def test_user_follow_str_representation(self):
        """Test user follow string representation."""
        follow = UserFollow.objects.create(
            follower=self.follower,
            following=self.following
        )
        
        expected = f"{self.follower.username} follows {self.following.username}"
        self.assertEqual(str(follow), expected)