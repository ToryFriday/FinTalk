"""
Email subscription and notification models for the enhanced blog platform.
"""

from django.contrib.auth.models import User
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import EmailValidator
import uuid
import re


class EmailSubscription(models.Model):
    """
    Model for managing user email subscriptions to blog notifications.
    Supports both registered users and anonymous email subscribers.
    """
    SUBSCRIPTION_TYPE_CHOICES = [
        ('all_posts', 'All New Posts'),
        ('weekly_digest', 'Weekly Digest'),
        ('featured_posts', 'Featured Posts Only'),
        ('author_posts', 'Specific Author Posts'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='email_subscriptions',
        help_text="Registered user (optional for anonymous subscriptions)"
    )
    email = models.EmailField(
        help_text="Email address for notifications"
    )
    subscription_type = models.CharField(
        max_length=50, 
        choices=SUBSCRIPTION_TYPE_CHOICES,
        default='all_posts',
        help_text="Type of email notifications to receive"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the subscription is active"
    )
    unsubscribe_token = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Unique token for unsubscribing"
    )
    
    # Optional fields for specific subscriptions
    author_filter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='author_subscriptions',
        help_text="Specific author to follow (for author_posts type)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_notification_sent = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the last notification was sent to this subscription"
    )
    
    class Meta:
        db_table = 'email_subscriptions'
        unique_together = [
            ['email', 'subscription_type', 'author_filter'],  # Prevent duplicate subscriptions
        ]
        indexes = [
            models.Index(fields=['email'], name='subscription_email_idx'),
            models.Index(fields=['user'], name='subscription_user_idx'),
            models.Index(fields=['is_active'], name='subscription_active_idx'),
            models.Index(fields=['subscription_type'], name='subscription_type_idx'),
            models.Index(fields=['unsubscribe_token'], name='subscription_token_idx'),
            models.Index(fields=['author_filter'], name='subscription_author_idx'),
            models.Index(fields=['-created_at'], name='subscription_created_idx'),
            models.Index(fields=['last_notification_sent'], name='subscription_last_sent_idx'),
        ]
    
    def __str__(self):
        return f"{self.email} - {self.get_subscription_type_display()}"
    
    def clean(self):
        """
        Custom validation for EmailSubscription model.
        """
        errors = {}
        
        # Validate email format
        if self.email:
            email_validator = EmailValidator()
            try:
                email_validator(self.email)
                self.email = self.email.lower().strip()
            except ValidationError:
                errors['email'] = 'Enter a valid email address'
        else:
            errors['email'] = 'Email address is required'
        
        # If user is provided, ensure email matches user's email
        if self.user and self.email and self.email != self.user.email.lower():
            errors['email'] = 'Email must match the registered user email'
        
        # Validate author_filter for author_posts subscription type
        if self.subscription_type == 'author_posts':
            if not self.author_filter:
                errors['author_filter'] = 'Author filter is required for author posts subscription'
        else:
            # Clear author_filter for non-author subscriptions
            self.author_filter = None
        
        # Validate subscription type
        if self.subscription_type not in dict(self.SUBSCRIPTION_TYPE_CHOICES):
            errors['subscription_type'] = f'Invalid subscription type. Must be one of: {", ".join(dict(self.SUBSCRIPTION_TYPE_CHOICES).keys())}'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """
        Override save method to ensure validation and generate unsubscribe token.
        """
        # Generate unsubscribe token if not provided
        if not self.unsubscribe_token:
            self.unsubscribe_token = self.generate_unsubscribe_token()
        
        # If user is provided but email is not, use user's email
        if self.user and not self.email:
            self.email = self.user.email.lower()
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def generate_unsubscribe_token(self):
        """
        Generate a unique unsubscribe token.
        """
        return uuid.uuid4().hex
    
    def get_subscriber_name(self):
        """
        Get the subscriber's name (from user if available, otherwise from email).
        """
        if self.user:
            if self.user.first_name and self.user.last_name:
                return f"{self.user.first_name} {self.user.last_name}"
            elif self.user.first_name:
                return self.user.first_name
            else:
                return self.user.username
        else:
            # Extract name from email (before @ symbol)
            return self.email.split('@')[0].replace('.', ' ').replace('_', ' ').title()
    
    def update_last_notification_sent(self):
        """
        Update the timestamp of the last notification sent.
        """
        self.last_notification_sent = timezone.now()
        self.save(update_fields=['last_notification_sent'])
    
    def can_receive_notification(self, cooldown_hours=1):
        """
        Check if enough time has passed since the last notification to send another one.
        """
        if not self.is_active:
            return False
        
        if not self.last_notification_sent:
            return True
        
        cooldown_time = self.last_notification_sent + timezone.timedelta(hours=cooldown_hours)
        return timezone.now() > cooldown_time
    
    def matches_post(self, post):
        """
        Check if this subscription should receive notifications for the given post.
        """
        if not self.is_active:
            return False
        
        if self.subscription_type == 'all_posts':
            return True
        elif self.subscription_type == 'featured_posts':
            # Assuming posts have an is_featured field (would need to be added to Post model)
            return getattr(post, 'is_featured', False)
        elif self.subscription_type == 'author_posts':
            return self.author_filter and post.author_user == self.author_filter
        elif self.subscription_type == 'weekly_digest':
            # Weekly digest is handled separately, not per-post
            return False
        
        return False


class NotificationLog(models.Model):
    """
    Model to track sent notifications for debugging and analytics.
    """
    NOTIFICATION_TYPE_CHOICES = [
        ('new_post', 'New Post Notification'),
        ('weekly_digest', 'Weekly Digest'),
        ('welcome', 'Welcome Email'),
        ('subscription_confirmation', 'Subscription Confirmation'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ]
    
    subscription = models.ForeignKey(
        EmailSubscription,
        on_delete=models.CASCADE,
        related_name='notification_logs',
        help_text="Subscription that received the notification"
    )
    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPE_CHOICES,
        help_text="Type of notification sent"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Status of the notification"
    )
    subject = models.CharField(
        max_length=200,
        help_text="Email subject line"
    )
    
    # Optional reference to the post that triggered the notification
    post = models.ForeignKey(
        'posts.Post',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notification_logs',
        help_text="Post that triggered this notification (if applicable)"
    )
    
    # Error information
    error_message = models.TextField(
        blank=True,
        help_text="Error message if notification failed"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the notification was successfully sent"
    )
    
    class Meta:
        db_table = 'notification_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subscription'], name='notif_log_subscription_idx'),
            models.Index(fields=['notification_type'], name='notif_log_type_idx'),
            models.Index(fields=['status'], name='notif_log_status_idx'),
            models.Index(fields=['post'], name='notif_log_post_idx'),
            models.Index(fields=['-created_at'], name='notif_log_created_idx'),
            models.Index(fields=['sent_at'], name='notif_log_sent_idx'),
        ]
    
    def __str__(self):
        return f"{self.subscription.email} - {self.get_notification_type_display()} - {self.get_status_display()}"
    
    def mark_as_sent(self):
        """
        Mark the notification as successfully sent.
        """
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at'])
    
    def mark_as_failed(self, error_message):
        """
        Mark the notification as failed with error message.
        """
        self.status = 'failed'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])
    
    def mark_as_bounced(self):
        """
        Mark the notification as bounced.
        """
        self.status = 'bounced'
        self.save(update_fields=['status'])


class UnsubscribeRequest(models.Model):
    """
    Model to track unsubscribe requests for analytics and potential re-subscription.
    """
    REASON_CHOICES = [
        ('too_frequent', 'Too Many Emails'),
        ('not_interested', 'Not Interested Anymore'),
        ('wrong_email', 'Wrong Email Address'),
        ('spam', 'Marked as Spam'),
        ('other', 'Other Reason'),
    ]
    
    email = models.EmailField(
        help_text="Email address that unsubscribed"
    )
    subscription_type = models.CharField(
        max_length=50,
        help_text="Type of subscription that was cancelled"
    )
    reason = models.CharField(
        max_length=50,
        choices=REASON_CHOICES,
        null=True,
        blank=True,
        help_text="Reason for unsubscribing"
    )
    feedback = models.TextField(
        blank=True,
        help_text="Additional feedback from the user"
    )
    unsubscribe_token = models.CharField(
        max_length=100,
        help_text="Token used for unsubscribing"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the unsubscribe request"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent string of the unsubscribe request"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'unsubscribe_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email'], name='unsub_email_idx'),
            models.Index(fields=['unsubscribe_token'], name='unsub_token_idx'),
            models.Index(fields=['reason'], name='unsub_reason_idx'),
            models.Index(fields=['-created_at'], name='unsub_created_idx'),
        ]
    
    def __str__(self):
        return f"{self.email} - {self.subscription_type} - {self.created_at.strftime('%Y-%m-%d')}"