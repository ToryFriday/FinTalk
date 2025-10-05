"""
URL configuration for blog_manager project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def api_root(request):
    """Root API endpoint that provides information about available endpoints."""
    return JsonResponse({
        'message': 'FinTalk API',
        'version': '1.0',
        'endpoints': {
            'posts': '/api/posts/',
            'auth': '/api/auth/',
            'notifications': '/api/notifications/',
            'moderation': '/api/moderation/',
            'monitoring': '/api/monitoring/',
            'health': '/health/',
            'admin': '/admin/',
        }
    })

urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    path('', include('posts.urls')),
    path('', include('moderation.urls')),
    path('', include('common.urls')),
    path('api/auth/', include('accounts.urls')),
    path('api/notifications/', include('notifications.urls')),
]

# Custom error handlers
handler404 = 'blog_manager.error_views.handler404'
handler500 = 'blog_manager.error_views.handler500'
