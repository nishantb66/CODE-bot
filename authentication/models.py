"""
Authentication Models

This module defines custom user models and authentication-related models.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    
    Features:
    - Unique email and username
    - Email verification support
    - Google OAuth integration
    """
    
    email = models.EmailField(
        _('email address'),
        unique=True,
        error_messages={
            'unique': _("A user with that email already exists."),
        },
    )
    
    # Google OAuth fields
    google_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        help_text="Google OAuth user ID"
    )
    
    is_email_verified = models.BooleanField(
        default=False,
        help_text="Indicates if the user's email has been verified"
    )
    
    # Profile fields
    profile_picture = models.URLField(
        blank=True,
        null=True,
        help_text="URL to user's profile picture"
    )
    
    # Timestamps
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['google_id']),
        ]
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        """Returns the user's full name."""
        return f"{self.first_name} {self.last_name}".strip() or self.username


class RefreshToken(models.Model):
    """
    Model to store refresh tokens for JWT authentication.
    
    This allows for token revocation and tracking of user sessions.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='refresh_tokens'
    )
    
    token = models.CharField(
        max_length=500,
        unique=True,
        help_text="The refresh token string"
    )
    
    jti = models.CharField(
        max_length=255,
        unique=True,
        help_text="JWT ID for token identification"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    # Token metadata
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        help_text="IP address from which token was created"
    )
    
    user_agent = models.TextField(
        blank=True,
        help_text="User agent string"
    )
    
    is_revoked = models.BooleanField(
        default=False,
        help_text="Whether this token has been revoked"
    )
    
    revoked_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When this token was revoked"
    )
    
    class Meta:
        verbose_name = _('refresh token')
        verbose_name_plural = _('refresh tokens')
        db_table = 'refresh_tokens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_revoked']),
            models.Index(fields=['jti']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"RefreshToken for {self.user.email}"
    
    def revoke(self):
        """Revoke this refresh token."""
        from django.utils import timezone
        self.is_revoked = True
        self.revoked_at = timezone.now()
        self.save(update_fields=['is_revoked', 'revoked_at'])
    
    @property
    def is_expired(self):
        """Check if the token has expired."""
        from django.utils import timezone
        return timezone.now() >= self.expires_at
    
    @property
    def is_valid(self):
        """Check if the token is valid (not revoked and not expired)."""
        return not self.is_revoked and not self.is_expired
