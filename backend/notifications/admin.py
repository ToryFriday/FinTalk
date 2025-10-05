"""
Admin configuration for notifications app.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import EmailSubscription, NotificationLog, UnsubscribeRequest


@admin.register(EmailSubscription)
class EmailSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'email', 
        'subscription_type', 
        'is_active', 
        'user_link',
        'author_filter_link',
        'created_at',
        'last_notification_sent'
    ]
    list_filter = [
        'subscription_type', 
        'is_active', 
        'created_at',
        'last_notification_sent'
    ]
    search_fields = ['email', 'user__username', 'user__email']
    readonly_fields = ['unsubscribe_token', 'created_at', 'updated_at']
    raw_id_fields = ['user', 'author_filter']
    
    fieldsets = (
        ('Subscription Details', {
            'fields': ('email', 'user', 'subscription_type', 'is_active')
        }),
        ('Filters', {
            'fields': ('author_filter',),
            'classes': ('collapse',)
        }),
        ('System Fields', {
            'fields': ('unsubscribe_token', 'created_at', 'updated_at', 'last_notification_sent'),
            'classes': ('collapse',)
        }),
    )
    
    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return '-'
    user_link.short_description = 'User'
    
    def author_filter_link(self, obj):
        if obj.author_filter:
            url = reverse('admin:auth_user_change', args=[obj.author_filter.pk])
            return format_html('<a href="{}">{}</a>', url, obj.author_filter.username)
        return '-'
    author_filter_link.short_description = 'Author Filter'
    
    actions = ['activate_subscriptions', 'deactivate_subscriptions']
    
    def activate_subscriptions(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} subscriptions were activated.')
    activate_subscriptions.short_description = 'Activate selected subscriptions'
    
    def deactivate_subscriptions(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} subscriptions were deactivated.')
    deactivate_subscriptions.short_description = 'Deactivate selected subscriptions'


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = [
        'subscription_email',
        'notification_type',
        'status',
        'subject',
        'post_link',
        'created_at',
        'sent_at'
    ]
    list_filter = [
        'notification_type',
        'status',
        'created_at',
        'sent_at'
    ]
    search_fields = [
        'subscription__email',
        'subject',
        'post__title'
    ]
    readonly_fields = [
        'subscription',
        'notification_type',
        'subject',
        'post',
        'created_at',
        'sent_at'
    ]
    raw_id_fields = ['subscription', 'post']
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('subscription', 'notification_type', 'status', 'subject')
        }),
        ('Related Content', {
            'fields': ('post',)
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'sent_at'),
            'classes': ('collapse',)
        }),
    )
    
    def subscription_email(self, obj):
        return obj.subscription.email
    subscription_email.short_description = 'Email'
    
    def post_link(self, obj):
        if obj.post:
            url = reverse('admin:posts_post_change', args=[obj.post.pk])
            return format_html('<a href="{}">{}</a>', url, obj.post.title[:50])
        return '-'
    post_link.short_description = 'Post'
    
    def has_add_permission(self, request):
        # Notification logs are created automatically, not manually
        return False


@admin.register(UnsubscribeRequest)
class UnsubscribeRequestAdmin(admin.ModelAdmin):
    list_display = [
        'email',
        'subscription_type',
        'reason',
        'created_at',
        'ip_address'
    ]
    list_filter = [
        'subscription_type',
        'reason',
        'created_at'
    ]
    search_fields = ['email', 'feedback']
    readonly_fields = [
        'email',
        'subscription_type',
        'unsubscribe_token',
        'ip_address',
        'user_agent',
        'created_at'
    ]
    
    fieldsets = (
        ('Unsubscribe Details', {
            'fields': ('email', 'subscription_type', 'reason', 'feedback')
        }),
        ('System Information', {
            'fields': ('unsubscribe_token', 'ip_address', 'user_agent', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Unsubscribe requests are created automatically, not manually
        return False
    
    def has_change_permission(self, request, obj=None):
        # Unsubscribe requests should not be modified
        return False