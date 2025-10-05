"""
Custom permissions and decorators for role-based access control (RBAC).
"""

from functools import wraps
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status


class RoleBasedPermission(permissions.BasePermission):
    """
    Custom permission class for role-based access control.
    """
    
    def __init__(self, required_roles=None, required_permissions=None):
        """
        Initialize with required roles and/or permissions.
        
        Args:
            required_roles: List of role names required
            required_permissions: List of permission codenames required
        """
        self.required_roles = required_roles or []
        self.required_permissions = required_permissions or []
    
    def has_permission(self, request, view):
        """
        Check if user has required roles or permissions.
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Superusers always have permission
        if user.is_superuser:
            return True
        
        # Check required roles
        if self.required_roles:
            if not user.has_any_role(self.required_roles):
                return False
        
        # Check required permissions
        if self.required_permissions:
            for permission in self.required_permissions:
                if not user.has_role_permission(permission):
                    return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        """
        Check object-level permissions.
        """
        return self.has_permission(request, view)


class AdminRequired(RoleBasedPermission):
    """Permission class that requires admin role."""
    
    def __init__(self):
        super().__init__(required_roles=['admin'])


class EditorRequired(RoleBasedPermission):
    """Permission class that requires editor role or higher."""
    
    def __init__(self):
        super().__init__(required_roles=['admin', 'editor'])


class WriterRequired(RoleBasedPermission):
    """Permission class that requires writer role or higher."""
    
    def __init__(self):
        super().__init__(required_roles=['admin', 'editor', 'writer'])


class ReaderRequired(RoleBasedPermission):
    """Permission class that requires reader role or higher."""
    
    def __init__(self):
        super().__init__(required_roles=['admin', 'editor', 'writer', 'reader'])


# Decorator functions for function-based views

def require_roles(*roles):
    """
    Decorator that requires user to have one of the specified roles.
    
    Usage:
        @require_roles('admin', 'editor')
        def my_view(request):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({
                    'error': 'Authentication required.'
                }, status=401)
            
            if not (request.user.is_superuser or request.user.has_any_role(roles)):
                return JsonResponse({
                    'error': 'Insufficient permissions.'
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_permissions(*permissions):
    """
    Decorator that requires user to have all specified permissions.
    
    Usage:
        @require_permissions('can_manage_roles', 'can_assign_roles')
        def my_view(request):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({
                    'error': 'Authentication required.'
                }, status=401)
            
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            for permission in permissions:
                if not request.user.has_role_permission(permission):
                    return JsonResponse({
                        'error': f'Permission required: {permission}'
                    }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def admin_required(view_func):
    """
    Decorator that requires admin role.
    
    Usage:
        @admin_required
        def my_view(request):
            pass
    """
    return require_roles('admin')(view_func)


def editor_required(view_func):
    """
    Decorator that requires editor role or higher.
    
    Usage:
        @editor_required
        def my_view(request):
            pass
    """
    return require_roles('admin', 'editor')(view_func)


def writer_required(view_func):
    """
    Decorator that requires writer role or higher.
    
    Usage:
        @writer_required
        def my_view(request):
            pass
    """
    return require_roles('admin', 'editor', 'writer')(view_func)


def reader_required(view_func):
    """
    Decorator that requires reader role or higher.
    
    Usage:
        @reader_required
        def my_view(request):
            pass
    """
    return require_roles('admin', 'editor', 'writer', 'reader')(view_func)


# DRF Permission Classes

class IsAdminRole(permissions.BasePermission):
    """
    Permission class for admin role.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_superuser or request.user.has_role('admin'))
        )


class IsEditorRole(permissions.BasePermission):
    """
    Permission class for editor role or higher.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_superuser or request.user.has_any_role(['admin', 'editor']))
        )


class IsWriterRole(permissions.BasePermission):
    """
    Permission class for writer role or higher.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_superuser or request.user.has_any_role(['admin', 'editor', 'writer']))
        )


class IsReaderRole(permissions.BasePermission):
    """
    Permission class for reader role or higher.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_superuser or request.user.has_any_role(['admin', 'editor', 'writer', 'reader']))
        )


class IsOwnerOrHigherRole(permissions.BasePermission):
    """
    Permission class that allows access to object owners or users with higher roles.
    """
    
    def has_object_permission(self, request, view, obj):
        # Superusers always have permission
        if request.user.is_superuser:
            return True
        
        # Admins and editors have permission
        if request.user.has_any_role(['admin', 'editor']):
            return True
        
        # Check if user is the owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'author'):
            return obj.author == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False


class CanManageRoles(permissions.BasePermission):
    """
    Permission class for role management operations.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_superuser or 
             request.user.has_role_permission('can_manage_roles'))
        )


class CanAssignRoles(permissions.BasePermission):
    """
    Permission class for role assignment operations.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_superuser or 
             request.user.has_role_permission('can_assign_roles'))
        )


# Utility functions for permission checking

def check_role_hierarchy(assigner_role, target_role):
    """
    Check if assigner can assign/modify target role based on hierarchy.
    
    Role hierarchy: admin > editor > writer > reader > guest
    """
    role_hierarchy = {
        'admin': 5,
        'editor': 4,
        'writer': 3,
        'reader': 2,
        'guest': 1
    }
    
    assigner_level = role_hierarchy.get(assigner_role, 0)
    target_level = role_hierarchy.get(target_role, 0)
    
    return assigner_level > target_level


def get_manageable_roles(user):
    """
    Get list of roles that user can manage based on their role.
    """
    if user.is_superuser or user.has_role('admin'):
        return ['admin', 'editor', 'writer', 'reader', 'guest']
    elif user.has_role('editor'):
        return ['writer', 'reader', 'guest']
    else:
        return []


def get_assignable_roles(user):
    """
    Get list of roles that user can assign to others.
    """
    if user.is_superuser:
        return ['admin', 'editor', 'writer', 'reader', 'guest']
    elif user.has_role('admin'):
        return ['editor', 'writer', 'reader', 'guest']
    elif user.has_role('editor'):
        return ['writer', 'reader', 'guest']
    else:
        return []


def can_user_access_resource(user, resource, action='view'):
    """
    Check if user can access a resource based on their roles and permissions.
    
    Args:
        user: User instance
        resource: Resource name (e.g., 'posts', 'users', 'roles')
        action: Action type ('view', 'create', 'update', 'delete')
    
    Returns:
        bool: True if user can access resource
    """
    if user.is_superuser:
        return True
    
    # Define resource access rules
    access_rules = {
        'posts': {
            'view': ['admin', 'editor', 'writer', 'reader'],
            'create': ['admin', 'editor', 'writer'],
            'update': ['admin', 'editor', 'writer'],
            'delete': ['admin', 'editor']
        },
        'users': {
            'view': ['admin', 'editor'],
            'create': ['admin'],
            'update': ['admin', 'editor'],
            'delete': ['admin']
        },
        'roles': {
            'view': ['admin', 'editor'],
            'create': ['admin'],
            'update': ['admin'],
            'delete': ['admin']
        }
    }
    
    required_roles = access_rules.get(resource, {}).get(action, [])
    return user.has_any_role(required_roles)