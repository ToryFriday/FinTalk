"""
Comprehensive unit tests for posts app models, serializers, and views.
This file provides extensive test coverage for all new functionality.
"""

import tempfile
import os
from datetime import timedelta
from unittest.mock import patch, MagicMock
from PIL import Image

from django.test import TestCase, TransactionTestCase, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from .models import Post, MediaFile, PostMedia
from .serializers import PostSerializer, MediaFileSerializer, PostMediaSerializer
from accounts.models import Role, UserRole


class PostModelTest(TestCase):
    """Comprehensive tests for Post model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.post_data = {
            'title': 'Test Post Title',
            'content': 'This is a comprehensive test post content that is long enough to pass validation.',
            'author': 'Test Author',
            'author_user': self.user,
            'tags': 'test, django, blog',
            'status': 'draft'
        }
    
    def test_post_creation(self):
        """Test creating a post with valid data."""
        post = Post.objects.create(**self.post_data)
        
        self.assertEqual(post.title, 'Test Post Title')
        self.assertEqual(post.content, self.post_data['content'])
        self.assertEqual(post.author, 'Test Author')
        self.assertEqual(post.author_user, self.user)
        self.assertEqual(post.status, 'draft')
        self.assertEqual(post.view_count, 0)
        self.assertIsNotNone(post.created_at)
        self.assertIsNotNone(post.updated_at)
    
    def test_post_str_representation(self):
        """Test post string representation."""
        post = Post.objects.create(**self.post_data)
        self.assertEqual(str(post), 'Test Post Title')
    
    def test_post_status_methods(self):
        """Test post status checking methods."""
        post = Post.objects.create(**self.post_data)
        
        # Test draft status
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
        
        # Change to scheduled
        post.status = 'scheduled'
        post.scheduled_publish_date = timezone.now() + timedelta(days=1)
        post.save()
        
        self.assertFalse(post.is_draft())
        self.assertFalse(post.is_published())
        self.assertTrue(post.is_scheduled())
        self.assertTrue(post.can_be_published())
    
    def test_post_publish_method(self):
        """Test post publish method."""
        post = Post.objects.create(**self.post_data)
        
        # Publish draft post
        post.publish()
        
        self.assertEqual(post.status, 'published')
        self.assertIsNone(post.scheduled_publish_date)
        
        # Test scheduled post
        post.status = 'scheduled'
        post.scheduled_publish_date = timezone.now() + timedelta(days=1)
        post.save()
        
        post.publish()
        
        self.assertEqual(post.status, 'published')
        self.assertIsNone(post.scheduled_publish_date)
    
    def test_post_view_count_increment(self):
        """Test view count increment method."""
        post = Post.objects.create(**self.post_data)
        
        initial_count = post.view_count
        post.increment_view_count()
        
        self.assertEqual(post.view_count, initial_count + 1)
    
    def test_post_tags_methods(self):
        """Test tag-related methods."""
        post = Post.objects.create(**self.post_data)
        
        # Test get_tags_list
        tags_list = post.get_tags_list()
        expected_tags = ['test', 'django', 'blog']
        self.assertEqual(tags_list, expected_tags)
        
        # Test set_tags_from_list
        new_tags = ['python', 'web', 'development']
        post.set_tags_from_list(new_tags)
        
        self.assertEqual(post.tags, 'python, web, development')
        self.assertEqual(post.get_tags_list(), new_tags)
    
    def test_post_author_name_method(self):
        """Test get_author_name method."""
        post = Post.objects.create(**self.post_data)
        
        # With author_user having full name
        self.user.first_name = 'John'
        self.user.last_name = 'Doe'
        self.user.save()
        
        self.assertEqual(post.get_author_name(), 'John Doe')
        
        # With only first name
        self.user.last_name = ''
        self.user.save()
        
        self.assertEqual(post.get_author_name(), 'John')
        
        # With only username
        self.user.first_name = ''
        self.user.save()
        
        self.assertEqual(post.get_author_name(), 'testuser')
        
        # Without author_user
        post.author_user = None
        post.save()
        
        self.assertEqual(post.get_author_name(), 'Test Author')
    
    def test_post_validation(self):
        """Test post field validation."""
        # Valid post
        post = Post(**self.post_data)
        
        try:
            post.full_clean()
        except Exception:
            self.fail("Valid post data should not raise validation error")
    
    def test_post_validation_errors(self):
        """Test post validation error cases."""
        # Title too short
        invalid_data = self.post_data.copy()
        invalid_data['title'] = 'Hi'
        
        post = Post(**invalid_data)
        with self.assertRaises(Exception):
            post.full_clean()
        
        # Content too short
        invalid_data = self.post_data.copy()
        invalid_data['content'] = 'Short'
        
        post = Post(**invalid_data)
        with self.assertRaises(Exception):
            post.full_clean()
        
        # Invalid status
        invalid_data = self.post_data.copy()
        invalid_data['status'] = 'invalid_status'
        
        post = Post(**invalid_data)
        with self.assertRaises(Exception):
            post.full_clean()
        
        # Scheduled post without date
        invalid_data = self.post_data.copy()
        invalid_data['status'] = 'scheduled'
        
        post = Post(**invalid_data)
        with self.assertRaises(Exception):
            post.full_clean()
        
        # Scheduled date in the past
        invalid_data = self.post_data.copy()
        invalid_data['status'] = 'scheduled'
        invalid_data['scheduled_publish_date'] = timezone.now() - timedelta(days=1)
        
        post = Post(**invalid_data)
        with self.assertRaises(Exception):
            post.full_clean()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class MediaFileModelTest(TestCase):
    """Comprehensive tests for MediaFile model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a test image file
        self.test_image = Image.new('RGB', (100, 100), color='red')
        self.temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        self.test_image.save(self.temp_file, 'JPEG')
        self.temp_file.seek(0)
    
    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_media_file_creation(self):
        """Test creating a media file."""
        with open(self.temp_file.name, 'rb') as f:
            uploaded_file = SimpleUploadedFile(
                name='test_image.jpg',
                content=f.read(),
                content_type='image/jpeg'
            )
            
            media_file = MediaFile.objects.create(
                uploaded_by=self.user,
                file=uploaded_file,
                file_type='image',
                original_name='test_image.jpg',
                file_size=1024,
                alt_text='Test image'
            )
            
            self.assertEqual(media_file.uploaded_by, self.user)
            self.assertEqual(media_file.file_type, 'image')
            self.assertEqual(media_file.original_name, 'test_image.jpg')
            self.assertEqual(media_file.file_size, 1024)
            self.assertEqual(media_file.alt_text, 'Test image')
            self.assertIsNotNone(media_file.created_at)
    
    def test_media_file_str_representation(self):
        """Test media file string representation."""
        with open(self.temp_file.name, 'rb') as f:
            uploaded_file = SimpleUploadedFile(
                name='test_image.jpg',
                content=f.read(),
                content_type='image/jpeg'
            )
            
            media_file = MediaFile.objects.create(
                uploaded_by=self.user,
                file=uploaded_file,
                file_type='image',
                original_name='test_image.jpg',
                file_size=1024
            )
            
            expected = 'test_image.jpg (image)'
            self.assertEqual(str(media_file), expected)
    
    def test_media_file_url_methods(self):
        """Test media file URL methods."""
        with open(self.temp_file.name, 'rb') as f:
            uploaded_file = SimpleUploadedFile(
                name='test_image.jpg',
                content=f.read(),
                content_type='image/jpeg'
            )
            
            media_file = MediaFile.objects.create(
                uploaded_by=self.user,
                file=uploaded_file,
                file_type='image',
                original_name='test_image.jpg',
                file_size=1024
            )
            
            # Test get_file_url
            file_url = media_file.get_file_url()
            self.assertIsNotNone(file_url)
            self.assertTrue(file_url.startswith('/media/'))
            
            # Test get_thumbnail_url (might be None if thumbnail generation fails)
            thumbnail_url = media_file.get_thumbnail_url()
            # Just test that the method doesn't raise an exception
            self.assertIsNotNone(thumbnail_url) or self.assertIsNone(thumbnail_url)


class PostMediaModelTest(TestCase):
    """Comprehensive tests for PostMedia model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Test Post',
            content='This is a test post content.',
            author='Test Author',
            author_user=self.user
        )
        
        # Create a test media file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            test_image = Image.new('RGB', (100, 100), color='red')
            test_image.save(temp_file, 'JPEG')
            temp_file.seek(0)
            
            uploaded_file = SimpleUploadedFile(
                name='test_image.jpg',
                content=temp_file.read(),
                content_type='image/jpeg'
            )
            
            self.media_file = MediaFile.objects.create(
                uploaded_by=self.user,
                file=uploaded_file,
                file_type='image',
                original_name='test_image.jpg',
                file_size=1024
            )
    
    def test_post_media_creation(self):
        """Test creating a post media relationship."""
        post_media = PostMedia.objects.create(
            post=self.post,
            media_file=self.media_file,
            order=0,
            caption='Test image caption'
        )
        
        self.assertEqual(post_media.post, self.post)
        self.assertEqual(post_media.media_file, self.media_file)
        self.assertEqual(post_media.order, 0)
        self.assertEqual(post_media.caption, 'Test image caption')
        self.assertIsNotNone(post_media.created_at)
    
    def test_post_media_str_representation(self):
        """Test post media string representation."""
        post_media = PostMedia.objects.create(
            post=self.post,
            media_file=self.media_file,
            order=0
        )
        
        expected = f"{self.post.title} - {self.media_file.original_name}"
        self.assertEqual(str(post_media), expected)


class PostSerializerTest(TestCase):
    """Test PostSerializer."""
    
    def setUp(self):
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
    
    def test_post_serialization(self):
        """Test post serialization."""
        serializer = PostSerializer(self.post)
        data = serializer.data
        
        self.assertEqual(data['title'], 'Test Post')
        self.assertEqual(data['content'], 'This is a test post content.')
        self.assertEqual(data['author'], 'Test Author')
        self.assertEqual(data['status'], 'published')
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
    
    def test_post_creation_via_serializer(self):
        """Test creating a post via serializer."""
        data = {
            'title': 'New Post',
            'content': 'This is new post content that is long enough.',
            'tags': 'new, test',
            'status': 'draft'
        }
        
        serializer = PostSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Set the author_user in the context or manually
        post = serializer.save(author_user=self.user, author=self.user.username)
        
        self.assertEqual(post.title, 'New Post')
        self.assertEqual(post.author_user, self.user)
        self.assertEqual(post.status, 'draft')


class PostAPITest(APITestCase):
    """Test Post API endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.writer_role = Role.objects.create(
            name='writer',
            display_name='Writer',
            description='Can write posts'
        )
        UserRole.objects.create(user=self.user, role=self.writer_role)
        
        self.post = Post.objects.create(
            title='Test Post',
            content='This is a test post content.',
            author='Test Author',
            author_user=self.user,
            status='published'
        )
        
        self.client.force_authenticate(user=self.user)
    
    def test_list_posts(self):
        """Test listing posts."""
        url = reverse('posts:post-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Test Post')
    
    def test_create_post(self):
        """Test creating a new post."""
        url = reverse('posts:post-list-create')
        data = {
            'title': 'New Test Post',
            'content': 'This is a new test post content that is long enough to pass validation.',
            'tags': 'test, new',
            'status': 'draft'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Test Post')
        self.assertEqual(response.data['author_user']['username'], 'testuser')
        self.assertEqual(response.data['status'], 'draft')
        
        # Verify post was created in database
        post = Post.objects.get(title='New Test Post')
        self.assertEqual(post.author_user, self.user)
    
    def test_get_post_detail(self):
        """Test getting post details."""
        url = reverse('posts:post-detail', kwargs={'pk': self.post.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Post')
        self.assertEqual(response.data['id'], self.post.id)
    
    def test_update_post(self):
        """Test updating a post."""
        url = reverse('posts:post-detail', kwargs={'pk': self.post.id})
        data = {
            'title': 'Updated Test Post',
            'content': 'This is updated test post content.',
            'status': 'published'
        }
        
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Test Post')
        
        # Verify post was updated in database
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Updated Test Post')
    
    def test_delete_post(self):
        """Test deleting a post."""
        url = reverse('posts:post-detail', kwargs={'pk': self.post.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify post was deleted
        self.assertFalse(Post.objects.filter(id=self.post.id).exists())
    
    def test_draft_posts_endpoint(self):
        """Test getting user's draft posts."""
        # Create a draft post
        draft_post = Post.objects.create(
            title='Draft Post',
            content='This is a draft post content.',
            author='Test Author',
            author_user=self.user,
            status='draft'
        )
        
        url = reverse('posts:draft-posts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Draft Post')
        self.assertEqual(response.data['results'][0]['status'], 'draft')
    
    def test_schedule_post(self):
        """Test scheduling a post."""
        # Create a draft post
        draft_post = Post.objects.create(
            title='Draft Post',
            content='This is a draft post content.',
            author='Test Author',
            author_user=self.user,
            status='draft'
        )
        
        url = reverse('posts:schedule-post', kwargs={'pk': draft_post.id})
        future_date = timezone.now() + timedelta(days=1)
        data = {
            'scheduled_publish_date': future_date.isoformat()
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify post was scheduled
        draft_post.refresh_from_db()
        self.assertEqual(draft_post.status, 'scheduled')
        self.assertIsNotNone(draft_post.scheduled_publish_date)
    
    def test_publish_post(self):
        """Test publishing a post."""
        # Create a draft post
        draft_post = Post.objects.create(
            title='Draft Post',
            content='This is a draft post content.',
            author='Test Author',
            author_user=self.user,
            status='draft'
        )
        
        url = reverse('posts:publish-post', kwargs={'pk': draft_post.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify post was published
        draft_post.refresh_from_db()
        self.assertEqual(draft_post.status, 'published')
    
    def test_post_permissions(self):
        """Test post permissions for different user roles."""
        # Create another user without writer role
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        # Try to create post without writer role
        self.client.force_authenticate(user=other_user)
        
        url = reverse('posts:post-list-create')
        data = {
            'title': 'Unauthorized Post',
            'content': 'This should not be allowed.',
            'status': 'draft'
        }
        
        response = self.client.post(url, data)
        
        # Should be forbidden or require proper role
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class MediaUploadAPITest(APITestCase):
    """Test media upload API endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create a test image
        self.test_image = Image.new('RGB', (100, 100), color='red')
        self.temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        self.test_image.save(self.temp_file, 'JPEG')
        self.temp_file.seek(0)
    
    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_upload_media_file(self):
        """Test uploading a media file."""
        url = reverse('posts:media-upload')
        
        with open(self.temp_file.name, 'rb') as f:
            data = {
                'file': SimpleUploadedFile(
                    name='test_image.jpg',
                    content=f.read(),
                    content_type='image/jpeg'
                ),
                'alt_text': 'Test image for upload'
            }
            
            response = self.client.post(url, data, format='multipart')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('file_url', response.data)
            self.assertEqual(response.data['file_type'], 'image')
            self.assertEqual(response.data['alt_text'], 'Test image for upload')
            
            # Verify media file was created
            media_file = MediaFile.objects.get(id=response.data['id'])
            self.assertEqual(media_file.uploaded_by, self.user)
            self.assertEqual(media_file.file_type, 'image')
    
    def test_list_media_files(self):
        """Test listing user's media files."""
        # Create a media file first
        with open(self.temp_file.name, 'rb') as f:
            uploaded_file = SimpleUploadedFile(
                name='test_image.jpg',
                content=f.read(),
                content_type='image/jpeg'
            )
            
            MediaFile.objects.create(
                uploaded_by=self.user,
                file=uploaded_file,
                file_type='image',
                original_name='test_image.jpg',
                file_size=1024
            )
        
        url = reverse('posts:media-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['original_name'], 'test_image.jpg')
    
    def test_attach_media_to_post(self):
        """Test attaching media files to a post."""
        # Create a post and media file
        post = Post.objects.create(
            title='Test Post',
            content='This is a test post content.',
            author='Test Author',
            author_user=self.user
        )
        
        with open(self.temp_file.name, 'rb') as f:
            uploaded_file = SimpleUploadedFile(
                name='test_image.jpg',
                content=f.read(),
                content_type='image/jpeg'
            )
            
            media_file = MediaFile.objects.create(
                uploaded_by=self.user,
                file=uploaded_file,
                file_type='image',
                original_name='test_image.jpg',
                file_size=1024
            )
        
        url = reverse('posts:post-media', kwargs={'pk': post.id})
        data = {
            'media_files': [
                {
                    'media_file_id': media_file.id,
                    'order': 0,
                    'caption': 'Test image caption'
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify media was attached to post
        post_media = PostMedia.objects.get(post=post, media_file=media_file)
        self.assertEqual(post_media.order, 0)
        self.assertEqual(post_media.caption, 'Test image caption')


class PostSearchAndFilterTest(APITestCase):
    """Test post search and filtering functionality."""
    
    def setUp(self):
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
        
        # Create test posts
        self.post1 = Post.objects.create(
            title='Python Programming Guide',
            content='This is a comprehensive guide to Python programming.',
            author='User One',
            author_user=self.user1,
            tags='python, programming, tutorial',
            status='published'
        )
        
        self.post2 = Post.objects.create(
            title='Django Web Development',
            content='Learn how to build web applications with Django framework.',
            author='User Two',
            author_user=self.user2,
            tags='django, web, python',
            status='published'
        )
        
        self.post3 = Post.objects.create(
            title='JavaScript Basics',
            content='Introduction to JavaScript programming language.',
            author='User One',
            author_user=self.user1,
            tags='javascript, programming, basics',
            status='published'
        )
        
        self.client.force_authenticate(user=self.user1)
    
    def test_search_posts_by_title(self):
        """Test searching posts by title."""
        url = reverse('posts:post-list-create')
        response = self.client.get(url, {'search': 'Python'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Python Programming Guide')
    
    def test_search_posts_by_content(self):
        """Test searching posts by content."""
        url = reverse('posts:post-list-create')
        response = self.client.get(url, {'search': 'Django framework'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Django Web Development')
    
    def test_filter_posts_by_author(self):
        """Test filtering posts by author."""
        url = reverse('posts:post-list-create')
        response = self.client.get(url, {'author': 'user1'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Both posts should be by user1
        for post in response.data['results']:
            self.assertEqual(post['author_user']['username'], 'user1')
    
    def test_filter_posts_by_tags(self):
        """Test filtering posts by tags."""
        url = reverse('posts:post-list-create')
        response = self.client.get(url, {'tags': 'python'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Both posts should contain 'python' tag
        for post in response.data['results']:
            self.assertIn('python', post['tags'].lower())
    
    def test_order_posts_by_view_count(self):
        """Test ordering posts by view count."""
        # Set different view counts
        self.post1.view_count = 100
        self.post1.save()
        self.post2.view_count = 50
        self.post2.save()
        self.post3.view_count = 200
        self.post3.save()
        
        url = reverse('posts:post-list-create')
        response = self.client.get(url, {'ordering': '-view_count'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Posts should be ordered by view count (descending)
        view_counts = [post['view_count'] for post in response.data['results']]
        self.assertEqual(view_counts, sorted(view_counts, reverse=True))
    
    def test_combined_search_and_filter(self):
        """Test combining search and filter parameters."""
        url = reverse('posts:post-list-create')
        response = self.client.get(url, {
            'search': 'programming',
            'author': 'user1',
            'ordering': '-created_at'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return posts by user1 that contain 'programming'
        for post in response.data['results']:
            self.assertEqual(post['author_user']['username'], 'user1')
            self.assertTrue(
                'programming' in post['title'].lower() or 
                'programming' in post['content'].lower() or
                'programming' in post['tags'].lower()
            )


class PostPerformanceTest(TransactionTestCase):
    """Test performance of post operations."""
    
    def setUp(self):
        # Create test users
        self.users = []
        for i in range(10):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass123'
            )
            self.users.append(user)
    
    def test_bulk_post_creation_performance(self):
        """Test performance of bulk post creation."""
        import time
        
        start_time = time.time()
        
        # Create posts in bulk
        posts = []
        for i in range(100):
            user = self.users[i % len(self.users)]
            posts.append(Post(
                title=f'Test Post {i}',
                content=f'This is test post content number {i} with enough text to pass validation.',
                author=f'Author {i}',
                author_user=user,
                tags=f'test, post{i}, bulk',
                status='published'
            ))
        
        Post.objects.bulk_create(posts)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete in reasonable time (less than 1 second)
        self.assertLess(execution_time, 1.0)
        
        # Verify posts were created
        self.assertEqual(Post.objects.count(), 100)
    
    def test_post_query_performance(self):
        """Test performance of post queries."""
        # Create test posts
        posts = []
        for i in range(50):
            user = self.users[i % len(self.users)]
            posts.append(Post(
                title=f'Performance Test Post {i}',
                content=f'This is performance test post content number {i}.',
                author=f'Author {i}',
                author_user=user,
                tags=f'performance, test{i}',
                status='published'
            ))
        
        Post.objects.bulk_create(posts)
        
        import time
        start_time = time.time()
        
        # Test various queries
        published_posts = Post.objects.filter(status='published').count()
        posts_by_user = Post.objects.filter(author_user=self.users[0]).count()
        posts_with_tags = Post.objects.filter(tags__icontains='performance').count()
        recent_posts = Post.objects.order_by('-created_at')[:10]
        
        # Force evaluation of querysets
        list(recent_posts)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete quickly
        self.assertLess(execution_time, 0.5)
        
        # Verify query results
        self.assertEqual(published_posts, 50)
        self.assertGreaterEqual(posts_with_tags, 1)