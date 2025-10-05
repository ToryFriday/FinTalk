"""
Custom exception handlers for Django REST Framework.
Provides consistent error responses and comprehensive logging.
"""
import logging
import traceback
from typing import Optional, Dict, Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from django.db import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework.exceptions import (
    ValidationError as DRFValidationError,
    NotFound,
    PermissionDenied,
    AuthenticationFailed,
    NotAuthenticated,
    MethodNotAllowed,
    NotAcceptable,
    UnsupportedMediaType,
    Throttled,
    ParseError,
)

from .exceptions import PostNotFoundError, ValidationError, ServiceError

logger = logging.getLogger(__name__)


def custom_exception_handler(exc: Exception, context: Dict[str, Any]) -> Optional[Response]:
    """
    Custom exception handler that provides consistent error responses
    and comprehensive logging for all API errors.
    
    Args:
        exc: The exception that was raised
        context: Context information about the request
        
    Returns:
        Response object with error details or None to use default handler
    """
    # Get the request object from context
    request = context.get('request')
    view = context.get('view')
    
    # Log the exception with context
    _log_exception(exc, request, view)
    
    # Handle custom application exceptions
    if isinstance(exc, PostNotFoundError):
        return _handle_post_not_found_error(exc, request)
    elif isinstance(exc, ValidationError):
        return _handle_validation_error(exc, request)
    elif isinstance(exc, ServiceError):
        return _handle_service_error(exc, request)
    
    # Handle Django exceptions
    elif isinstance(exc, DjangoValidationError):
        return _handle_django_validation_error(exc, request)
    elif isinstance(exc, IntegrityError):
        return _handle_integrity_error(exc, request)
    elif isinstance(exc, Http404):
        return _handle_http_404_error(exc, request)
    
    # Handle DRF exceptions with custom formatting
    elif isinstance(exc, (DRFValidationError, NotFound, PermissionDenied, 
                         AuthenticationFailed, NotAuthenticated, MethodNotAllowed, NotAcceptable,
                         UnsupportedMediaType, Throttled, ParseError)):
        return _handle_drf_exception(exc, request)
    
    # Handle unexpected exceptions
    else:
        return _handle_unexpected_exception(exc, request, context)


def _log_exception(exc: Exception, request, view) -> None:
    """
    Log exception details with request context.
    """
    try:
        # Extract request information
        method = getattr(request, 'method', 'UNKNOWN') if request else 'UNKNOWN'
        path = getattr(request, 'path', 'UNKNOWN') if request else 'UNKNOWN'
        user = getattr(request, 'user', 'Anonymous') if request else 'Anonymous'
        view_name = getattr(view, '__class__.__name__', 'UnknownView') if view else 'UnknownView'
        
        # Log based on exception type
        if isinstance(exc, (PostNotFoundError, Http404, NotFound)):
            logger.warning(
                f"Resource not found - {exc.__class__.__name__}: {str(exc)} | "
                f"Request: {method} {path} | User: {user} | View: {view_name}"
            )
        elif isinstance(exc, (ValidationError, DjangoValidationError, DRFValidationError)):
            logger.warning(
                f"Validation error - {exc.__class__.__name__}: {str(exc)} | "
                f"Request: {method} {path} | User: {user} | View: {view_name}"
            )
        elif isinstance(exc, ServiceError):
            logger.error(
                f"Service error - {exc.__class__.__name__}: {str(exc)} | "
                f"Request: {method} {path} | User: {user} | View: {view_name}"
            )
        else:
            logger.error(
                f"Unexpected error - {exc.__class__.__name__}: {str(exc)} | "
                f"Request: {method} {path} | User: {user} | View: {view_name} | "
                f"Traceback: {traceback.format_exc()}"
            )
    except Exception as log_exc:
        # Fallback logging if context extraction fails
        logger.error(f"Failed to log exception context: {str(log_exc)}")
        logger.error(f"Original exception: {exc.__class__.__name__}: {str(exc)}")


def _handle_post_not_found_error(exc: PostNotFoundError, request) -> Response:
    """Handle PostNotFoundError exceptions."""
    return Response(
        {
            'error': True,
            'error_type': 'resource_not_found',
            'message': 'The requested post was not found',
            'detail': str(exc),
            'post_id': getattr(exc, 'post_id', None),
            'timestamp': _get_timestamp(),
        },
        status=status.HTTP_404_NOT_FOUND
    )


def _handle_validation_error(exc: ValidationError, request) -> Response:
    """Handle custom ValidationError exceptions."""
    return Response(
        {
            'error': True,
            'error_type': 'validation_error',
            'message': 'Data validation failed',
            'detail': str(exc),
            'field_errors': getattr(exc, 'errors', {}),
            'timestamp': _get_timestamp(),
        },
        status=status.HTTP_400_BAD_REQUEST
    )


def _handle_service_error(exc: ServiceError, request) -> Response:
    """Handle ServiceError exceptions."""
    return Response(
        {
            'error': True,
            'error_type': 'service_error',
            'message': 'A service error occurred',
            'detail': str(exc),
            'timestamp': _get_timestamp(),
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


def _handle_django_validation_error(exc: DjangoValidationError, request) -> Response:
    """Handle Django ValidationError exceptions."""
    if hasattr(exc, 'message_dict'):
        field_errors = exc.message_dict
        detail = 'Multiple field validation errors'
    elif hasattr(exc, 'messages'):
        field_errors = {'non_field_errors': exc.messages}
        detail = '; '.join(exc.messages)
    else:
        field_errors = {'non_field_errors': [str(exc)]}
        detail = str(exc)
    
    return Response(
        {
            'error': True,
            'error_type': 'validation_error',
            'message': 'Data validation failed',
            'detail': detail,
            'field_errors': field_errors,
            'timestamp': _get_timestamp(),
        },
        status=status.HTTP_400_BAD_REQUEST
    )


def _handle_integrity_error(exc: IntegrityError, request) -> Response:
    """Handle database IntegrityError exceptions."""
    return Response(
        {
            'error': True,
            'error_type': 'database_error',
            'message': 'Database constraint violation',
            'detail': 'The operation violates database constraints',
            'timestamp': _get_timestamp(),
        },
        status=status.HTTP_400_BAD_REQUEST
    )


def _handle_http_404_error(exc: Http404, request) -> Response:
    """Handle Django Http404 exceptions."""
    return Response(
        {
            'error': True,
            'error_type': 'resource_not_found',
            'message': 'The requested resource was not found',
            'detail': str(exc),
            'timestamp': _get_timestamp(),
        },
        status=status.HTTP_404_NOT_FOUND
    )


def _handle_drf_exception(exc, request) -> Response:
    """Handle Django REST Framework exceptions with custom formatting."""
    # Get the default DRF response
    response = exception_handler(exc, {'request': request})
    
    if response is not None:
        # For authentication/permission errors, return them as-is with proper status codes
        # Don't convert them to 500 errors
        from rest_framework.exceptions import NotAuthenticated
        if isinstance(exc, (AuthenticationFailed, NotAuthenticated, PermissionDenied)):
            # Keep the original status code (401, 403) instead of converting to 500
            custom_response_data = {
                'error': True,
                'error_type': 'authentication_required' if isinstance(exc, (AuthenticationFailed, NotAuthenticated)) else 'permission_denied',
                'message': 'Authentication required' if isinstance(exc, (AuthenticationFailed, NotAuthenticated)) else 'Permission denied',
                'detail': str(exc),
                'timestamp': _get_timestamp(),
                'hint': 'Please login to perform this action' if isinstance(exc, (AuthenticationFailed, NotAuthenticated)) else 'You do not have permission to perform this action'
            }
            response.data = custom_response_data
            return response
        
        # Determine error type based on exception class
        error_type_map = {
            DRFValidationError: 'validation_error',
            NotFound: 'resource_not_found',
            PermissionDenied: 'permission_denied',
            AuthenticationFailed: 'authentication_failed',
            MethodNotAllowed: 'method_not_allowed',
            NotAcceptable: 'not_acceptable',
            UnsupportedMediaType: 'unsupported_media_type',
            Throttled: 'throttled',
            ParseError: 'parse_error',
        }
        
        error_type = error_type_map.get(type(exc), 'api_error')
        
        # Create custom response format
        custom_response_data = {
            'error': True,
            'error_type': error_type,
            'message': _get_error_message(exc),
            'detail': response.data,
            'timestamp': _get_timestamp(),
        }
        
        # Add specific fields for certain error types
        if isinstance(exc, Throttled):
            custom_response_data['retry_after'] = getattr(exc, 'wait', None)
        elif isinstance(exc, MethodNotAllowed):
            custom_response_data['allowed_methods'] = getattr(exc, 'allowed_methods', [])
        
        response.data = custom_response_data
    
    return response


def _handle_unexpected_exception(exc: Exception, request, context: Dict[str, Any]) -> Response:
    """Handle unexpected exceptions that aren't specifically handled."""
    # Log the full traceback for debugging
    logger.error(f"Unexpected exception: {traceback.format_exc()}")
    
    return Response(
        {
            'error': True,
            'error_type': 'internal_server_error',
            'message': 'An unexpected error occurred',
            'detail': 'Please contact support if this problem persists',
            'timestamp': _get_timestamp(),
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


def _get_error_message(exc) -> str:
    """Extract appropriate error message from exception."""
    if hasattr(exc, 'default_detail'):
        return str(exc.default_detail)
    elif hasattr(exc, 'detail'):
        detail = exc.detail
        if isinstance(detail, dict):
            # For validation errors, create a summary message
            return 'Validation failed for one or more fields'
        elif isinstance(detail, list):
            return '; '.join(str(item) for item in detail)
        else:
            return str(detail)
    else:
        return str(exc)


def _get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    from datetime import datetime
    return datetime.now().isoformat()