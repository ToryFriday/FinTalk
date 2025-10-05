"""
Celery tasks for email notifications.
"""

from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q
from posts.models import Post
from .models import EmailSubscription, NotificationLog
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_new_post_notification(post_id):
    """
    Celery task to send new post notifications to all relevant subscribers.
    """
    try:
        post = Post.objects.get(id=post_id, status='published')
        
        # Get all active subscriptions that should receive this notification
        subscriptions = EmailSubscription.objects.filter(
            is_active=True
        ).select_related('user', 'author_filter')
        
        # Filter subscriptions based on their type and the post
        relevant_subscriptions = []
        for subscription in subscriptions:
            if subscription.matches_post(post) and subscription.can_receive_notification():
                relevant_subscriptions.append(subscription)
        
        if not relevant_subscriptions:
            logger.info(f"No relevant subscriptions found for post {post_id}")
            return f"No subscribers for post: {post.title}"
        
        # Send notifications in batches to avoid overwhelming the email server
        batch_size = 50
        total_sent = 0
        total_failed = 0
        
        for i in range(0, len(relevant_subscriptions), batch_size):
            batch = relevant_subscriptions[i:i + batch_size]
            sent, failed = _send_notification_batch(post, batch, 'new_post')
            total_sent += sent
            total_failed += failed
        
        logger.info(f"New post notification for '{post.title}': {total_sent} sent, {total_failed} failed")
        return f"Sent {total_sent} notifications, {total_failed} failed for post: {post.title}"
        
    except Post.DoesNotExist:
        logger.error(f"Post with ID {post_id} does not exist or is not published")
        return f"Post with ID {post_id} not found or not published"
    except Exception as e:
        logger.error(f"Failed to send new post notifications for post {post_id}: {str(e)}")
        raise e


@shared_task
def send_weekly_digest():
    """
    Celery task to send weekly digest emails to subscribers.
    """
    try:
        # Get posts from the last week
        one_week_ago = timezone.now() - timezone.timedelta(days=7)
        recent_posts = Post.objects.filter(
            status='published',
            created_at__gte=one_week_ago
        ).order_by('-created_at')[:10]  # Top 10 posts from last week
        
        if not recent_posts:
            logger.info("No posts from the last week for weekly digest")
            return "No posts from the last week"
        
        # Get weekly digest subscribers
        subscriptions = EmailSubscription.objects.filter(
            is_active=True,
            subscription_type='weekly_digest'
        ).select_related('user')
        
        if not subscriptions:
            logger.info("No weekly digest subscribers found")
            return "No weekly digest subscribers"
        
        # Send digest emails in batches
        batch_size = 50
        total_sent = 0
        total_failed = 0
        
        for i in range(0, len(subscriptions), batch_size):
            batch = list(subscriptions[i:i + batch_size])
            sent, failed = _send_digest_batch(recent_posts, batch)
            total_sent += sent
            total_failed += failed
        
        logger.info(f"Weekly digest: {total_sent} sent, {total_failed} failed")
        return f"Weekly digest: {total_sent} sent, {total_failed} failed"
        
    except Exception as e:
        logger.error(f"Failed to send weekly digest: {str(e)}")
        raise e


@shared_task
def send_subscription_confirmation(subscription_id):
    """
    Celery task to send subscription confirmation email.
    """
    try:
        subscription = EmailSubscription.objects.get(id=subscription_id)
        
        # Create notification log
        log = NotificationLog.objects.create(
            subscription=subscription,
            notification_type='subscription_confirmation',
            subject='Welcome to FinTalk Notifications!'
        )
        
        try:
            # Prepare email context
            context = {
                'subscriber_name': subscription.get_subscriber_name(),
                'subscription_type': subscription.get_subscription_type_display(),
                'unsubscribe_url': _get_unsubscribe_url(subscription.unsubscribe_token),
                'site_name': 'FinTalk',
                'site_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:3000'),
            }
            
            # Render email templates
            html_message = render_to_string('notifications/subscription_confirmation.html', context)
            plain_message = strip_tags(html_message)
            
            # Send email
            send_mail(
                subject=log.subject,
                message=plain_message,
                from_email=_get_from_email(),
                recipient_list=[subscription.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            # Mark as sent
            log.mark_as_sent()
            subscription.update_last_notification_sent()
            
            logger.info(f"Subscription confirmation sent to {subscription.email}")
            return f"Confirmation sent to {subscription.email}"
            
        except Exception as e:
            log.mark_as_failed(str(e))
            raise e
            
    except EmailSubscription.DoesNotExist:
        logger.error(f"EmailSubscription with ID {subscription_id} does not exist")
        return f"Subscription with ID {subscription_id} not found"
    except Exception as e:
        logger.error(f"Failed to send subscription confirmation for {subscription_id}: {str(e)}")
        raise e


@shared_task
def cleanup_old_notification_logs(days=30):
    """
    Celery task to clean up old notification logs.
    """
    try:
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        deleted_count, _ = NotificationLog.objects.filter(
            created_at__lt=cutoff_date
        ).delete()
        
        logger.info(f"Cleaned up {deleted_count} old notification logs")
        return f"Cleaned up {deleted_count} old notification logs"
        
    except Exception as e:
        logger.error(f"Failed to cleanup old notification logs: {str(e)}")
        raise e


def _send_notification_batch(post, subscriptions, notification_type):
    """
    Helper function to send a batch of notifications.
    """
    sent_count = 0
    failed_count = 0
    
    for subscription in subscriptions:
        log = NotificationLog.objects.create(
            subscription=subscription,
            notification_type=notification_type,
            subject=f'New Post: {post.title}',
            post=post
        )
        
        try:
            # Prepare email context
            context = {
                'subscriber_name': subscription.get_subscriber_name(),
                'post': post,
                'post_url': _get_post_url(post),
                'unsubscribe_url': _get_unsubscribe_url(subscription.unsubscribe_token),
                'site_name': 'FinTalk',
                'site_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:3000'),
            }
            
            # Render email templates
            html_message = render_to_string('notifications/new_post_notification.html', context)
            plain_message = strip_tags(html_message)
            
            # Send email
            send_mail(
                subject=log.subject,
                message=plain_message,
                from_email=_get_from_email(),
                recipient_list=[subscription.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            # Mark as sent
            log.mark_as_sent()
            subscription.update_last_notification_sent()
            sent_count += 1
            
        except Exception as e:
            log.mark_as_failed(str(e))
            failed_count += 1
            logger.error(f"Failed to send notification to {subscription.email}: {str(e)}")
    
    return sent_count, failed_count


def _send_digest_batch(posts, subscriptions):
    """
    Helper function to send a batch of weekly digest emails.
    """
    sent_count = 0
    failed_count = 0
    
    for subscription in subscriptions:
        log = NotificationLog.objects.create(
            subscription=subscription,
            notification_type='weekly_digest',
            subject='FinTalk Weekly Digest'
        )
        
        try:
            # Prepare email context
            context = {
                'subscriber_name': subscription.get_subscriber_name(),
                'posts': posts,
                'week_start': timezone.now() - timezone.timedelta(days=7),
                'week_end': timezone.now(),
                'unsubscribe_url': _get_unsubscribe_url(subscription.unsubscribe_token),
                'site_name': 'FinTalk',
                'site_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:3000'),
            }
            
            # Render email templates
            html_message = render_to_string('notifications/weekly_digest.html', context)
            plain_message = strip_tags(html_message)
            
            # Send email
            send_mail(
                subject=log.subject,
                message=plain_message,
                from_email=_get_from_email(),
                recipient_list=[subscription.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            # Mark as sent
            log.mark_as_sent()
            subscription.update_last_notification_sent()
            sent_count += 1
            
        except Exception as e:
            log.mark_as_failed(str(e))
            failed_count += 1
            logger.error(f"Failed to send digest to {subscription.email}: {str(e)}")
    
    return sent_count, failed_count


def _get_from_email():
    """
    Get the from email address for notifications.
    """
    return getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@fintalk.com')


def _get_post_url(post):
    """
    Get the full URL for a post.
    """
    base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    return f"{base_url}/posts/{post.id}"


def _get_unsubscribe_url(token):
    """
    Get the unsubscribe URL for a token.
    """
    base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    return f"{base_url}/unsubscribe/{token}"