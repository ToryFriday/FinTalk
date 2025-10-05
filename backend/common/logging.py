"""
Enhanced logging utilities for comprehensive monitoring and debugging.
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from django.utils import timezone
# from django.contrib.auth.models import AnonymousUser  # Removed to avoid circular import


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    Converts log records to JSON format for better parsing and analysis.
    """
    
    def format(self, record):
        """
        Format the log record as JSON.
        """
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
            'process_id': record.process,
            'thread_id': record.thread,
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields from the record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'exc_info',
                          'exc_text', 'stack_info']:
                try:
                    # Ensure the value is JSON serializable
                    json.dumps(value)
                    extra_fields[key] = value
                except (TypeError, ValueError):
                    # Convert non-serializable values to strings
                    extra_fields[key] = str(value)
        
        if extra_fields:
            log_entry['extra'] = extra_fields
        
        return json.dumps(log_entry)


class UserActionFilter(logging.Filter):
    """
    Filter for user action logs.
    """
    
    def filter(self, record):
        """Filter records that contain user action information."""
        return hasattr(record, 'user_id') or hasattr(record, 'action_type')


class PerformanceFilter(logging.Filter):
    """
    Filter for performance-related logs.
    """
    
    def filter(self, record):
        """Filter records that contain performance metrics."""
        return hasattr(record, 'duration') or hasattr(record, 'operation')


class StructuredLogger:
    """
    Enhanced logger for structured logging with context information.
    """
    
    def __init__(self, logger_name: str):
        self.logger = logging.getLogger(logger_name)
    
    def log_user_action(self, user, action_type: str, resource_type: str = None, 
                       resource_id: str = None, details: Dict[str, Any] = None,
                       level: int = logging.INFO):
        """
        Log user actions with structured data.
        """
        extra = {
            'event_type': 'user_action',
            'user_id': user.id if user and hasattr(user, 'id') else None,
            'username': user.username if user and hasattr(user, 'username') else 'anonymous',
            'action_type': action_type,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        
        message = f"User action: {action_type}"
        if resource_type:
            message += f" on {resource_type}"
        if resource_id:
            message += f" (ID: {resource_id})"
        
        self.logger.log(level, message, extra=extra)
    
    def log_authentication_event(self, user, event_type: str, success: bool = True,
                                ip_address: str = None, user_agent: str = None,
                                details: Dict[str, Any] = None):
        """
        Log authentication events with security context.
        """
        username = user.username if user and hasattr(user, 'username') else 'unknown'
        
        extra = {
            'event_type': 'authentication',
            'auth_event': event_type,
            'username': username,
            'user_id': user.id if user and hasattr(user, 'id') else None,
            'success': success,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        
        level = logging.INFO if success else logging.WARNING
        
        message = f"Authentication {event_type} {'succeeded' if success else 'failed'} for {username}"
        
        self.logger.log(level, message, extra=extra)    

    def log_performance_metric(self, operation: str, duration: float,
                              query_count: int = None, cache_hits: int = None,
                              details: Dict[str, Any] = None):
        """
        Log performance metrics for operations.
        """
        extra = {
            'event_type': 'performance',
            'operation': operation,
            'duration': duration,
            'query_count': query_count,
            'cache_hits': cache_hits,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        
        # Determine log level based on performance
        if duration > 5.0:  # Slow operation
            level = logging.WARNING
        elif duration > 2.0:  # Moderate operation
            level = logging.INFO
        else:  # Fast operation
            level = logging.DEBUG
        
        message = f"Operation '{operation}' completed in {duration:.3f}s"
        if query_count:
            message += f" with {query_count} queries"
        
        self.logger.log(level, message, extra=extra)
    
    def log_security_event(self, event_type: str, severity: str = 'medium',
                          user=None, ip_address: str = None,
                          details: Dict[str, Any] = None):
        """
        Log security-related events.
        """
        extra = {
            'event_type': 'security',
            'security_event': event_type,
            'severity': severity,
            'user_id': user.id if user and hasattr(user, 'id') else None,
            'username': user.username if user and hasattr(user, 'username') else None,
            'ip_address': ip_address,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        
        # Map severity to log level
        severity_levels = {
            'low': logging.INFO,
            'medium': logging.WARNING,
            'high': logging.ERROR,
            'critical': logging.CRITICAL
        }
        level = severity_levels.get(severity.lower(), logging.WARNING)
        
        message = f"Security event: {event_type} (severity: {severity})"
        if user:
            message += f" for user {user.username}"
        
        self.logger.log(level, message, extra=extra)
    
    def log_email_event(self, event_type: str, recipient: str, success: bool = True,
                       subject: str = None, template: str = None,
                       details: Dict[str, Any] = None):
        """
        Log email-related events.
        """
        extra = {
            'event_type': 'email',
            'email_event': event_type,
            'recipient': recipient,
            'success': success,
            'subject': subject,
            'template': template,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        
        level = logging.INFO if success else logging.ERROR
        
        message = f"Email {event_type} to {recipient}"
        if subject:
            message += f" with subject '{subject}'"
        
        self.logger.log(level, message, extra=extra)
    
    def log_celery_task(self, task_name: str, task_id: str, status: str,
                       duration: float = None, result: Any = None,
                       error_message: str = None, details: Dict[str, Any] = None):
        """
        Log Celery task events.
        """
        extra = {
            'event_type': 'celery_task',
            'task_name': task_name,
            'task_id': task_id,
            'status': status,
            'duration': duration,
            'result': str(result) if result else None,
            'error_message': error_message,
            'timestamp': timezone.now().isoformat(),
            'details': details or {}
        }
        
        # Map status to log level
        status_levels = {
            'started': logging.INFO,
            'success': logging.INFO,
            'failure': logging.ERROR,
            'retry': logging.WARNING,
        }
        level = status_levels.get(status.lower(), logging.INFO)
        
        message = f"Celery task {task_name} ({task_id}) - {status}"
        if duration:
            message += f" in {duration:.3f}s"
        if error_message:
            message += f" - Error: {error_message}"
        
        self.logger.log(level, message, extra=extra)


class PerformanceMonitor:
    """
    Context manager for monitoring performance of code blocks.
    """
    
    def __init__(self, operation_name: str, logger_name: str = 'performance'):
        self.operation_name = operation_name
        self.logger = StructuredLogger(logger_name)
        self.start_time = None
        self.query_count_start = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        details = {}
        if exc_type:
            details['exception'] = str(exc_val)
        
        self.logger.log_performance_metric(
            operation=self.operation_name,
            duration=duration,
            details=details
        )


# Convenience functions for common logging patterns
def get_structured_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)


def log_user_action(user, action: str, **kwargs):
    """Convenience function for logging user actions."""
    logger = get_structured_logger('accounts')
    logger.log_user_action(user, action, **kwargs)


def log_authentication(user, event: str, success: bool = True, **kwargs):
    """Convenience function for logging authentication events."""
    logger = get_structured_logger('accounts')
    logger.log_authentication_event(user, event, success, **kwargs)


def log_security_event(event_type: str, severity: str = 'medium', **kwargs):
    """Convenience function for logging security events."""
    logger = get_structured_logger('security')
    logger.log_security_event(event_type, severity, **kwargs)


def log_email_event(event_type: str, recipient: str, success: bool = True, **kwargs):
    """Convenience function for logging email events."""
    logger = get_structured_logger('notifications')
    logger.log_email_event(event_type, recipient, success, **kwargs)


def monitor_performance(operation_name: str, logger_name: str = 'performance'):
    """Context manager for performance monitoring."""
    return PerformanceMonitor(operation_name, logger_name)