"""
URL configuration for posts app.
Defines API endpoints for blog post CRUD operations.
"""
from django.urls import path
from .views import PostListCreateView, PostRetrieveUpdateDestroyView

app_name = 'posts'

urlpatterns = [
    # List all posts (GET) and create new post (POST)
    path('api/posts/', PostListCreateView.as_view(), name='post-list-create'),
    
    # Retrieve (GET), update (PUT), and delete (DELETE) specific post
    path('api/posts/<int:pk>/', PostRetrieveUpdateDestroyView.as_view(), name='post-detail'),
]