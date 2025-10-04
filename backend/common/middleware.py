"""
Custom middleware for additional security and CORS handling.
"""

import logging
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add additional security headers to responses.
    """
    
    def process_response(self, request, response):
        """
        Add security headers to the response.
        """
        # Add additional security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add CORS headers for preflight requests
        if request.method == 'OPTIONS':
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRFToken'
            response['Access-Control-Max-Age'] = '86400'  # 24 hours
        
        # Log security-related requests
        if hasattr(request, 'META'):
            origin = request.META.get('HTTP_ORIGIN')
            if origin:
                logger.info(f"Cross-origin request from: {origin} to {request.path}")
        
        return response


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log requests for security monitoring.
    """
    
    def process_request(self, request):
        """
        Log incoming requests for security monitoring.
        """
        # Log potentially suspicious requests
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        remote_addr = self.get_client_ip(request)
        
        # Log requests with suspicious patterns
        suspicious_patterns = [
            'script',
            'union',
            'select',
            'drop',
            'delete',
            'insert',
            'update',
            'exec',
            'eval',
        ]
        
        request_data = str(request.GET) + str(getattr(request, 'POST', ''))
        if any(pattern in request_data.lower() for pattern in suspicious_patterns):
            logger.warning(
                f"Suspicious request detected - IP: {remote_addr}, "
                f"Path: {request.path}, Data: {request_data[:200]}"
            )
        
        return None
    
    def get_client_ip(self, request):
        """
        Get the client IP address from the request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CSRFFailureLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log CSRF failures for security monitoring.
    """
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Log CSRF token validation failures.
        """
        # This will be called before the view is executed
        return None
    
    def process_exception(self, request, exception):
        """
        Log CSRF-related exceptions.
        """
        if 'CSRF' in str(exception):
            remote_addr = self.get_client_ip(request)
            logger.warning(
                f"CSRF failure - IP: {remote_addr}, "
                f"Path: {request.path}, Exception: {str(exception)}"
            )
        return None
    
    def get_client_ip(self, request):
        """
        Get the client IP address from the request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip