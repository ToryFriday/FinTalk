from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.models import User
from .models import Post, MediaFile, PostMedia
from common.security import InputSanitizer, SecurityValidator
import os


class NullableDateTimeField(serializers.DateTimeField):
    """
    Custom DateTimeField that converts empty strings to None.
    """
    def to_internal_value(self, value):
        if value == '' or value is None:
            return None
        return super().to_internal_value(value)


class PostSerializer(serializers.ModelSerializer):
    """
    Serializer for the Post model with comprehensive field validation.
    Enhanced with user authentication, status management, and scheduling.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the queryset for author_user field
        from django.contrib.auth.models import User
        if 'author_user' in self.fields:
            self.fields['author_user'].queryset = User.objects.all()
    
    # Override fields to customize error messages
    title = serializers.CharField(
        max_length=200,
        required=True,
        allow_blank=True,  # Allow blank so we can do custom validation
        error_messages={
            'required': 'Title is required.',
            'max_length': 'Title cannot exceed 200 characters.'
        }
    )
    
    content = serializers.CharField(
        required=True,
        allow_blank=True,  # Allow blank so we can do custom validation
        error_messages={
            'required': 'Content is required.'
        }
    )
    
    author = serializers.CharField(
        max_length=100,
        required=True,
        allow_blank=True,  # Allow blank so we can do custom validation
        error_messages={
            'required': 'Author is required.',
            'max_length': 'Author name cannot exceed 100 characters.'
        }
    )
    
    tags = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        error_messages={
            'max_length': 'Tags cannot exceed 500 characters.'
        }
    )
    
    status = serializers.ChoiceField(
        choices=Post.STATUS_CHOICES,
        default='draft',
        required=False,
        error_messages={
            'invalid_choice': 'Invalid status. Must be one of: draft, published, scheduled.'
        }
    )
    
    scheduled_publish_date = NullableDateTimeField(
        required=False,
        allow_null=True,
        error_messages={
            'invalid': 'Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS).'
        }
    )
    
    author_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
        error_messages={
            'does_not_exist': 'User does not exist.'
        }
    )
    
    class Meta:
        model = Post
        fields = [
            'id', 'title', 'content', 'author', 'author_user', 'tags', 'image_url', 
            'status', 'scheduled_publish_date', 'view_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'view_count']
    
    def validate_title(self, value):
        """
        Validate the title field with security checks.
        """
        if value is None:
            raise serializers.ValidationError("Title is required.")
        
        title_stripped = value.strip()
        if len(title_stripped) < 5:
            raise serializers.ValidationError("Title must be at least 5 characters long.")
        
        if len(title_stripped) > 200:
            raise serializers.ValidationError("Title cannot exceed 200 characters.")
        
        # Security validations
        try:
            InputSanitizer.validate_no_html(title_stripped)
            SecurityValidator.validate_no_sql_injection_patterns(title_stripped)
            SecurityValidator.validate_rate_limit_safe(title_stripped)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
        
        # Sanitize the title
        sanitized_title = InputSanitizer.sanitize_plain_text(title_stripped)
        
        return sanitized_title
    
    def validate_content(self, value):
        """
        Validate the content field with security checks.
        """
        if value is None:
            raise serializers.ValidationError("Content is required.")
        
        content_stripped = value.strip()
        if len(content_stripped) < 10:
            raise serializers.ValidationError("Content must be at least 10 characters long.")
        
        # Security validations
        try:
            SecurityValidator.validate_content_length(content_stripped, max_length=50000)
            SecurityValidator.validate_no_sql_injection_patterns(content_stripped)
            SecurityValidator.validate_rate_limit_safe(content_stripped)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
        
        # Sanitize the content (allow some HTML but make it safe)
        sanitized_content = InputSanitizer.sanitize_html_content(content_stripped)
        
        return sanitized_content
    
    def validate_author(self, value):
        """
        Validate the author field with security checks.
        """
        if value is None:
            raise serializers.ValidationError("Author is required.")
        
        author_stripped = value.strip()
        if len(author_stripped) < 2:
            raise serializers.ValidationError("Author name must be at least 2 characters long.")
        
        if len(author_stripped) > 100:
            raise serializers.ValidationError("Author name cannot exceed 100 characters.")
        
        # Security validations
        try:
            InputSanitizer.validate_no_html(author_stripped)
            SecurityValidator.validate_no_sql_injection_patterns(author_stripped)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
        
        # Sanitize the author name
        sanitized_author = InputSanitizer.sanitize_plain_text(author_stripped)
        
        return sanitized_author
    
    def validate_tags(self, value):
        """
        Validate the tags field (optional) with security checks.
        """
        if value:
            tags_stripped = value.strip()
            if len(tags_stripped) > 500:
                raise serializers.ValidationError("Tags cannot exceed 500 characters.")
            
            # Security validations
            try:
                InputSanitizer.validate_no_html(tags_stripped)
                SecurityValidator.validate_no_sql_injection_patterns(tags_stripped)
            except DjangoValidationError as e:
                raise serializers.ValidationError(str(e))
            
            # Sanitize the tags
            sanitized_tags = InputSanitizer.sanitize_plain_text(tags_stripped)
            return sanitized_tags
        return value
    
    def validate_image_url(self, value):
        """
        Validate the image_url field (optional) with security checks.
        """
        if value:
            url_stripped = value.strip()
            
            # Security validations
            try:
                InputSanitizer.validate_safe_url(url_stripped)
            except DjangoValidationError as e:
                raise serializers.ValidationError(str(e))
            
            return url_stripped
        return value
    
    def validate_status(self, value):
        """
        Validate the status field.
        """
        if value not in dict(Post.STATUS_CHOICES):
            raise serializers.ValidationError(
                f'Invalid status. Must be one of: {", ".join(dict(Post.STATUS_CHOICES).keys())}'
            )
        return value
    
    def validate_scheduled_publish_date(self, value):
        """
        Validate the scheduled_publish_date field.
        """
        if value:
            from django.utils import timezone
            if value <= timezone.now():
                raise serializers.ValidationError(
                    'Scheduled publish date must be in the future.'
                )
        return value
    
    def validate(self, attrs):
        """
        Object-level validation for additional business rules.
        """
        # Ensure title and content are not identical
        title = attrs.get('title', '').strip().lower()
        content = attrs.get('content', '').strip().lower()
        
        if title and content and title == content:
            raise serializers.ValidationError({
                'content': 'Content cannot be identical to the title.'
            })
        
        # Validate scheduled_publish_date based on status
        status = attrs.get('status', 'draft')
        scheduled_date = attrs.get('scheduled_publish_date')
        
        if status == 'scheduled' and not scheduled_date:
            raise serializers.ValidationError({
                'scheduled_publish_date': 'Scheduled publish date is required for scheduled posts.'
            })
        elif status != 'scheduled' and scheduled_date:
            raise serializers.ValidationError({
                'scheduled_publish_date': 'Scheduled publish date can only be set for scheduled posts.'
            })
        
        # Ensure either author or author_user is provided (backward compatibility)
        author = attrs.get('author')
        author_user = attrs.get('author_user')
        
        if not author and not author_user:
            raise serializers.ValidationError({
                'author': 'Either author name or author user must be provided.'
            })
        
        return attrs
    
    def to_representation(self, instance):
        """
        Customize the serialized output.
        """
        data = super().to_representation(instance)
        
        # Convert tags string to list for better frontend handling
        if data.get('tags'):
            data['tags_list'] = instance.get_tags_list()
        else:
            data['tags_list'] = []
        
        # Add computed fields
        data['author_name'] = instance.get_author_name()
        data['status_display'] = instance.get_status_display()
        data['status_color'] = instance.get_status_display_color()
        data['is_published'] = instance.is_published()
        data['is_draft'] = instance.is_draft()
        data['is_scheduled'] = instance.is_scheduled()
        data['can_be_published'] = instance.can_be_published()
        
        # Add author_user details if available
        if instance.author_user:
            data['author_user_details'] = {
                'id': instance.author_user.id,
                'username': instance.author_user.username,
                'first_name': instance.author_user.first_name,
                'last_name': instance.author_user.last_name,
                'email': instance.author_user.email,
            }
        else:
            data['author_user_details'] = None
        
        return data
    
    def create(self, validated_data):
        """
        Create and return a new Post instance.
        """
        # Set author from author_user if not provided (backward compatibility)
        if validated_data.get('author_user') and not validated_data.get('author'):
            user = validated_data['author_user']
            if user.first_name and user.last_name:
                validated_data['author'] = f"{user.first_name} {user.last_name}"
            elif user.first_name:
                validated_data['author'] = user.first_name
            else:
                validated_data['author'] = user.username
        
        return Post.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """
        Update and return an existing Post instance.
        """
        # Update author from author_user if author_user is being updated
        if 'author_user' in validated_data and validated_data['author_user']:
            user = validated_data['author_user']
            if user.first_name and user.last_name:
                validated_data['author'] = f"{user.first_name} {user.last_name}"
            elif user.first_name:
                validated_data['author'] = user.first_name
            else:
                validated_data['author'] = user.username
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class MediaFileSerializer(serializers.ModelSerializer):
    """
    Serializer for MediaFile model with file upload validation.
    """
    file = serializers.FileField(
        required=True,
        error_messages={
            'required': 'File is required.',
            'invalid': 'Invalid file format.'
        }
    )
    
    alt_text = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        error_messages={
            'max_length': 'Alt text cannot exceed 255 characters.'
        }
    )
    
    class Meta:
        model = MediaFile
        fields = [
            'id', 'file', 'file_type', 'original_name', 'file_size', 
            'alt_text', 'thumbnail', 'width', 'height', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'original_name', 'file_size', 'thumbnail', 'width', 'height', 
            'created_at', 'updated_at'
        ]
    
    def validate_file(self, value):
        """
        Validate uploaded file with security checks.
        """
        if not value:
            raise serializers.ValidationError("File is required.")
        
        # Get file extension
        file_extension = os.path.splitext(value.name)[1].lower()
        
        # Define allowed extensions
        allowed_image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        allowed_video_extensions = ['.mp4', '.webm', '.ogg', '.mov', '.avi']
        all_allowed_extensions = allowed_image_extensions + allowed_video_extensions
        
        # Check if file extension is allowed
        if file_extension not in all_allowed_extensions:
            raise serializers.ValidationError(
                f'Invalid file type. Allowed extensions: {", ".join(all_allowed_extensions)}'
            )
        
        # Check file size limits
        max_image_size = 10 * 1024 * 1024  # 10MB
        max_video_size = 50 * 1024 * 1024  # 50MB
        
        if file_extension in allowed_image_extensions:
            if value.size > max_image_size:
                raise serializers.ValidationError(
                    f'Image file size cannot exceed {max_image_size / (1024 * 1024):.0f}MB'
                )
        elif file_extension in allowed_video_extensions:
            if value.size > max_video_size:
                raise serializers.ValidationError(
                    f'Video file size cannot exceed {max_video_size / (1024 * 1024):.0f}MB'
                )
        
        # Security validation - check for malicious content
        try:
            SecurityValidator.validate_file_upload(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
        
        return value
    
    def validate_alt_text(self, value):
        """
        Validate alt text with security checks.
        """
        if value:
            alt_text_stripped = value.strip()
            if len(alt_text_stripped) > 255:
                raise serializers.ValidationError("Alt text cannot exceed 255 characters.")
            
            # Security validations
            try:
                InputSanitizer.validate_no_html(alt_text_stripped)
                SecurityValidator.validate_no_sql_injection_patterns(alt_text_stripped)
            except DjangoValidationError as e:
                raise serializers.ValidationError(str(e))
            
            # Sanitize the alt text
            sanitized_alt_text = InputSanitizer.sanitize_plain_text(alt_text_stripped)
            return sanitized_alt_text
        return value
    
    def validate(self, attrs):
        """
        Object-level validation.
        """
        file = attrs.get('file')
        if file:
            # Determine file type based on extension
            file_extension = os.path.splitext(file.name)[1].lower()
            allowed_image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            
            if file_extension in allowed_image_extensions:
                attrs['file_type'] = 'image'
            else:
                attrs['file_type'] = 'video'
            
            # Set original name and file size
            attrs['original_name'] = file.name
            attrs['file_size'] = file.size
        
        return attrs
    
    def create(self, validated_data):
        """
        Create MediaFile instance with uploaded_by from request user.
        """
        # Set uploaded_by from request context
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['uploaded_by'] = request.user
        else:
            raise serializers.ValidationError("Authentication required to upload files.")
        
        return MediaFile.objects.create(**validated_data)
    
    def to_representation(self, instance):
        """
        Customize serialized output.
        """
        data = super().to_representation(instance)
        
        # Add file URLs
        data['file_url'] = instance.get_file_url()
        data['thumbnail_url'] = instance.get_thumbnail_url()
        
        # Add uploader details
        if instance.uploaded_by:
            data['uploaded_by_details'] = {
                'id': instance.uploaded_by.id,
                'username': instance.uploaded_by.username,
                'first_name': instance.uploaded_by.first_name,
                'last_name': instance.uploaded_by.last_name,
            }
        
        # Add file size in human readable format
        file_size_mb = instance.file_size / (1024 * 1024) if instance.file_size else 0
        data['file_size_mb'] = round(file_size_mb, 2)
        
        return data


class PostMediaSerializer(serializers.ModelSerializer):
    """
    Serializer for PostMedia model to associate media with posts.
    """
    media_file = MediaFileSerializer(read_only=True)
    media_file_id = serializers.PrimaryKeyRelatedField(
        queryset=MediaFile.objects.all(),
        source='media_file',
        write_only=True,
        error_messages={
            'does_not_exist': 'Media file does not exist.'
        }
    )
    
    caption = serializers.CharField(
        required=False,
        allow_blank=True,
        error_messages={
            'max_length': 'Caption is too long.'
        }
    )
    
    class Meta:
        model = PostMedia
        fields = [
            'id', 'media_file', 'media_file_id', 'order', 'caption', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate_caption(self, value):
        """
        Validate caption with security checks.
        """
        if value:
            caption_stripped = value.strip()
            
            # Security validations
            try:
                SecurityValidator.validate_content_length(caption_stripped, max_length=1000)
                SecurityValidator.validate_no_sql_injection_patterns(caption_stripped)
            except DjangoValidationError as e:
                raise serializers.ValidationError(str(e))
            
            # Sanitize the caption (allow some HTML but make it safe)
            sanitized_caption = InputSanitizer.sanitize_html_content(caption_stripped)
            return sanitized_caption
        return value
    
    def validate(self, attrs):
        """
        Object-level validation.
        """
        # Ensure user can only attach their own media files
        request = self.context.get('request')
        media_file = attrs.get('media_file')
        
        if request and request.user.is_authenticated and media_file:
            if media_file.uploaded_by != request.user:
                # Allow if user has permission to use others' media (e.g., editors/admins)
                if not request.user.has_perm('posts.can_moderate_posts'):
                    raise serializers.ValidationError({
                        'media_file_id': 'You can only attach your own media files.'
                    })
        
        return attrs


class PostWithMediaSerializer(PostSerializer):
    """
    Extended Post serializer that includes media files.
    """
    media_files = PostMediaSerializer(many=True, read_only=True)
    
    class Meta(PostSerializer.Meta):
        fields = PostSerializer.Meta.fields + ['media_files']
    
    def to_representation(self, instance):
        """
        Customize serialized output to include media information.
        """
        data = super().to_representation(instance)
        
        # Add media count
        data['media_count'] = instance.media_files.count()
        
        # Add media types summary
        media_types = instance.media_files.values_list('media_file__file_type', flat=True)
        data['has_images'] = 'image' in media_types
        data['has_videos'] = 'video' in media_types
        
        return data