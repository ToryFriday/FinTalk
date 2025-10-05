"""
Django admin configuration for moderation models.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone
from .models import ContentFlag, ModerationAction, ModerationSettings


@admin.register(ContentFlag)
class ContentFlagAdmin(admin.ModelAdmin):
    """
    Admin interface for ContentFlag model.
    """
    list_display = [
        'id', 'post_title_link', 'reason', 'status', 'flagged_by_link', 
        'reviewed_by_link', 'created_at', 'flag_count_for_post'
    ]
    list_filter = [
        'status', 'reason', 'created_at', 'reviewed_at'
    ]
    search_fields = [
        'post__title', 'flagged_by__username', 'reviewed_by__username',
        'description', 'resolution_notes'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'flag_count_for_post'
    ]
    fieldsets = (
        ('Flag Information', {
            'fields': ('id', 'post', 'flagged_by', 'reason', 'description', 'created_at')
        }),
        ('Review Information', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'resolution_notes', 'action_taken')
        }),
        ('Metadata', {
            'fields': ('updated_at', 'flag_count_for_post'),
            'classes': ('collapse',)
        })
    )
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    actions = ['mark_as_under_review', 'mark_as_resolved_valid', 'mark_as_resolved_invalid']
    
    def post_title_link(self, obj):
        """Display post title as link to post admin."""
        if obj.post:
            url = reverse('admin:posts_post_change', args=[obj.post.id])
            return format_html('<a href="{}">{}</a>', url, obj.post.title)
        return '-'
    post_title_link.short_description = 'Post'
    post_title_link.admin_order_field = 'post__title'
    
    def flagged_by_link(self, obj):
        """Display flagged by user as link to user admin."""
        if obj.flagged_by:
            url = reverse('admin:auth_user_change', args=[obj.flagged_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.flagged_by.username)
        return '-'
    flagged_by_link.short_description = 'Flagged By'
    flagged_by_link.admin_order_field = 'flagged_by__username'
    
    def reviewed_by_link(self, obj):
        """Display reviewed by user as link to user admin."""
        if obj.reviewed_by:
            url = reverse('admin:auth_user_change', args=[obj.reviewed_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.reviewed_by.username)
        return '-'
    reviewed_by_link.short_description = 'Reviewed By'
    reviewed_by_link.admin_order_field = 'reviewed_by__username'
    
    def flag_count_for_post(self, obj):
        """Display total flag count for the post."""
        return obj.get_flag_count_for_post()
    flag_count_for_post.short_description = 'Total Flags'
    
    def mark_as_under_review(self, request, queryset):
        """Admin action to mark flags as under review."""
        updated = queryset.filter(status='pending').update(
            status='under_review',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} flags marked as under review.')
    mark_as_under_review.short_description = 'Mark selected flags as under review'
    
    def mark_as_resolved_valid(self, request, queryset):
        """Admin action to mark flags as resolved valid."""
        updated = queryset.filter(status__in=['pending', 'under_review']).update(
            status='resolved_valid',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} flags marked as resolved (valid).')
    mark_as_resolved_valid.short_description = 'Mark selected flags as resolved (valid)'
    
    def mark_as_resolved_invalid(self, request, queryset):
        """Admin action to mark flags as resolved invalid."""
        updated = queryset.filter(status__in=['pending', 'under_review']).update(
            status='resolved_invalid',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} flags marked as resolved (invalid).')
    mark_as_resolved_invalid.short_description = 'Mark selected flags as resolved (invalid)'


@admin.register(ModerationAction)
class ModerationActionAdmin(admin.ModelAdmin):
    """
    Admin interface for ModerationAction model.
    """
    list_display = [
        'id', 'flag_link', 'post_title_link', 'action_type', 'moderator_link',
        'affected_user_link', 'severity_level', 'is_automated', 'created_at'
    ]
    list_filter = [
        'action_type', 'is_automated', 'severity_level', 'created_at'
    ]
    search_fields = [
        'flag__post__title', 'moderator__username', 'affected_user__username',
        'reason', 'notes'
    ]
    readonly_fields = [
        'id', 'created_at'
    ]
    fieldsets = (
        ('Action Information', {
            'fields': ('id', 'flag', 'post', 'action_type', 'moderator', 'created_at')
        }),
        ('Details', {
            'fields': ('reason', 'notes', 'affected_user', 'severity_level', 'is_automated')
        })
    )
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def flag_link(self, obj):
        """Display flag as link to flag admin."""
        if obj.flag:
            url = reverse('admin:moderation_contentflag_change', args=[obj.flag.id])
            return format_html('<a href="{}">Flag #{}</a>', url, obj.flag.id)
        return '-'
    flag_link.short_description = 'Flag'
    flag_link.admin_order_field = 'flag__id'
    
    def post_title_link(self, obj):
        """Display post title as link to post admin."""
        if obj.post:
            url = reverse('admin:posts_post_change', args=[obj.post.id])
            return format_html('<a href="{}">{}</a>', url, obj.post.title)
        return '-'
    post_title_link.short_description = 'Post'
    post_title_link.admin_order_field = 'post__title'
    
    def moderator_link(self, obj):
        """Display moderator as link to user admin."""
        if obj.moderator:
            url = reverse('admin:auth_user_change', args=[obj.moderator.id])
            return format_html('<a href="{}">{}</a>', url, obj.moderator.username)
        return '-'
    moderator_link.short_description = 'Moderator'
    moderator_link.admin_order_field = 'moderator__username'
    
    def affected_user_link(self, obj):
        """Display affected user as link to user admin."""
        if obj.affected_user:
            url = reverse('admin:auth_user_change', args=[obj.affected_user.id])
            return format_html('<a href="{}">{}</a>', url, obj.affected_user.username)
        return '-'
    affected_user_link.short_description = 'Affected User'
    affected_user_link.admin_order_field = 'affected_user__username'


@admin.register(ModerationSettings)
class ModerationSettingsAdmin(admin.ModelAdmin):
    """
    Admin interface for ModerationSettings model.
    """
    list_display = [
        'id', 'auto_flag_threshold', 'auto_hide_threshold',
        'notify_moderators_on_flag', 'notify_author_on_action',
        'enable_spam_detection', 'enable_profanity_filter',
        'updated_at'
    ]
    fieldsets = (
        ('Auto-Moderation Thresholds', {
            'fields': ('auto_flag_threshold', 'auto_hide_threshold'),
            'description': 'Configure automatic moderation thresholds based on flag counts.'
        }),
        ('Notification Settings', {
            'fields': ('notify_moderators_on_flag', 'notify_author_on_action'),
            'description': 'Configure when to send email notifications.'
        }),
        ('Content Filtering', {
            'fields': ('enable_spam_detection', 'enable_profanity_filter'),
            'description': 'Enable automatic content filtering features.'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        """Only allow one settings instance."""
        return not ModerationSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Don't allow deletion of settings."""
        return False


# Customize admin site header and title
admin.site.site_header = 'FinTalk Administration'
admin.site.site_title = 'FinTalk Admin'
admin.site.index_title = 'Welcome to FinTalk Administration'
