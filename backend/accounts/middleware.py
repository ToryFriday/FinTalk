"""
Middleware for role-based access control (RBAC).
"""

import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class RoleBasedAccessMiddleware(MiddlewareMixin):
    """
    Middleware to enforce role-based access control on specific URL patterns.
    """
    
    # Define URL patterns and required roles
    PROTECTED_URLS = {
        # Admin-only URLs
        'admin:': ['admin'],
        'accounts:role-': ['admin', 'editor'],
        'accounts:user-role': ['admin', 'editor'],
        'accounts:role-assignment': ['admin', 'editor'],
        
        # Editor and above URLs
        'posts:moderate': ['admin', 'editor'],
        'posts:flag': ['admin', 'editor'],
        
        # Writer and above URLs
        'posts:create': ['admin', 'editor', 'writer'],
        'posts:update': ['admin', 'editor', 'writer'],
        'posts:draft': ['admin', 'editor', 'writer'],
        'posts:schedule': ['admin', 'editor', 'writer'],
    }
    
    def process_request(self, request):
        """
        Process request and check role-based permissions.
        """
        # Skip for non-authenticated users on public endpoints
        if not request.user.is_authenticated:
            return None
        
        # Skip for superusers
        if request.user.is_superuser:
            return None
        
        try:
            # Resolve URL name
            resolved = resolve(request.path_info)
            url_name = resolved.url_name
            namespace = resolved.namespace
            
            if namespace:
                full_url_name = f"{namespace}:{url_name}"
            else:
                full_url_name = url_name
            
            # Check if URL requires specific roles
            required_roles = self._get_required_roles(full_url_name)
            
            if required_roles:
                if not request.user.has_any_role(required_roles):
                    logger.warning(
                        f"Access denied for user {request.user.username} "
                        f"to {full_url_name}. Required roles: {required_roles}"
                    )
                    
                    return JsonResponse({
                        'error': 'Insufficient permissions to access this resource.',
                        'required_roles': required_roles,
                        'user_roles': [role.name for role in request.user.get_user_roles()]
                    }, status=403)
        
        except Exception as e:
            logger.error(f"Error in RoleBasedAccessMiddleware: {str(e)}")
        
        return None
    
    def _get_required_roles(self, url_name):
        """
        Get required roles for a URL pattern.
        """
        for pattern, roles in self.PROTECTED_URLS.items():
            if url_name.startswith(pattern):
                return roles
        return None


class UserRoleContextMiddleware(MiddlewareMixin):
    """
    Middleware to add user role context to requests.
    """
    
    def process_request(self, request):
        """
        Add user role information to request context.
        """
        if request.user.is_authenticated:
            # Add role information to request
            request.user_roles = request.user.get_user_roles()
            request.user_permissions = request.user.get_role_permissions()
            request.highest_role = request.user.get_highest_role()
            
            # Add convenience methods
            request.is_admin = request.user.has_role('admin')
            request.is_editor = request.user.has_role('editor')
            request.is_writer = request.user.has_role('writer')
            request.is_reader = request.user.has_role('reader')
        else:
            # Set default values for anonymous users
            request.user_roles = []
            request.user_permissions = []
            request.highest_role = 'guest'
            request.is_admin = False
            request.is_editor = False
            request.is_writer = False
            request.is_reader = False
        
        return None


class RoleAuditMiddleware(MiddlewareMixin):
    """
    Middleware to audit role-based actions and access attempts.
    """
    
    # Actions to audit
    AUDIT_ACTIONS = [
        'POST',  # Create operations
        'PUT',   # Update operations
        'PATCH', # Partial update operations
        'DELETE' # Delete operations
    ]
    
    # URLs to audit
    AUDIT_URLS = [
        'accounts/roles/',
        'accounts/user-roles/',
        'accounts/role-assignment/',
        'posts/moderate/',
        'posts/flag/',
    ]
    
    def process_response(self, request, response):
        """
        Audit role-based actions after response.
        """
        # Only audit specific methods and URLs
        if (request.method in self.AUDIT_ACTIONS and 
            any(url in request.path_info for url in self.AUDIT_URLS)):
            
            self._log_action(request, response)
        
        return response
    
    def _log_action(self, request, response):
        """
        Log role-based action with context.
        """
        try:
            user = request.user if request.user.is_authenticated else None
            
            audit_data = {
                'user': user.username if user else 'anonymous',
                'user_id': user.id if user else None,
                'user_roles': [role.name for role in user.get_user_roles()] if user else [],
                'method': request.method,
                'path': request.path_info,
                'status_code': response.status_code,
                'ip_address': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }
            
            # Log successful actions
            if 200 <= response.status_code < 300:
                logger.info(f"Role-based action successful: {audit_data}")
            
            # Log failed actions
            elif response.status_code >= 400:
                logger.warning(f"Role-based action failed: {audit_data}")
        
        except Exception as e:
            logger.error(f"Error in RoleAuditMiddleware: {str(e)}")
    
    def _get_client_ip(self, request):
        """
        Get client IP address from request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RoleSessionMiddleware(MiddlewareMixin):
    """
    Middleware to manage role-based session data.
    """
    
    def process_request(self, request):
        """
        Add role information to session.
        """
        if request.user.is_authenticated:
            # Store role information in session for quick access
            user_roles = [role.name for role in request.user.get_user_roles()]
            highest_role = request.user.get_highest_role()
            
            # Update session if roles have changed
            if (request.session.get('user_roles') != user_roles or
                request.session.get('highest_role') != highest_role):
                
                request.session['user_roles'] = user_roles
                request.session['highest_role'] = highest_role
                request.session['role_updated_at'] = str(timezone.now())
                
                logger.info(f"Updated session roles for user {request.user.username}: {user_roles}")
        
        return None


class RoleRateLimitMiddleware(MiddlewareMixin):
    """
    Middleware to apply different rate limits based on user roles.
    """
    
    # Rate limits per role (requests per minute)
    ROLE_RATE_LIMITS = {
        'admin': 1000,
        'editor': 500,
        'writer': 200,
        'reader': 100,
        'guest': 50
    }
    
    def process_request(self, request):
        """
        Apply role-based rate limiting.
        """
        # This is a simplified implementation
        # In production, you would use a proper rate limiting solution like django-ratelimit
        
        if request.user.is_authenticated:
            highest_role = request.user.get_highest_role()
            rate_limit = self.ROLE_RATE_LIMITS.get(highest_role, 50)
            
            # Add rate limit info to request for use by other middleware/views
            request.role_rate_limit = rate_limit
        else:
            request.role_rate_limit = self.ROLE_RATE_LIMITS['guest']
        
        return None


# Utility functions for middleware

def get_user_role_context(user):
    """
    Get comprehensive role context for a user.
    """
    if not user.is_authenticated:
        return {
            'roles': [],
            'permissions': [],
            'highest_role': 'guest',
            'is_admin': False,
            'is_editor': False,
            'is_writer': False,
            'is_reader': False
        }
    
    return {
        'roles': [role.name for role in user.get_user_roles()],
        'permissions': [perm.codename for perm in user.get_role_permissions()],
        'highest_role': user.get_highest_role(),
        'is_admin': user.has_role('admin'),
        'is_editor': user.has_role('editor'),
        'is_writer': user.has_role('writer'),
        'is_reader': user.has_role('reader')
    }


def check_url_access(user, url_name, method='GET'):
    """
    Check if user can access a specific URL based on their roles.
    """
    # Define access rules
    access_rules = {
        'GET': {
            'accounts:role-list': ['admin', 'editor'],
            'accounts:user-role-list': ['admin', 'editor'],
            'posts:moderate-list': ['admin', 'editor'],
        },
        'POST': {
            'accounts:role-create': ['admin'],
            'accounts:role-assignment': ['admin', 'editor'],
            'posts:create': ['admin', 'editor', 'writer'],
        },
        'PUT': {
            'accounts:role-update': ['admin'],
            'posts:update': ['admin', 'editor', 'writer'],
        },
        'DELETE': {
            'accounts:role-delete': ['admin'],
            'posts:delete': ['admin', 'editor'],
        }
    }
    
    required_roles = access_rules.get(method, {}).get(url_name, [])
    
    if not required_roles:
        return True  # No restrictions
    
    if user.is_superuser:
        return True
    
    return user.has_any_role(required_roles)