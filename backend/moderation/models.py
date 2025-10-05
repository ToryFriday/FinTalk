"""
Content moderation models for tracking flagged content and moderation actions.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


class ContentFlag(models.Model):
    """
    Model for tracking reported/flagged content that needs moderation review.
    """
    
    FLAG_REASON_CHOICES = [
        ('spam', 'Spam'),
        ('inappropriate', 'Inappropriate Content'),
        ('harassment', 'Harassment'),
        ('hate_speech', 'Hate Speech'),
        ('violence', 'Violence'),
        ('copyright', 'Copyright Violation'),
        ('misinformation', 'Misinformation'),
        ('off_topic', 'Off Topic'),
        ('other', 'Other'),
    ]
    
    FLAG_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('resolved_valid', 'Resolved - Valid Flag'),
        ('resolved_invalid', 'Resolved - Invalid Flag'),
        ('dismissed', 'Dismissed'),
    ]
    
    # Content being flagged
    post = models.ForeignKey(
        'posts.Post',
        on_delete=models.CASCADE,
        related_name='flags',
        help_text="Post that was flagged"
    )
    
    # Flag details
    flagged_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='flags_created',
        help_text="User who flagged the content"
    )
    reason = models.CharField(
        max_length=20,
        choices=FLAG_REASON_CHOICES,
        help_text="Reason for flagging the content"
    )
    description = models.TextField(
        blank=True,
        max_length=1000,
        help_text="Additional details about why the content was flagged"
    )
    
    # Status and resolution
    status = models.CharField(
        max_length=20,
        choices=FLAG_STATUS_CHOICES,
        default='pending',
        help_text="Current status of the flag"
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='flags_reviewed',
        help_text="Moderator who reviewed this flag"
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the flag was reviewed"
    )
    resolution_notes = models.TextField(
        blank=True,
        max_length=1000,
        help_text="Notes from the moderator about the resolution"
    )
    
    # Moderation actions taken
    action_taken = models.CharField(
        max_length=50,
        blank=True,
        help_text="Action taken by moderator (e.g., 'content_removed', 'warning_issued')"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the flag was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When the flag was last updated"
    )
    
    class Meta:
        db_table = 'content_flags'
        ordering = ['-created_at']
        unique_together = ['post', 'flagged_by']  # Prevent duplicate flags from same user
        indexes = [
            models.Index(fields=['post'], name='flags_post_idx'),
            models.Index(fields=['flagged_by'], name='flags_flagged_by_idx'),
            models.Index(fields=['status'], name='flags_status_idx'),
            models.Index(fields=['reason'], name='flags_reason_idx'),
            models.Index(fields=['reviewed_by'], name='flags_reviewed_by_idx'),
            models.Index(fields=['-created_at'], name='flags_created_at_idx'),
            models.Index(fields=['status', '-created_at'], name='flags_status_created_idx'),
            models.Index(fields=['post', 'status'], name='flags_post_status_idx'),
        ]
        permissions = [
            ('can_moderate_content', 'Can moderate flagged content'),
            ('can_view_flags', 'Can view content flags'),
            ('can_resolve_flags', 'Can resolve content flags'),
            ('can_dismiss_flags', 'Can dismiss content flags'),
        ]
    
    def __str__(self):
        return f"Flag #{self.id}: {self.post.title} - {self.get_reason_display()}"
    
    def clean(self):
        """
        Custom validation for ContentFlag model.
        """
        errors = {}
        
        # Validate description length
        if self.description and len(self.description.strip()) > 1000:
            errors['description'] = 'Description cannot exceed 1000 characters'
        
        # Validate resolution notes length
        if self.resolution_notes and len(self.resolution_notes.strip()) > 1000:
            errors['resolution_notes'] = 'Resolution notes cannot exceed 1000 characters'
        
        # Validate that reviewed fields are set together
        if self.status in ['resolved_valid', 'resolved_invalid', 'dismissed']:
            if not self.reviewed_by:
                errors['reviewed_by'] = 'Reviewer is required for resolved/dismissed flags'
            if not self.reviewed_at:
                self.reviewed_at = timezone.now()
        
        # Validate that pending flags don't have review information
        if self.status == 'pending':
            if self.reviewed_by:
                errors['reviewed_by'] = 'Pending flags should not have a reviewer assigned'
            if self.reviewed_at:
                errors['reviewed_at'] = 'Pending flags should not have a review date'
        
        # Prevent users from flagging their own content
        if hasattr(self.post, 'author_user') and self.post.author_user == self.flagged_by:
            errors['flagged_by'] = 'Users cannot flag their own content'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """
        Override save method to ensure validation and clean data.
        """
        # Clean whitespace from text fields
        if self.description:
            self.description = self.description.strip()
        if self.resolution_notes:
            self.resolution_notes = self.resolution_notes.strip()
        if self.action_taken:
            self.action_taken = self.action_taken.strip()
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def is_pending(self):
        """Check if flag is pending review."""
        return self.status == 'pending'
    
    def is_under_review(self):
        """Check if flag is under review."""
        return self.status == 'under_review'
    
    def is_resolved(self):
        """Check if flag has been resolved."""
        return self.status in ['resolved_valid', 'resolved_invalid', 'dismissed']
    
    def is_valid_flag(self):
        """Check if flag was resolved as valid."""
        return self.status == 'resolved_valid'
    
    def is_invalid_flag(self):
        """Check if flag was resolved as invalid."""
        return self.status == 'resolved_invalid'
    
    def is_dismissed(self):
        """Check if flag was dismissed."""
        return self.status == 'dismissed'
    
    def can_be_reviewed_by(self, user):
        """
        Check if user can review this flag.
        """
        if not user or not user.is_authenticated:
            return False
        
        # Superusers can review any flag
        if user.is_superuser:
            return True
        
        # Admins and editors can review flags
        if user.has_any_role(['admin', 'editor']):
            return True
        
        # Users with specific moderation permission can review
        if user.has_role_permission('can_moderate_content'):
            return True
        
        return False
    
    def start_review(self, reviewer):
        """
        Start reviewing this flag.
        """
        if not self.can_be_reviewed_by(reviewer):
            raise ValidationError("User does not have permission to review this flag")
        
        if self.status != 'pending':
            raise ValidationError("Only pending flags can be put under review")
        
        self.status = 'under_review'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save()
    
    def resolve_as_valid(self, reviewer, resolution_notes='', action_taken=''):
        """
        Resolve flag as valid (content is inappropriate).
        """
        if not self.can_be_reviewed_by(reviewer):
            raise ValidationError("User does not have permission to resolve this flag")
        
        self.status = 'resolved_valid'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.resolution_notes = resolution_notes
        self.action_taken = action_taken
        self.save()
    
    def resolve_as_invalid(self, reviewer, resolution_notes=''):
        """
        Resolve flag as invalid (content is appropriate).
        """
        if not self.can_be_reviewed_by(reviewer):
            raise ValidationError("User does not have permission to resolve this flag")
        
        self.status = 'resolved_invalid'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.resolution_notes = resolution_notes
        self.action_taken = ''
        self.save()
    
    def dismiss(self, reviewer, resolution_notes=''):
        """
        Dismiss flag without resolution.
        """
        if not self.can_be_reviewed_by(reviewer):
            raise ValidationError("User does not have permission to dismiss this flag")
        
        self.status = 'dismissed'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.resolution_notes = resolution_notes
        self.action_taken = ''
        self.save()
    
    def get_flag_count_for_post(self):
        """
        Get total number of flags for this post.
        """
        return ContentFlag.objects.filter(post=self.post).count()
    
    def get_pending_flag_count_for_post(self):
        """
        Get number of pending flags for this post.
        """
        return ContentFlag.objects.filter(
            post=self.post,
            status='pending'
        ).count()


class ModerationAction(models.Model):
    """
    Model for tracking moderation actions taken on content.
    """
    
    ACTION_TYPE_CHOICES = [
        ('content_removed', 'Content Removed'),
        ('content_edited', 'Content Edited'),
        ('warning_issued', 'Warning Issued'),
        ('user_suspended', 'User Suspended'),
        ('user_banned', 'User Banned'),
        ('flag_dismissed', 'Flag Dismissed'),
        ('no_action', 'No Action Taken'),
    ]
    
    # Related flag and content
    flag = models.ForeignKey(
        ContentFlag,
        on_delete=models.CASCADE,
        related_name='moderation_actions',
        help_text="Flag that triggered this action"
    )
    post = models.ForeignKey(
        'posts.Post',
        on_delete=models.CASCADE,
        related_name='moderation_actions',
        help_text="Post that was moderated"
    )
    
    # Action details
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_TYPE_CHOICES,
        help_text="Type of moderation action taken"
    )
    moderator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='moderation_actions_taken',
        help_text="Moderator who took the action"
    )
    reason = models.TextField(
        help_text="Reason for taking this action"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about the action"
    )
    
    # Affected user
    affected_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderation_actions_received',
        help_text="User affected by this action"
    )
    
    # Action metadata
    is_automated = models.BooleanField(
        default=False,
        help_text="Whether this action was taken automatically"
    )
    severity_level = models.IntegerField(
        default=1,
        help_text="Severity level of the action (1-5)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the action was taken"
    )
    
    class Meta:
        db_table = 'moderation_actions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['flag'], name='mod_actions_flag_idx'),
            models.Index(fields=['post'], name='mod_actions_post_idx'),
            models.Index(fields=['moderator'], name='mod_actions_moderator_idx'),
            models.Index(fields=['affected_user'], name='mod_actions_affected_user_idx'),
            models.Index(fields=['action_type'], name='mod_actions_type_idx'),
            models.Index(fields=['-created_at'], name='mod_actions_created_idx'),
            models.Index(fields=['is_automated'], name='mod_actions_automated_idx'),
        ]
    
    def __str__(self):
        return f"Moderation Action: {self.get_action_type_display()} on {self.post.title}"
    
    def clean(self):
        """
        Custom validation for ModerationAction model.
        """
        errors = {}
        
        # Validate severity level
        if self.severity_level < 1 or self.severity_level > 5:
            errors['severity_level'] = 'Severity level must be between 1 and 5'
        
        # Validate that user actions have affected_user set
        if self.action_type in ['warning_issued', 'user_suspended', 'user_banned']:
            if not self.affected_user:
                errors['affected_user'] = f'Affected user is required for {self.get_action_type_display()}'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """
        Override save method to ensure validation.
        """
        # Set affected_user from post author if not set
        if not self.affected_user and hasattr(self.post, 'author_user'):
            self.affected_user = self.post.author_user
        
        self.full_clean()
        super().save(*args, **kwargs)


class ModerationSettings(models.Model):
    """
    Model for storing moderation settings and thresholds.
    """
    
    # Auto-moderation thresholds
    auto_flag_threshold = models.IntegerField(
        default=3,
        help_text="Number of flags that trigger automatic review"
    )
    auto_hide_threshold = models.IntegerField(
        default=5,
        help_text="Number of flags that automatically hide content"
    )
    
    # Notification settings
    notify_moderators_on_flag = models.BooleanField(
        default=True,
        help_text="Send notifications to moderators when content is flagged"
    )
    notify_author_on_action = models.BooleanField(
        default=True,
        help_text="Notify content author when moderation action is taken"
    )
    
    # Content filtering
    enable_spam_detection = models.BooleanField(
        default=True,
        help_text="Enable automatic spam detection"
    )
    enable_profanity_filter = models.BooleanField(
        default=False,
        help_text="Enable automatic profanity filtering"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'moderation_settings'
        verbose_name = 'Moderation Settings'
        verbose_name_plural = 'Moderation Settings'
    
    def __str__(self):
        return "Moderation Settings"
    
    @classmethod
    def get_settings(cls):
        """
        Get the current moderation settings (singleton pattern).
        """
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
    
    def should_auto_flag(self, flag_count):
        """
        Check if content should be automatically flagged for review.
        """
        return flag_count >= self.auto_flag_threshold
    
    def should_auto_hide(self, flag_count):
        """
        Check if content should be automatically hidden.
        """
        return flag_count >= self.auto_hide_threshold