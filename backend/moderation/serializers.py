"""
Serializers for content moderation models.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ContentFlag, ModerationAction, ModerationSettings
from posts.models import Post


class ContentFlagSerializer(serializers.ModelSerializer):
    """
    Serializer for ContentFlag model.
    """
    flagged_by_username = serializers.CharField(source='flagged_by.username', read_only=True)
    flagged_by_name = serializers.SerializerMethodField()
    reviewed_by_username = serializers.CharField(source='reviewed_by.username', read_only=True)
    reviewed_by_name = serializers.SerializerMethodField()
    post_title = serializers.CharField(source='post.title', read_only=True)
    post_author = serializers.SerializerMethodField()
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    flag_count_for_post = serializers.SerializerMethodField()
    can_review = serializers.SerializerMethodField()
    
    class Meta:
        model = ContentFlag
        fields = [
            'id', 'post', 'post_title', 'post_author',
            'flagged_by', 'flagged_by_username', 'flagged_by_name',
            'reason', 'reason_display', 'description',
            'status', 'status_display',
            'reviewed_by', 'reviewed_by_username', 'reviewed_by_name',
            'reviewed_at', 'resolution_notes', 'action_taken',
            'flag_count_for_post', 'can_review',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'flagged_by', 'reviewed_by', 'reviewed_at',
            'created_at', 'updated_at'
        ]
    
    def get_flagged_by_name(self, obj):
        """Get display name for user who flagged the content."""
        if hasattr(obj.flagged_by, 'profile'):
            return obj.flagged_by.profile.get_full_name()
        return obj.flagged_by.get_full_name() or obj.flagged_by.username
    
    def get_reviewed_by_name(self, obj):
        """Get display name for reviewer."""
        if not obj.reviewed_by:
            return None
        if hasattr(obj.reviewed_by, 'profile'):
            return obj.reviewed_by.profile.get_full_name()
        return obj.reviewed_by.get_full_name() or obj.reviewed_by.username
    
    def get_post_author(self, obj):
        """Get post author information."""
        if obj.post.author_user:
            if hasattr(obj.post.author_user, 'profile'):
                return obj.post.author_user.profile.get_full_name()
            return obj.post.author_user.get_full_name() or obj.post.author_user.username
        return obj.post.author
    
    def get_flag_count_for_post(self, obj):
        """Get total flag count for the post."""
        return obj.get_flag_count_for_post()
    
    def get_can_review(self, obj):
        """Check if current user can review this flag."""
        request = self.context.get('request')
        if not request or not request.user:
            return False
        return obj.can_be_reviewed_by(request.user)
    
    def validate(self, data):
        """
        Custom validation for flag creation.
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required to flag content.")
        
        # Check if user is trying to flag their own content
        post = data.get('post')
        if post and hasattr(post, 'author_user') and post.author_user == request.user:
            raise serializers.ValidationError("You cannot flag your own content.")
        
        # Check if user has already flagged this post
        if post and ContentFlag.objects.filter(post=post, flagged_by=request.user).exists():
            raise serializers.ValidationError("You have already flagged this content.")
        
        return data
    
    def create(self, validated_data):
        """
        Create a new content flag.
        """
        request = self.context.get('request')
        validated_data['flagged_by'] = request.user
        return super().create(validated_data)


class ContentFlagCreateSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for creating content flags.
    """
    
    class Meta:
        model = ContentFlag
        fields = ['post', 'reason', 'description']
    
    def validate(self, data):
        """
        Custom validation for flag creation.
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required to flag content.")
        
        # Check if user is trying to flag their own content
        post = data.get('post')
        if post and hasattr(post, 'author_user') and post.author_user == request.user:
            raise serializers.ValidationError("You cannot flag your own content.")
        
        # Check if user has already flagged this post
        if post and ContentFlag.objects.filter(post=post, flagged_by=request.user).exists():
            raise serializers.ValidationError("You have already flagged this content.")
        
        return data
    
    def create(self, validated_data):
        """
        Create a new content flag.
        """
        request = self.context.get('request')
        validated_data['flagged_by'] = request.user
        return super().create(validated_data)


class ContentFlagReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for reviewing content flags.
    """
    
    class Meta:
        model = ContentFlag
        fields = ['status', 'resolution_notes', 'action_taken']
    
    def validate_status(self, value):
        """
        Validate status transitions.
        """
        if self.instance:
            current_status = self.instance.status
            
            # Define valid status transitions
            valid_transitions = {
                'pending': ['under_review', 'resolved_valid', 'resolved_invalid', 'dismissed'],
                'under_review': ['resolved_valid', 'resolved_invalid', 'dismissed'],
                'resolved_valid': [],  # Final state
                'resolved_invalid': [],  # Final state
                'dismissed': []  # Final state
            }
            
            if value not in valid_transitions.get(current_status, []):
                raise serializers.ValidationError(
                    f"Cannot change status from {current_status} to {value}"
                )
        
        return value
    
    def validate(self, data):
        """
        Custom validation for flag review.
        """
        status = data.get('status')
        
        # Require resolution notes for resolved flags
        if status in ['resolved_valid', 'resolved_invalid', 'dismissed']:
            if not data.get('resolution_notes'):
                raise serializers.ValidationError({
                    'resolution_notes': 'Resolution notes are required when resolving flags.'
                })
        
        # Require action_taken for valid flags
        if status == 'resolved_valid' and not data.get('action_taken'):
            raise serializers.ValidationError({
                'action_taken': 'Action taken is required for valid flags.'
            })
        
        return data
    
    def update(self, instance, validated_data):
        """
        Update flag with review information.
        """
        request = self.context.get('request')
        
        # Set reviewer information
        if validated_data.get('status') in ['under_review', 'resolved_valid', 'resolved_invalid', 'dismissed']:
            instance.reviewed_by = request.user
            from django.utils import timezone
            instance.reviewed_at = timezone.now()
        
        return super().update(instance, validated_data)


class ModerationActionSerializer(serializers.ModelSerializer):
    """
    Serializer for ModerationAction model.
    """
    moderator_username = serializers.CharField(source='moderator.username', read_only=True)
    moderator_name = serializers.SerializerMethodField()
    affected_user_username = serializers.CharField(source='affected_user.username', read_only=True)
    affected_user_name = serializers.SerializerMethodField()
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)
    post_title = serializers.CharField(source='post.title', read_only=True)
    flag_id = serializers.IntegerField(source='flag.id', read_only=True)
    
    class Meta:
        model = ModerationAction
        fields = [
            'id', 'flag', 'flag_id', 'post', 'post_title',
            'action_type', 'action_type_display',
            'moderator', 'moderator_username', 'moderator_name',
            'reason', 'notes',
            'affected_user', 'affected_user_username', 'affected_user_name',
            'is_automated', 'severity_level',
            'created_at'
        ]
        read_only_fields = ['id', 'moderator', 'created_at']
    
    def get_moderator_name(self, obj):
        """Get display name for moderator."""
        if not obj.moderator:
            return None
        if hasattr(obj.moderator, 'profile'):
            return obj.moderator.profile.get_full_name()
        return obj.moderator.get_full_name() or obj.moderator.username
    
    def get_affected_user_name(self, obj):
        """Get display name for affected user."""
        if not obj.affected_user:
            return None
        if hasattr(obj.affected_user, 'profile'):
            return obj.affected_user.profile.get_full_name()
        return obj.affected_user.get_full_name() or obj.affected_user.username
    
    def create(self, validated_data):
        """
        Create a new moderation action.
        """
        request = self.context.get('request')
        validated_data['moderator'] = request.user
        return super().create(validated_data)


class ModerationSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for ModerationSettings model.
    """
    
    class Meta:
        model = ModerationSettings
        fields = [
            'auto_flag_threshold', 'auto_hide_threshold',
            'notify_moderators_on_flag', 'notify_author_on_action',
            'enable_spam_detection', 'enable_profanity_filter',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_auto_flag_threshold(self, value):
        """Validate auto flag threshold."""
        if value < 1:
            raise serializers.ValidationError("Auto flag threshold must be at least 1.")
        return value
    
    def validate_auto_hide_threshold(self, value):
        """Validate auto hide threshold."""
        if value < 1:
            raise serializers.ValidationError("Auto hide threshold must be at least 1.")
        return value
    
    def validate(self, data):
        """
        Cross-field validation.
        """
        auto_flag = data.get('auto_flag_threshold')
        auto_hide = data.get('auto_hide_threshold')
        
        # If both are provided, auto_hide should be >= auto_flag
        if auto_flag and auto_hide and auto_hide < auto_flag:
            raise serializers.ValidationError({
                'auto_hide_threshold': 'Auto hide threshold should be greater than or equal to auto flag threshold.'
            })
        
        return data


class FlagSummarySerializer(serializers.Serializer):
    """
    Serializer for flag summary statistics.
    """
    total_flags = serializers.IntegerField()
    pending_flags = serializers.IntegerField()
    under_review_flags = serializers.IntegerField()
    resolved_flags = serializers.IntegerField()
    dismissed_flags = serializers.IntegerField()
    flags_by_reason = serializers.DictField()
    recent_flags = ContentFlagSerializer(many=True)
    
    class Meta:
        fields = [
            'total_flags', 'pending_flags', 'under_review_flags',
            'resolved_flags', 'dismissed_flags', 'flags_by_reason',
            'recent_flags'
        ]