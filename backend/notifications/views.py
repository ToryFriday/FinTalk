"""
API views for notifications app.
"""

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from django.utils import timezone
from django.contrib.auth.models import User
from django.http import Http404
from .models import EmailSubscription, NotificationLog, UnsubscribeRequest
from .serializers import (
    EmailSubscriptionSerializer,
    EmailSubscriptionCreateSerializer,
    NotificationLogSerializer,
    UnsubscribeSerializer,
    SubscriptionStatsSerializer,
    AuthorSubscriptionSerializer
)
from .tasks import send_subscription_confirmation
import logging

logger = logging.getLogger(__name__)


class EmailSubscriptionListCreateView(generics.ListCreateAPIView):
    """
    List and create email subscriptions.
    GET: List user's subscriptions (authenticated) or all subscriptions (admin)
    POST: Create new subscription
    """
    serializer_class = EmailSubscriptionSerializer
    permission_classes = [permissions.AllowAny]  # Allow anonymous subscriptions
    
    def get_queryset(self):
        """
        Return subscriptions based on user permissions.
        """
        if self.request.user.is_authenticated:
            if self.request.user.is_staff:
                # Staff can see all subscriptions
                return EmailSubscription.objects.all().select_related('user', 'author_filter')
            else:
                # Regular users can only see their own subscriptions
                return EmailSubscription.objects.filter(
                    Q(user=self.request.user) | Q(email=self.request.user.email.lower())
                ).select_related('user', 'author_filter')
        else:
            # Anonymous users cannot list subscriptions
            return EmailSubscription.objects.none()
    
    def get_serializer_class(self):
        """
        Use different serializers for different actions.
        """
        if self.request.method == 'POST':
            return EmailSubscriptionCreateSerializer
        return EmailSubscriptionSerializer
    
    def perform_create(self, serializer):
        """
        Create subscription and send confirmation email.
        """
        # Set user if authenticated
        if self.request.user.is_authenticated:
            serializer.validated_data['user'] = self.request.user
            if not serializer.validated_data.get('email'):
                serializer.validated_data['email'] = self.request.user.email.lower()
        
        subscription = serializer.save()
        
        # Send confirmation email asynchronously
        send_subscription_confirmation.delay(subscription.id)
        
        logger.info(f"New subscription created: {subscription.email} - {subscription.subscription_type}")


class EmailSubscriptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a specific email subscription.
    """
    serializer_class = EmailSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Users can only access their own subscriptions, staff can access all.
        """
        if self.request.user.is_staff:
            return EmailSubscription.objects.all().select_related('user', 'author_filter')
        else:
            return EmailSubscription.objects.filter(
                Q(user=self.request.user) | Q(email=self.request.user.email.lower())
            ).select_related('user', 'author_filter')


class PublicSubscribeView(APIView):
    """
    Public endpoint for creating email subscriptions (no authentication required).
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        Create a new email subscription.
        """
        serializer = EmailSubscriptionCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Check for existing subscription
            email = serializer.validated_data['email']
            subscription_type = serializer.validated_data['subscription_type']
            author_filter = serializer.validated_data.get('author_filter')
            
            existing_subscription = EmailSubscription.objects.filter(
                email=email,
                subscription_type=subscription_type,
                author_filter=author_filter
            ).first()
            
            if existing_subscription:
                if existing_subscription.is_active:
                    return Response(
                        {'detail': 'You are already subscribed to this type of notification.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    # Reactivate existing subscription
                    existing_subscription.is_active = True
                    existing_subscription.save()
                    send_subscription_confirmation.delay(existing_subscription.id)
                    return Response(
                        {'detail': 'Your subscription has been reactivated.'},
                        status=status.HTTP_200_OK
                    )
            
            # Create new subscription
            subscription = serializer.save()
            send_subscription_confirmation.delay(subscription.id)
            
            return Response(
                {'detail': 'Subscription created successfully. Please check your email for confirmation.'},
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UnsubscribeView(APIView):
    """
    Handle unsubscribe requests using tokens.
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, token):
        """
        Get subscription details for unsubscribe confirmation.
        """
        try:
            subscription = EmailSubscription.objects.get(
                unsubscribe_token=token,
                is_active=True
            )
            serializer = EmailSubscriptionSerializer(subscription)
            return Response(serializer.data)
        except EmailSubscription.DoesNotExist:
            return Response(
                {'detail': 'Invalid or expired unsubscribe token.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def post(self, request, token):
        """
        Process unsubscribe request.
        """
        serializer = UnsubscribeSerializer(data={**request.data, 'token': token})
        if serializer.is_valid():
            try:
                subscription = EmailSubscription.objects.get(
                    unsubscribe_token=token,
                    is_active=True
                )
                
                # Create unsubscribe request record
                UnsubscribeRequest.objects.create(
                    email=subscription.email,
                    subscription_type=subscription.subscription_type,
                    reason=serializer.validated_data.get('reason'),
                    feedback=serializer.validated_data.get('feedback'),
                    unsubscribe_token=token,
                    ip_address=self._get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                # Deactivate subscription
                subscription.is_active = False
                subscription.save()
                
                logger.info(f"Unsubscribed: {subscription.email} from {subscription.subscription_type}")
                
                return Response(
                    {'detail': 'You have been successfully unsubscribed.'},
                    status=status.HTTP_200_OK
                )
                
            except EmailSubscription.DoesNotExist:
                return Response(
                    {'detail': 'Invalid or expired unsubscribe token.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_client_ip(self, request):
        """
        Get client IP address from request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class NotificationLogListView(generics.ListAPIView):
    """
    List notification logs (admin only).
    """
    serializer_class = NotificationLogSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        """
        Return notification logs with optional filtering.
        """
        queryset = NotificationLog.objects.all().select_related('subscription', 'post')
        
        # Filter by subscription email
        email = self.request.query_params.get('email')
        if email:
            queryset = queryset.filter(subscription__email__icontains=email)
        
        # Filter by notification type
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-created_at')


class SubscriptionStatsView(APIView):
    """
    Get subscription statistics (admin only).
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """
        Return subscription statistics.
        """
        # Basic counts
        total_subscriptions = EmailSubscription.objects.count()
        active_subscriptions = EmailSubscription.objects.filter(is_active=True).count()
        inactive_subscriptions = total_subscriptions - active_subscriptions
        
        # Subscriptions by type
        subscriptions_by_type = dict(
            EmailSubscription.objects.filter(is_active=True)
            .values('subscription_type')
            .annotate(count=Count('id'))
            .values_list('subscription_type', 'count')
        )
        
        # Recent activity (last 7 days)
        week_ago = timezone.now() - timezone.timedelta(days=7)
        recent_subscriptions = EmailSubscription.objects.filter(
            created_at__gte=week_ago
        ).count()
        recent_unsubscribes = UnsubscribeRequest.objects.filter(
            created_at__gte=week_ago
        ).count()
        
        data = {
            'total_subscriptions': total_subscriptions,
            'active_subscriptions': active_subscriptions,
            'inactive_subscriptions': inactive_subscriptions,
            'subscriptions_by_type': subscriptions_by_type,
            'recent_subscriptions': recent_subscriptions,
            'recent_unsubscribes': recent_unsubscribes,
        }
        
        serializer = SubscriptionStatsSerializer(data)
        return Response(serializer.data)


class AuthorSubscribersView(generics.ListAPIView):
    """
    List authors and their subscriber counts.
    """
    serializer_class = AuthorSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Return authors with their subscriber counts.
        """
        return (
            EmailSubscription.objects
            .filter(is_active=True, subscription_type='author_posts')
            .values('author_filter')
            .annotate(subscriber_count=Count('id'))
            .select_related('author_filter')
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_subscription(request, author_id):
    """
    Toggle subscription to a specific author.
    """
    try:
        author = User.objects.get(id=author_id)
    except User.DoesNotExist:
        return Response(
            {'detail': 'Author not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    user_email = request.user.email.lower()
    
    # Check if subscription exists
    subscription = EmailSubscription.objects.filter(
        email=user_email,
        subscription_type='author_posts',
        author_filter=author
    ).first()
    
    if subscription:
        # Toggle existing subscription
        subscription.is_active = not subscription.is_active
        subscription.save()
        action = 'subscribed' if subscription.is_active else 'unsubscribed'
    else:
        # Create new subscription
        subscription = EmailSubscription.objects.create(
            user=request.user,
            email=user_email,
            subscription_type='author_posts',
            author_filter=author
        )
        send_subscription_confirmation.delay(subscription.id)
        action = 'subscribed'
    
    return Response({
        'detail': f'Successfully {action} to {author.username}.',
        'is_subscribed': subscription.is_active
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_author_subscription(request, author_id):
    """
    Check if user is subscribed to a specific author.
    """
    try:
        author = User.objects.get(id=author_id)
    except User.DoesNotExist:
        return Response(
            {'detail': 'Author not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    is_subscribed = EmailSubscription.objects.filter(
        email=request.user.email.lower(),
        subscription_type='author_posts',
        author_filter=author,
        is_active=True
    ).exists()
    
    return Response({
        'is_subscribed': is_subscribed,
        'author_id': author_id,
        'author_username': author.username
    })