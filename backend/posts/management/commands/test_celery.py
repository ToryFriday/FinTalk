"""
Management command to test Celery setup.
"""

from django.core.management.base import BaseCommand
from posts.tasks import publish_scheduled_posts, send_new_post_notification


class Command(BaseCommand):
    help = 'Test Celery task execution'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Testing Celery task execution...')
        )
        
        try:
            # Test synchronous task execution
            result = publish_scheduled_posts.delay()
            self.stdout.write(
                self.style.SUCCESS(f'Task queued successfully. Task ID: {result.id}')
            )
            
            # Test notification task
            notification_result = send_new_post_notification.delay(1)
            self.stdout.write(
                self.style.SUCCESS(f'Notification task queued. Task ID: {notification_result.id}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error testing Celery: {str(e)}')
            )
            
        self.stdout.write(
            self.style.SUCCESS('Celery test completed. Check worker logs for task execution.')
        )