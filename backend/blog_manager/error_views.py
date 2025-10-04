"""
Custom error views for handling HTTP errors.
Provides consistent error pages and logging for 404 and 500 errors.
"""
import logging
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import requires_csrf_token
from django.views.decorators.cache import never_cache

logger = logging.getLogger(__name__)


@never_cache
def handler404(request: HttpRequest, exception=None) -> HttpResponse:
    """
    Custom 404 error handler.
    
    Args:
        request: The HTTP request object
        exception: The exception that caused the 404 (optional)
        
    Returns:
        HttpResponse with 404 status and custom error page
    """
    # Log the 404 error with request details
    logger.warning(
        f"404 Error - Path: {request.path} | "
        f"Method: {request.method} | "
        f"User: {getattr(request.user, 'username', 'Anonymous')} | "
        f"IP: {_get_client_ip(request)} | "
        f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')} | "
        f"Referer: {request.META.get('HTTP_REFERER', 'None')}"
    )
    
    # Prepare context for the template
    context = {
        'request_path': request.path,
        'request_method': request.method,
        'exception': str(exception) if exception else None,
    }
    
    # Render the custom 404 template
    response = render(request, '404.html', context)
    response.status_code = 404
    return response


@never_cache
@requires_csrf_token
def handler500(request: HttpRequest) -> HttpResponse:
    """
    Custom 500 error handler.
    
    Args:
        request: The HTTP request object
        
    Returns:
        HttpResponse with 500 status and custom error page
    """
    # Log the 500 error with request details
    logger.error(
        f"500 Error - Path: {request.path} | "
        f"Method: {request.method} | "
        f"User: {getattr(request.user, 'username', 'Anonymous')} | "
        f"IP: {_get_client_ip(request)} | "
        f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')} | "
        f"Referer: {request.META.get('HTTP_REFERER', 'None')}"
    )
    
    # Prepare context for the template
    context = {
        'request_path': request.path,
        'request_method': request.method,
    }
    
    try:
        # Render the custom 500 template
        response = render(request, '500.html', context)
        response.status_code = 500
        return response
    except Exception as e:
        # Fallback in case template rendering fails
        logger.error(f"Failed to render 500 template: {str(e)}")
        return HttpResponse(
            '<h1>Internal Server Error</h1>'
            '<p>We are experiencing technical difficulties. Please try again later.</p>',
            status=500,
            content_type='text/html'
        )


def _get_client_ip(request: HttpRequest) -> str:
    """
    Extract client IP address from request.
    
    Args:
        request: The HTTP request object
        
    Returns:
        str: Client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'Unknown')
    return ip