"""
Notifications app configuration.
"""

from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'
    verbose_name = 'Email Notifications'
    
    def ready(self):
        """
        Import signals when the app is ready.
        """
        import notifications.signals