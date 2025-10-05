"""
Tests for media models.
"""

import tempfile
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from posts.models import Post, MediaFile, PostMedia


class MediaModelsTestCase(TestCase):
    """Test cases for media models."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.post = Post.objects.create(
            title='Test Post',
            content='Test content',
            author='Test Author',
            author_user=self.user,
            status='draft'
        )
    
    def test_media_file_creation(self):
        """Test MediaFile model creation."""
        media_file = MediaFile.objects.create(
            uploaded_by=self.user,
            file='test.jpg',
            file_type='image',
            original_name='test.jpg',
            file_size=1024,
            alt_text='Test image'
        )
        
        self.assertEqual(media_file.uploaded_by, self.user)
        self.assertEqual(media_file.file_type, 'image')
        self.assertEqual(media_file.original_name, 'test.jpg')
        self.assertEqual(media_file.file_size, 1024)
        self.assertEqual(media_file.alt_text, 'Test image')
        self.assertIsNotNone(media_file.created_at)
        self.assertIsNotNone(media_file.updated_at)
    
    def test_media_file_str_representation(self):
        """Test MediaFile string representation."""
        media_file = MediaFile.objects.create(
            uploaded_by=self.user,
            file='test.jpg',
            file_type='image',
            original_name='test.jpg',
            file_size=1024
        )
        
        expected_str = "test.jpg (image)"
        self.assertEqual(str(media_file), expected_str)
    
    def test_media_file_validation_invalid_type(self):
        """Test MediaFile validation with invalid file type."""
        media_file = MediaFile(
            uploaded_by=self.user,
            file='test.txt',
            file_type='image',  # Type says image but extension is .txt
            original_name='test.txt',
            file_size=1024
        )
        
        with self.assertRaises(ValidationError):
            media_file.full_clean()
    
    def test_media_file_validation_oversized_image(self):
        """Test MediaFile validation with oversized image."""
        media_file = MediaFile(
            uploaded_by=self.user,
            file='test.jpg',
            file_type='image',
            original_name='test.jpg',
            file_size=11 * 1024 * 1024  # 11MB, over the 10MB limit
        )
        
        with self.assertRaises(ValidationError):
            media_file.full_clean()
    
    def test_media_file_validation_oversized_video(self):
        """Test MediaFile validation with oversized video."""
        media_file = MediaFile(
            uploaded_by=self.user,
            file='test.mp4',
            file_type='video',
            original_name='test.mp4',
            file_size=51 * 1024 * 1024  # 51MB, over the 50MB limit
        )
        
        with self.assertRaises(ValidationError):
            media_file.full_clean()
    
    def test_media_file_get_file_url(self):
        """Test MediaFile get_file_url method."""
        media_file = MediaFile.objects.create(
            uploaded_by=self.user,
            file='test.jpg',
            file_type='image',
            original_name='test.jpg',
            file_size=1024
        )
        
        # Should return the file URL
        url = media_file.get_file_url()
        self.assertIsNotNone(url)
        self.assertIn('test.jpg', url)
    
    def test_post_media_creation(self):
        """Test PostMedia model creation."""
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
            order=1,
            caption='Test caption'
        )
        
        self.assertEqual(post_media.post, self.post)
        self.assertEqual(post_media.media_file, media_file)
        self.assertEqual(post_media.order, 1)
        self.assertEqual(post_media.caption, 'Test caption')
        self.assertIsNotNone(post_media.created_at)
    
    def test_post_media_str_representation(self):
        """Test PostMedia string representation."""
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
            order=1
        )
        
        expected_str = f"{self.post.title} - test.jpg"
        self.assertEqual(str(post_media), expected_str)
    
    def test_post_media_unique_constraint(self):
        """Test PostMedia unique constraint for post-media combination."""
        media_file = MediaFile.objects.create(
            uploaded_by=self.user,
            file='test.jpg',
            file_type='image',
            original_name='test.jpg',
            file_size=1024
        )
        
        # Create first PostMedia
        PostMedia.objects.create(
            post=self.post,
            media_file=media_file,
            order=1
        )
        
        # Try to create duplicate - should raise IntegrityError
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            PostMedia.objects.create(
                post=self.post,
                media_file=media_file,
                order=2
            )
    
    def test_post_media_ordering(self):
        """Test PostMedia ordering by order field."""
        media_file1 = MediaFile.objects.create(
            uploaded_by=self.user,
            file='test1.jpg',
            file_type='image',
            original_name='test1.jpg',
            file_size=1024
        )
        
        media_file2 = MediaFile.objects.create(
            uploaded_by=self.user,
            file='test2.jpg',
            file_type='image',
            original_name='test2.jpg',
            file_size=1024
        )
        
        # Create in reverse order
        post_media2 = PostMedia.objects.create(
            post=self.post,
            media_file=media_file2,
            order=2
        )
        
        post_media1 = PostMedia.objects.create(
            post=self.post,
            media_file=media_file1,
            order=1
        )
        
        # Should be ordered by order field
        post_media_list = list(PostMedia.objects.filter(post=self.post))
        self.assertEqual(post_media_list[0], post_media1)
        self.assertEqual(post_media_list[1], post_media2)
    
    def test_media_file_related_names(self):
        """Test MediaFile related names work correctly."""
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
            order=1
        )
        
        # Test reverse relationship
        self.assertEqual(media_file.post_attachments.count(), 1)
        self.assertEqual(media_file.post_attachments.first().post, self.post)
        
        # Test post media_files relationship
        self.assertEqual(self.post.media_files.count(), 1)
        self.assertEqual(self.post.media_files.first().media_file, media_file)