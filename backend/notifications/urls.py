"""
URL configuration for notifications app.
"""

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Email subscription management
    path('subscriptions/', views.EmailSubscriptionListCreateView.as_view(), name='subscription-list-create'),
    path('subscriptions/<int:pk>/', views.EmailSubscriptionDetailView.as_view(), name='subscription-detail'),
    
    # Public subscription endpoint (no auth required)
    path('subscribe/', views.PublicSubscribeView.as_view(), name='public-subscribe'),
    
    # Unsubscribe functionality
    path('unsubscribe/<str:token>/', views.UnsubscribeView.as_view(), name='unsubscribe'),
    
    # Author-specific subscriptions
    path('authors/<int:author_id>/toggle/', views.toggle_subscription, name='toggle-author-subscription'),
    path('authors/<int:author_id>/check/', views.check_author_subscription, name='check-author-subscription'),
    path('authors/subscribers/', views.AuthorSubscribersView.as_view(), name='author-subscribers'),
    
    # Admin endpoints
    path('logs/', views.NotificationLogListView.as_view(), name='notification-logs'),
    path('stats/', views.SubscriptionStatsView.as_view(), name='subscription-stats'),
]