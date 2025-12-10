"""
Authentication Admin Configuration

This module configures Django admin interface for authentication models.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from authentication.models import User, RefreshToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin interface for User model.
    """
    
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_email_verified',
        'google_id',
        'is_staff',
        'is_active',
        'date_joined',
    )
    
    list_filter = (
        'is_staff',
        'is_active',
        'is_email_verified',
        'date_joined',
    )
    
    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
        'google_id',
    )
    
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'email', 'profile_picture')
        }),
        (_('OAuth'), {
            'fields': ('google_id', 'is_email_verified')
        }),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined', 'updated_at')
        }),
    )
    
    readonly_fields = ('date_joined', 'updated_at', 'last_login')
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'email',
                'password1',
                'password2',
                'is_staff',
                'is_active',
            ),
        }),
    )


@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    """
    Admin interface for RefreshToken model.
    """
    
    list_display = (
        'id',
        'user',
        'jti',
        'created_at',
        'expires_at',
        'is_revoked',
        'ip_address',
    )
    
    list_filter = (
        'is_revoked',
        'created_at',
        'expires_at',
    )
    
    search_fields = (
        'user__username',
        'user__email',
        'jti',
        'ip_address',
    )
    
    ordering = ('-created_at',)
    
    readonly_fields = (
        'user',
        'token',
        'jti',
        'created_at',
        'expires_at',
        'ip_address',
        'user_agent',
    )
    
    fieldsets = (
        (_('Token Info'), {
            'fields': ('user', 'jti', 'token')
        }),
        (_('Status'), {
            'fields': ('is_revoked', 'revoked_at', 'expires_at')
        }),
        (_('Metadata'), {
            'fields': ('ip_address', 'user_agent', 'created_at')
        }),
    )
    
    def has_add_permission(self, request):
        """Disable manual token creation."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Allow changing only revoked status."""
        return True
    
    actions = ['revoke_tokens', 'delete_expired_tokens']
    
    def revoke_tokens(self, request, queryset):
        """Admin action to revoke selected tokens."""
        count = 0
        for token in queryset.filter(is_revoked=False):
            token.revoke()
            count += 1
        
        self.message_user(
            request,
            f'{count} token(s) revoked successfully.'
        )
    
    revoke_tokens.short_description = "Revoke selected tokens"
    
    def delete_expired_tokens(self, request, queryset):
        """Admin action to delete expired tokens."""
        from django.utils import timezone
        expired = queryset.filter(expires_at__lt=timezone.now())
        count = expired.count()
        expired.delete()
        
        self.message_user(
            request,
            f'{count} expired token(s) deleted successfully.'
        )
    
    delete_expired_tokens.short_description = "Delete expired tokens"
