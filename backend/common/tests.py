"""
Tests for logging and monitoring functionality.
"""

import json
import tempfile
import os
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .logging import (
    StructuredLogger, JSONFormatter, UserActionFilter, PerformanceFilter,
    get_structured_logger, log_user_action, log_authentication,
    log_security_event, log_email_event, monitor_performance
)
from .monitoring import SystemMonitor, MetricsCollector, get_system_monitor, get_metrics_collector


class JSONFormatterTest(TestCase):
    """Test JSON formatter for structured logging."""
    
    def setUp(self):
        self.formatter = JSONFormatter()
    
    def test_format_basic_record(self):
        """Test formatting a basic log record."""
        import logging
        
        record = logging.LogRecord(
            name='test_logger',
            level=logging.INFO,
            pathname='/test/path.py',
            lineno=42,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        formatted = self.formatter.format(record)
        data = json.loads(formatted)
        
        self.assertEqual(data['level'], 'INFO')
        self.assertEqual(data['logger'], 'test_logger')
        self.assertEqual(data['message'], 'Test message')
        self.assertEqual(data['line'], 42)
        self.assertIn('timestamp', data)
    
    def test_format_record_with_extra_fields(self):
        """Test formatting a log record with extra fields."""
        import logging
        
        record = logging.LogRecord(
            name='test_logger',
            level=logging.INFO,
            pathname='/test/path.py',
            lineno=42,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        # Add extra fields
        record.user_id = 123
        record.action_type = 'create'
        
        formatted = self.formatter.format(record)
        data = json.loads(formatted)
        
        self.assertIn('extra', data)
        self.assertEqual(data['extra']['user_id'], 123)
        self.assertEqual(data['extra']['action_type'], 'create')
    
    def test_format_record_with_exception(self):
        """Test formatting a log record with exception information."""
        import logging
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            record = logging.LogRecord(
                name='test_logger',
                level=logging.ERROR,
                pathname='/test/path.py',
                lineno=42,
                msg='Test error message',
                args=(),
                exc_info=True
            )
        
        formatted = self.formatter.format(record)
        data = json.loads(formatted)
        
        self.assertIn('exception', data)
        self.assertIn('ValueError: Test exception', data['exception'])
    
    def test_format_record_with_extra_fields(self):
        """Test formatting a record with extra fields."""
        import logging
        
        record = logging.LogRecord(
            name='test_logger',
            level=logging.INFO,
            pathname='/test/path.py',
            lineno=42,
            msg='Test message',
            args=(),
            exc_info=None
        )
        record.user_id = 123
        record.action_type = 'test_action'
        
        formatted = self.formatter.format(record)
        data = json.loads(formatted)
        
        self.assertIn('extra', data)
        self.assertEqual(data['extra']['user_id'], 123)
        self.assertEqual(data['extra']['action_type'], 'test_action')


class StructuredLoggerTest(TestCase):
    """Test structured logger functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.logger = StructuredLogger('test_logger')
    
    def test_log_user_action(self):
        """Test logging user actions."""
        with patch.object(self.logger.logger, 'log') as mock_log:
            self.logger.log_user_action(
                user=self.user,
                action_type='create',
                resource_type='post',
                resource_id='123',
                details={'title': 'Test Post'}
            )
            
            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            
            self.assertEqual(kwargs['extra']['user_id'], self.user.id)
            self.assertEqual(kwargs['extra']['action_type'], 'create')
            self.assertEqual(kwargs['extra']['resource_type'], 'post')
            self.assertEqual(kwargs['extra']['resource_id'], '123')
    
    def test_log_authentication_event(self):
        """Test logging authentication events."""
        with patch.object(self.logger.logger, 'log') as mock_log:
            self.logger.log_authentication_event(
                user=self.user,
                event_type='login',
                success=True,
                ip_address='192.168.1.1'
            )
            
            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            
            self.assertEqual(kwargs['extra']['username'], self.user.username)
            self.assertEqual(kwargs['extra']['event_type'], 'login')
            self.assertTrue(kwargs['extra']['success'])
            self.assertEqual(kwargs['extra']['ip_address'], '192.168.1.1')
    
    def test_log_security_event(self):
        """Test logging security events."""
        with patch.object(self.logger.logger, 'log') as mock_log:
            self.logger.log_security_event(
                event_type='suspicious_request',
                severity='high',
                user=self.user,
                ip_address='192.168.1.100'
            )
            
            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            
            self.assertEqual(kwargs['extra']['event_type'], 'suspicious_request')
            self.assertEqual(kwargs['extra']['severity'], 'high')
            self.assertEqual(kwargs['extra']['username'], self.user.username)
    
    def test_log_email_event(self):
        """Test logging email events."""
        with patch.object(self.logger.logger, 'log') as mock_log:
            self.logger.log_email_event(
                event_type='sent',
                recipient='test@example.com',
                subject='Test Email',
                success=True
            )
            
            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            
            self.assertEqual(kwargs['extra']['event_type'], 'sent')
            self.assertEqual(kwargs['extra']['recipient'], 'test@example.com')
            self.assertEqual(kwargs['extra']['subject'], 'Test Email')
            self.assertTrue(kwargs['extra']['success'])
    
    def test_log_celery_task(self):
        """Test logging Celery task events."""
        with patch.object(self.logger.logger, 'log') as mock_log:
            self.logger.log_celery_task(
                task_name='test_task',
                task_id='abc123',
                status='success',
                duration=1.5
            )
            
            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            
            self.assertEqual(kwargs['extra']['task_name'], 'test_task')
            self.assertEqual(kwargs['extra']['task_id'], 'abc123')
            self.assertEqual(kwargs['extra']['status'], 'success')
            self.assertEqual(kwargs['extra']['duration'], 1.5)


class SystemMonitorTest(TestCase):
    """Test system monitoring functionality."""
    
    def setUp(self):
        self.monitor = SystemMonitor()
        cache.clear()  # Clear cache before each test
    
    def test_check_database_health(self):
        """Test database health check."""
        health = self.monitor._check_database_health()
        
        self.assertIn('status', health)
        self.assertIn('response_time', health)
        self.assertEqual(health['status'], 'healthy')
        self.assertIsInstance(health['response_time'], float)
    
    def test_check_cache_health(self):
        """Test cache health check."""
        health = self.monitor._check_cache_health()
        
        self.assertIn('status', health)
        self.assertIn('response_time', health)
        self.assertEqual(health['status'], 'healthy')
        self.assertIsInstance(health['response_time'], float)
    
    @patch('os.statvfs')
    def test_check_disk_space(self, mock_statvfs):
        """Test disk space check."""
        # Mock disk space data
        mock_stat = MagicMock()
        mock_stat.f_frsize = 4096
        mock_stat.f_blocks = 1000000
        mock_stat.f_available = 500000
        mock_statvfs.return_value = mock_stat
        
        disk_info = self.monitor._check_disk_space()
        
        self.assertIn('status', disk_info)
        self.assertIn('usage_percent', disk_info)
        self.assertIn('total_gb', disk_info)
        self.assertEqual(disk_info['status'], 'healthy')
    
    def test_get_new_registrations(self):
        """Test getting new user registrations."""
        from datetime import timedelta
        from django.utils import timezone
        
        # Create test users
        User.objects.create_user('user1', 'user1@test.com', 'pass')
        User.objects.create_user('user2', 'user2@test.com', 'pass')
        
        since = timezone.now() - timedelta(hours=1)
        count = self.monitor._get_new_registrations(since)
        
        self.assertEqual(count, 2)
    
    def test_get_system_health(self):
        """Test getting overall system health."""
        health = self.monitor.get_system_health()
        
        required_keys = [
            'timestamp', 'database', 'cache', 'disk_space',
            'memory_usage', 'active_users', 'error_rate',
            'response_time', 'status'
        ]
        
        for key in required_keys:
            self.assertIn(key, health)
        
        self.assertIn(health['status'], ['healthy', 'warning', 'critical'])
    
    def test_get_user_activity_metrics(self):
        """Test getting user activity metrics."""
        activity = self.monitor.get_user_activity_metrics(24)
        
        required_keys = [
            'timestamp', 'period_hours', 'new_registrations',
            'active_users', 'login_attempts', 'failed_logins',
            'posts_created', 'user_follows', 'email_notifications'
        ]
        
        for key in required_keys:
            self.assertIn(key, activity)
        
        self.assertEqual(activity['period_hours'], 24)


class MetricsCollectorTest(TestCase):
    """Test metrics collector functionality."""
    
    def setUp(self):
        self.collector = MetricsCollector()
        cache.clear()
    
    def test_collect_all_metrics(self):
        """Test collecting all metrics."""
        metrics = self.collector.collect_all_metrics()
        
        required_sections = [
            'timestamp', 'system_health', 'user_activity',
            'content_metrics', 'security_metrics', 'performance_metrics'
        ]
        
        for section in required_sections:
            self.assertIn(section, metrics)
    
    def test_get_dashboard_data(self):
        """Test getting dashboard data."""
        dashboard = self.collector.get_dashboard_data()
        
        required_sections = [
            'overview', 'system', 'activity', 'content',
            'security', 'performance'
        ]
        
        for section in required_sections:
            self.assertIn(section, dashboard)
        
        # Check overview section
        overview = dashboard['overview']
        self.assertIn('status', overview)
        self.assertIn('active_users', overview)
        self.assertIn('error_rate', overview)
        self.assertIn('response_time', overview)


class MonitoringAPITest(APITestCase):
    """Test monitoring API endpoints."""
    
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@test.com',
            password='userpass123'
        )
    
    def test_system_health_endpoint_admin_access(self):
        """Test system health endpoint with admin access."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('system-health')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertIn('database', response.data)
        self.assertIn('cache', response.data)
    
    def test_system_health_endpoint_regular_user_denied(self):
        """Test system health endpoint denies regular users."""
        self.client.force_authenticate(user=self.regular_user)
        
        url = reverse('system-health')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_monitoring_dashboard_endpoint(self):
        """Test monitoring dashboard endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('monitoring-dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('overview', response.data)
        self.assertIn('system', response.data)
        self.assertIn('activity', response.data)
    
    def test_user_activity_metrics_endpoint(self):
        """Test user activity metrics endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('user-activity-metrics')
        response = self.client.get(url, {'hours': 48})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('period_hours', response.data)
        self.assertEqual(response.data['period_hours'], 48)
    
    def test_health_check_endpoint(self):
        """Test simple health check endpoint."""
        url = reverse('health-check')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('status', response.json())


class LoggingIntegrationTest(TestCase):
    """Test logging integration with various components."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_convenience_functions(self):
        """Test convenience logging functions."""
        with patch('common.logging.get_structured_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            # Test log_user_action
            log_user_action(self.user, 'test_action', resource_type='test')
            mock_logger.log_user_action.assert_called_once()
            
            # Test log_authentication
            log_authentication(self.user, 'login', success=True)
            mock_logger.log_authentication_event.assert_called_once()
            
            # Test log_security_event
            log_security_event('test_event', severity='medium')
            mock_logger.log_security_event.assert_called_once()
            
            # Test log_email_event
            log_email_event('sent', 'test@example.com', success=True)
            mock_logger.log_email_event.assert_called_once()
    
    def test_performance_monitor_decorator(self):
        """Test performance monitoring decorator."""
        @monitor_performance('test_operation')
        def test_function():
            return 'test_result'
        
        with patch('common.logging.PerformanceMonitor') as mock_monitor:
            mock_context = MagicMock()
            mock_monitor.return_value = mock_context
            
            result = test_function()
            
            self.assertEqual(result, 'test_result')
            mock_monitor.assert_called_once_with('test_operation')
            mock_context.__enter__.assert_called_once()
            mock_context.__exit__.assert_called_once()


class LogFileParsingTest(TestCase):
    """Test log file parsing functionality."""
    
    def setUp(self):
        self.monitor = SystemMonitor()
    
    def test_matches_event_type(self):
        """Test event type matching logic."""
        # Test authentication login
        log_entry = {
            'extra': {'event_type': 'login'},
            'message': 'user logged in'
        }
        self.assertTrue(self.monitor._matches_event_type(log_entry, 'authentication_login'))
        
        # Test authentication failure
        log_entry = {
            'extra': {'event_type': 'login', 'success': False},
            'message': 'login failed'
        }
        self.assertTrue(self.monitor._matches_event_type(log_entry, 'authentication_failure'))
        
        # Test email sent
        log_entry = {
            'extra': {'event_type': 'sent'},
            'message': 'email sent to user'
        }
        self.assertTrue(self.monitor._matches_event_type(log_entry, 'email_sent'))
        
        # Test celery task
        log_entry = {
            'extra': {'status': 'success'},
            'message': 'task completed successfully'
        }
        self.assertTrue(self.monitor._matches_event_type(log_entry, 'celery_task_success'))
    
    @patch('builtins.open')
    @patch('os.path.exists')
    def test_count_log_events_with_file(self, mock_exists, mock_open):
        """Test counting log events from files."""
        mock_exists.return_value = True
        
        # Mock log file content
        log_entries = [
            '{"timestamp": "2023-01-01T12:00:00", "extra": {"event_type": "login"}, "message": "user login"}',
            '{"timestamp": "2023-01-01T12:01:00", "extra": {"event_type": "login", "success": false}, "message": "failed login"}',
            '{"timestamp": "2023-01-01T12:02:00", "extra": {"event_type": "sent"}, "message": "email sent"}'
        ]
        
        mock_file = MagicMock()
        mock_file.__iter__ = lambda self: iter(log_entries)
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Count login events
        count = self.monitor._count_log_events('authentication_login', 24)
        
        # Should find 2 login events (including the failed one)
        self.assertEqual(count, 2)

cla
ss StructuredLoggerTest(TestCase):
    """Test structured logger functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.logger = StructuredLogger('test_logger')
    
    def test_log_user_action(self):
        """Test logging user actions."""
        with self.assertLogs('test_logger', level='INFO') as cm:
            self.logger.log_user_action(
                user=self.user,
                action_type='create',
                resource_type='post',
                resource_id='123',
                details={'title': 'Test Post'}
            )
        
        self.assertEqual(len(cm.records), 1)
        record = cm.records[0]
        self.assertEqual(record.levelname, 'INFO')
        self.assertIn('User action: create', record.getMessage())
    
    def test_log_authentication_event_success(self):
        """Test logging successful authentication."""
        with self.assertLogs('test_logger', level='INFO') as cm:
            self.logger.log_authentication_event(
                user=self.user,
                event_type='login',
                success=True,
                ip_address='127.0.0.1'
            )
        
        self.assertEqual(len(cm.records), 1)
        record = cm.records[0]
        self.assertEqual(record.levelname, 'INFO')
        self.assertIn('Authentication login succeeded', record.getMessage())
    
    def test_log_authentication_event_failure(self):
        """Test logging failed authentication."""
        with self.assertLogs('test_logger', level='WARNING') as cm:
            self.logger.log_authentication_event(
                user=self.user,
                event_type='login',
                success=False,
                ip_address='127.0.0.1'
            )
        
        self.assertEqual(len(cm.records), 1)
        record = cm.records[0]
        self.assertEqual(record.levelname, 'WARNING')
        self.assertIn('Authentication login failed', record.getMessage())
    
    def test_log_performance_metric(self):
        """Test logging performance metrics."""
        with self.assertLogs('test_logger', level='INFO') as cm:
            self.logger.log_performance_metric(
                operation='database_query',
                duration=1.5,
                query_count=3
            )
        
        self.assertEqual(len(cm.records), 1)
        record = cm.records[0]
        self.assertEqual(record.levelname, 'INFO')
        self.assertIn('Operation \'database_query\' completed in 1.500s', record.getMessage())
    
    def test_log_security_event(self):
        """Test logging security events."""
        with self.assertLogs('test_logger', level='ERROR') as cm:
            self.logger.log_security_event(
                event_type='suspicious_login',
                severity='high',
                user=self.user,
                ip_address='192.168.1.100'
            )
        
        self.assertEqual(len(cm.records), 1)
        record = cm.records[0]
        self.assertEqual(record.levelname, 'ERROR')
        self.assertIn('Security event: suspicious_login', record.getMessage())
    
    def test_log_email_event(self):
        """Test logging email events."""
        with self.assertLogs('test_logger', level='INFO') as cm:
            self.logger.log_email_event(
                event_type='sent',
                recipient='test@example.com',
                success=True,
                subject='Test Email'
            )
        
        self.assertEqual(len(cm.records), 1)
        record = cm.records[0]
        self.assertEqual(record.levelname, 'INFO')
        self.assertIn('Email sent to test@example.com', record.getMessage())
    
    def test_log_celery_task(self):
        """Test logging Celery task events."""
        with self.assertLogs('test_logger', level='INFO') as cm:
            self.logger.log_celery_task(
                task_name='send_email',
                task_id='abc123',
                status='success',
                duration=2.3
            )
        
        self.assertEqual(len(cm.records), 1)
        record = cm.records[0]
        self.assertEqual(record.levelname, 'INFO')
        self.assertIn('Celery task send_email (abc123) - success', record.getMessage())
    
    def test_log_social_action(self):
        """Test logging social actions."""
        target_user = User.objects.create_user(
            username='targetuser',
            email='target@example.com',
            password='testpass123'
        )
        
        with self.assertLogs('test_logger', level='INFO') as cm:
            self.logger.log_social_action(
                user=self.user,
                action_type='follow',
                target_user=target_user
            )
        
        self.assertEqual(len(cm.records), 1)
        record = cm.records[0]
        self.assertEqual(record.levelname, 'INFO')
        self.assertIn('Social action: follow', record.getMessage())
    
    def test_log_moderation_action(self):
        """Test logging moderation actions."""
        with self.assertLogs('test_logger', level='INFO') as cm:
            self.logger.log_moderation_action(
                moderator=self.user,
                action_type='flag_resolved',
                reason='Inappropriate content'
            )
        
        self.assertEqual(len(cm.records), 1)
        record = cm.records[0]
        self.assertEqual(record.levelname, 'INFO')
        self.assertIn('Moderation action: flag_resolved', record.getMessage())
    
    def test_log_file_operation_success(self):
        """Test logging successful file operations."""
        with self.assertLogs('test_logger', level='INFO') as cm:
            self.logger.log_file_operation(
                user=self.user,
                operation='upload',
                file_path='/media/uploads/test.jpg',
                file_size=1024000,
                file_type='image/jpeg',
                success=True
            )
        
        self.assertEqual(len(cm.records), 1)
        record = cm.records[0]
        self.assertEqual(record.levelname, 'INFO')
        self.assertIn('File operation: upload', record.getMessage())
    
    def test_log_file_operation_failure(self):
        """Test logging failed file operations."""
        with self.assertLogs('test_logger', level='ERROR') as cm:
            self.logger.log_file_operation(
                user=self.user,
                operation='upload',
                file_path='/media/uploads/test.jpg',
                success=False,
                error='File too large'
            )
        
        self.assertEqual(len(cm.records), 1)
        record = cm.records[0]
        self.assertEqual(record.levelname, 'ERROR')
        self.assertIn('File operation: upload', record.getMessage())
        self.assertIn('failed: File too large', record.getMessage())


class PerformanceMonitorTest(TestCase):
    """Test performance monitoring context manager."""
    
    def test_performance_monitor_success(self):
        """Test performance monitor with successful operation."""
        with self.assertLogs('performance', level='DEBUG') as cm:
            with monitor_performance('test_operation'):
                time.sleep(0.1)  # Simulate work
        
        self.assertEqual(len(cm.records), 1)
        record = cm.records[0]
        self.assertIn('Operation \'test_operation\' completed', record.getMessage())
    
    def test_performance_monitor_with_exception(self):
        """Test performance monitor with exception."""
        with self.assertLogs('performance', level='DEBUG') as cm:
            try:
                with monitor_performance('test_operation_with_error'):
                    time.sleep(0.1)
                    raise ValueError("Test error")
            except ValueError:
                pass
        
        self.assertEqual(len(cm.records), 1)
        record = cm.records[0]
        self.assertIn('Operation \'test_operation_with_error\' completed', record.getMessage())


class ConvenienceFunctionsTest(TestCase):
    """Test convenience functions for logging."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_log_user_action_convenience(self):
        """Test convenience function for user actions."""
        with self.assertLogs('accounts', level='INFO') as cm:
            log_user_action(self.user, 'create', resource_type='post')
        
        self.assertEqual(len(cm.records), 1)
        self.assertIn('User action: create', cm.records[0].getMessage())
    
    def test_log_authentication_convenience(self):
        """Test convenience function for authentication."""
        with self.assertLogs('accounts', level='INFO') as cm:
            log_authentication(self.user, 'login', success=True)
        
        self.assertEqual(len(cm.records), 1)
        self.assertIn('Authentication login succeeded', cm.records[0].getMessage())
    
    def test_log_security_event_convenience(self):
        """Test convenience function for security events."""
        with self.assertLogs('security', level='WARNING') as cm:
            log_security_event('suspicious_activity', severity='medium')
        
        self.assertEqual(len(cm.records), 1)
        self.assertIn('Security event: suspicious_activity', cm.records[0].getMessage())
    
    def test_log_email_event_convenience(self):
        """Test convenience function for email events."""
        with self.assertLogs('notifications', level='INFO') as cm:
            log_email_event('sent', 'test@example.com', success=True)
        
        self.assertEqual(len(cm.records), 1)
        self.assertIn('Email sent to test@example.com', cm.records[0].getMessage())
    
    def test_log_social_action_convenience(self):
        """Test convenience function for social actions."""
        with self.assertLogs('social', level='INFO') as cm:
            log_social_action(self.user, 'like')
        
        self.assertEqual(len(cm.records), 1)
        self.assertIn('Social action: like', cm.records[0].getMessage())
    
    def test_log_moderation_action_convenience(self):
        """Test convenience function for moderation actions."""
        with self.assertLogs('moderation', level='INFO') as cm:
            log_moderation_action(self.user, 'approve')
        
        self.assertEqual(len(cm.records), 1)
        self.assertIn('Moderation action: approve', cm.records[0].getMessage())
    
    def test_log_file_operation_convenience(self):
        """Test convenience function for file operations."""
        with self.assertLogs('media', level='INFO') as cm:
            log_file_operation(self.user, 'upload', success=True)
        
        self.assertEqual(len(cm.records), 1)
        self.assertIn('File operation: upload', cm.records[0].getMessage())

c
lass SystemMonitorTest(TestCase):
    """Test system monitoring functionality."""
    
    def setUp(self):
        self.monitor = SystemMonitor()
        cache.clear()  # Clear cache before each test
    
    def test_get_system_health(self):
        """Test getting system health metrics."""
        health_data = self.monitor.get_system_health()
        
        self.assertIn('timestamp', health_data)
        self.assertIn('database', health_data)
        self.assertIn('cache', health_data)
        self.assertIn('status', health_data)
        self.assertIn(health_data['status'], ['healthy', 'warning'