"""
Serializers for notifications app API endpoints.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from django.core.validators import EmailValidator
from .models import EmailSubscription, NotificationLog, UnsubscribeRequest


class EmailSubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for EmailSubscription model.
    """
    subscriber_name = serializers.CharField(source='get_subscriber_name', read_only=True)
    author_filter_username = serializers.CharField(source='author_filter.username', read_only=True)
    
    class Meta:
        model = EmailSubscription
        fields = [
            'id',
            'email',
            'subscription_type',
            'is_active',
            'author_filter',
            'author_filter_username',
            'subscriber_name',
            'created_at',
            'last_notification_sent'
        ]
        read_only_fields = [
            'id',
            'subscriber_name',
            'author_filter_username',
            'created_at',
            'last_notification_sent'
        ]
    
    def validate_email(self, value):
        """
        Validate email format and normalize.
        """
        email_validator = EmailValidator()
        email_validator(value)
        return value.lower().strip()
    
    def validate(self, data):
        """
        Custom validation for subscription data.
        """
        # Check if author_filter is required for author_posts subscription
        if data.get('subscription_type') == 'author_posts':
            if not data.get('author_filter'):
                raise serializers.ValidationError({
                    'author_filter': 'Author filter is required for author posts subscription.'
                })
        
        # If user is authenticated, ensure email matches user's email
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            user_email = request.user.email.lower()
            if data.get('email') and data['email'] != user_email:
                raise serializers.ValidationError({
                    'email': 'Email must match your registered email address.'
                })
        
        return data
    
    def create(self, validated_data):
        """
        Create a new email subscription.
        """
        request = self.context.get('request')
        
        # Set user if authenticated
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
            # Use user's email if not provided
            if not validated_data.get('email'):
                validated_data['email'] = request.user.email.lower()
        
        return super().create(validated_data)


class EmailSubscriptionCreateSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for creating email subscriptions (public endpoint).
    """
    author_filter = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = EmailSubscription
        fields = [
            'email',
            'subscription_type',
            'author_filter'
        ]
    
    def validate_email(self, value):
        """
        Validate email format and normalize.
        """
        email_validator = EmailValidator()
        email_validator(value)
        return value.lower().strip()
    
    def validate(self, data):
        """
        Custom validation for subscription data.
        """
        # Check if author_filter is required for author_posts subscription
        if data.get('subscription_type') == 'author_posts':
            if not data.get('author_filter'):
                raise serializers.ValidationError({
                    'author_filter': 'Author filter is required for author posts subscription.'
                })
        else:
            # Clear author_filter for non-author subscriptions
            data.pop('author_filter', None)
        
        return data


class NotificationLogSerializer(serializers.ModelSerializer):
    """
    Serializer for NotificationLog model (read-only).
    """
    subscription_email = serializers.CharField(source='subscription.email', read_only=True)
    post_title = serializers.CharField(source='post.title', read_only=True)
    
    class Meta:
        model = NotificationLog
        fields = [
            'id',
            'subscription_email',
            'notification_type',
            'status',
            'subject',
            'post_title',
            'error_message',
            'created_at',
            'sent_at'
        ]
        read_only_fields = '__all__'


class UnsubscribeSerializer(serializers.Serializer):
    """
    Serializer for unsubscribe requests.
    """
    token = serializers.CharField(max_length=100)
    reason = serializers.ChoiceField(
        choices=UnsubscribeRequest.REASON_CHOICES,
        required=False,
        allow_blank=True
    )
    feedback = serializers.CharField(
        max_length=1000,
        required=False,
        allow_blank=True
    )
    
    def validate_token(self, value):
        """
        Validate that the unsubscribe token exists.
        """
        try:
            subscription = EmailSubscription.objects.get(
                unsubscribe_token=value,
                is_active=True
            )
            return value
        except EmailSubscription.DoesNotExist:
            raise serializers.ValidationError('Invalid or expired unsubscribe token.')


class SubscriptionStatsSerializer(serializers.Serializer):
    """
    Serializer for subscription statistics (admin use).
    """
    total_subscriptions = serializers.IntegerField(read_only=True)
    active_subscriptions = serializers.IntegerField(read_only=True)
    inactive_subscriptions = serializers.IntegerField(read_only=True)
    subscriptions_by_type = serializers.DictField(read_only=True)
    recent_subscriptions = serializers.IntegerField(read_only=True)
    recent_unsubscribes = serializers.IntegerField(read_only=True)


class AuthorSubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for author-specific subscriptions.
    """
    author_name = serializers.CharField(source='author_filter.get_full_name', read_only=True)
    author_username = serializers.CharField(source='author_filter.username', read_only=True)
    subscriber_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = EmailSubscription
        fields = [
            'author_filter',
            'author_name',
            'author_username',
            'subscriber_count'
        ]
        read_only_fields = '__all__'