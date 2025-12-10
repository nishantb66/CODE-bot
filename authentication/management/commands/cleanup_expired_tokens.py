"""
Django management command to clean up expired refresh tokens.

Usage:
    python manage.py cleanup_expired_tokens
    
This should be run periodically via cron job or task scheduler.
"""

from django.core.management.base import BaseCommand
from authentication.services import JWTService


class Command(BaseCommand):
    """
    Management command to delete expired refresh tokens from the database.
    """
    
    help = 'Deletes expired refresh tokens from the database'
    
    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write('Cleaning up expired tokens...')
        
        try:
            count = JWTService.clean_expired_tokens()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {count} expired token(s)'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Error cleaning up tokens: {str(e)}'
                )
            )
