"""
Enhanced middleware for security, CORS handling, and comprehensive logging.
"""

import logging
import time
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from .logging import get_structured_logger, log_security_event

logger = logging.getLogger(__name__)
security_logger = get_structured_logger('security')
performance_logger = get_structured_logger('performance')


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
    Enhanced middleware for comprehensive request logging and monitoring.
    """
    
    def process_request(self, request):
        """
        Log incoming requests for security and performance monitoring.
        """
        # Store request start time for performance monitoring
        request._start_time = time.time()
        
        # Get client information
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        remote_addr = self.get_client_ip(request)
        
        # Log authentication attempts
        if request.path.startswith('/api/auth/'):
            user = getattr(request, 'user', None)
            
            security_logger.log_security_event(
                event_type='authentication_attempt',
                severity='low',
                user=user if user and not isinstance(user, AnonymousUser) else None,
                ip_address=remote_addr,
                details={
                    'path': request.path,
                    'method': request.method,
                    'user_agent': user_agent[:200]
                }
            )
        
        # Log potentially suspicious requests
        suspicious_patterns = [
            'script', 'union', 'select', 'drop', 'delete', 'insert', 'update',
            'exec', 'eval', '<script', 'javascript:', 'vbscript:', 'onload=',
            'onerror=', 'onclick=', '../', '..\\', 'etc/passwd', 'cmd.exe'
        ]
        
        request_data = str(request.GET) + str(getattr(request, 'POST', ''))
        suspicious_found = [pattern for pattern in suspicious_patterns 
                          if pattern in request_data.lower()]
        
        if suspicious_found:
            security_logger.log_security_event(
                event_type='suspicious_request',
                severity='high',
                user=getattr(request, 'user', None) if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser) else None,
                ip_address=remote_addr,
                details={
                    'path': request.path,
                    'method': request.method,
                    'patterns_found': suspicious_found,
                    'request_data': request_data[:500],
                    'user_agent': user_agent[:200]
                }
            )
        
        # Log admin access attempts
        if request.path.startswith('/admin/'):
            security_logger.log_security_event(
                event_type='admin_access_attempt',
                severity='medium',
                user=getattr(request, 'user', None) if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser) else None,
                ip_address=remote_addr,
                details={
                    'path': request.path,
                    'method': request.method,
                    'user_agent': user_agent[:200]
                }
            )
        
        # Log API access patterns
        if request.path.startswith('/api/'):
            # Track API usage for rate limiting and monitoring
            request._api_request = True
        
        return None
    
    def process_response(self, request, response):
        """
        Log response information and performance metrics.
        """
        # Calculate request duration
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            
            # Log slow requests
            if duration > 2.0:  # Requests taking more than 2 seconds
                performance_logger.log_performance_metric(
                    operation=f"{request.method} {request.path}",
                    duration=duration,
                    details={
                        'status_code': response.status_code,
                        'user': getattr(request, 'user', None) if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser) else None,
                        'ip_address': self.get_client_ip(request)
                    }
                )
            
            # Log failed requests
            if response.status_code >= 400:
                severity = 'high' if response.status_code >= 500 else 'medium'
                security_logger.log_security_event(
                    event_type='request_failure',
                    severity=severity,
                    user=getattr(request, 'user', None) if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser) else None,
                    ip_address=self.get_client_ip(request),
                    details={
                        'path': request.path,
                        'method': request.method,
                        'status_code': response.status_code,
                        'duration': duration
                    }
                )
        
        return response
    
    def get_client_ip(self, request):
        """
        Get the client IP address from the request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CSRFFailureLoggingMiddleware(MiddlewareMixin):
    """
    Enhanced middleware to log CSRF failures for security monitoring.
    """
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Log CSRF token validation failures.
        """
        # This will be called before the view is executed
        return None
    
    def process_exception(self, request, exception):
        """
        Log CSRF-related exceptions with enhanced details.
        """
        if 'CSRF' in str(exception):
            remote_addr = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            security_logger.log_security_event(
                event_type='csrf_failure',
                severity='high',
                user=getattr(request, 'user', None) if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser) else None,
                ip_address=remote_addr,
                details={
                    'path': request.path,
                    'method': request.method,
                    'exception': str(exception),
                    'user_agent': user_agent[:200],
                    'referer': request.META.get('HTTP_REFERER', '')
                }
            )
        return None
    
    def get_client_ip(self, request):
        """
        Get the client IP address from the request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip