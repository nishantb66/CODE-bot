"""
JWT Cookie Authentication Backend for Django REST Framework

This module provides custom authentication for DRF using JWT tokens from cookies.
Uses MongoDB for user storage.
"""

from rest_framework import authentication
from rest_framework import exceptions
from authentication.services import JWTService, get_user_service
from authentication.middleware import MongoUser
import logging

logger = logging.getLogger(__name__)


class JWTCookieAuthentication(authentication.BaseAuthentication):
    """
    Custom DRF authentication backend that extracts JWT from httpOnly cookies.
    Uses MongoDB for user lookup instead of Django ORM.
    
    This works with Django REST Framework's authentication system.
    """
    
    def authenticate(self, request):
        """
        Authenticate the request using JWT token from cookies.
        
        Args:
            request: DRF Request object
        
        Returns:
            tuple: (user, token) if authentication succeeds
            None: if no token is present (allows other auth methods)
        
        Raises:
            AuthenticationFailed: if token is invalid
        """
        # Get access token from cookies
        access_token = request.COOKIES.get('access_token')
        
        if not access_token:
            # No token present, let other authentication methods try
            return None
        
        try:
            # Validate and decode the token
            payload = JWTService.verify_access_token(access_token)
            
            # Get email from token
            email = payload.get('email')
            
            if not email:
                raise exceptions.AuthenticationFailed('Invalid token: email not found')
            
            # Fetch user from MongoDB
            user_service = get_user_service()
            user_data = user_service.find_user_by_email(email)
            
            if not user_data:
                raise exceptions.AuthenticationFailed('User not found')
            
            if not user_data.get('is_active', True):
                raise exceptions.AuthenticationFailed('User account is inactive')
            
            # Create MongoUser object
            user = MongoUser(user_data)
            
            # Store email on request for easy access in views
            request.user_email = email
            
            # Return user and payload
            return (user, payload)
            
        except ValueError as e:
            # Token is invalid or expired
            raise exceptions.AuthenticationFailed(f'Invalid token: {str(e)}')
        except Exception as e:
            # Any other error
            logger.error(f'Unexpected error in JWT cookie authentication: {str(e)}')
            raise exceptions.AuthenticationFailed('Authentication failed')
    
    def authenticate_header(self, request):
        """
        Return WWW-Authenticate header for 401 responses.
        """
        return 'Bearer realm="api"'
