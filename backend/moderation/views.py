"""
Views for content moderation and flagging system.
"""

import logging
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from .models import ContentFlag, ModerationAction, ModerationSettings
from .serializers import (
    ContentFlagSerializer, ContentFlagCreateSerializer, ContentFlagReviewSerializer,
    ModerationActionSerializer, ModerationSettingsSerializer, FlagSummarySerializer
)
from posts.models import Post
from accounts.permissions import IsEditorRole, IsAdminRole
from .permissions import CanModerateFlagsPermission, CanViewFlagsPermission
from .tasks import send_flag_notification, send_moderation_notification

logger = logging.getLogger(__name__)


class FlagPagination(PageNumberPagination):
    """
    Custom pagination for flags.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class FlagPostView(APIView):
    """
    API view for flagging posts as inappropriate content.
    
    POST /api/posts/{id}/flag/ - Flag a post for moderation review
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        """
        Flag a post for moderation review.
        """
        logger.info(f"User {request.user.username} flagging post {pk}")
        
        try:
            post = get_object_or_404(Post, pk=pk)
        except Post.DoesNotExist:
            return Response(
                {'error': 'Post not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user is trying to flag their own content
        if hasattr(post, 'author_user') and post.author_user == request.user:
            return Response(
                {'error': 'You cannot flag your own content.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user has already flagged this post
        existing_flag = ContentFlag.objects.filter(post=post, flagged_by=request.user).first()
        if existing_flag:
            return Response(
                {'error': 'You have already flagged this content.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create the flag
        serializer = ContentFlagCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Set the post
            serializer.validated_data['post'] = post
            flag = serializer.save()
            
            # Send notification to moderators
            try:
                send_flag_notification.delay(flag.id)
            except Exception as e:
                logger.error(f"Failed to send flag notification: {str(e)}")
            
            # Check if auto-moderation thresholds are met
            self._check_auto_moderation(post)
            
            logger.info(f"Post {pk} flagged successfully by user {request.user.username}")
            
            # Return the created flag
            response_serializer = ContentFlagSerializer(flag, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _check_auto_moderation(self, post):
        """
        Check if post meets auto-moderation thresholds.
        """
        try:
            settings = ModerationSettings.get_settings()
            flag_count = ContentFlag.objects.filter(post=post).count()
            
            # Auto-flag for review
            if settings.should_auto_flag(flag_count):
                # Update pending flags to under_review
                ContentFlag.objects.filter(
                    post=post,
                    status='pending'
                ).update(
                    status='under_review',
                    reviewed_at=timezone.now()
                )
                logger.info(f"Post {post.id} auto-flagged for review (flag count: {flag_count})")
            
            # Auto-hide content
            if settings.should_auto_hide(flag_count):
                # This could set post status to 'hidden' or similar
                # For now, we'll just log it
                logger.warning(f"Post {post.id} should be auto-hidden (flag count: {flag_count})")
                
        except Exception as e:
            logger.error(f"Error in auto-moderation check: {str(e)}")


class ContentFlagListView(generics.ListAPIView):
    """
    API view for listing content flags for moderation review.
    
    GET /api/moderation/flags/ - List all flags (with filtering)
    """
    serializer_class = ContentFlagSerializer
    pagination_class = FlagPagination
    permission_classes = [CanViewFlagsPermission]
    
    def get_queryset(self):
        """
        Get flags based on user permissions and filters.
        """
        queryset = ContentFlag.objects.select_related(
            'post', 'flagged_by', 'reviewed_by'
        ).prefetch_related(
            'post__author_user'
        ).order_by('-created_at')
        
        # Apply filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        reason_filter = self.request.query_params.get('reason')
        if reason_filter:
            queryset = queryset.filter(reason=reason_filter)
        
        post_id_filter = self.request.query_params.get('post_id')
        if post_id_filter:
            queryset = queryset.filter(post_id=post_id_filter)
        
        reviewer_filter = self.request.query_params.get('reviewer')
        if reviewer_filter:
            queryset = queryset.filter(reviewed_by__username=reviewer_filter)
        
        # Date range filters
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """
        List flags with additional metadata.
        """
        logger.info(f"User {request.user.username} listing content flags")
        
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            
            # Add summary statistics
            response.data['summary'] = self._get_flag_summary()
            return response
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'results': serializer.data,
            'summary': self._get_flag_summary()
        })
    
    def _get_flag_summary(self):
        """
        Get summary statistics for flags.
        """
        total_flags = ContentFlag.objects.count()
        pending_flags = ContentFlag.objects.filter(status='pending').count()
        under_review_flags = ContentFlag.objects.filter(status='under_review').count()
        resolved_flags = ContentFlag.objects.filter(
            status__in=['resolved_valid', 'resolved_invalid']
        ).count()
        dismissed_flags = ContentFlag.objects.filter(status='dismissed').count()
        
        # Flags by reason
        flags_by_reason = dict(
            ContentFlag.objects.values('reason').annotate(
                count=Count('id')
            ).values_list('reason', 'count')
        )
        
        return {
            'total_flags': total_flags,
            'pending_flags': pending_flags,
            'under_review_flags': under_review_flags,
            'resolved_flags': resolved_flags,
            'dismissed_flags': dismissed_flags,
            'flags_by_reason': flags_by_reason
        }


class ContentFlagDetailView(generics.RetrieveUpdateAPIView):
    """
    API view for retrieving and updating individual content flags.
    
    GET /api/moderation/flags/{id}/ - Get flag details
    PUT /api/moderation/flags/{id}/ - Update flag (review/resolve)
    """
    queryset = ContentFlag.objects.select_related(
        'post', 'flagged_by', 'reviewed_by'
    ).prefetch_related('post__author_user')
    permission_classes = [CanModerateFlagsPermission]
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on request method.
        """
        if self.request.method in ['PUT', 'PATCH']:
            return ContentFlagReviewSerializer
        return ContentFlagSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve flag details.
        """
        instance = self.get_object()
        logger.info(f"User {request.user.username} viewing flag {instance.id}")
        
        serializer = ContentFlagSerializer(instance, context={'request': request})
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """
        Update flag status and resolution.
        """
        instance = self.get_object()
        logger.info(f"User {request.user.username} updating flag {instance.id}")
        
        # Check if user can review this flag
        if not instance.can_be_reviewed_by(request.user):
            return Response(
                {'error': 'You do not have permission to review this flag.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            updated_flag = serializer.save()
            
            # Create moderation action if flag is resolved
            if updated_flag.status in ['resolved_valid', 'resolved_invalid', 'dismissed']:
                self._create_moderation_action(updated_flag, request.user)
            
            # Send notification to content author if action was taken
            if updated_flag.status == 'resolved_valid' and updated_flag.action_taken:
                try:
                    send_moderation_notification.delay(updated_flag.id)
                except Exception as e:
                    logger.error(f"Failed to send moderation notification: {str(e)}")
            
            logger.info(f"Flag {instance.id} updated to status: {updated_flag.status}")
            
            # Return updated flag
            response_serializer = ContentFlagSerializer(updated_flag, context={'request': request})
            return Response(response_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _create_moderation_action(self, flag, moderator):
        """
        Create a moderation action record.
        """
        try:
            action_type_mapping = {
                'resolved_valid': 'content_removed' if 'removed' in flag.action_taken.lower() else 'warning_issued',
                'resolved_invalid': 'no_action',
                'dismissed': 'flag_dismissed'
            }
            
            action_type = action_type_mapping.get(flag.status, 'no_action')
            
            ModerationAction.objects.create(
                flag=flag,
                post=flag.post,
                action_type=action_type,
                moderator=moderator,
                reason=flag.resolution_notes or f"Flag {flag.status}",
                notes=f"Flag resolved as {flag.get_status_display()}",
                affected_user=flag.post.author_user if hasattr(flag.post, 'author_user') else None,
                severity_level=3 if flag.status == 'resolved_valid' else 1
            )
            
        except Exception as e:
            logger.error(f"Failed to create moderation action: {str(e)}")


class ModerationDashboardView(APIView):
    """
    API view for moderation dashboard with statistics and recent activity.
    
    GET /api/moderation/dashboard/ - Get moderation dashboard data
    """
    permission_classes = [CanViewFlagsPermission]
    
    def get(self, request):
        """
        Get moderation dashboard data.
        """
        logger.info(f"User {request.user.username} accessing moderation dashboard")
        
        # Get summary statistics
        summary = self._get_comprehensive_summary()
        
        # Get recent flags
        recent_flags = ContentFlag.objects.select_related(
            'post', 'flagged_by', 'reviewed_by'
        ).order_by('-created_at')[:10]
        
        recent_flags_serializer = ContentFlagSerializer(
            recent_flags, many=True, context={'request': request}
        )
        
        # Get recent moderation actions
        recent_actions = ModerationAction.objects.select_related(
            'flag', 'post', 'moderator', 'affected_user'
        ).order_by('-created_at')[:10]
        
        recent_actions_serializer = ModerationActionSerializer(
            recent_actions, many=True, context={'request': request}
        )
        
        return Response({
            'summary': summary,
            'recent_flags': recent_flags_serializer.data,
            'recent_actions': recent_actions_serializer.data,
            'moderation_settings': self._get_moderation_settings()
        })
    
    def _get_comprehensive_summary(self):
        """
        Get comprehensive moderation statistics.
        """
        # Flag statistics
        total_flags = ContentFlag.objects.count()
        pending_flags = ContentFlag.objects.filter(status='pending').count()
        under_review_flags = ContentFlag.objects.filter(status='under_review').count()
        resolved_valid_flags = ContentFlag.objects.filter(status='resolved_valid').count()
        resolved_invalid_flags = ContentFlag.objects.filter(status='resolved_invalid').count()
        dismissed_flags = ContentFlag.objects.filter(status='dismissed').count()
        
        # Flags by reason
        flags_by_reason = dict(
            ContentFlag.objects.values('reason').annotate(
                count=Count('id')
            ).values_list('reason', 'count')
        )
        
        # Recent activity (last 7 days)
        from datetime import timedelta
        week_ago = timezone.now() - timedelta(days=7)
        recent_flags = ContentFlag.objects.filter(created_at__gte=week_ago).count()
        recent_actions = ModerationAction.objects.filter(created_at__gte=week_ago).count()
        
        # Posts with multiple flags
        posts_with_multiple_flags = ContentFlag.objects.values('post').annotate(
            flag_count=Count('id')
        ).filter(flag_count__gt=1).count()
        
        return {
            'total_flags': total_flags,
            'pending_flags': pending_flags,
            'under_review_flags': under_review_flags,
            'resolved_valid_flags': resolved_valid_flags,
            'resolved_invalid_flags': resolved_invalid_flags,
            'dismissed_flags': dismissed_flags,
            'flags_by_reason': flags_by_reason,
            'recent_flags_7_days': recent_flags,
            'recent_actions_7_days': recent_actions,
            'posts_with_multiple_flags': posts_with_multiple_flags
        }
    
    def _get_moderation_settings(self):
        """
        Get current moderation settings.
        """
        settings_obj = ModerationSettings.get_settings()
        serializer = ModerationSettingsSerializer(settings_obj)
        return serializer.data


class ModerationSettingsView(generics.RetrieveUpdateAPIView):
    """
    API view for managing moderation settings.
    
    GET /api/moderation/settings/ - Get current settings
    PUT /api/moderation/settings/ - Update settings
    """
    permission_classes = [IsAdminRole]
    serializer_class = ModerationSettingsSerializer
    
    def get_object(self):
        """
        Get the moderation settings singleton.
        """
        return ModerationSettings.get_settings()
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve moderation settings.
        """
        logger.info(f"User {request.user.username} retrieving moderation settings")
        return super().retrieve(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """
        Update moderation settings.
        """
        logger.info(f"User {request.user.username} updating moderation settings")
        return super().update(request, *args, **kwargs)


@api_view(['GET'])
@permission_classes([CanViewFlagsPermission])
def flag_statistics(request):
    """
    Get flag statistics for dashboard widgets.
    
    GET /api/moderation/statistics/ - Get flag statistics
    """
    logger.info(f"User {request.user.username} requesting flag statistics")
    
    try:
        from django.db.models import Count, Q
        from datetime import timedelta
        
        # Basic counts
        total_flags = ContentFlag.objects.count()
        pending_flags = ContentFlag.objects.filter(status='pending').count()
        under_review_flags = ContentFlag.objects.filter(status='under_review').count()
        resolved_flags = ContentFlag.objects.filter(
            status__in=['resolved_valid', 'resolved_invalid']
        ).count()
        
        # Recent activity (last 24 hours)
        yesterday = timezone.now() - timedelta(days=1)
        recent_flags = ContentFlag.objects.filter(created_at__gte=yesterday).count()
        
        # Flags by reason
        flags_by_reason = dict(
            ContentFlag.objects.values('reason').annotate(
                count=Count('id')
            ).values_list('reason', 'count')
        )
        
        # Top flagged posts
        top_flagged_posts = list(
            ContentFlag.objects.values('post__id', 'post__title')
            .annotate(flag_count=Count('id'))
            .order_by('-flag_count')[:5]
        )
        
        # Most active moderators (last 30 days)
        month_ago = timezone.now() - timedelta(days=30)
        active_moderators = list(
            ContentFlag.objects.filter(
                reviewed_at__gte=month_ago,
                reviewed_by__isnull=False
            ).values('reviewed_by__username')
            .annotate(reviews=Count('id'))
            .order_by('-reviews')[:5]
        )
        
        statistics = {
            'total_flags': total_flags,
            'pending_flags': pending_flags,
            'under_review_flags': under_review_flags,
            'resolved_flags': resolved_flags,
            'recent_flags_24h': recent_flags,
            'flags_by_reason': flags_by_reason,
            'top_flagged_posts': top_flagged_posts,
            'active_moderators': active_moderators,
            'generated_at': timezone.now().isoformat()
        }
        
        return Response(statistics)
    
    except Exception as e:
        logger.error(f"Error generating flag statistics: {str(e)}")
        return Response(
            {'error': 'Failed to generate statistics'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )