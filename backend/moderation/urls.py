"""
URL configuration for moderation app.
Defines API endpoints for content moderation and flagging system.
"""
from django.urls import path
from .views import (
    FlagPostView,
    ContentFlagListView,
    ContentFlagDetailView,
    ModerationDashboardView,
    ModerationSettingsView,
    flag_statistics
)

app_name = 'moderation'

urlpatterns = [
    # Flag content endpoints
    path('api/posts/<int:pk>/flag/', FlagPostView.as_view(), name='flag-post'),
    
    # Moderation management endpoints
    path('api/moderation/flags/', ContentFlagListView.as_view(), name='content-flags'),
    path('api/moderation/flags/<int:pk>/', ContentFlagDetailView.as_view(), name='flag-detail'),
    path('api/moderation/dashboard/', ModerationDashboardView.as_view(), name='moderation-dashboard'),
    path('api/moderation/settings/', ModerationSettingsView.as_view(), name='moderation-settings'),
    path('api/moderation/statistics/', flag_statistics, name='flag-statistics'),
]