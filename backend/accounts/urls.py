"""
URL patterns for accounts app.
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication endpoints
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    
    # Email verification endpoints
    path('verify-email/<str:token>/', views.EmailVerificationView.as_view(), name='verify-email'),
    path('verify-email/', views.EmailVerificationView.as_view(), name='verify-email-post'),
    path('resend-verification/', views.ResendVerificationView.as_view(), name='resend-verification'),
    
    # Profile endpoints
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('profile/<int:id>/', views.PublicUserProfileView.as_view(), name='public-profile'),
    path('me/', views.CurrentUserView.as_view(), name='current-user'),
    
    # Utility endpoints
    path('check-username/', views.check_username_availability, name='check-username'),
    path('check-email/', views.check_email_availability, name='check-email'),
    
    # RBAC endpoints
    path('roles/', views.RoleListCreateView.as_view(), name='role-list-create'),
    path('roles/<int:pk>/', views.RoleDetailView.as_view(), name='role-detail'),
    path('user-roles/', views.UserRoleListView.as_view(), name='user-role-list'),
    path('role-assignment/', views.RoleAssignmentView.as_view(), name='role-assignment'),
    path('role-revocation/', views.RoleRevocationView.as_view(), name='role-revocation'),
    path('users/<int:pk>/roles/', views.UserWithRolesView.as_view(), name='user-with-roles'),
    path('role-management/', views.RoleManagementView.as_view(), name='role-management'),
    path('permissions/', views.PermissionListView.as_view(), name='permission-list'),
    path('user-permissions/', views.user_permissions, name='user-permissions'),
    path('check-permission/', views.check_user_permission, name='check-permission'),
    
    # Social features endpoints
    path('users/<int:pk>/follow/', views.FollowUserView.as_view(), name='follow-user'),
    path('users/<int:pk>/followers/', views.UserFollowersView.as_view(), name='user-followers'),
    path('users/<int:pk>/following/', views.UserFollowingView.as_view(), name='user-following'),
    path('users/<int:pk>/social-profile/', views.UserSocialProfileView.as_view(), name='user-social-profile'),
    path('users/<int:pk>/follow-status/', views.check_follow_status, name='check-follow-status'),
    path('users/<int:pk>/mutual-followers/', views.mutual_followers, name='mutual-followers'),
    path('users/suggested/', views.SuggestedUsersView.as_view(), name='suggested-users'),
    
    # Saved articles endpoints (moved from posts app for better organization)
    path('saved-articles/', views.SavedPostsView.as_view(), name='saved-articles-list'),
    path('saved-articles/<int:pk>/', views.SavedArticleDetailView.as_view(), name='saved-article-detail'),
]