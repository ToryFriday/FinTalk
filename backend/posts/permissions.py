"""
Custom permissions for posts app with role-based access control.
"""

from rest_framework import permissions
from accounts.permissions import IsOwnerOrHigherRole


class PostPermission(permissions.BasePermission):
    """
    Custom permission class for post operations based on user roles and post status.
    
    Rules:
    - Anyone can view published posts
    - Only authenticated users can view drafts they own
    - Admins and editors can view all posts
    - Writers can create posts (as drafts)
    - Only post authors, editors, and admins can update posts
    - Only editors and admins can delete posts
    - Only editors and admins can publish posts
    - Only editors and admins can schedule posts
    """
    
    def has_permission(self, request, view):
        """
        Check if user has permission to access the view.
        """
        # Allow read access to published posts for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Require authentication for write operations
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Allow writers and above to create posts
        if request.method == 'POST':
            return (
                request.user.is_superuser or 
                request.user.has_any_role(['admin', 'editor', 'writer'])
            )
        
        return True
    
    def has_object_permission(self, request, view, obj):
        """
        Check object-level permissions for specific post operations.
        """
        user = request.user
        
        # Superusers always have permission
        if user.is_superuser:
            return True
        
        # Read permissions
        if request.method in permissions.SAFE_METHODS:
            # Published posts are visible to everyone
            if obj.status == 'published':
                return True
            
            # Draft and scheduled posts are only visible to:
            # - The author (if author_user is set)
            # - Admins and editors
            if obj.status in ['draft', 'scheduled']:
                if not user.is_authenticated:
                    return False
                
                # Check if user is the author
                if obj.author_user and obj.author_user == user:
                    return True
                
                # Check if user has admin or editor role
                return user.has_any_role(['admin', 'editor'])
            
            return False
        
        # Write permissions
        if not user.is_authenticated:
            return False
        
        # Admins and editors can do anything
        if user.has_any_role(['admin', 'editor']):
            return True
        
        # Writers can only update their own posts
        if request.method in ['PUT', 'PATCH']:
            # Check if user is the author
            if obj.author_user and obj.author_user == user:
                return True
        
        # Delete permissions - only admins and editors
        if request.method == 'DELETE':
            return user.has_any_role(['admin', 'editor'])
        
        return False


class CanPublishPost(permissions.BasePermission):
    """
    Permission to publish posts - only editors and admins.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_superuser or 
             request.user.has_any_role(['admin', 'editor']))
        )


class CanSchedulePost(permissions.BasePermission):
    """
    Permission to schedule posts - only editors and admins.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_superuser or 
             request.user.has_any_role(['admin', 'editor']))
        )


class CanModeratePost(permissions.BasePermission):
    """
    Permission to moderate posts - only editors and admins.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_superuser or 
             request.user.has_any_role(['admin', 'editor']) or
             request.user.has_role_permission('can_moderate_posts'))
        )


class CanViewDrafts(permissions.BasePermission):
    """
    Permission to view draft posts - authors, editors, and admins.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated
        )
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        if user.is_superuser:
            return True
        
        # Admins and editors can view all drafts
        if user.has_any_role(['admin', 'editor']):
            return True
        
        # Authors can view their own drafts
        if obj.author_user and obj.author_user == user:
            return True
        
        # Check permission
        return user.has_role_permission('can_view_drafts')


def can_user_modify_post_status(user, post, new_status):
    """
    Check if user can change post status to new_status.
    
    Args:
        user: User instance
        post: Post instance
        new_status: New status to set
    
    Returns:
        bool: True if user can change status
    """
    if user.is_superuser:
        return True
    
    # Admins and editors can change any status
    if user.has_any_role(['admin', 'editor']):
        return True
    
    # Writers can only change their own posts
    if post.author_user and post.author_user == user:
        # Writers can only set to draft or request publication
        if new_status in ['draft']:
            return True
        # Writers cannot directly publish or schedule
        if new_status in ['published', 'scheduled']:
            return False
    
    return False


def can_user_delete_post(user, post):
    """
    Check if user can delete a post.
    
    Args:
        user: User instance
        post: Post instance
    
    Returns:
        bool: True if user can delete post
    """
    if user.is_superuser:
        return True
    
    # Only admins and editors can delete posts
    return user.has_any_role(['admin', 'editor'])


def can_user_view_post(user, post):
    """
    Check if user can view a post based on its status.
    
    Args:
        user: User instance (can be None for anonymous users)
        post: Post instance
    
    Returns:
        bool: True if user can view post
    """
    # Published posts are visible to everyone
    if post.status == 'published':
        return True
    
    # Draft and scheduled posts require authentication
    if not user or not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    # Admins and editors can view all posts
    if user.has_any_role(['admin', 'editor']):
        return True
    
    # Authors can view their own posts
    if post.author_user and post.author_user == user:
        return True
    
    # Check specific permission
    return user.has_role_permission('can_view_drafts')