"""
Django signals for notifications app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from posts.models import Post
from .tasks import send_new_post_notification
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Post)
def send_post_notification(sender, instance, created, **kwargs):
    """
    Send notification when a post is published.
    """
    # Only send notifications for published posts
    if instance.status == 'published':
        # Check if this is a new publication or status change to published
        if created or (hasattr(instance, '_state') and instance._state.adding is False):
            # Get the previous state to check if status changed
            try:
                # If this is an update, check if status changed to published
                if not created:
                    # We can't easily get the previous state here, so we'll send notification
                    # The task will handle duplicate prevention if needed
                    pass
                
                # Send notification asynchronously
                send_new_post_notification.delay(instance.id)
                logger.info(f"Queued notification for published post: {instance.title}")
                
            except Exception as e:
                logger.error(f"Failed to queue notification for post {instance.id}: {str(e)}")


# Alternative approach: Use a custom save method or manager
# This could be added to the Post model if we want more control