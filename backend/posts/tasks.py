"""
Celery tasks for posts app.
"""

from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@shared_task
def publish_scheduled_posts():
    """
    Celery task to publish posts that are scheduled for publication.
    This task will be called periodically by Celery Beat.
    """
    from .models import Post
    
    try:
        # Find posts that are scheduled and ready to be published
        now = timezone.now()
        scheduled_posts = Post.objects.filter(
            status='scheduled',
            scheduled_publish_date__lte=now
        )
        
        published_count = 0
        for post in scheduled_posts:
            try:
                # Use the model's publish method for consistency
                post.publish()
                published_count += 1
                logger.info(f"Published scheduled post: {post.title} (ID: {post.id})")
                
                # Queue notification task for new post (will be implemented in later tasks)
                send_new_post_notification.delay(post.id)
                
            except Exception as post_error:
                logger.error(f"Error publishing individual post {post.id}: {str(post_error)}")
                continue
        
        logger.info(f"Published {published_count} scheduled posts")
        return f"Published {published_count} scheduled posts"
        
    except Exception as e:
        logger.error(f"Error in publish_scheduled_posts task: {str(e)}")
        raise

@shared_task
def send_new_post_notification(post_id):
    """
    Celery task to send email notifications for new posts.
    This will be implemented in later tasks.
    """
    logger.info(f"New post notification task queued for post ID: {post_id}")
    # Implementation will be added in email subscription task
    return f"Notification queued for post {post_id}"

@shared_task
def process_media_upload(media_file_id):
    """
    Celery task to process uploaded media files (thumbnails, optimization).
    This will be implemented in later tasks.
    """
    logger.info(f"Media processing task queued for media file ID: {media_file_id}")
    # Implementation will be added in multimedia support task
    return f"Media processing queued for file {media_file_id}"