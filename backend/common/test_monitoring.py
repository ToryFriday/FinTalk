"""
Comprehensive tests for monitoring and logging functionality.
"""

import json
import tempfile
import os
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache
from rest_framework.test import APITestCase
from rest_framework import status

from .monitoring import SystemMonitor, MetricsCollector
from .logging import (
    StructuredLogger, 
    get_structured_logger,
    log_user_action,
    log_authentication,
    log_security_event,
    monitor_performance
)


class StructuredLoggerTestCase(TestCase):
    """Test cases for structured logging functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.logger = StructuredLogger('test_logger')
    
    def test_log_user_action(self):
        """Test user action logging."""
        with patch('common.logging.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            self.logger.log_user_action(
                user=self.user,
                action_type='create',
                resource_type='post',
                resource_id='123',
                details={'title': 'Test Post'}
            )
            
            # Verify logger was called
            mock_logger.log.assert_called_once()
            args, kwargs = mock_logger.log.call_args
            
            # Check log level and message
            self.assertEqual(args[0], 20)  # INFO level
            self.assertIn('User action: create', args[1])
            
            # Check extra data
            extra = kwargs['extra']
            self.assertEqual(extra['event_type'], 'user_action')
            self.assertEqual(extra['user_id'], self.user.id)
            self.assertEqual(extra['action_type'], 'create')
            self.assertEqual(extra['resource_type'], 'post')
            self.assertEqual(extra['resource_id'], '123')
    
    def test_log_authentication_event(self):
        """Test authentication event logging."""
        with patch('common.logging.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            self.logger.log_authentication_event(
                user=self.user,
                event_type='login',
                success=True,
                ip_address='192.168.1.1',
                user_agent='Mozilla/5.0'
            )
            
            mock_logger.log.assert_called_once()
            args, kwargs = mock_logger.log.call_args
            
            # Check log level (INFO for successful auth)
            self.assertEqual(args[0], 20)
            self.assertIn('Authentication login succeeded', args[1])
            
            # Check extra data
            extra = kwargs['extra']
            self.assertEqual(extra['event_type'], 'authentication')
            self.assertEqual(extra['auth_event'], 'login')
            self.assertTrue(extra['success'])
            self.assertEqual(extra['ip_address'], '192.168.1.1')    d
ef test_log_security_event(self):
        """Test security event logging."""
        with patch('common.logging.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            self.logger.log_security_event(
                event_type='suspicious_activity',
                severity='high',
                user=self.user,
                ip_address='192.168.1.1',
                details={'reason': 'Multiple failed attempts'}
            )
            
            mock_logger.log.assert_called_once()
            args, kwargs = mock_logger.log.call_args
            
            # Check log level (ERROR for high severity)
            self.assertEqual(args[0], 40)
            self.assertIn('Security event: suspicious_activity', args[1])
            
            extra = kwargs['extra']
            self.assertEqual(extra['event_type'], 'security')
            self.assertEqual(extra['severity'], 'high')


class SystemMonitorTestCase(TestCase):
    """Test cases for system monitoring functionality."""
    
    def setUp(self):
        self.monitor = SystemMonitor()
        cache.clear()  # Clear cache before each test
    
    def test_get_system_health(self):
        """Test system health monitoring."""
        health = self.monitor.get_system_health()
        
        # Check required fields
        self.assertIn('timestamp', health)
        self.assertIn('database', health)
        self.assertIn('cache', health)
        self.assertIn('status', health)
        
        # Check status is valid
        self.assertIn(health['status'], ['healthy', 'warning', 'critical'])
    
    def test_database_health_check(self):
        """Test database health checking."""
        db_health = self.monitor._check_database_health()
        
        self.assertIn('status', db_health)
        self.assertIn('response_time', db_health)
        
        # Should be healthy in test environment
        self.assertEqual(db_health['status'], 'healthy')
        self.assertIsInstance(db_health['response_time'], float)


class MonitoringAPITestCase(APITestCase):
    """Test cases for monitoring API endpoints."""
    
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
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
    
    def test_health_check_endpoint_public(self):
        """Test public health check endpoint."""
        url = reverse('health-check')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('status', data)
        self.assertIn('timestamp', data)