"""
Monitoring and system health API views.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework import status
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.utils import timezone

from .monitoring import SystemMonitor, MetricsCollector
from .logging import get_structured_logger

logger = get_structured_logger('monitoring')


class SystemHealthView(APIView):
    """
    API endpoint for system health monitoring.
    """
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """Get system health metrics."""
        try:
            monitor = SystemMonitor()
            health_data = monitor.get_system_health()
            
            logger.log_user_action(
                user=request.user,
                action_type='view_system_health',
                details={'status': health_data.get('status')}
            )
            
            return Response(health_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.log_security_event(
                event_type='monitoring_error',
                severity='high',
                user=request.user,
                details={'error': str(e)}
            )
            return Response(
                {'error': 'Failed to retrieve system health'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MonitoringDashboardView(APIView):
    """
    API endpoint for complete monitoring dashboard data.
    """
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """Get complete dashboard data."""
        try:
            collector = MetricsCollector()
            dashboard_data = collector.get_dashboard_data()
            
            return Response(dashboard_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': 'Failed to retrieve dashboard data'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# Function-based view for simple health check
def health_check(request):
    """Simple health check endpoint for load balancers."""
    try:
        # Basic database check
        User.objects.count()
        
        return JsonResponse({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'version': '1.0.0'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)