from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.files.storage import default_storage
from PIL import Image
import os


class Post(models.Model):
    """
    Blog post model with all required fields and validation.
    Enhanced with user authentication, status management, and scheduling.
    """
    # Post status choices
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('scheduled', 'Scheduled'),
    ]
    
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200, null=False, blank=False)
    content = models.TextField(null=False, blank=False)
    author = models.CharField(max_length=100, null=False, blank=False)  # Keep for backward compatibility
    author_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='posts',
        help_text="User who authored this post"
    )
    tags = models.CharField(max_length=500, blank=True, default='')
    image_url = models.URLField(blank=True, null=True)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft',
        help_text="Current status of the post"
    )
    scheduled_publish_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Date and time when the post should be automatically published"
    )
    view_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this post has been viewed"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        db_table = 'blog_posts'
        indexes = [
            # Primary ordering index for listing posts
            models.Index(fields=['-created_at'], name='posts_created_at_idx'),
            # Index for author-based queries (backward compatibility)
            models.Index(fields=['author'], name='posts_author_idx'),
            # Index for author_user-based queries
            models.Index(fields=['author_user'], name='posts_author_user_idx'),
            # Index for title searches and sorting
            models.Index(fields=['title'], name='posts_title_idx'),
            # Composite index for author + created_at (common query pattern)
            models.Index(fields=['author', '-created_at'], name='posts_author_created_idx'),
            # Composite index for author_user + created_at
            models.Index(fields=['author_user', '-created_at'], name='posts_author_user_created_idx'),
            # Index for updated_at for recently modified posts
            models.Index(fields=['-updated_at'], name='posts_updated_at_idx'),
            # Partial index for posts with tags (only index non-empty tags)
            models.Index(fields=['tags'], name='posts_tags_idx', condition=models.Q(tags__gt='')),
            # Index for status-based queries
            models.Index(fields=['status'], name='posts_status_idx'),
            # Index for scheduled posts
            models.Index(fields=['scheduled_publish_date'], name='posts_scheduled_idx'),
            # Composite index for status + created_at (common query pattern)
            models.Index(fields=['status', '-created_at'], name='posts_status_created_idx'),
            # Index for view count (for popular posts)
            models.Index(fields=['-view_count'], name='posts_view_count_idx'),
        ]
        permissions = [
            ('can_moderate_posts', 'Can moderate posts'),
            ('can_schedule_posts', 'Can schedule posts'),
            ('can_feature_posts', 'Can feature posts'),
            ('can_view_drafts', 'Can view draft posts'),
            ('can_publish_posts', 'Can publish posts'),
        ]
    
    def __str__(self):
        return self.title
    
    def clean(self):
        """
        Custom validation for the Post model.
        """
        errors = {}
        
        # Validate title
        if self.title:
            title_stripped = self.title.strip()
            if len(title_stripped) < 5:
                errors['title'] = 'Title must be at least 5 characters long'
            elif len(title_stripped) > 200:
                errors['title'] = 'Title cannot exceed 200 characters'
            else:
                self.title = title_stripped
        else:
            errors['title'] = 'Title is required'
        
        # Validate content
        if self.content:
            content_stripped = self.content.strip()
            if len(content_stripped) < 10:
                errors['content'] = 'Content must be at least 10 characters long'
            else:
                self.content = content_stripped
        else:
            errors['content'] = 'Content is required'
        
        # Validate author (backward compatibility)
        if self.author:
            author_stripped = self.author.strip()
            if len(author_stripped) < 2:
                errors['author'] = 'Author name must be at least 2 characters long'
            elif len(author_stripped) > 100:
                errors['author'] = 'Author name cannot exceed 100 characters'
            else:
                self.author = author_stripped
        else:
            errors['author'] = 'Author is required'
        
        # Validate tags (optional field)
        if self.tags:
            tags_stripped = self.tags.strip()
            if len(tags_stripped) > 500:
                errors['tags'] = 'Tags cannot exceed 500 characters'
            else:
                self.tags = tags_stripped
        
        # Validate status
        if self.status not in dict(self.STATUS_CHOICES):
            errors['status'] = f'Invalid status. Must be one of: {", ".join(dict(self.STATUS_CHOICES).keys())}'
        
        # Validate scheduled_publish_date
        if self.scheduled_publish_date:
            if self.status != 'scheduled':
                errors['scheduled_publish_date'] = 'Scheduled publish date can only be set for scheduled posts'
            elif self.scheduled_publish_date <= timezone.now():
                errors['scheduled_publish_date'] = 'Scheduled publish date must be in the future'
        elif self.status == 'scheduled':
            errors['scheduled_publish_date'] = 'Scheduled publish date is required for scheduled posts'
        
        # Validate view_count
        if self.view_count < 0:
            errors['view_count'] = 'View count cannot be negative'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """
        Override save method to ensure validation is called.
        """
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_tags_list(self):
        """
        Return tags as a list, splitting by comma.
        """
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    
    def set_tags_from_list(self, tags_list):
        """
        Set tags from a list of strings.
        """
        if tags_list:
            self.tags = ', '.join(str(tag).strip() for tag in tags_list if str(tag).strip())
        else:
            self.tags = ''
    
    def get_author_name(self):
        """
        Get the author name, preferring author_user over author field.
        """
        if self.author_user:
            if self.author_user.first_name and self.author_user.last_name:
                return f"{self.author_user.first_name} {self.author_user.last_name}"
            elif self.author_user.first_name:
                return self.author_user.first_name
            else:
                return self.author_user.username
        return self.author
    
    def is_published(self):
        """
        Check if the post is published.
        """
        return self.status == 'published'
    
    def is_draft(self):
        """
        Check if the post is a draft.
        """
        return self.status == 'draft'
    
    def is_scheduled(self):
        """
        Check if the post is scheduled for future publication.
        """
        return self.status == 'scheduled'
    
    def can_be_published(self):
        """
        Check if the post can be published (is draft or scheduled).
        """
        return self.status in ['draft', 'scheduled']
    
    def publish(self):
        """
        Publish the post by changing status to published.
        """
        if self.can_be_published():
            self.status = 'published'
            self.scheduled_publish_date = None
            self.save()
    
    def increment_view_count(self):
        """
        Increment the view count for this post.
        """
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def get_status_display_color(self):
        """
        Get a color code for the status (useful for frontend display).
        """
        status_colors = {
            'draft': 'gray',
            'published': 'green',
            'scheduled': 'blue',
        }
        return status_colors.get(self.status, 'gray')


class MediaFile(models.Model):
    """
    Model for storing uploaded media files (images and videos).
    """
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    
    uploaded_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='uploaded_media',
        help_text="User who uploaded this media file"
    )
    file = models.FileField(
        upload_to='media/%Y/%m/%d/',
        help_text="The uploaded media file"
    )
    file_type = models.CharField(
        max_length=20, 
        choices=MEDIA_TYPE_CHOICES,
        help_text="Type of media file"
    )
    original_name = models.CharField(
        max_length=255,
        help_text="Original filename when uploaded"
    )
    file_size = models.PositiveIntegerField(
        help_text="File size in bytes"
    )
    alt_text = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Alternative text for accessibility"
    )
    thumbnail = models.ImageField(
        upload_to='thumbnails/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text="Generated thumbnail for images"
    )
    width = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Width of image in pixels"
    )
    height = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Height of image in pixels"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at'], name='media_created_at_idx'),
            models.Index(fields=['uploaded_by'], name='media_uploaded_by_idx'),
            models.Index(fields=['file_type'], name='media_file_type_idx'),
        ]
    
    def __str__(self):
        return f"{self.original_name} ({self.file_type})"
    
    def clean(self):
        """
        Custom validation for MediaFile model.
        """
        errors = {}
        
        # Validate file type based on file extension
        if self.file:
            file_extension = os.path.splitext(self.file.name)[1].lower()
            
            if self.file_type == 'image':
                allowed_image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
                if file_extension not in allowed_image_extensions:
                    errors['file'] = f'Invalid image file type. Allowed: {", ".join(allowed_image_extensions)}'
            elif self.file_type == 'video':
                allowed_video_extensions = ['.mp4', '.webm', '.ogg', '.mov', '.avi']
                if file_extension not in allowed_video_extensions:
                    errors['file'] = f'Invalid video file type. Allowed: {", ".join(allowed_video_extensions)}'
        
        # Validate file size (max 10MB for images, 50MB for videos)
        if self.file_size:
            max_size = 10 * 1024 * 1024 if self.file_type == 'image' else 50 * 1024 * 1024  # 10MB or 50MB
            if self.file_size > max_size:
                max_size_mb = max_size / (1024 * 1024)
                errors['file_size'] = f'File size exceeds maximum allowed size of {max_size_mb}MB'
        
        # Validate alt_text length
        if self.alt_text and len(self.alt_text) > 255:
            errors['alt_text'] = 'Alt text cannot exceed 255 characters'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """
        Override save method to generate thumbnails and extract metadata.
        """
        # Set original name if not provided
        if not self.original_name and self.file:
            self.original_name = self.file.name
        
        # Set file size if not provided
        if not self.file_size and self.file:
            self.file_size = self.file.size
        
        # Validate before saving
        self.full_clean()
        
        # Save the instance first
        super().save(*args, **kwargs)
        
        # Generate thumbnail and extract metadata for images
        if self.file_type == 'image' and self.file:
            self._generate_thumbnail()
            self._extract_image_metadata()
    
    def _generate_thumbnail(self):
        """
        Generate thumbnail for image files.
        """
        if not self.file or self.file_type != 'image':
            return
        
        try:
            # Open the image
            with Image.open(self.file.path) as image:
                # Convert to RGB if necessary (for PNG with transparency)
                if image.mode in ('RGBA', 'LA', 'P'):
                    image = image.convert('RGB')
                
                # Create thumbnail
                thumbnail_size = (300, 300)
                image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
                
                # Save thumbnail
                thumbnail_name = f"thumb_{os.path.basename(self.file.name)}"
                thumbnail_path = os.path.join('thumbnails', timezone.now().strftime('%Y/%m/%d'), thumbnail_name)
                
                # Ensure directory exists
                thumbnail_dir = os.path.dirname(os.path.join(default_storage.location, thumbnail_path))
                os.makedirs(thumbnail_dir, exist_ok=True)
                
                # Save thumbnail
                full_thumbnail_path = os.path.join(default_storage.location, thumbnail_path)
                image.save(full_thumbnail_path, 'JPEG', quality=85)
                
                # Update thumbnail field
                self.thumbnail.name = thumbnail_path
                super().save(update_fields=['thumbnail'])
                
        except Exception as e:
            # Log error but don't fail the save
            print(f"Error generating thumbnail for {self.file.name}: {e}")
    
    def _extract_image_metadata(self):
        """
        Extract width and height from image files.
        """
        if not self.file or self.file_type != 'image':
            return
        
        try:
            with Image.open(self.file.path) as image:
                self.width = image.width
                self.height = image.height
                super().save(update_fields=['width', 'height'])
        except Exception as e:
            # Log error but don't fail the save
            print(f"Error extracting metadata for {self.file.name}: {e}")
    
    def get_file_url(self):
        """
        Get the URL for the media file.
        """
        if self.file:
            return self.file.url
        return None
    
    def get_thumbnail_url(self):
        """
        Get the URL for the thumbnail.
        """
        if self.thumbnail:
            return self.thumbnail.url
        return None
    
    def delete(self, *args, **kwargs):
        """
        Override delete to remove files from storage.
        """
        # Delete the main file
        if self.file:
            if default_storage.exists(self.file.name):
                default_storage.delete(self.file.name)
        
        # Delete the thumbnail
        if self.thumbnail:
            if default_storage.exists(self.thumbnail.name):
                default_storage.delete(self.thumbnail.name)
        
        super().delete(*args, **kwargs)


class PostMedia(models.Model):
    """
    Junction model for associating media files with posts.
    """
    post = models.ForeignKey(
        Post, 
        on_delete=models.CASCADE,
        related_name='media_files',
        help_text="Post this media is attached to"
    )
    media_file = models.ForeignKey(
        MediaFile, 
        on_delete=models.CASCADE,
        related_name='post_attachments',
        help_text="Media file attached to the post"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order of media in the post"
    )
    caption = models.TextField(
        blank=True,
        help_text="Optional caption for the media"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'created_at']
        unique_together = ['post', 'media_file']
        indexes = [
            models.Index(fields=['post', 'order'], name='postmedia_post_order_idx'),
            models.Index(fields=['media_file'], name='postmedia_media_file_idx'),
        ]
    
    def __str__(self):
        return f"{self.post.title} - {self.media_file.original_name}"
