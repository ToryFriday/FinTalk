"""
Management command to collect and display system metrics.
"""

import json
from django.core.management.base import BaseCommand
from django.utils import timezone
from common.monitoring import get_metrics_collector, get_system_monitor


class Command(BaseCommand):
    help = 'Collect and display system metrics'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'table'],
            default='table',
            help='Output format (json or table)'
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Time period in hours for metrics collection'
        )
        parser.add_argument(
            '--section',
            type=str,
            choices=['health', 'activity', 'content', 'security', 'performance', 'all'],
            default='all',
            help='Specific section to display'
        )
        parser.add_argument(
            '--output-file',
            type=str,
            help='Output file path (optional)'
        )
    
    def handle(self, *args, **options):
        """Handle the command execution."""
        try:
            collector = get_metrics_collector()
            monitor = get_system_monitor()
            
            # Collect metrics based on section
            if options['section'] == 'health':
                data = monitor.get_system_health()
            elif options['section'] == 'activity':
                data = monitor.get_user_activity_metrics(options['hours'])
            elif options['section'] == 'content':
                data = monitor.get_content_metrics(options['hours'])
            elif options['section'] == 'security':
                data = monitor.get_security_metrics(options['hours'])
            elif options['section'] == 'performance':
                data = monitor.get_performance_metrics(options['hours'])
            else:  # all
                data = collector.collect_all_metrics()
            
            # Format output
            if options['format'] == 'json':
                output = json.dumps(data, indent=2, default=str)
            else:
                output = self._format_table(data, options['section'])
            
            # Output to file or console
            if options['output_file']:
                with open(options['output_file'], 'w') as f:
                    f.write(output)
                self.stdout.write(
                    self.style.SUCCESS(f'Metrics saved to {options["output_file"]}')
                )
            else:
                self.stdout.write(output)
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error collecting metrics: {str(e)}')
            )
    
    def _format_table(self, data, section):
        """Format data as a readable table."""
        output = []
        output.append("=" * 80)
        output.append(f"FINTALK SYSTEM METRICS - {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("=" * 80)
        
        if section == 'health' or section == 'all':
            if 'system_health' in data:
                health = data['system_health']
            else:
                health = data
            
            output.append("\n📊 SYSTEM HEALTH")
            output.append("-" * 40)
            output.append(f"Overall Status: {health.get('status', 'unknown').upper()}")
            output.append(f"Active Users: {health.get('active_users', 0)}")
            output.append(f"Error Rate: {health.get('error_rate', 0)}%")
            output.append(f"Response Time: {health.get('response_time', 0):.3f}s")
            
            # Database
            db = health.get('database', {})
            output.append(f"\nDatabase: {db.get('status', 'unknown')}")
            if db.get('response_time'):
                output.append(f"  Response Time: {db['response_time']:.3f}s")
            
            # Cache
            cache = health.get('cache', {})
            output.append(f"Cache: {cache.get('status', 'unknown')}")
            if cache.get('response_time'):
                output.append(f"  Response Time: {cache['response_time']:.3f}s")
            
            # Disk Space
            disk = health.get('disk_space', {})
            if disk.get('usage_percent'):
                output.append(f"Disk Usage: {disk['usage_percent']}% ({disk.get('used_gb', 0):.1f}GB used)")
            
            # Memory
            memory = health.get('memory_usage', {})
            if memory.get('usage_percent'):
                output.append(f"Memory Usage: {memory['usage_percent']}% ({memory.get('used_gb', 0):.1f}GB used)")
        
        if section == 'activity' or section == 'all':
            if 'user_activity' in data:
                activity = data['user_activity']
            else:
                activity = data
            
            output.append(f"\n👥 USER ACTIVITY (Last {activity.get('period_hours', 24)} hours)")
            output.append("-" * 40)
            output.append(f"New Registrations: {activity.get('new_registrations', 0)}")
            output.append(f"Active Users: {activity.get('active_users', 0)}")
            output.append(f"Login Attempts: {activity.get('login_attempts', 0)}")
            output.append(f"Failed Logins: {activity.get('failed_logins', 0)}")
            output.append(f"Posts Created: {activity.get('posts_created', 0)}")
            output.append(f"User Follows: {activity.get('user_follows', 0)}")
            output.append(f"Email Notifications: {activity.get('email_notifications', 0)}")
        
        if section == 'content' or section == 'all':
            if 'content_metrics' in data:
                content = data['content_metrics']
            else:
                content = data
            
            output.append(f"\n📝 CONTENT METRICS")
            output.append("-" * 40)
            output.append(f"Total Posts: {content.get('total_posts', 0)}")
            output.append(f"Published Posts: {content.get('published_posts', 0)}")
            output.append(f"Draft Posts: {content.get('draft_posts', 0)}")
            output.append(f"Scheduled Posts: {content.get('scheduled_posts', 0)}")
            output.append(f"Flagged Content: {content.get('flagged_content', 0)}")
            output.append(f"Moderation Actions: {content.get('moderation_actions', 0)}")
        
        if section == 'security' or section == 'all':
            if 'security_metrics' in data:
                security = data['security_metrics']
            else:
                security = data
            
            output.append(f"\n🔒 SECURITY METRICS (Last {security.get('period_hours', 24)} hours)")
            output.append("-" * 40)
            output.append(f"Authentication Failures: {security.get('authentication_failures', 0)}")
            output.append(f"Suspicious Requests: {security.get('suspicious_requests', 0)}")
            output.append(f"CSRF Failures: {security.get('csrf_failures', 0)}")
            output.append(f"Admin Access Attempts: {security.get('admin_access_attempts', 0)}")
            output.append(f"Security Alerts: {security.get('security_alerts', 0)}")
        
        if section == 'performance' or section == 'all':
            if 'performance_metrics' in data:
                performance = data['performance_metrics']
            else:
                performance = data
            
            output.append(f"\n⚡ PERFORMANCE METRICS (Last {performance.get('period_hours', 24)} hours)")
            output.append("-" * 40)
            output.append(f"Average Response Time: {performance.get('average_response_time', 0):.3f}s")
            output.append(f"Slow Requests: {performance.get('slow_requests', 0)}")
            output.append(f"Error Rate: {performance.get('error_rate', 0)}%")
            output.append(f"Cache Hit Rate: {performance.get('cache_hit_rate', 0)}%")
            
            celery = performance.get('celery_tasks', {})
            output.append(f"Celery Tasks - Total: {celery.get('total_tasks', 0)}, "
                         f"Success: {celery.get('successful_tasks', 0)}, "
                         f"Failed: {celery.get('failed_tasks', 0)}")
        
        output.append("\n" + "=" * 80)
        return "\n".join(output)