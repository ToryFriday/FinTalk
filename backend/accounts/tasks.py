"""
Celery tasks for accounts app.
"""

from celery import shared_task
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_verification_email(user_id):
    """
    Celery task to send email verification.
    """
    try:
        user = User.objects.get(id=user_id)
        profile = user.profile
        
        # Generate verification URL
        verification_url = f"{settings.FRONTEND_URL}/verify-email/{profile.email_verification_token}" if hasattr(settings, 'FRONTEND_URL') else f"http://localhost:3000/verify-email/{profile.email_verification_token}"
        
        # Email context
        context = {
            'user': user,
            'verification_url': verification_url,
            'site_name': 'FinTalk',
        }
        
        # Render email templates
        html_message = render_to_string('accounts/verification_email.html', context)
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject='Verify your FinTalk account',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@fintalk.com',
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Verification email sent successfully to {user.email}")
        return f"Verification email sent to {user.email}"
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} does not exist")
        return f"User with ID {user_id} not found"
    except Exception as e:
        logger.error(f"Failed to send verification email to user {user_id}: {str(e)}")
        raise e


@shared_task
def cleanup_expired_tokens():
    """
    Celery task to clean up expired email verification tokens.
    """
    try:
        from .models import UserProfile
        
        # Find profiles with expired tokens (older than 24 hours)
        expired_time = timezone.now() - timezone.timedelta(hours=24)
        expired_profiles = UserProfile.objects.filter(
            email_verification_sent_at__lt=expired_time,
            is_email_verified=False,
            email_verification_token__isnull=False
        ).exclude(email_verification_token='')
        
        count = expired_profiles.count()
        
        # Clear expired tokens
        expired_profiles.update(
            email_verification_token='',
            email_verification_sent_at=None
        )
        
        logger.info(f"Cleaned up {count} expired verification tokens")
        return f"Cleaned up {count} expired tokens"
        
    except Exception as e:
        logger.error(f"Failed to cleanup expired tokens: {str(e)}")
        raise e


@shared_task
def send_welcome_email(user_id):
    """
    Celery task to send welcome email after successful verification.
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Email context
        context = {
            'user': user,
            'site_name': 'FinTalk',
            'login_url': f"{settings.FRONTEND_URL}/login" if hasattr(settings, 'FRONTEND_URL') else "http://localhost:3000/login",
        }
        
        # Render email templates
        html_message = render_to_string('accounts/welcome_email.html', context)
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject='Welcome to FinTalk!',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@fintalk.com',
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Welcome email sent successfully to {user.email}")
        return f"Welcome email sent to {user.email}"
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} does not exist")
        return f"User with ID {user_id} not found"
    except Exception as e:
        logger.error(f"Failed to send welcome email to user {user_id}: {str(e)}")
        raise e

@shared_task
def send_new_follower_notification(follower_id, following_id):
    """
    Celery task to send notification when someone follows a user.
    """
    try:
        follower = User.objects.get(id=follower_id)
        following = User.objects.get(id=following_id)
        
        # Email context
        context = {
            'follower': follower,
            'following': following,
            'site_name': 'FinTalk',
            'profile_url': f"{settings.FRONTEND_URL}/users/{follower.id}" if hasattr(settings, 'FRONTEND_URL') else f"http://localhost:3000/users/{follower.id}",
            'followers_url': f"{settings.FRONTEND_URL}/users/{following.id}/followers" if hasattr(settings, 'FRONTEND_URL') else f"http://localhost:3000/users/{following.id}/followers",
        }
        
        # Render email templates
        html_message = render_to_string('accounts/new_follower_notification.html', context)
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=f'{follower.profile.get_full_name()} is now following you on FinTalk',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@fintalk.com',
            recipient_list=[following.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"New follower notification sent to {following.email} about {follower.username}")
        return f"New follower notification sent to {following.email}"
        
    except User.DoesNotExist:
        logger.error(f"User not found - follower_id: {follower_id}, following_id: {following_id}")
        return "User not found"
    except Exception as e:
        logger.error(f"Failed to send new follower notification: {str(e)}")
        raise e


@shared_task
def send_new_post_notification_to_followers(post_id):
    """
    Celery task to send notifications to followers when a user publishes a new post.
    """
    try:
        from posts.models import Post
        from .models import UserFollow
        
        post = Post.objects.get(id=post_id)
        author = post.author_user
        
        if not author:
            logger.warning(f"Post {post_id} has no author_user, skipping follower notifications")
            return "No author found for post"
        
        # Get all followers of the post author
        followers = User.objects.filter(
            following__following=author,
            is_active=True
        ).distinct()
        
        notification_count = 0
        
        for follower in followers:
            try:
                # Email context
                context = {
                    'follower': follower,
                    'author': author,
                    'post': post,
                    'site_name': 'FinTalk',
                    'post_url': f"{settings.FRONTEND_URL}/posts/{post.id}" if hasattr(settings, 'FRONTEND_URL') else f"http://localhost:3000/posts/{post.id}",
                    'author_url': f"{settings.FRONTEND_URL}/users/{author.id}" if hasattr(settings, 'FRONTEND_URL') else f"http://localhost:3000/users/{author.id}",
                    'unsubscribe_url': f"{settings.FRONTEND_URL}/unsubscribe" if hasattr(settings, 'FRONTEND_URL') else "http://localhost:3000/unsubscribe",
                }
                
                # Render email templates
                html_message = render_to_string('accounts/new_post_notification.html', context)
                plain_message = strip_tags(html_message)
                
                # Send email
                send_mail(
                    subject=f'New post from {author.profile.get_full_name()}: {post.title}',
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@fintalk.com',
                    recipient_list=[follower.email],
                    html_message=html_message,
                    fail_silently=True,  # Don't fail the entire task if one email fails
                )
                
                notification_count += 1
                
            except Exception as e:
                logger.error(f"Failed to send new post notification to {follower.email}: {str(e)}")
                continue
        
        logger.info(f"New post notifications sent to {notification_count} followers for post {post_id}")
        return f"Notifications sent to {notification_count} followers"
        
    except Exception as e:
        logger.error(f"Failed to send new post notifications for post {post_id}: {str(e)}")
        raise e