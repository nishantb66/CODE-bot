"""
Authentication Serializers

This module defines serializers for Google SSO authentication endpoints.
Google SSO is the ONLY authentication method - no username/password.
"""

from rest_framework import serializers


class GoogleAuthCodeSerializer(serializers.Serializer):
    """
    Serializer for Google OAuth authorization code.
    """
    
    code = serializers.CharField(
        required=True,
        help_text="Authorization code from Google OAuth"
    )
    
    redirect_uri = serializers.URLField(
        required=False,
        help_text="Redirect URI used in the OAuth flow"
    )


class GoogleUserInfoSerializer(serializers.Serializer):
    """
    Serializer for Google user information.
    Used for creating new users.
    """
    
    email = serializers.EmailField(
        required=True,
        help_text="User's email address from Google"
    )
    
    name = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="User's full name from Google"
    )
    
    first_name = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="User's first name"
    )
    
    last_name = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="User's last name"
    )
    
    google_id = serializers.CharField(
        required=False,
        help_text="Google OAuth user ID"
    )
    
    profile_picture = serializers.URLField(
        required=False,
        allow_blank=True,
        help_text="URL to user's profile picture"
    )


class UserSerializer(serializers.Serializer):
    """
    Serializer for user details (MongoDB user documents).
    """
    
    id = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    name = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    profile_picture = serializers.URLField(read_only=True, allow_blank=True)
    auth_provider = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True)
