"""
Admin configuration for accounts app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.db.models import Count
from .models import UserProfile, Role, UserRole


class UserProfileInline(admin.StackedInline):
    """
    Inline admin for UserProfile.
    """
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = (
        'bio', 'avatar', 'website', 'location', 'birth_date',
        'is_email_verified', 'email_verification_token', 'email_verification_sent_at'
    )
    readonly_fields = ('email_verification_token', 'email_verification_sent_at')


class UserAdmin(BaseUserAdmin):
    """
    Extended User admin with profile information.
    """
    inlines = (UserProfileInline,)
    list_display = (
        'username', 'email', 'first_name', 'last_name', 
        'is_email_verified', 'is_active', 'date_joined'
    )
    list_filter = (
        'is_active', 'is_staff', 'is_superuser', 'date_joined',
        'profile__is_email_verified'
    )
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    
    def is_email_verified(self, obj):
        """
        Display email verification status.
        """
        if hasattr(obj, 'profile'):
            if obj.profile.is_email_verified:
                return format_html('<span style="color: green;">✓ Verified</span>')
            else:
                return format_html('<span style="color: red;">✗ Not Verified</span>')
        return format_html('<span style="color: gray;">No Profile</span>')
    
    is_email_verified.short_description = 'Email Verified'
    is_email_verified.admin_order_field = 'profile__is_email_verified'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for UserProfile model.
    """
    list_display = (
        'user', 'get_full_name', 'is_email_verified', 
        'has_avatar', 'created_at', 'updated_at'
    )
    list_filter = (
        'is_email_verified', 'created_at', 'updated_at'
    )
    search_fields = (
        'user__username', 'user__first_name', 'user__last_name', 
        'user__email', 'bio', 'location'
    )
    readonly_fields = (
        'created_at', 'updated_at', 'email_verification_sent_at',
        'get_avatar_preview'
    )
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Profile Information', {
            'fields': ('bio', 'avatar', 'get_avatar_preview', 'website', 'location', 'birth_date')
        }),
        ('Email Verification', {
            'fields': (
                'is_email_verified', 'email_verification_token', 
                'email_verification_sent_at'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_full_name(self, obj):
        """
        Display user's full name.
        """
        return obj.get_full_name()
    
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'user__first_name'
    
    def has_avatar(self, obj):
        """
        Display whether user has an avatar.
        """
        if obj.avatar:
            return format_html('<span style="color: green;">✓ Yes</span>')
        return format_html('<span style="color: gray;">✗ No</span>')
    
    has_avatar.short_description = 'Has Avatar'
    has_avatar.admin_order_field = 'avatar'
    
    def get_avatar_preview(self, obj):
        """
        Display avatar preview in admin.
        """
        if obj.avatar:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: cover; border-radius: 50%;" />',
                obj.avatar.url
            )
        return format_html('<span style="color: gray;">No avatar</span>')
    
    get_avatar_preview.short_description = 'Avatar Preview'


# RBAC Admin Classes

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """
    Admin interface for Role model.
    """
    list_display = (
        'name', 'display_name', 'is_active', 'permission_count', 
        'user_count', 'created_at', 'updated_at'
    )
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'display_name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'permission_count', 'user_count')
    filter_horizontal = ('permissions',)
    
    fieldsets = (
        ('Role Information', {
            'fields': ('name', 'display_name', 'description', 'is_active')
        }),
        ('Permissions', {
            'fields': ('permissions',)
        }),
        ('Statistics', {
            'fields': ('permission_count', 'user_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def permission_count(self, obj):
        """
        Display number of permissions assigned to role.
        """
        return obj.permissions.count()
    
    permission_count.short_description = 'Permissions'
    
    def user_count(self, obj):
        """
        Display number of users assigned to role.
        """
        return obj.user_assignments.filter(is_active=True).count()
    
    user_count.short_description = 'Active Users'
    
    def get_queryset(self, request):
        """
        Optimize queryset with prefetch_related.
        """
        return super().get_queryset(request).prefetch_related('permissions')


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """
    Admin interface for UserRole model.
    """
    list_display = (
        'user', 'role', 'assigned_by', 'assigned_at', 
        'is_active', 'expires_at', 'is_expired_status'
    )
    list_filter = (
        'is_active', 'role', 'assigned_at', 'expires_at'
    )
    search_fields = (
        'user__username', 'user__email', 'role__name', 
        'assigned_by__username', 'notes'
    )
    readonly_fields = ('assigned_at', 'is_expired_status', 'is_valid_status')
    date_hierarchy = 'assigned_at'
    
    fieldsets = (
        ('Assignment Information', {
            'fields': ('user', 'role', 'assigned_by', 'is_active')
        }),
        ('Expiration', {
            'fields': ('expires_at', 'is_expired_status', 'is_valid_status')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('assigned_at',),
            'classes': ('collapse',)
        }),
    )
    
    def is_expired_status(self, obj):
        """
        Display expiration status.
        """
        if obj.is_expired():
            return format_html('<span style="color: red;">✗ Expired</span>')
        return format_html('<span style="color: green;">✓ Active</span>')
    
    is_expired_status.short_description = 'Expiration Status'
    
    def is_valid_status(self, obj):
        """
        Display validity status.
        """
        if obj.is_valid():
            return format_html('<span style="color: green;">✓ Valid</span>')
        return format_html('<span style="color: red;">✗ Invalid</span>')
    
    is_valid_status.short_description = 'Validity Status'
    
    def get_queryset(self, request):
        """
        Optimize queryset with select_related.
        """
        return super().get_queryset(request).select_related('user', 'role', 'assigned_by')


# Enhanced UserAdmin with role information
class UserRoleInline(admin.TabularInline):
    """
    Inline admin for UserRole in User admin.
    """
    model = UserRole
    fk_name = 'user'  # Specify which ForeignKey to use
    extra = 0
    fields = ('role', 'assigned_by', 'assigned_at', 'is_active', 'expires_at')
    readonly_fields = ('assigned_at',)
    
    def get_queryset(self, request):
        """
        Optimize queryset.
        """
        return super().get_queryset(request).select_related('role', 'assigned_by')


class EnhancedUserAdmin(BaseUserAdmin):
    """
    Enhanced User admin with profile and role information.
    """
    inlines = (UserProfileInline, UserRoleInline)
    list_display = (
        'username', 'email', 'first_name', 'last_name', 
        'is_email_verified', 'user_roles_display', 'is_active', 'date_joined'
    )
    list_filter = (
        'is_active', 'is_staff', 'is_superuser', 'date_joined',
        'profile__is_email_verified', 'user_roles__role__name'
    )
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    
    def is_email_verified(self, obj):
        """
        Display email verification status.
        """
        if hasattr(obj, 'profile'):
            if obj.profile.is_email_verified:
                return format_html('<span style="color: green;">✓ Verified</span>')
            else:
                return format_html('<span style="color: red;">✗ Not Verified</span>')
        return format_html('<span style="color: gray;">No Profile</span>')
    
    is_email_verified.short_description = 'Email Verified'
    is_email_verified.admin_order_field = 'profile__is_email_verified'
    
    def user_roles_display(self, obj):
        """
        Display user's active roles.
        """
        active_roles = obj.user_roles.filter(is_active=True).select_related('role')
        if active_roles:
            role_names = [ur.role.display_name for ur in active_roles]
            return ', '.join(role_names)
        return format_html('<span style="color: gray;">No roles</span>')
    
    user_roles_display.short_description = 'Roles'
    
    def get_queryset(self, request):
        """
        Optimize queryset with prefetch_related.
        """
        return super().get_queryset(request).select_related('profile').prefetch_related('user_roles__role')


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, EnhancedUserAdmin)