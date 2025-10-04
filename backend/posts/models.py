from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class Post(models.Model):
    """
    Blog post model with all required fields and validation.
    """
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200, null=False, blank=False)
    content = models.TextField(null=False, blank=False)
    author = models.CharField(max_length=100, null=False, blank=False)
    tags = models.CharField(max_length=500, blank=True, default='')
    image_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        db_table = 'blog_posts'
        indexes = [
            # Primary ordering index for listing posts
            models.Index(fields=['-created_at'], name='posts_created_at_idx'),
            # Index for author-based queries
            models.Index(fields=['author'], name='posts_author_idx'),
            # Index for title searches and sorting
            models.Index(fields=['title'], name='posts_title_idx'),
            # Composite index for author + created_at (common query pattern)
            models.Index(fields=['author', '-created_at'], name='posts_author_created_idx'),
            # Index for updated_at for recently modified posts
            models.Index(fields=['-updated_at'], name='posts_updated_at_idx'),
            # Partial index for posts with tags (only index non-empty tags)
            models.Index(fields=['tags'], name='posts_tags_idx', condition=models.Q(tags__gt='')),
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
        
        # Validate author
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
