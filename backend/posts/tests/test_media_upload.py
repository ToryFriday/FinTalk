"""
Tests for media upload functionality.
"""

import os
import tempfile
from PIL import Image
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from posts.models import Post, MediaFile, PostMedia


class MediaUploadTestCase(TestCase):
    """Test cases for media upload functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create a test post
        self.post = Post.objects.create(
            title='Test Post',
            content='Test content',
            author='Test Author',
            author_user=self.user,
            status='draft'
        )
    
    def create_test_image(self, name='test.jpg', size=(100, 100), format='JPEG'):
        """Create a test image file."""
        image = Image.new('RGB', size, color='red')
        temp_file = tempfile.NamedTemporaryFile(suffix=f'.{format.lower()}', delete=False)
        image.save(temp_file.name, format)
        temp_file.seek(0)
        
        with open(temp_file.name, 'rb') as f:
            content = f.read()
        
        os.unlink(temp_file.name)
        
        return SimpleUploadedFile(
            name=name,
            content=content,
            content_type=f'image/{format.lower()}'
        )
    
    def create_test_video(self, name='test.mp4'):
        """Create a test video file (mock)."""
        # Create a small mock video file
        content = b'fake video content for testing'
        return SimpleUploadedFile(
            name=name,
            content=content,
            content_type='video/mp4'
        )
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_upload_image_success(self):
        """Test successful image upload."""
        image_file = self.create_test_image('test_image.jpg')
        
        response = self.client.post('/api/posts/media/upload/', {
            'file': image_file,
            'alt_text': 'Test image'
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['file_type'], 'image')
        self.assertEqual(response.data['alt_text'], 'Test image')
        self.assertEqual(response.data['original_name'], 'test_image.jpg')
        
        # Verify database record
        media_file = MediaFile.objects.get(id=response.data['id'])
        self.assertEqual(media_file.uploaded_by, self.user)
        self.assertEqual(media_file.file_type, 'image')
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_upload_video_success(self):
        """Test successful video upload."""
        video_file = self.create_test_video('test_video.mp4')
        
        response = self.client.post('/api/posts/media/upload/', {
            'file': video_file,
            'alt_text': 'Test video'
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['file_type'], 'video')
        self.assertEqual(response.data['alt_text'], 'Test video')
    
    def test_upload_without_authentication(self):
        """Test upload without authentication fails."""
        self.client.force_authenticate(user=None)
        image_file = self.create_test_image()
        
        response = self.client.post('/api/posts/media/upload/', {
            'file': image_file
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_upload_invalid_file_type(self):
        """Test upload with invalid file type fails."""
        invalid_file = SimpleUploadedFile(
            name='test.txt',
            content=b'This is a text file',
            content_type='text/plain'
        )
        
        response = self.client.post('/api/posts/media/upload/', {
            'file': invalid_file
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_upload_oversized_file(self):
        """Test upload with oversized file fails."""
        # Create a large mock file
        large_content = b'x' * (11 * 1024 * 1024)  # 11MB
        large_file = SimpleUploadedFile(
            name='large.jpg',
            content=large_content,
            content_type='image/jpeg'
        )
        
        response = self.client.post('/api/posts/media/upload/', {
            'file': large_file
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_get_media_files(self):
        """Test retrieving media files list."""
        # Create some media files
        MediaFile.objects.create(
            uploaded_by=self.user,
            file='test1.jpg',
            file_type='image',
            original_name='test1.jpg',
            file_size=1024
        )
        MediaFile.objects.create(
            uploaded_by=self.user,
            file='test2.mp4',
            file_type='video',
            original_name='test2.mp4',
            file_size=2048
        )
        
        response = self.client.get('/api/posts/media/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_get_media_file_detail(self):
        """Test retrieving specific media file."""
        media_file = MediaFile.objects.create(
            uploaded_by=self.user,
            file='test.jpg',
            file_type='image',
            original_name='test.jpg',
            file_size=1024
        )
        
        response = self.client.get(f'/api/posts/media/{media_file.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], media_file.id)
        self.assertEqual(response.data['original_name'], 'test.jpg')
    
    def test_delete_media_file(self):
        """Test deleting media file."""
        media_file = MediaFile.objects.create(
            uploaded_by=self.user,
            file='test.jpg',
            file_type='image',
            original_name='test.jpg',
            file_size=1024
        )
        
        response = self.client.delete(f'/api/posts/media/{media_file.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(MediaFile.objects.filter(id=media_file.id).exists())
    
    def test_attach_media_to_post(self):
        """Test attaching media files to a post."""
        media_file = MediaFile.objects.create(
            uploaded_by=self.user,
            file='test.jpg',
            file_type='image',
            original_name='test.jpg',
            file_size=1024
        )
        
        response = self.client.post(f'/api/posts/{self.post.id}/media/', {
            'media_file_ids': [media_file.id],
            'captions': {str(media_file.id): 'Test caption'}
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['caption'], 'Test caption')
        
        # Verify database record
        post_media = PostMedia.objects.get(post=self.post, media_file=media_file)
        self.assertEqual(post_media.caption, 'Test caption')
    
    def test_get_post_media(self):
        """Test retrieving media files attached to a post."""
        media_file = MediaFile.objects.create(
            uploaded_by=self.user,
            file='test.jpg',
            file_type='image',
            original_name='test.jpg',
            file_size=1024
        )
        
        PostMedia.objects.create(
            post=self.post,
            media_file=media_file,
            caption='Test caption'
        )
        
        response = self.client.get(f'/api/posts/{self.post.id}/media/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['caption'], 'Test caption')
    
    def test_remove_media_from_post(self):
        """Test removing media file from a post."""
        media_file = MediaFile.objects.create(
            uploaded_by=self.user,
            file='test.jpg',
            file_type='image',
            original_name='test.jpg',
            file_size=1024
        )
        
        post_media = PostMedia.objects.create(
            post=self.post,
            media_file=media_file,
            caption='Test caption'
        )
        
        response = self.client.delete(f'/api/posts/{self.post.id}/media/{media_file.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PostMedia.objects.filter(id=post_media.id).exists())
    
    def test_cannot_attach_others_media(self):
        """Test that users cannot attach other users' media files."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        media_file = MediaFile.objects.create(
            uploaded_by=other_user,
            file='test.jpg',
            file_type='image',
            original_name='test.jpg',
            file_size=1024
        )
        
        response = self.client.post(f'/api/posts/{self.post.id}/media/', {
            'media_file_ids': [media_file.id]
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_cannot_delete_others_media(self):
        """Test that users cannot delete other users' media files."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        media_file = MediaFile.objects.create(
            uploaded_by=other_user,
            file='test.jpg',
            file_type='image',
            original_name='test.jpg',
            file_size=1024
        )
        
        response = self.client.delete(f'/api/posts/media/{media_file.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)