"""
Tests for enhanced Post model functionality.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

from posts.models import Post
from accounts.models import Role, UserRole


class EnhancedPostModelTest(TestCase):
    """Test cases for enhanced Post model functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.writer_user = User.objects.create_user(
            username='writer',
            email='writer@test.com',
            password='testpass123'
        )
        
        # Create roles
        self.admin_role = Role.objects.create(
            name='admin',
            display_name='Administrator',
            description='Full access'
        )
        
        self.writer_role = Role.objects.create(
            name='writer',
            display_name='Writer',
            description='Can write posts'
        )
        
        # Assign roles
        UserRole.objects.create(user=self.admin_user, role=self.admin_role)
        UserRole.objects.create(user=self.writer_user, role=self.writer_role)
    
    def test_post_creation_with_new_fields(self):
        """Test creating a post with new fields."""
        future_date = timezone.now() + timedelta(days=1)
        
        post = Post.objects.create(
            title='Test Post',
            content='This is test content for the post.',
            author='Test Author',
            author_user=self.writer_user,
            status='scheduled',
            scheduled_publish_date=future_date,
            tags='test, django'
        )
        
        self.assertEqual(post.status, 'scheduled')
        self.assertEqual(post.scheduled_publish_date, future_date)
        self.assertEqual(post.view_count, 0)
        self.assertEqual(post.author_user, self.writer_user)
    
    def test_post_status_choices(self):
        """Test post status validation."""
        post = Post(
            title='Test Post',
            content='This is test content.',
            author='Test Author',
            status='invalid_status'
        )
        
        with self.assertRaises(ValidationError):
            post.full_clean()
    
    def test_scheduled_post_validation(self):
        """Test validation for scheduled posts."""
        # Scheduled post without date should fail
        post = Post(
            title='Test Post',
            content='This is test content.',
            author='Test Author',
            status='scheduled'
        )
        
        with self.assertRaises(ValidationError):
            post.full_clean()
        
        # Scheduled post with past date should fail
        past_date = timezone.now() - timedelta(days=1)
        post.scheduled_publish_date = past_date
        
        with self.assertRaises(ValidationError):
            post.full_clean()
    
    def test_get_author_name_method(self):
        """Test the get_author_name method."""
        # Test with author_user having full name
        self.writer_user.first_name = 'John'
        self.writer_user.last_name = 'Doe'
        self.writer_user.save()
        
        post = Post.objects.create(
            title='Test Post',
            content='This is test content.',
            author='Test Author',
            author_user=self.writer_user
        )
        
        self.assertEqual(post.get_author_name(), 'John Doe')
        
        # Test with only first name
        self.writer_user.last_name = ''
        self.writer_user.save()
        
        self.assertEqual(post.get_author_name(), 'John')
        
        # Test with no names (should use username)
        self.writer_user.first_name = ''
        self.writer_user.save()
        
        self.assertEqual(post.get_author_name(), 'writer')
        
        # Test with no author_user (should use author field)
        post.author_user = None
        post.save()
        
        self.assertEqual(post.get_author_name(), 'Test Author')
    
    def test_post_status_methods(self):
        """Test post status checking methods."""
        post = Post.objects.create(
            title='Test Post',
            content='This is test content.',
            author='Test Author',
            status='draft'
        )
        
        self.assertTrue(post.is_draft())
        self.assertFalse(post.is_published())
        self.assertFalse(post.is_scheduled())
        self.assertTrue(post.can_be_published())
        
        # Change to published
        post.status = 'published'
        post.save()
        
        self.assertFalse(post.is_draft())
        self.assertTrue(post.is_published())
        self.assertFalse(post.is_scheduled())
        self.assertFalse(post.can_be_published())
    
    def test_publish_method(self):
        """Test the publish method."""
        future_date = timezone.now() + timedelta(days=1)
        
        post = Post.objects.create(
            title='Test Post',
            content='This is test content.',
            author='Test Author',
            status='scheduled',
            scheduled_publish_date=future_date
        )
        
        post.publish()
        
        self.assertEqual(post.status, 'published')
        self.assertIsNone(post.scheduled_publish_date)
    
    def test_increment_view_count(self):
        """Test the increment_view_count method."""
        post = Post.objects.create(
            title='Test Post',
            content='This is test content.',
            author='Test Author'
        )
        
        initial_count = post.view_count
        post.increment_view_count()
        
        self.assertEqual(post.view_count, initial_count + 1)
    
    def test_get_status_display_color(self):
        """Test the get_status_display_color method."""
        post = Post.objects.create(
            title='Test Post',
            content='This is test content.',
            author='Test Author',
            status='draft'
        )
        
        self.assertEqual(post.get_status_display_color(), 'gray')
        
        post.status = 'published'
        self.assertEqual(post.get_status_display_color(), 'green')
        
        post.status = 'scheduled'
        self.assertEqual(post.get_status_display_color(), 'blue')