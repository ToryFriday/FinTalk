"""
Celery tasks for content moderation system.
Handles automated notifications and moderation workflows.
"""

import logging
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_flag_notification(self, flag_id):
    """
    Send notification to moderators when content is flagged.
    
    Args:
        flag_id: ID of the ContentFlag instance
    """
    try:
        from .models import ContentFlag, ModerationSettings
        
        # Get the flag
        try:
            flag = ContentFlag.objects.select_related(
                'post', 'flagged_by', 'post__author_user'
            ).get(id=flag_id)
        except ContentFlag.DoesNotExist:
            logger.error(f"ContentFlag with id {flag_id} not found")
            return
        
        # Check if notifications are enabled
        settings_obj = ModerationSettings.get_settings()
        if not settings_obj.notify_moderators_on_flag:
            logger.info(f"Flag notifications disabled, skipping notification for flag {flag_id}")
            return
        
        # Get moderators (users with editor or admin roles)
        moderators = []
        
        # Get users with moderation permissions
        try:
            # Try to get users with roles first
            from accounts.models import UserRole
            moderator_roles = UserRole.objects.filter(
                role__name__in=['admin', 'editor']
            ).select_related('user')
            moderators.extend([ur.user for ur in moderator_roles if ur.user.is_active])
        except ImportError:
            # Fallback to Django permissions
            moderators = User.objects.filter(
                is_active=True,
                groups__permissions__codename='can_moderate_content'
            ).distinct()
        
        # Also include superusers
        superusers = User.objects.filter(is_superuser=True, is_active=True)
        moderators.extend(superusers)
        
        # Remove duplicates
        moderators = list(set(moderators))
        
        if not moderators:
            logger.warning("No moderators found to notify about flag")
            return
        
        # Prepare email context
        context = {
            'flag': flag,
            'post': flag.post,
            'flagged_by': flag.flagged_by,
            'reason': flag.get_reason_display(),
            'description': flag.description,
            'post_url': f"{settings.FRONTEND_URL}/posts/{flag.post.id}",
            'moderation_url': f"{settings.FRONTEND_URL}/moderation/flags/{flag.id}",
            'site_name': getattr(settings, 'SITE_NAME', 'FinTalk'),
        }
        
        # Render email templates
        subject = f"Content Flagged for Review - {flag.post.title}"
        html_message = render_to_string('moderation/flag_notification.html', context)
        text_message = render_to_string('moderation/flag_notification.txt', context)
        
        # Send emails to moderators
        moderator_emails = [mod.email for mod in moderators if mod.email]
        
        if moderator_emails:
            try:
                send_mail(
                    subject=subject,
                    message=text_message,
                    html_message=html_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=moderator_emails,
                    fail_silently=False
                )
                
                logger.info(f"Flag notification sent to {len(moderator_emails)} moderators for flag {flag_id}")
                
            except Exception as e:
                logger.error(f"Failed to send flag notification email: {str(e)}")
                # Retry the task
                raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        else:
            logger.warning("No moderator email addresses found")
    
    except Exception as e:
        logger.error(f"Error in send_flag_notification task: {str(e)}")
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3)
def send_moderation_notification(self, flag_id):
    """
    Send notification to content author when moderation action is taken.
    
    Args:
        flag_id: ID of the ContentFlag instance
    """
    try:
        from .models import ContentFlag, ModerationSettings
        
        # Get the flag
        try:
            flag = ContentFlag.objects.select_related(
                'post', 'flagged_by', 'reviewed_by', 'post__author_user'
            ).get(id=flag_id)
        except ContentFlag.DoesNotExist:
            logger.error(f"ContentFlag with id {flag_id} not found")
            return
        
        # Check if notifications are enabled
        settings_obj = ModerationSettings.get_settings()
        if not settings_obj.notify_author_on_action:
            logger.info(f"Author notifications disabled, skipping notification for flag {flag_id}")
            return
        
        # Get the content author
        author = None
        if hasattr(flag.post, 'author_user') and flag.post.author_user:
            author = flag.post.author_user
        
        if not author or not author.email:
            logger.warning(f"No author or author email found for post {flag.post.id}")
            return
        
        # Only notify for resolved valid flags (where action was taken)
        if flag.status != 'resolved_valid':
            logger.info(f"Flag {flag_id} not resolved as valid, skipping author notification")
            return
        
        # Prepare email context
        context = {
            'flag': flag,
            'post': flag.post,
            'author': author,
            'moderator': flag.reviewed_by,
            'reason': flag.get_reason_display(),
            'resolution_notes': flag.resolution_notes,
            'action_taken': flag.action_taken,
            'post_url': f"{settings.FRONTEND_URL}/posts/{flag.post.id}",
            'site_name': getattr(settings, 'SITE_NAME', 'FinTalk'),
        }
        
        # Render email templates
        subject = f"Moderation Action Taken - {flag.post.title}"
        html_message = render_to_string('moderation/moderation_notification.html', context)
        text_message = render_to_string('moderation/moderation_notification.txt', context)
        
        # Send email to author
        try:
            send_mail(
                subject=subject,
                message=text_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[author.email],
                fail_silently=False
            )
            
            logger.info(f"Moderation notification sent to author {author.email} for flag {flag_id}")
            
        except Exception as e:
            logger.error(f"Failed to send moderation notification email: {str(e)}")
            # Retry the task
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
    
    except Exception as e:
        logger.error(f"Error in send_moderation_notification task: {str(e)}")
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@shared_task
def auto_moderate_flagged_content():
    """
    Periodic task to check for content that should be auto-moderated.
    This task runs periodically to check flagging thresholds.
    """
    try:
        from .models import ContentFlag, ModerationSettings
        from django.db.models import Count
        
        logger.info("Running auto-moderation check")
        
        settings_obj = ModerationSettings.get_settings()
        
        # Find posts with multiple flags that haven't been reviewed
        flagged_posts = ContentFlag.objects.filter(
            status='pending'
        ).values('post').annotate(
            flag_count=Count('id')
        ).filter(
            flag_count__gte=settings_obj.auto_flag_threshold
        )
        
        auto_flagged_count = 0
        auto_hidden_count = 0
        
        for post_data in flagged_posts:
            post_id = post_data['post']
            flag_count = post_data['flag_count']
            
            # Auto-flag for review
            if flag_count >= settings_obj.auto_flag_threshold:
                ContentFlag.objects.filter(
                    post_id=post_id,
                    status='pending'
                ).update(
                    status='under_review',
                    reviewed_at=timezone.now()
                )
                auto_flagged_count += 1
                
                logger.info(f"Auto-flagged post {post_id} for review (flag count: {flag_count})")
            
            # Auto-hide content if threshold is met
            if flag_count >= settings_obj.auto_hide_threshold:
                # For now, we'll just log this. In a full implementation,
                # you might want to set the post status to 'hidden' or similar
                logger.warning(f"Post {post_id} should be auto-hidden (flag count: {flag_count})")
                auto_hidden_count += 1
        
        logger.info(f"Auto-moderation complete: {auto_flagged_count} posts flagged, {auto_hidden_count} posts should be hidden")
        
        return {
            'auto_flagged': auto_flagged_count,
            'auto_hidden': auto_hidden_count
        }
    
    except Exception as e:
        logger.error(f"Error in auto_moderate_flagged_content task: {str(e)}")
        raise


@shared_task
def cleanup_old_flags():
    """
    Periodic task to clean up old resolved flags.
    Removes flags older than a specified period to keep the database clean.
    """
    try:
        from .models import ContentFlag
        from datetime import timedelta
        
        # Remove resolved flags older than 6 months
        cutoff_date = timezone.now() - timedelta(days=180)
        
        old_flags = ContentFlag.objects.filter(
            status__in=['resolved_valid', 'resolved_invalid', 'dismissed'],
            reviewed_at__lt=cutoff_date
        )
        
        count = old_flags.count()
        old_flags.delete()
        
        logger.info(f"Cleaned up {count} old resolved flags")
        
        return {'cleaned_up': count}
    
    except Exception as e:
        logger.error(f"Error in cleanup_old_flags task: {str(e)}")
        raise


@shared_task
def generate_moderation_report():
    """
    Generate periodic moderation reports for administrators.
    """
    try:
        from .models import ContentFlag, ModerationAction
        from datetime import timedelta
        
        # Generate report for the last week
        week_ago = timezone.now() - timedelta(days=7)
        
        # Flag statistics
        total_flags = ContentFlag.objects.filter(created_at__gte=week_ago).count()
        pending_flags = ContentFlag.objects.filter(
            created_at__gte=week_ago,
            status='pending'
        ).count()
        resolved_flags = ContentFlag.objects.filter(
            created_at__gte=week_ago,
            status__in=['resolved_valid', 'resolved_invalid']
        ).count()
        
        # Action statistics
        total_actions = ModerationAction.objects.filter(created_at__gte=week_ago).count()
        
        # Top flagged reasons
        from django.db.models import Count
        top_reasons = list(
            ContentFlag.objects.filter(created_at__gte=week_ago)
            .values('reason')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        
        report_data = {
            'period': 'Last 7 days',
            'total_flags': total_flags,
            'pending_flags': pending_flags,
            'resolved_flags': resolved_flags,
            'total_actions': total_actions,
            'top_reasons': top_reasons,
            'generated_at': timezone.now().isoformat()
        }
        
        logger.info(f"Generated moderation report: {report_data}")
        
        # Here you could send this report via email to administrators
        # or store it in a database for later retrieval
        
        return report_data
    
    except Exception as e:
        logger.error(f"Error in generate_moderation_report task: {str(e)}")
        raise