from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Post
from common.security import InputSanitizer, SecurityValidator


class PostSerializer(serializers.ModelSerializer):
    """
    Serializer for the Post model with comprehensive field validation.
    """
    
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
    
    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author', 'tags', 'image_url', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
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
        
        return data
    
    def create(self, validated_data):
        """
        Create and return a new Post instance.
        """
        return Post.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """
        Update and return an existing Post instance.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance