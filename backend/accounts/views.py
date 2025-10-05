"""
Views for user authentication and profile management.
"""

from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Permission
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count
import logging

from .models import UserProfile, Role, UserRole, SavedArticle, UserFollow
from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    EmailVerificationSerializer,
    ResendVerificationSerializer,
    UserLoginSerializer,
    UserBasicSerializer,
    RoleSerializer,
    UserRoleSerializer,
    RoleAssignmentSerializer,
    UserWithRolesSerializer,
    RoleManagementSerializer,
    PermissionSerializer,
    SavedArticleSerializer,
    SavedArticleListSerializer,
    UserFollowSerializer,
    UserFollowListSerializer,
    UserSocialProfileSerializer,
    FollowActionSerializer,
    SuggestedUsersSerializer
)
from .tasks import send_verification_email

logger = logging.getLogger(__name__)


class UserRegistrationView(APIView):
    """
    API view for user registration with email verification.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        Register a new user and send email verification.
        """
        serializer = UserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    # Create user
                    user = serializer.save()
                    
                    # Generate verification token
                    profile = user.profile
                    token = profile.generate_verification_token()
                    profile.save()
                    
                    # Queue email verification task
                    send_verification_email.delay(user.id)
                    
                    logger.info(f"User registered successfully: {user.username}")
                    
                    return Response({
                        'message': 'Registration successful. Please check your email to verify your account.',
                        'user_id': user.id,
                        'username': user.username,
                        'email': user.email
                    }, status=status.HTTP_201_CREATED)
                    
            except Exception as e:
                logger.error(f"Registration failed: {str(e)}")
                return Response({
                    'error': 'Registration failed. Please try again.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailVerificationView(APIView):
    """
    API view for email verification using token.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, token=None):
        """
        Verify user email with token.
        """
        # Get token from URL parameter or request data
        verification_token = token or request.data.get('token')
        
        if not verification_token:
            return Response({
                'error': 'Verification token is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = EmailVerificationSerializer(data={'token': verification_token})
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    # Get user profile by token
                    profile = UserProfile.objects.get(
                        email_verification_token=verification_token
                    )
                    
                    # Activate user and mark email as verified
                    user = profile.user
                    user.is_active = True
                    user.save()
                    
                    profile.is_email_verified = True
                    profile.email_verification_token = ''  # Clear token
                    profile.save()
                    
                    logger.info(f"Email verified successfully for user: {user.username}")
                    
                    return Response({
                        'message': 'Email verified successfully. You can now log in.',
                        'user_id': user.id,
                        'username': user.username
                    }, status=status.HTTP_200_OK)
                    
            except UserProfile.DoesNotExist:
                return Response({
                    'error': 'Invalid verification token.'
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Email verification failed: {str(e)}")
                return Response({
                    'error': 'Email verification failed. Please try again.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request, token):
        """
        Handle GET request for email verification (for email links).
        """
        return self.post(request, token)


class ResendVerificationView(APIView):
    """
    API view for resending email verification.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        Resend email verification for a user.
        """
        serializer = ResendVerificationSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                email = serializer.validated_data['email']
                user = User.objects.get(email=email)
                profile = user.profile
                
                # Generate new verification token
                token = profile.generate_verification_token()
                profile.save()
                
                # Queue email verification task
                send_verification_email.delay(user.id)
                
                logger.info(f"Verification email resent for user: {user.username}")
                
                return Response({
                    'message': 'Verification email sent. Please check your email.'
                }, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                return Response({
                    'error': 'No user found with this email address.'
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Resend verification failed: {str(e)}")
                return Response({
                    'error': 'Failed to send verification email. Please try again.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    """
    API view for user login.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        Authenticate user and create session.
        """
        serializer = UserLoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Log in the user
            login(request, user)
            
            # Get user profile data
            profile_serializer = UserProfileSerializer(user.profile)
            
            logger.info(f"User logged in successfully: {user.username}")
            
            return Response({
                'message': 'Login successful.',
                'user': profile_serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLogoutView(APIView):
    """
    API view for user logout.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Log out the current user.
        """
        username = request.user.username
        logout(request)
        
        logger.info(f"User logged out successfully: {username}")
        
        return Response({
            'message': 'Logout successful.'
        }, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API view for retrieving and updating user profile.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """
        Get the current user's profile.
        """
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on request method.
        """
        if self.request.method == 'GET':
            return UserProfileSerializer
        return UserProfileUpdateSerializer
    
    def update(self, request, *args, **kwargs):
        """
        Update user profile with logging.
        """
        response = super().update(request, *args, **kwargs)
        
        if response.status_code == 200:
            logger.info(f"Profile updated successfully for user: {request.user.username}")
        
        return response


class PublicUserProfileView(generics.RetrieveAPIView):
    """
    API view for retrieving public user profile information.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = UserBasicSerializer
    queryset = User.objects.filter(is_active=True)
    lookup_field = 'id'
    
    def get_object(self):
        """
        Get user by ID with profile prefetch.
        """
        user_id = self.kwargs.get('id')
        return get_object_or_404(
            User.objects.select_related('profile').filter(is_active=True),
            id=user_id
        )


class CurrentUserView(APIView):
    """
    API view for getting current authenticated user information.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """
        Get current user profile information.
        """
        serializer = UserProfileSerializer(request.user.profile)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def check_username_availability(request):
    """
    Check if a username is available.
    """
    username = request.GET.get('username')
    
    if not username:
        return Response({
            'error': 'Username parameter is required.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    is_available = not User.objects.filter(username=username).exists()
    
    return Response({
        'username': username,
        'available': is_available
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def check_email_availability(request):
    """
    Check if an email is available.
    """
    email = request.GET.get('email')
    
    if not email:
        return Response({
            'error': 'Email parameter is required.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    is_available = not User.objects.filter(email=email).exists()
    
    return Response({
        'email': email,
        'available': is_available
    }, status=status.HTTP_200_OK)


# RBAC Views

class RoleListCreateView(generics.ListCreateAPIView):
    """
    API view for listing and creating roles.
    """
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Get roles based on user permissions.
        """
        user = self.request.user
        
        # Check if user is authenticated
        if not user.is_authenticated:
            return Role.objects.none()
        
        # Admins can see all roles
        if user.is_superuser or user.has_role('admin'):
            return Role.objects.all().prefetch_related('permissions')
        
        # Editors can see non-admin roles
        elif user.has_role('editor'):
            return Role.objects.exclude(name='admin').prefetch_related('permissions')
        
        # Other users can only see basic roles
        else:
            return Role.objects.filter(name__in=['reader', 'writer']).prefetch_related('permissions')
    
    def perform_create(self, serializer):
        """
        Create role with permission check.
        """
        user = self.request.user
        
        # Only admins can create roles
        if not (user.is_superuser or user.has_role('admin')):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only administrators can create roles.")
        
        serializer.save()
        logger.info(f"Role created by {user.username}: {serializer.instance.name}")


class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting roles.
    """
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Get roles based on user permissions.
        """
        user = self.request.user
        
        # Check if user is authenticated
        if not user.is_authenticated:
            return Role.objects.none()
        
        if user.is_superuser or user.has_role('admin'):
            return Role.objects.all().prefetch_related('permissions')
        elif user.has_role('editor'):
            return Role.objects.exclude(name='admin').prefetch_related('permissions')
        else:
            return Role.objects.filter(name__in=['reader', 'writer']).prefetch_related('permissions')
    
    def perform_update(self, serializer):
        """
        Update role with permission check.
        """
        user = self.request.user
        role = self.get_object()
        
        # Only admins can update admin role
        if role.name == 'admin' and not (user.is_superuser or user.has_role('admin')):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only administrators can update admin role.")
        
        # Editors can update non-admin roles
        if not (user.is_superuser or user.has_role('admin') or user.has_role('editor')):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Insufficient permissions to update roles.")
        
        serializer.save()
        logger.info(f"Role updated by {user.username}: {role.name}")
    
    def perform_destroy(self, instance):
        """
        Delete role with permission check.
        """
        user = self.request.user
        
        # Only admins can delete roles
        if not (user.is_superuser or user.has_role('admin')):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only administrators can delete roles.")
        
        # Prevent deletion of roles with active assignments
        if instance.user_assignments.filter(is_active=True).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Cannot delete role with active user assignments.")
        
        logger.info(f"Role deleted by {user.username}: {instance.name}")
        instance.delete()


class UserRoleListView(generics.ListAPIView):
    """
    API view for listing user role assignments.
    """
    serializer_class = UserRoleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Get user role assignments based on permissions.
        """
        user = self.request.user
        
        # Check if user is authenticated
        if not user.is_authenticated:
            return UserRole.objects.none()
        
        # Admins can see all assignments
        if user.is_superuser or user.has_role('admin'):
            return UserRole.objects.all().select_related('user', 'role', 'assigned_by')
        
        # Editors can see non-admin assignments
        elif user.has_role('editor'):
            return UserRole.objects.exclude(role__name='admin').select_related('user', 'role', 'assigned_by')
        
        # Users can only see their own assignments
        else:
            return UserRole.objects.filter(user=user).select_related('user', 'role', 'assigned_by')


class RoleAssignmentView(APIView):
    """
    API view for assigning roles to users.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Assign a role to a user.
        """
        serializer = RoleAssignmentSerializer(data=request.data)
        
        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            role_id = serializer.validated_data['role_id']
            expires_at = serializer.validated_data.get('expires_at')
            notes = serializer.validated_data.get('notes', '')
            
            try:
                with transaction.atomic():
                    user = User.objects.get(id=user_id)
                    role = Role.objects.get(id=role_id)
                    
                    # Permission checks
                    if not self._can_assign_role(request.user, role):
                        return Response({
                            'error': 'Insufficient permissions to assign this role.'
                        }, status=status.HTTP_403_FORBIDDEN)
                    
                    # Create role assignment
                    user_role = UserRole.objects.create(
                        user=user,
                        role=role,
                        assigned_by=request.user,
                        expires_at=expires_at,
                        notes=notes
                    )
                    
                    logger.info(f"Role {role.name} assigned to {user.username} by {request.user.username}")
                    
                    serializer_response = UserRoleSerializer(user_role)
                    return Response({
                        'message': f'Role {role.display_name} assigned successfully.',
                        'assignment': serializer_response.data
                    }, status=status.HTTP_201_CREATED)
                    
            except Exception as e:
                logger.error(f"Role assignment failed: {str(e)}")
                return Response({
                    'error': 'Role assignment failed. Please try again.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _can_assign_role(self, assigner, role):
        """
        Check if user can assign a specific role.
        """
        # Superusers can assign any role
        if assigner.is_superuser:
            return True
        
        # Admins can assign any role except to themselves
        if assigner.has_role('admin'):
            return True
        
        # Editors can assign writer and reader roles
        if assigner.has_role('editor') and role.name in ['writer', 'reader']:
            return True
        
        return False


class RoleRevocationView(APIView):
    """
    API view for revoking roles from users.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Revoke a role from a user.
        """
        user_id = request.data.get('user_id')
        role_id = request.data.get('role_id')
        
        if not user_id or not role_id:
            return Response({
                'error': 'user_id and role_id are required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                user_role = UserRole.objects.get(
                    user_id=user_id,
                    role_id=role_id,
                    is_active=True
                )
                
                # Permission checks
                if not self._can_revoke_role(request.user, user_role):
                    return Response({
                        'error': 'Insufficient permissions to revoke this role.'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                # Deactivate role assignment
                user_role.is_active = False
                user_role.save()
                
                logger.info(f"Role {user_role.role.name} revoked from {user_role.user.username} by {request.user.username}")
                
                return Response({
                    'message': f'Role {user_role.role.display_name} revoked successfully.'
                }, status=status.HTTP_200_OK)
                
        except UserRole.DoesNotExist:
            return Response({
                'error': 'Role assignment not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Role revocation failed: {str(e)}")
            return Response({
                'error': 'Role revocation failed. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _can_revoke_role(self, revoker, user_role):
        """
        Check if user can revoke a specific role assignment.
        """
        # Superusers can revoke any role
        if revoker.is_superuser:
            return True
        
        # Admins can revoke any role except from other admins
        if revoker.has_role('admin'):
            return user_role.role.name != 'admin' or user_role.user == revoker
        
        # Editors can revoke writer and reader roles
        if revoker.has_role('editor') and user_role.role.name in ['writer', 'reader']:
            return True
        
        return False


class UserWithRolesView(generics.RetrieveAPIView):
    """
    API view for retrieving user with their roles.
    """
    serializer_class = UserWithRolesSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Get users based on permissions.
        """
        user = self.request.user
        
        # Check if user is authenticated
        if not user.is_authenticated:
            return User.objects.none()
        
        if user.is_superuser or user.has_role('admin') or user.has_role('editor'):
            return User.objects.all().select_related('profile').prefetch_related('user_roles__role')
        else:
            # Users can only see their own information
            return User.objects.filter(id=user.id).select_related('profile').prefetch_related('user_roles__role')


class RoleManagementView(APIView):
    """
    API view for comprehensive role management operations.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Handle role management operations (assign, revoke, update).
        """
        serializer = RoleManagementSerializer(data=request.data)
        
        if serializer.is_valid():
            action = serializer.validated_data['action']
            user_id = serializer.validated_data['user_id']
            role_id = serializer.validated_data['role_id']
            
            try:
                user = User.objects.get(id=user_id)
                role = Role.objects.get(id=role_id)
                
                if action == 'assign':
                    return self._assign_role(request, user, role, serializer.validated_data)
                elif action == 'revoke':
                    return self._revoke_role(request, user, role)
                elif action == 'update':
                    return self._update_role_assignment(request, user, role, serializer.validated_data)
                
            except (User.DoesNotExist, Role.DoesNotExist):
                return Response({
                    'error': 'User or role not found.'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _assign_role(self, request, user, role, data):
        """Assign role to user."""
        # Implementation similar to RoleAssignmentView
        pass
    
    def _revoke_role(self, request, user, role):
        """Revoke role from user."""
        # Implementation similar to RoleRevocationView
        pass
    
    def _update_role_assignment(self, request, user, role, data):
        """Update role assignment."""
        # Implementation for updating role assignment details
        pass


class PermissionListView(generics.ListAPIView):
    """
    API view for listing available permissions.
    """
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Get permissions based on user role.
        """
        user = self.request.user
        
        # Check if user is authenticated
        if not user.is_authenticated:
            return Permission.objects.none()
        
        # Only admins and editors can view permissions
        if user.is_superuser or user.has_role('admin') or user.has_role('editor'):
            return Permission.objects.all().select_related('content_type')
        
        return Permission.objects.none()


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_permissions(request):
    """
    Get current user's permissions from roles.
    """
    user = request.user
    permissions = user.get_role_permissions()
    serializer = PermissionSerializer(permissions, many=True)
    
    return Response({
        'user_id': user.id,
        'username': user.username,
        'roles': [role.name for role in user.get_user_roles()],
        'permissions': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def check_user_permission(request):
    """
    Check if user has a specific permission.
    """
    permission_codename = request.data.get('permission')
    
    if not permission_codename:
        return Response({
            'error': 'Permission codename is required.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    has_permission = user.has_role_permission(permission_codename)
    
    return Response({
        'user_id': user.id,
        'username': user.username,
        'permission': permission_codename,
        'has_permission': has_permission
    }, status=status.HTTP_200_OK)


# Saved Articles Views

class SavePostView(APIView):
    """
    API view for saving/unsaving articles by authenticated users.
    
    POST /api/posts/{id}/save/ - Save an article
    DELETE /api/posts/{id}/save/ - Unsave an article
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        """
        Save an article for the authenticated user.
        """
        logger.info(f"User {request.user.username} attempting to save post {pk}")
        
        try:
            from posts.models import Post
            post = get_object_or_404(Post, pk=pk)
            
            # Check if post is published
            if post.status != 'published':
                return Response({
                    'error': 'Only published posts can be saved.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if already saved
            saved_article, created = SavedArticle.objects.get_or_create(
                user=request.user,
                post=post,
                defaults={'notes': request.data.get('notes', '')}
            )
            
            if not created:
                return Response({
                    'message': 'Article is already saved.',
                    'saved_article_id': saved_article.id
                }, status=status.HTTP_200_OK)
            
            serializer = SavedArticleSerializer(saved_article, context={'request': request})
            logger.info(f"User {request.user.username} successfully saved post {pk}")
            
            return Response({
                'message': 'Article saved successfully.',
                'saved_article': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error saving post {pk} for user {request.user.username}: {str(e)}")
            return Response({
                'error': 'Failed to save article.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, pk):
        """
        Unsave an article for the authenticated user.
        """
        logger.info(f"User {request.user.username} attempting to unsave post {pk}")
        
        try:
            from posts.models import Post
            post = get_object_or_404(Post, pk=pk)
            
            # Find and delete the saved article
            try:
                saved_article = SavedArticle.objects.get(user=request.user, post=post)
                saved_article.delete()
                
                logger.info(f"User {request.user.username} successfully unsaved post {pk}")
                return Response({
                    'message': 'Article unsaved successfully.'
                }, status=status.HTTP_200_OK)
                
            except SavedArticle.DoesNotExist:
                return Response({
                    'error': 'Article is not saved.'
                }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            logger.error(f"Error unsaving post {pk} for user {request.user.username}: {str(e)}")
            return Response({
                'error': 'Failed to unsave article.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SavedPostsView(generics.ListAPIView):
    """
    API view for retrieving user's saved articles with filtering and search.
    
    GET /api/posts/saved/ - Get user's saved articles
    """
    serializer_class = SavedArticleListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Get saved articles for the authenticated user with filtering.
        """
        user = self.request.user
        queryset = SavedArticle.objects.filter(user=user).select_related('post', 'post__author_user')
        
        # Apply search filter
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(post__title__icontains=search) |
                Q(post__content__icontains=search) |
                Q(post__tags__icontains=search) |
                Q(notes__icontains=search)
            )
        
        # Apply tag filter
        tag = self.request.query_params.get('tag')
        if tag:
            queryset = queryset.filter(post__tags__icontains=tag)
        
        # Apply author filter
        author = self.request.query_params.get('author')
        if author:
            queryset = queryset.filter(
                Q(post__author__icontains=author) |
                Q(post__author_user__username__icontains=author) |
                Q(post__author_user__first_name__icontains=author) |
                Q(post__author_user__last_name__icontains=author)
            )
        
        # Apply date range filter
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            try:
                from django.utils.dateparse import parse_date
                parsed_date = parse_date(date_from)
                if parsed_date:
                    queryset = queryset.filter(saved_at__date__gte=parsed_date)
            except ValueError:
                pass
        
        if date_to:
            try:
                from django.utils.dateparse import parse_date
                parsed_date = parse_date(date_to)
                if parsed_date:
                    queryset = queryset.filter(saved_at__date__lte=parsed_date)
            except ValueError:
                pass
        
        # Apply ordering
        ordering = self.request.query_params.get('ordering', '-saved_at')
        valid_orderings = ['saved_at', '-saved_at', 'post__title', '-post__title', 
                          'post__created_at', '-post__created_at', 'post__view_count', '-post__view_count']
        
        if ordering in valid_orderings:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-saved_at')
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """
        Handle GET request to list saved articles with metadata.
        """
        logger.info(f"User {request.user.username} requesting saved articles")
        
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response_data = self.get_paginated_response(serializer.data).data
        else:
            serializer = self.get_serializer(queryset, many=True)
            response_data = {
                'count': queryset.count(),
                'results': serializer.data
            }
        
        # Add metadata
        response_data['metadata'] = {
            'total_saved': SavedArticle.objects.filter(user=request.user).count(),
            'filters_applied': {
                'search': request.query_params.get('search'),
                'tag': request.query_params.get('tag'),
                'author': request.query_params.get('author'),
                'date_from': request.query_params.get('date_from'),
                'date_to': request.query_params.get('date_to'),
                'ordering': request.query_params.get('ordering', '-saved_at')
            }
        }
        
        logger.info(f"Successfully returned {len(serializer.data)} saved articles for user {request.user.username}")
        return Response(response_data, status=status.HTTP_200_OK)


class SavedArticleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting individual saved articles.
    
    GET /api/saved-articles/{id}/ - Get saved article details
    PUT /api/saved-articles/{id}/ - Update saved article notes
    DELETE /api/saved-articles/{id}/ - Delete saved article
    """
    serializer_class = SavedArticleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Get saved articles for the authenticated user only.
        """
        return SavedArticle.objects.filter(user=self.request.user).select_related('post', 'post__author_user')
    
    def update(self, request, *args, **kwargs):
        """
        Update saved article (only notes can be updated).
        """
        instance = self.get_object()
        
        # Only allow updating notes
        allowed_fields = ['notes']
        update_data = {k: v for k, v in request.data.items() if k in allowed_fields}
        
        serializer = self.get_serializer(instance, data=update_data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        logger.info(f"User {request.user.username} updated saved article {instance.id}")
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete saved article.
        """
        instance = self.get_object()
        post_title = instance.post.title
        
        self.perform_destroy(instance)
        
        logger.info(f"User {request.user.username} deleted saved article: {post_title}")
        return Response({
            'message': f'Saved article "{post_title}" deleted successfully.'
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_article_saved(request, pk):
    """
    Check if a specific article is saved by the authenticated user.
    
    GET /api/posts/{id}/saved/ - Check if article is saved
    """
    try:
        from posts.models import Post
        post = get_object_or_404(Post, pk=pk)
        
        is_saved = SavedArticle.objects.filter(user=request.user, post=post).exists()
        
        saved_article = None
        if is_saved:
            saved_article_obj = SavedArticle.objects.get(user=request.user, post=post)
            saved_article = {
                'id': saved_article_obj.id,
                'saved_at': saved_article_obj.saved_at,
                'notes': saved_article_obj.notes
            }
        
        return Response({
            'post_id': pk,
            'is_saved': is_saved,
            'saved_article': saved_article
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error checking if post {pk} is saved by user {request.user.username}: {str(e)}")
        return Response({
            'error': 'Failed to check saved status.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Social Features Views

class FollowUserView(APIView):
    """
    API view for following/unfollowing users.
    
    POST /api/users/{id}/follow/ - Follow/unfollow a user
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        """
        Follow or unfollow a user.
        """
        try:
            target_user = get_object_or_404(User, pk=pk, is_active=True)
            
            # Prevent users from following themselves
            if target_user == request.user:
                return Response({
                    'error': 'Users cannot follow themselves.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if already following
            is_following = request.user.is_following(target_user)
            
            if is_following:
                # Unfollow
                success = request.user.unfollow(target_user)
                if success:
                    logger.info(f"User {request.user.username} unfollowed {target_user.username}")
                    
                    # Send notification about unfollow (optional)
                    # send_unfollow_notification.delay(request.user.id, target_user.id)
                    
                    return Response({
                        'message': f'You are no longer following {target_user.username}.',
                        'action': 'unfollowed',
                        'is_following': False,
                        'followers_count': target_user.get_followers_count()
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'error': 'Failed to unfollow user.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Follow
                success = request.user.follow(target_user)
                if success:
                    logger.info(f"User {request.user.username} followed {target_user.username}")
                    
                    # Send notification about new follower
                    from .tasks import send_new_follower_notification
                    send_new_follower_notification.delay(request.user.id, target_user.id)
                    
                    return Response({
                        'message': f'You are now following {target_user.username}.',
                        'action': 'followed',
                        'is_following': True,
                        'followers_count': target_user.get_followers_count()
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response({
                        'error': 'Failed to follow user.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
        except Exception as e:
            logger.error(f"Error in follow/unfollow for user {request.user.username}: {str(e)}")
            return Response({
                'error': 'Failed to process follow/unfollow request.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserFollowersView(generics.ListAPIView):
    """
    API view for listing user's followers.
    
    GET /api/users/{id}/followers/ - Get list of users who follow this user
    """
    serializer_class = UserFollowListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """
        Get followers for the specified user.
        """
        user_id = self.kwargs.get('pk')
        user = get_object_or_404(User, pk=user_id, is_active=True)
        
        return UserFollow.objects.filter(
            following=user
        ).select_related(
            'follower', 'follower__profile'
        ).order_by('-created_at')
    
    def get_serializer_context(self):
        """
        Add follow_type to serializer context.
        """
        context = super().get_serializer_context()
        context['follow_type'] = 'followers'
        return context
    
    def list(self, request, *args, **kwargs):
        """
        Handle GET request to list followers with metadata.
        """
        user_id = self.kwargs.get('pk')
        user = get_object_or_404(User, pk=user_id, is_active=True)
        
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response_data = self.get_paginated_response(serializer.data).data
        else:
            serializer = self.get_serializer(queryset, many=True)
            response_data = {
                'count': queryset.count(),
                'results': serializer.data
            }
        
        # Add metadata
        response_data['metadata'] = {
            'user_id': user.id,
            'username': user.username,
            'total_followers': user.get_followers_count(),
            'total_following': user.get_following_count()
        }
        
        logger.info(f"Successfully returned {len(serializer.data)} followers for user {user.username}")
        return Response(response_data, status=status.HTTP_200_OK)


class UserFollowingView(generics.ListAPIView):
    """
    API view for listing users that a user is following.
    
    GET /api/users/{id}/following/ - Get list of users this user is following
    """
    serializer_class = UserFollowListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """
        Get users that the specified user is following.
        """
        user_id = self.kwargs.get('pk')
        user = get_object_or_404(User, pk=user_id, is_active=True)
        
        return UserFollow.objects.filter(
            follower=user
        ).select_related(
            'following', 'following__profile'
        ).order_by('-created_at')
    
    def get_serializer_context(self):
        """
        Add follow_type to serializer context.
        """
        context = super().get_serializer_context()
        context['follow_type'] = 'following'
        return context
    
    def list(self, request, *args, **kwargs):
        """
        Handle GET request to list following with metadata.
        """
        user_id = self.kwargs.get('pk')
        user = get_object_or_404(User, pk=user_id, is_active=True)
        
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response_data = self.get_paginated_response(serializer.data).data
        else:
            serializer = self.get_serializer(queryset, many=True)
            response_data = {
                'count': queryset.count(),
                'results': serializer.data
            }
        
        # Add metadata
        response_data['metadata'] = {
            'user_id': user.id,
            'username': user.username,
            'total_followers': user.get_followers_count(),
            'total_following': user.get_following_count()
        }
        
        logger.info(f"Successfully returned {len(serializer.data)} following for user {user.username}")
        return Response(response_data, status=status.HTTP_200_OK)


class UserSocialProfileView(generics.RetrieveAPIView):
    """
    API view for retrieving user profile with social information.
    
    GET /api/users/{id}/social-profile/ - Get user profile with social stats
    """
    serializer_class = UserSocialProfileSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_object(self):
        """
        Get user profile by ID with social information.
        """
        user_id = self.kwargs.get('pk')
        user = get_object_or_404(User, pk=user_id, is_active=True)
        profile, created = UserProfile.objects.get_or_create(user=user)
        return profile


class SuggestedUsersView(generics.ListAPIView):
    """
    API view for getting suggested users to follow.
    
    GET /api/users/suggested/ - Get suggested users based on mutual connections
    """
    serializer_class = SuggestedUsersSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Get suggested users to follow.
        """
        user = self.request.user
        limit = int(self.request.query_params.get('limit', 10))
        
        # Get users suggested based on mutual connections
        suggested_users = user.get_suggested_users_to_follow(limit=limit)
        
        # If not enough suggestions, add popular users (most followers)
        if suggested_users.count() < limit:
            remaining_limit = limit - suggested_users.count()
            
            # Get users with most followers, excluding already suggested and current user
            popular_users = User.objects.filter(
                is_active=True
            ).exclude(
                id=user.id
            ).exclude(
                id__in=suggested_users.values_list('id', flat=True)
            ).exclude(
                id__in=user.following.values_list('following_id', flat=True)
            ).annotate(
                followers_count=Count('followers')
            ).order_by('-followers_count')[:remaining_limit]
            
            # Combine suggested and popular users
            all_user_ids = list(suggested_users.values_list('id', flat=True)) + \
                          list(popular_users.values_list('id', flat=True))
            
            return User.objects.filter(
                id__in=all_user_ids,
                is_active=True
            ).select_related('profile').distinct()
        
        return suggested_users.select_related('profile')
    
    def list(self, request, *args, **kwargs):
        """
        Handle GET request to list suggested users.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        logger.info(f"Successfully returned {len(serializer.data)} suggested users for {request.user.username}")
        
        return Response({
            'count': len(serializer.data),
            'results': serializer.data,
            'metadata': {
                'user_id': request.user.id,
                'username': request.user.username,
                'current_following_count': request.user.get_following_count()
            }
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_follow_status(request, pk):
    """
    Check if current user is following another user.
    
    GET /api/users/{id}/follow-status/ - Check follow status
    """
    try:
        target_user = get_object_or_404(User, pk=pk, is_active=True)
        
        is_following = request.user.is_following(target_user)
        is_followed_by = target_user.is_following(request.user)
        
        return Response({
            'user_id': target_user.id,
            'username': target_user.username,
            'is_following': is_following,
            'is_followed_by': is_followed_by,
            'followers_count': target_user.get_followers_count(),
            'following_count': target_user.get_following_count(),
            'mutual_followers_count': request.user.get_mutual_followers(target_user).count()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error checking follow status for user {request.user.username}: {str(e)}")
        return Response({
            'error': 'Failed to check follow status.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def mutual_followers(request, pk):
    """
    Get mutual followers between current user and another user.
    
    GET /api/users/{id}/mutual-followers/ - Get mutual followers
    """
    try:
        target_user = get_object_or_404(User, pk=pk, is_active=True)
        
        mutual_followers = request.user.get_mutual_followers(target_user)
        
        # Serialize mutual followers
        mutual_followers_data = []
        for user in mutual_followers:
            mutual_followers_data.append({
                'user_id': user.id,
                'username': user.username,
                'full_name': user.profile.get_full_name(),
                'avatar_url': user.profile.get_avatar_url(),
                'bio': user.profile.bio
            })
        
        return Response({
            'user_id': target_user.id,
            'username': target_user.username,
            'mutual_followers_count': len(mutual_followers_data),
            'mutual_followers': mutual_followers_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting mutual followers for user {request.user.username}: {str(e)}")
        return Response({
            'error': 'Failed to get mutual followers.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)