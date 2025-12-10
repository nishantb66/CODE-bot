"""
Authentication App Configuration

This module defines the configuration for the authentication app.
"""

from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    """
    Configuration for the authentication app.
    """
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'
    verbose_name = 'Authentication'
    
    def ready(self):
        """
        Import signals and perform app initialization tasks when Django starts.
        """
        # Import signals here if needed
        pass
