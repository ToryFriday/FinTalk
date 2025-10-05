"""
URL configuration for posts app.
Defines API endpoints for blog post CRUD operations.
"""
from django.urls import path
from .views import (
    PostListCreateView, 
    PostRetrieveUpdateDestroyView,
    DraftPostsView,
    SchedulePostView,
    PublishPostView,
    MediaFileUploadView,
    MediaFileListView,
    MediaFileDetailView,
    PostMediaView
)
from accounts.views import SavePostView, SavedPostsView, check_article_saved

app_name = 'posts'

urlpatterns = [
    # List all posts (GET) and create new post (POST)
    path('api/posts/', PostListCreateView.as_view(), name='post-list-create'),
    
    # Retrieve (GET), update (PUT), and delete (DELETE) specific post
    path('api/posts/<int:pk>/', PostRetrieveUpdateDestroyView.as_view(), name='post-detail'),
    
    # Draft management endpoints
    path('api/posts/drafts/', DraftPostsView.as_view(), name='draft-posts'),
    
    # Post scheduling and publishing endpoints
    path('api/posts/<int:pk>/schedule/', SchedulePostView.as_view(), name='schedule-post'),
    path('api/posts/<int:pk>/publish/', PublishPostView.as_view(), name='publish-post'),
    
    # Saved articles endpoints
    path('api/posts/<int:pk>/save/', SavePostView.as_view(), name='save-post'),
    path('api/posts/<int:pk>/saved/', check_article_saved, name='check-article-saved'),
    path('api/posts/saved/', SavedPostsView.as_view(), name='saved-posts'),
    
    # Media file endpoints
    path('api/posts/media/upload/', MediaFileUploadView.as_view(), name='media-upload'),
    path('api/posts/media/', MediaFileListView.as_view(), name='media-list'),
    path('api/posts/media/<int:pk>/', MediaFileDetailView.as_view(), name='media-detail'),
    
    # Post media attachment endpoints
    path('api/posts/<int:pk>/media/', PostMediaView.as_view(), name='post-media'),
    path('api/posts/<int:pk>/media/<int:media_id>/', PostMediaView.as_view(), name='post-media-detail'),
]