"""
Celery tasks for monitoring and system maintenance.
"""

import json
import os
from datetime import datetime, timedelta
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.core.mail import mail_admins
from django.core.cache import cache

from .monitoring import get_system_monitor, get_metrics_collector
from .logging import get_structured_logger

logger = get_structured_logger('celery')


@shared_task(bind=True, max_retries=3)
def collect_system_metrics(self):
    """
    Periodic task to collect and store system metrics.
    """
    try:
        logger.log_celery_task(
            task_name='collect_system_metrics',
            task_id=str(self.request.id),
            status='started'
        )
        
        collector = get_metrics_collector()
        metrics = collector.collect_all_metrics()
        
        # Store metrics in cache with timestamp
        cache_key = f"metrics:{timezone.now().strftime('%Y%m%d_%H%M')}"
        cache.set(cache_key, metrics, timeout=86400)  # Store for 24 hours
        
        # Store metrics to file for historical analysis
        metrics_dir = settings.BASE_DIR / 'logs' / 'metrics'
        metrics_dir.mkdir(exist_ok=True)
        
        filename = f"metrics_{timezone.now().strftime('%Y%m%d_%H%M')}.json"
        filepath = metrics_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(metrics, f, indent=2, default=str)
        
        logger.log_celery_task(
            task_name='collect_system_metrics',
            task_id=str(self.request.id),
            status='success',
            duration=0,  # Will be calculated by monitoring
            result={'metrics_stored': True, 'file': str(filepath)}
        )
        
        return {'status': 'success', 'metrics_file': str(filepath)}
        
    except Exception as exc:
        logger.log_celery_task(
            task_name='collect_system_metrics',
            task_id=str(self.request.id),
            status='failure',
            error_message=str(exc)
        )
        
        # Retry the task
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=2)
def check_system_alerts(self):
    """
    Periodic task to check for system alerts and notify administrators.
    """
    try:
        logger.log_celery_task(
            task_name='check_system_alerts',
            task_id=str(self.request.id),
            status='started'
        )
        
        monitor = get_system_monitor()
        health = monitor.get_system_health()
        
        alerts = []
        
        # Check system status
        if health['status'] == 'critical':
            alerts.append({
                'type': 'critical',
                'title': 'System Health Critical',
                'message': 'Multiple system components are experiencing issues',
                'details': health
            })
        
        # Check disk space
        disk_usage = health.get('disk_space', {}).get('usage_percent', 0)
        if disk_usage > 90:
            alerts.append({
                'type': 'critical',
                'title': 'Critical Disk Space',
                'message': f'Disk usage is at {disk_usage}%'
            })
        
        # Check memory usage
        memory_usage = health.get('memory_usage', {}).get('usage_percent', 0)
        if memory_usage > 90:
            alerts.append({
                'type': 'critical',
                'title': 'Critical Memory Usage',
                'message': f'Memory usage is at {memory_usage}%'
            })
        
        # Check error rate
        error_rate = health.get('error_rate', 0)
        if error_rate > 10:
            alerts.append({
                'type': 'critical',
                'title': 'High Error Rate',
                'message': f'Error rate is at {error_rate}%'
            })
        
        # Send alerts to administrators
        if alerts:
            critical_alerts = [a for a in alerts if a['type'] == 'critical']
            if critical_alerts:
                subject = f'FinTalk Critical System Alert - {len(critical_alerts)} issues'
                message = 'Critical system issues detected:\n\n'
                
                for alert in critical_alerts:
                    message += f"• {alert['title']}: {alert['message']}\n"
                
                message += f"\nTimestamp: {timezone.now()}\n"
                message += "Please check the monitoring dashboard for more details."
                
                try:
                    mail_admins(subject, message, fail_silently=False)
                    logger.log_email_event(
                        event_type='sent',
                        recipient='administrators',
                        success=True,
                        subject=subject
                    )
                except Exception as e:
                    logger.log_email_event(
                        event_type='failed',
                        recipient='administrators',
                        success=False,
                        subject=subject,
                        details={'error': str(e)}
                    )
        
        logger.log_celery_task(
            task_name='check_system_alerts',
            task_id=str(self.request.id),
            status='success',
            result={'alerts_found': len(alerts), 'critical_alerts': len([a for a in alerts if a['type'] == 'critical'])}
        )
        
        return {'status': 'success', 'alerts': len(alerts)}
        
    except Exception as exc:
        logger.log_celery_task(
            task_name='check_system_alerts',
            task_id=str(self.request.id),
            status='failure',
            error_message=str(exc)
        )
        
        raise self.retry(exc=exc, countdown=300)  # Retry after 5 minutes


@shared_task(bind=True)
def cleanup_old_logs(self, days_to_keep=30):
    """
    Task to clean up old log files and metrics.
    """
    try:
        logger.log_celery_task(
            task_name='cleanup_old_logs',
            task_id=str(self.request.id),
            status='started'
        )
        
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        logs_dir = settings.BASE_DIR / 'logs'
        metrics_dir = logs_dir / 'metrics'
        
        cleaned_files = 0
        
        # Clean up old metric files
        if metrics_dir.exists():
            for file_path in metrics_dir.glob('metrics_*.json'):
                try:
                    # Extract date from filename
                    filename = file_path.name
                    date_str = filename.replace('metrics_', '').replace('.json', '')[:8]
                    file_date = datetime.strptime(date_str, '%Y%m%d')
                    
                    if file_date.replace(tzinfo=timezone.utc) < cutoff_date:
                        file_path.unlink()
                        cleaned_files += 1
                        
                except (ValueError, OSError):
                    continue
        
        # Clean up old cache entries
        cache_keys_pattern = 'metrics:*'
        # Note: This would require Redis-specific commands for pattern deletion
        # For now, we'll rely on TTL expiration
        
        logger.log_celery_task(
            task_name='cleanup_old_logs',
            task_id=str(self.request.id),
            status='success',
            result={'files_cleaned': cleaned_files}
        )
        
        return {'status': 'success', 'files_cleaned': cleaned_files}
        
    except Exception as exc:
        logger.log_celery_task(
            task_name='cleanup_old_logs',
            task_id=str(self.request.id),
            status='failure',
            error_message=str(exc)
        )
        
        return {'status': 'error', 'error': str(exc)}


@shared_task(bind=True)
def generate_daily_report(self):
    """
    Generate daily system report and send to administrators.
    """
    try:
        logger.log_celery_task(
            task_name='generate_daily_report',
            task_id=str(self.request.id),
            status='started'
        )
        
        monitor = get_system_monitor()
        
        # Collect 24-hour metrics
        health = monitor.get_system_health()
        activity = monitor.get_user_activity_metrics(24)
        content = monitor.get_content_metrics(24)
        security = monitor.get_security_metrics(24)
        performance = monitor.get_performance_metrics(24)
        
        # Generate report
        report_date = timezone.now().strftime('%Y-%m-%d')
        subject = f'FinTalk Daily System Report - {report_date}'
        
        message = f"""
FinTalk Daily System Report
Date: {report_date}

SYSTEM HEALTH
=============
Overall Status: {health.get('status', 'unknown').upper()}
Active Users: {health.get('active_users', 0)}
Error Rate: {health.get('error_rate', 0)}%
Response Time: {health.get('response_time', 0):.3f}s

Database: {health.get('database', {}).get('status', 'unknown')}
Cache: {health.get('cache', {}).get('status', 'unknown')}
Disk Usage: {health.get('disk_space', {}).get('usage_percent', 0)}%
Memory Usage: {health.get('memory_usage', {}).get('usage_percent', 0)}%

USER ACTIVITY (Last 24 Hours)
=============================
New Registrations: {activity.get('new_registrations', 0)}
Active Users: {activity.get('active_users', 0)}
Login Attempts: {activity.get('login_attempts', 0)}
Failed Logins: {activity.get('failed_logins', 0)}
Posts Created: {activity.get('posts_created', 0)}
User Follows: {activity.get('user_follows', 0)}
Email Notifications: {activity.get('email_notifications', 0)}

CONTENT METRICS
===============
Total Posts: {content.get('total_posts', 0)}
Published Posts: {content.get('published_posts', 0)}
Draft Posts: {content.get('draft_posts', 0)}
Scheduled Posts: {content.get('scheduled_posts', 0)}
Flagged Content: {content.get('flagged_content', 0)}
Moderation Actions: {content.get('moderation_actions', 0)}

SECURITY METRICS (Last 24 Hours)
================================
Authentication Failures: {security.get('authentication_failures', 0)}
Suspicious Requests: {security.get('suspicious_requests', 0)}
CSRF Failures: {security.get('csrf_failures', 0)}
Admin Access Attempts: {security.get('admin_access_attempts', 0)}
Security Alerts: {security.get('security_alerts', 0)}

PERFORMANCE METRICS (Last 24 Hours)
===================================
Average Response Time: {performance.get('average_response_time', 0):.3f}s
Slow Requests: {performance.get('slow_requests', 0)}
Error Rate: {performance.get('error_rate', 0)}%
Cache Hit Rate: {performance.get('cache_hit_rate', 0)}%

Celery Tasks:
- Total: {performance.get('celery_tasks', {}).get('total_tasks', 0)}
- Successful: {performance.get('celery_tasks', {}).get('successful_tasks', 0)}
- Failed: {performance.get('celery_tasks', {}).get('failed_tasks', 0)}

Generated at: {timezone.now()}
"""
        
        try:
            mail_admins(subject, message, fail_silently=False)
            logger.log_email_event(
                event_type='sent',
                recipient='administrators',
                success=True,
                subject=subject
            )
        except Exception as e:
            logger.log_email_event(
                event_type='failed',
                recipient='administrators',
                success=False,
                subject=subject,
                details={'error': str(e)}
            )
        
        logger.log_celery_task(
            task_name='generate_daily_report',
            task_id=str(self.request.id),
            status='success',
            result={'report_sent': True}
        )
        
        return {'status': 'success', 'report_sent': True}
        
    except Exception as exc:
        logger.log_celery_task(
            task_name='generate_daily_report',
            task_id=str(self.request.id),
            status='failure',
            error_message=str(exc)
        )
        
        return {'status': 'error', 'error': str(exc)}


@shared_task(bind=True)
def analyze_performance_trends(self):
    """
    Analyze performance trends and identify potential issues.
    """
    try:
        logger.log_celery_task(
            task_name='analyze_performance_trends',
            task_id=str(self.request.id),
            status='started'
        )
        
        # Load recent metrics files for trend analysis
        metrics_dir = settings.BASE_DIR / 'logs' / 'metrics'
        recent_metrics = []
        
        if metrics_dir.exists():
            # Get metrics from last 7 days
            for i in range(7):
                date = timezone.now() - timedelta(days=i)
                pattern = f"metrics_{date.strftime('%Y%m%d')}_*.json"
                
                for file_path in metrics_dir.glob(pattern):
                    try:
                        with open(file_path, 'r') as f:
                            metrics = json.load(f)
                            recent_metrics.append(metrics)
                    except (json.JSONDecodeError, OSError):
                        continue
        
        # Analyze trends
        trends = {
            'response_time_trend': 'stable',
            'error_rate_trend': 'stable',
            'memory_usage_trend': 'stable',
            'disk_usage_trend': 'stable',
            'recommendations': []
        }
        
        if len(recent_metrics) >= 2:
            # Simple trend analysis (could be enhanced with more sophisticated algorithms)
            latest = recent_metrics[0]
            previous = recent_metrics[-1]
            
            # Response time trend
            latest_rt = latest.get('performance_metrics', {}).get('average_response_time', 0)
            previous_rt = previous.get('performance_metrics', {}).get('average_response_time', 0)
            
            if latest_rt > previous_rt * 1.2:
                trends['response_time_trend'] = 'increasing'
                trends['recommendations'].append('Response times are increasing. Consider optimizing database queries.')
            elif latest_rt < previous_rt * 0.8:
                trends['response_time_trend'] = 'decreasing'
            
            # Memory usage trend
            latest_mem = latest.get('system_health', {}).get('memory_usage', {}).get('usage_percent', 0)
            previous_mem = previous.get('system_health', {}).get('memory_usage', {}).get('usage_percent', 0)
            
            if latest_mem > previous_mem + 10:
                trends['memory_usage_trend'] = 'increasing'
                trends['recommendations'].append('Memory usage is increasing. Monitor for memory leaks.')
        
        logger.log_celery_task(
            task_name='analyze_performance_trends',
            task_id=str(self.request.id),
            status='success',
            result=trends
        )
        
        return {'status': 'success', 'trends': trends}
        
    except Exception as exc:
        logger.log_celery_task(
            task_name='analyze_performance_trends',
            task_id=str(self.request.id),
            status='failure',
            error_message=str(exc)
        )
        
        return {'status': 'error', 'error': str(exc)}