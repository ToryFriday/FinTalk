"""
System monitoring utilities for tracking platform usage and performance.
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from django.conf import settings
from django.db import connection
from django.core.cache import cache
from django.contrib.auth.models import User
from django.utils import timezone
from .logging import get_structured_logger

logger = get_structured_logger('performance')


class SystemMonitor:
    """
    System monitoring class for collecting and analyzing platform metrics.
    """
    
    def __init__(self):
        self.cache_prefix = 'monitor:'
        self.cache_timeout = 300  # 5 minutes
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Get overall system health metrics.
        """
        cache_key = f"{self.cache_prefix}system_health"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        health_data = {
            'timestamp': timezone.now().isoformat(),
            'database': self._check_database_health(),
            'cache': self._check_cache_health(),
            'disk_space': self._check_disk_space(),
            'memory_usage': self._get_memory_usage(),
            'active_users': self._get_active_users_count(),
            'error_rate': self._get_error_rate(),
            'response_time': self._get_average_response_time(),
            'status': 'healthy'  # Will be updated based on checks
        }
        
        # Determine overall health status
        health_data['status'] = self._determine_health_status(health_data)
        
        cache.set(cache_key, health_data, self.cache_timeout)
        return health_data
    
    def get_user_activity_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get user activity metrics for the specified time period.
        """
        cache_key = f"{self.cache_prefix}user_activity_{hours}h"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        since = timezone.now() - timedelta(hours=hours)
        
        activity_data = {
            'timestamp': timezone.now().isoformat(),
            'period_hours': hours,
            'new_registrations': self._get_new_registrations(since),
            'active_users': self._get_active_users(since),
            'login_attempts': self._get_login_attempts(since),
            'failed_logins': self._get_failed_logins(since),
            'posts_created': self._get_posts_created(since),
            'comments_posted': self._get_comments_posted(since),
            'user_follows': self._get_user_follows(since),
            'email_notifications': self._get_email_notifications(since)
        }
        
        cache.set(cache_key, activity_data, self.cache_timeout)
        return activity_data
    
    def get_content_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get content-related metrics.
        """
        cache_key = f"{self.cache_prefix}content_metrics_{hours}h"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        since = timezone.now() - timedelta(hours=hours)
        
        content_data = {
            'timestamp': timezone.now().isoformat(),
            'period_hours': hours,
            'total_posts': self._get_total_posts(),
            'published_posts': self._get_published_posts(),
            'draft_posts': self._get_draft_posts(),
            'scheduled_posts': self._get_scheduled_posts(),
            'flagged_content': self._get_flagged_content(since),
            'moderation_actions': self._get_moderation_actions(since),
            'popular_posts': self._get_popular_posts(hours),
            'top_authors': self._get_top_authors(hours)
        }
        
        cache.set(cache_key, content_data, self.cache_timeout)
        return content_data
    
    def get_security_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get security-related metrics.
        """
        cache_key = f"{self.cache_prefix}security_metrics_{hours}h"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        security_data = {
            'timestamp': timezone.now().isoformat(),
            'period_hours': hours,
            'suspicious_requests': self._count_log_events('suspicious_request', hours),
            'csrf_failures': self._count_log_events('csrf_failure', hours),
            'admin_access_attempts': self._count_log_events('admin_access_attempt', hours),
            'authentication_failures': self._count_log_events('authentication_failure', hours),
            'blocked_ips': self._get_blocked_ips(hours),
            'security_alerts': self._get_security_alerts(hours)
        }
        
        cache.set(cache_key, security_data, self.cache_timeout)
        return security_data
    
    def get_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get performance-related metrics.
        """
        cache_key = f"{self.cache_prefix}performance_metrics_{hours}h"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        performance_data = {
            'timestamp': timezone.now().isoformat(),
            'period_hours': hours,
            'average_response_time': self._get_average_response_time(hours),
            'slow_requests': self._count_log_events('slow_request', hours),
            'error_rate': self._get_error_rate(hours),
            'database_queries': self._get_database_query_stats(hours),
            'cache_hit_rate': self._get_cache_hit_rate(),
            'celery_tasks': self._get_celery_task_stats(hours)
        }
        
        cache.set(cache_key, performance_data, self.cache_timeout)
        return performance_data
    
    def _check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            start_time = time.time()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            response_time = time.time() - start_time
            
            return {
                'status': 'healthy',
                'response_time': response_time,
                'connections': len(connection.queries)
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'response_time': None
            }
    
    def _check_cache_health(self) -> Dict[str, Any]:
        """Check cache connectivity and performance."""
        try:
            start_time = time.time()
            test_key = 'health_check_test'
            cache.set(test_key, 'test_value', 10)
            result = cache.get(test_key)
            cache.delete(test_key)
            response_time = time.time() - start_time
            
            return {
                'status': 'healthy' if result == 'test_value' else 'unhealthy',
                'response_time': response_time
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'response_time': None
            }
    
    def _check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space."""
        try:
            statvfs = os.statvfs(settings.BASE_DIR)
            total_space = statvfs.f_frsize * statvfs.f_blocks
            free_space = statvfs.f_frsize * statvfs.f_available
            used_space = total_space - free_space
            usage_percent = (used_space / total_space) * 100
            
            return {
                'total_gb': round(total_space / (1024**3), 2),
                'free_gb': round(free_space / (1024**3), 2),
                'used_gb': round(used_space / (1024**3), 2),
                'usage_percent': round(usage_percent, 2),
                'status': 'healthy' if usage_percent < 90 else 'warning'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage information."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            return {
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'usage_percent': memory.percent,
                'status': 'healthy' if memory.percent < 85 else 'warning'
            }
        except ImportError:
            return {
                'status': 'unavailable',
                'error': 'psutil not installed'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _get_active_users_count(self) -> int:
        """Get count of active users in the last hour."""
        try:
            from django.contrib.sessions.models import Session
            active_sessions = Session.objects.filter(
                expire_date__gte=timezone.now()
            ).count()
            return active_sessions
        except Exception:
            return 0
    
    def _get_error_rate(self, hours: int = 1) -> float:
        """Get error rate from logs."""
        try:
            total_requests = self._count_log_events('request', hours)
            error_requests = self._count_log_events('request_failure', hours)
            
            if total_requests == 0:
                return 0.0
            
            return round((error_requests / total_requests) * 100, 2)
        except Exception:
            return 0.0
    
    def _get_average_response_time(self, hours: int = 1) -> float:
        """Get average response time from performance logs."""
        # This would require parsing performance logs
        # For now, return a placeholder
        return 0.5  
  
    def _get_new_registrations(self, since: datetime) -> int:
        """Get count of new user registrations since given time."""
        try:
            return User.objects.filter(date_joined__gte=since).count()
        except Exception:
            return 0
    
    def _get_active_users(self, since: datetime) -> int:
        """Get count of active users since given time."""
        try:
            return User.objects.filter(last_login__gte=since).count()
        except Exception:
            return 0
    
    def _get_login_attempts(self, since: datetime) -> int:
        """Get count of login attempts from logs."""
        return self._count_log_events('authentication_login', since)
    
    def _get_failed_logins(self, since: datetime) -> int:
        """Get count of failed login attempts from logs."""
        return self._count_log_events('authentication_failure', since)
    
    def _get_posts_created(self, since: datetime) -> int:
        """Get count of posts created since given time."""
        try:
            from posts.models import Post
            return Post.objects.filter(created_at__gte=since).count()
        except Exception:
            return 0
    
    def _get_comments_posted(self, since: datetime) -> int:
        """Get count of comments posted (placeholder for Disqus integration)."""
        # This would integrate with Disqus API or local comment tracking
        return 0
    
    def _get_user_follows(self, since: datetime) -> int:
        """Get count of user follows since given time."""
        try:
            from accounts.models import UserFollow
            return UserFollow.objects.filter(created_at__gte=since).count()
        except Exception:
            return 0
    
    def _get_email_notifications(self, since: datetime) -> int:
        """Get count of email notifications sent."""
        return self._count_log_events('email_sent', since)
    
    def _get_total_posts(self) -> int:
        """Get total number of posts."""
        try:
            from posts.models import Post
            return Post.objects.count()
        except Exception:
            return 0
    
    def _get_published_posts(self) -> int:
        """Get count of published posts."""
        try:
            from posts.models import Post
            return Post.objects.filter(status='published').count()
        except Exception:
            return 0
    
    def _get_draft_posts(self) -> int:
        """Get count of draft posts."""
        try:
            from posts.models import Post
            return Post.objects.filter(status='draft').count()
        except Exception:
            return 0
    
    def _get_scheduled_posts(self) -> int:
        """Get count of scheduled posts."""
        try:
            from posts.models import Post
            return Post.objects.filter(status='scheduled').count()
        except Exception:
            return 0
    
    def _get_flagged_content(self, since: datetime) -> int:
        """Get count of flagged content since given time."""
        try:
            from moderation.models import ContentFlag
            return ContentFlag.objects.filter(created_at__gte=since).count()
        except Exception:
            return 0
    
    def _get_moderation_actions(self, since: datetime) -> int:
        """Get count of moderation actions since given time."""
        try:
            from moderation.models import ContentFlag
            return ContentFlag.objects.filter(
                reviewed_at__gte=since,
                status__in=['resolved', 'dismissed']
            ).count()
        except Exception:
            return 0
    
    def _get_popular_posts(self, hours: int) -> List[Dict[str, Any]]:
        """Get popular posts based on view count."""
        try:
            from posts.models import Post
            posts = Post.objects.filter(
                status='published'
            ).order_by('-view_count')[:10]
            
            return [
                {
                    'id': post.id,
                    'title': post.title,
                    'view_count': getattr(post, 'view_count', 0),
                    'author': post.author,
                    'created_at': post.created_at.isoformat()
                }
                for post in posts
            ]
        except Exception:
            return []
    
    def _get_top_authors(self, hours: int) -> List[Dict[str, Any]]:
        """Get top authors by post count."""
        try:
            from posts.models import Post
            from django.db.models import Count
            
            since = timezone.now() - timedelta(hours=hours)
            authors = User.objects.filter(
                post__created_at__gte=since
            ).annotate(
                post_count=Count('post')
            ).order_by('-post_count')[:10]
            
            return [
                {
                    'id': author.id,
                    'username': author.username,
                    'post_count': author.post_count,
                    'email': author.email
                }
                for author in authors
            ]
        except Exception:
            return []
    
    def _get_blocked_ips(self, hours: int) -> List[str]:
        """Get list of blocked IP addresses."""
        # This would integrate with security middleware or firewall logs
        return []
    
    def _get_security_alerts(self, hours: int) -> int:
        """Get count of security alerts."""
        return self._count_log_events('security_alert', hours)
    
    def _get_database_query_stats(self, hours: int) -> Dict[str, Any]:
        """Get database query statistics."""
        try:
            # This would require parsing Django debug logs or using database monitoring
            return {
                'total_queries': 0,
                'slow_queries': 0,
                'average_duration': 0.0
            }
        except Exception:
            return {
                'total_queries': 0,
                'slow_queries': 0,
                'average_duration': 0.0
            }
    
    def _get_cache_hit_rate(self) -> float:
        """Get cache hit rate."""
        try:
            # This would require Redis monitoring or cache statistics
            return 85.0  # Placeholder
        except Exception:
            return 0.0
    
    def _get_celery_task_stats(self, hours: int) -> Dict[str, Any]:
        """Get Celery task statistics."""
        return {
            'total_tasks': self._count_log_events('celery_task_started', hours),
            'successful_tasks': self._count_log_events('celery_task_success', hours),
            'failed_tasks': self._count_log_events('celery_task_failure', hours),
            'retry_tasks': self._count_log_events('celery_task_retry', hours)
        }
    
    def _determine_health_status(self, health_data: Dict[str, Any]) -> str:
        """Determine overall system health status."""
        issues = []
        
        # Check database health
        if health_data['database']['status'] != 'healthy':
            issues.append('database')
        
        # Check cache health
        if health_data['cache']['status'] != 'healthy':
            issues.append('cache')
        
        # Check disk space
        if health_data['disk_space'].get('usage_percent', 0) > 90:
            issues.append('disk_space')
        
        # Check memory usage
        if health_data['memory_usage'].get('usage_percent', 0) > 90:
            issues.append('memory')
        
        # Check error rate
        if health_data['error_rate'] > 5.0:  # More than 5% error rate
            issues.append('high_error_rate')
        
        if not issues:
            return 'healthy'
        elif len(issues) == 1:
            return 'warning'
        else:
            return 'critical'
    
    def _count_log_events(self, event_type: str, hours_or_since) -> int:
        """Count specific events in logs for the given time period."""
        try:
            import os
            import json
            from datetime import datetime
            
            if isinstance(hours_or_since, int):
                since = timezone.now() - timedelta(hours=hours_or_since)
            else:
                since = hours_or_since
            
            count = 0
            log_files = [
                'authentication.log',
                'social.log',
                'moderation.log',
                'email.log',
                'celery.log',
                'performance.log',
                'security.log'
            ]
            
            logs_dir = settings.BASE_DIR / 'logs'
            
            for log_file in log_files:
                log_path = logs_dir / log_file
                if log_path.exists():
                    try:
                        with open(log_path, 'r') as f:
                            for line in f:
                                try:
                                    log_entry = json.loads(line.strip())
                                    log_time = datetime.fromisoformat(
                                        log_entry.get('timestamp', '').replace('Z', '+00:00')
                                    )
                                    
                                    if log_time >= since:
                                        # Check if this log entry matches the event type
                                        if self._matches_event_type(log_entry, event_type):
                                            count += 1
                                except (json.JSONDecodeError, ValueError, KeyError):
                                    continue
                    except Exception:
                        continue
            
            return count
        except Exception:
            return 0
    
    def _matches_event_type(self, log_entry: Dict[str, Any], event_type: str) -> bool:
        """Check if a log entry matches the specified event type."""
        extra = log_entry.get('extra', {})
        message = log_entry.get('message', '').lower()
        
        event_patterns = {
            'authentication_login': lambda e, m: e.get('event_type') == 'login' or 'login' in m,
            'authentication_failure': lambda e, m: e.get('event_type') == 'login' and not e.get('success', True),
            'email_sent': lambda e, m: e.get('event_type') == 'sent' or 'email sent' in m,
            'celery_task_started': lambda e, m: e.get('status') == 'started' or 'task started' in m,
            'celery_task_success': lambda e, m: e.get('status') == 'success' or 'task success' in m,
            'celery_task_failure': lambda e, m: e.get('status') == 'failure' or 'task failure' in m,
            'celery_task_retry': lambda e, m: e.get('status') == 'retry' or 'task retry' in m,
            'security_alert': lambda e, m: e.get('event_type', '').startswith('security') or 'security' in m,
            'suspicious_request': lambda e, m: 'suspicious' in m or e.get('severity') in ['high', 'critical'],
            'csrf_failure': lambda e, m: 'csrf' in m.lower(),
            'admin_access_attempt': lambda e, m: 'admin' in m and 'access' in m,
            'slow_request': lambda e, m: e.get('duration', 0) > 2.0 or 'slow' in m,
            'request_failure': lambda e, m: log_entry.get('level') == 'ERROR' and 'request' in m,
            'request': lambda e, m: 'request' in m or e.get('operation', '').startswith('request')
        }
        
        pattern_func = event_patterns.get(event_type)
        if pattern_func:
            return pattern_func(extra, message)
        
        return False


class MetricsCollector:
    """
    Collects and aggregates metrics for monitoring dashboard.
    """
    
    def __init__(self):
        self.monitor = SystemMonitor()
        self.cache_prefix = 'metrics:'
        self.cache_timeout = 60  # 1 minute
    
    def collect_all_metrics(self) -> Dict[str, Any]:
        """Collect all system metrics."""
        cache_key = f"{self.cache_prefix}all_metrics"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        metrics = {
            'timestamp': timezone.now().isoformat(),
            'system_health': self.monitor.get_system_health(),
            'user_activity': self.monitor.get_user_activity_metrics(24),
            'content_metrics': self.monitor.get_content_metrics(24),
            'security_metrics': self.monitor.get_security_metrics(24),
            'performance_metrics': self.monitor.get_performance_metrics(24)
        }
        
        cache.set(cache_key, metrics, self.cache_timeout)
        return metrics
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get formatted data for monitoring dashboard."""
        metrics = self.collect_all_metrics()
        
        return {
            'overview': {
                'status': metrics['system_health']['status'],
                'active_users': metrics['system_health']['active_users'],
                'error_rate': metrics['system_health']['error_rate'],
                'response_time': metrics['system_health']['response_time']
            },
            'system': {
                'database': metrics['system_health']['database'],
                'cache': metrics['system_health']['cache'],
                'disk_space': metrics['system_health']['disk_space'],
                'memory_usage': metrics['system_health']['memory_usage']
            },
            'activity': {
                'new_users': metrics['user_activity']['new_registrations'],
                'active_users': metrics['user_activity']['active_users'],
                'posts_created': metrics['user_activity']['posts_created'],
                'email_notifications': metrics['user_activity']['email_notifications']
            },
            'content': {
                'total_posts': metrics['content_metrics']['total_posts'],
                'published_posts': metrics['content_metrics']['published_posts'],
                'draft_posts': metrics['content_metrics']['draft_posts'],
                'flagged_content': metrics['content_metrics']['flagged_content']
            },
            'security': {
                'failed_logins': metrics['security_metrics']['authentication_failures'],
                'suspicious_requests': metrics['security_metrics']['suspicious_requests'],
                'security_alerts': metrics['security_metrics']['security_alerts']
            },
            'performance': {
                'average_response_time': metrics['performance_metrics']['average_response_time'],
                'slow_requests': metrics['performance_metrics']['slow_requests'],
                'error_rate': metrics['performance_metrics']['error_rate'],
                'cache_hit_rate': metrics['performance_metrics']['cache_hit_rate']
            }
        }


# Convenience functions
def get_system_monitor() -> SystemMonitor:
    """Get a system monitor instance."""
    return SystemMonitor()


def get_metrics_collector() -> MetricsCollector:
    """Get a metrics collector instance."""
    return MetricsCollector()


def collect_metrics() -> Dict[str, Any]:
    """Convenience function to collect all metrics."""
    collector = get_metrics_collector()
    return collector.collect_all_metrics()