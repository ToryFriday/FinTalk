"""
Celery configuration for blog_manager project.
"""

import os
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure, task_retry
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog_manager.settings.development')

app = Celery('blog_manager')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Enhanced Celery logging and monitoring
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Log task start."""
    try:
        from common.logging import get_structured_logger
        logger = get_structured_logger('celery')
        logger.log_celery_task(
            task_name=task.name if task else sender,
            task_id=task_id,
            status='started',
            details={'args': str(args), 'kwargs': str(kwargs)}
        )
    except Exception:
        pass  # Don't let logging errors break task execution


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, 
                        retval=None, state=None, **kwds):
    """Log task completion."""
    try:
        from common.logging import get_structured_logger
        import time
        
        logger = get_structured_logger('celery')
        
        # Calculate duration if available
        duration = None
        if hasattr(task, '_start_time'):
            duration = time.time() - task._start_time
        
        logger.log_celery_task(
            task_name=task.name if task else sender,
            task_id=task_id,
            status='success' if state == 'SUCCESS' else state.lower(),
            duration=duration,
            result=str(retval) if retval else None,
            details={'state': state}
        )
    except Exception:
        pass  # Don't let logging errors break task execution


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds):
    """Log task failure."""
    try:
        from common.logging import get_structured_logger
        logger = get_structured_logger('celery')
        logger.log_celery_task(
            task_name=sender.name if sender else 'unknown',
            task_id=task_id,
            status='failure',
            error_message=str(exception),
            details={'traceback': str(traceback) if traceback else None}
        )
    except Exception:
        pass  # Don't let logging errors break task execution


@task_retry.connect
def task_retry_handler(sender=None, task_id=None, reason=None, einfo=None, **kwds):
    """Log task retry."""
    try:
        from common.logging import get_structured_logger
        logger = get_structured_logger('celery')
        logger.log_celery_task(
            task_name=sender.name if sender else 'unknown',
            task_id=task_id,
            status='retry',
            error_message=str(reason),
            details={'retry_info': str(einfo) if einfo else None}
        )
    except Exception:
        pass  # Don't let logging errors break task execution

# Celery beat schedule for periodic tasks
app.conf.beat_schedule = {
    'publish-scheduled-posts': {
        'task': 'posts.tasks.publish_scheduled_posts',
        'schedule': 60.0,  # Run every minute
    },
    'cleanup-expired-tokens': {
        'task': 'accounts.tasks.cleanup_expired_tokens',
        'schedule': 3600.0,  # Run every hour
    },
    'send-weekly-digest': {
        'task': 'notifications.tasks.send_weekly_digest',
        'schedule': 604800.0,  # Run weekly (7 days * 24 hours * 60 minutes * 60 seconds)
    },
    'cleanup-old-notification-logs': {
        'task': 'notifications.tasks.cleanup_old_notification_logs',
        'schedule': 86400.0,  # Run daily
    },
    # Monitoring and system maintenance tasks
    'collect-system-metrics': {
        'task': 'common.tasks.collect_system_metrics',
        'schedule': 300.0,  # Run every 5 minutes
    },
    'check-system-alerts': {
        'task': 'common.tasks.check_system_alerts',
        'schedule': 600.0,  # Run every 10 minutes
    },
    'generate-daily-report': {
        'task': 'common.tasks.generate_daily_report',
        'schedule': 86400.0,  # Run daily at midnight
    },
    'cleanup-old-logs': {
        'task': 'common.tasks.cleanup_old_logs',
        'schedule': 86400.0,  # Run daily
    },
    'analyze-performance-trends': {
        'task': 'common.tasks.analyze_performance_trends',
        'schedule': 21600.0,  # Run every 6 hours
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')