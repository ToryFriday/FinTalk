"""
URL patterns for common monitoring and system endpoints.
"""

from django.urls import path
from .views import (
    SystemHealthView,
    MonitoringDashboardView,
    health_check
)

urlpatterns = [
    # Simple health check for load balancers
    path('health/', health_check, name='health-check'),
    
    # Admin monitoring endpoints
    path('api/monitoring/health/', SystemHealthView.as_view(), name='system-health'),
    path('api/monitoring/dashboard/', MonitoringDashboardView.as_view(), name='monitoring-dashboard'),
]