"""
Custom permissions for content moderation system.
"""

from rest_framework import permissions
from accounts.permissions import RoleBasedPermission


class CanModerateFlagsPermission(permissions.BasePermission):
    """
    Permission class for moderating content flags.
    Allows admins, editors, and users with specific moderation permissions.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Superusers always have permission
        if user.is_superuser:
            return True
        
        # Admins and editors can moderate
        if hasattr(user, 'has_any_role') and user.has_any_role(['admin', 'editor']):
            return True
        
        # Users with specific moderation permission
        if hasattr(user, 'has_role_permission') and user.has_role_permission('can_moderate_content'):
            return True
        
        # Check Django permissions as fallback
        return user.has_perm('moderation.can_moderate_content')
    
    def has_object_permission(self, request, view, obj):
        """
        Check object-level permissions for flag moderation.
        """
        return self.has_permission(request, view)


class CanViewFlagsPermission(permissions.BasePermission):
    """
    Permission class for viewing content flags.
    More permissive than moderation permission.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Superusers always have permission
        if user.is_superuser:
            return True
        
        # Admins and editors can view flags
        if hasattr(user, 'has_any_role') and user.has_any_role(['admin', 'editor']):
            return True
        
        # Users with specific view permission
        if hasattr(user, 'has_role_permission') and user.has_role_permission('can_view_flags'):
            return True
        
        # Check Django permissions as fallback
        return user.has_perm('moderation.can_view_flags')


class CanResolveFlagsPermission(permissions.BasePermission):
    """
    Permission class for resolving content flags.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Superusers always have permission
        if user.is_superuser:
            return True
        
        # Admins and editors can resolve flags
        if hasattr(user, 'has_any_role') and user.has_any_role(['admin', 'editor']):
            return True
        
        # Users with specific resolve permission
        if hasattr(user, 'has_role_permission') and user.has_role_permission('can_resolve_flags'):
            return True
        
        # Check Django permissions as fallback
        return user.has_perm('moderation.can_resolve_flags')


class CanDismissFlagsPermission(permissions.BasePermission):
    """
    Permission class for dismissing content flags.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Superusers always have permission
        if user.is_superuser:
            return True
        
        # Admins and editors can dismiss flags
        if hasattr(user, 'has_any_role') and user.has_any_role(['admin', 'editor']):
            return True
        
        # Users with specific dismiss permission
        if hasattr(user, 'has_role_permission') and user.has_role_permission('can_dismiss_flags'):
            return True
        
        # Check Django permissions as fallback
        return user.has_perm('moderation.can_dismiss_flags')


class IsContentOwnerOrModerator(permissions.BasePermission):
    """
    Permission class that allows content owners or moderators to access content.
    """
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Superusers always have permission
        if user.is_superuser:
            return True
        
        # Admins and editors have permission
        if hasattr(user, 'has_any_role') and user.has_any_role(['admin', 'editor']):
            return True
        
        # Check if user is the content owner
        if hasattr(obj, 'author_user') and obj.author_user == user:
            return True
        
        if hasattr(obj, 'user') and obj.user == user:
            return True
        
        return False


# Role-based permission classes using the existing system

class ModerationAdminRequired(RoleBasedPermission):
    """Permission class that requires admin role for moderation admin tasks."""
    
    def __init__(self):
        super().__init__(required_roles=['admin'])


class ModerationEditorRequired(RoleBasedPermission):
    """Permission class that requires editor role or higher for moderation tasks."""
    
    def __init__(self):
        super().__init__(required_roles=['admin', 'editor'])


class ModerationPermissionRequired(RoleBasedPermission):
    """Permission class that requires specific moderation permissions."""
    
    def __init__(self, permissions=None):
        super().__init__(required_permissions=permissions or ['can_moderate_content'])