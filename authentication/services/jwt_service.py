"""
JWT Service

This module handles JWT token generation, validation, and management.
Implements secure token handling with httpOnly cookies.
Uses MongoDB for token storage.
"""

from datetime import timedelta
from django.conf import settings
from django.utils import timezone
import jwt
from authentication.services.mongodb_token_service import get_token_service
from authentication.services.mongodb_user_service import get_user_service
import uuid
import logging

logger = logging.getLogger(__name__)


class JWTService:
    """
    Service class for handling JWT tokens.
    
    Features:
    - Generate access and refresh tokens
    - Store refresh tokens in MongoDB for revocation
    - Validate and refresh tokens
    - Secure cookie management
    """
    
    # Token expiry durations
    ACCESS_TOKEN_LIFETIME = timedelta(minutes=30)
    REFRESH_TOKEN_LIFETIME = timedelta(days=7)
    
    @staticmethod
    def generate_tokens(user: dict, request=None) -> dict:
        """
        Generate access and refresh tokens for a user.
        
        Args:
            user: User document from MongoDB (must have 'email' and '_id')
            request: HTTP request object for metadata
        
        Returns:
            dict: Contains 'access', 'refresh' tokens and expiry info
        """
        now = timezone.now()
        jti = str(uuid.uuid4())
        user_id = str(user['_id'])
        email = user['email']
        
        # Generate access token
        access_payload = {
            'user_id': user_id,
            'email': email,
            'name': user.get('name', ''),
            'exp': now + JWTService.ACCESS_TOKEN_LIFETIME,
            'iat': now,
            'token_type': 'access',
        }
        access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm='HS256')
        
        # Generate refresh token
        refresh_exp = now + JWTService.REFRESH_TOKEN_LIFETIME
        refresh_payload = {
            'user_id': user_id,
            'email': email,
            'jti': jti,
            'exp': refresh_exp,
            'iat': now,
            'token_type': 'refresh',
        }
        refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm='HS256')
        
        # Store refresh token in MongoDB
        token_service = get_token_service()
        token_service.store_refresh_token(
            user_email=email,
            token=refresh_token,
            jti=jti,
            expires_at=refresh_exp,
            ip_address=JWTService._get_client_ip(request) if request else None,
            user_agent=request.META.get('HTTP_USER_AGENT', '') if request else '',
        )
        
        return {
            'access': access_token,
            'refresh': refresh_token,
            'access_expires_in': int(JWTService.ACCESS_TOKEN_LIFETIME.total_seconds()),
            'refresh_expires_in': int(JWTService.REFRESH_TOKEN_LIFETIME.total_seconds()),
        }
    
    @staticmethod
    def verify_access_token(token: str) -> dict:
        """
        Verify and decode an access token.
        
        Args:
            token: The access token string
        
        Returns:
            dict: Decoded token payload
        
        Raises:
            ValueError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            
            if payload.get('token_type') != 'access':
                raise ValueError("Invalid token type")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")
    
    @staticmethod
    def verify_refresh_token(token: str) -> dict:
        """
        Verify and decode a refresh token.
        
        Args:
            token: The refresh token string
        
        Returns:
            dict: Decoded token payload
        
        Raises:
            ValueError: If token is invalid, expired, or revoked
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            
            if payload.get('token_type') != 'refresh':
                raise ValueError("Invalid token type")
            
            # Check if token is revoked in MongoDB
            token_service = get_token_service()
            jti = payload.get('jti')
            
            if not token_service.is_token_valid(jti):
                raise ValueError("Token has been revoked")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise ValueError("Refresh token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> dict:
        """
        Generate a new access token from a refresh token.
        
        Args:
            refresh_token: The refresh token string
        
        Returns:
            dict: Contains new 'access' token
        
        Raises:
            ValueError: If refresh token is invalid or revoked
        """
        # Verify refresh token
        payload = JWTService.verify_refresh_token(refresh_token)
        
        # Get user from MongoDB
        user_service = get_user_service()
        user = user_service.find_user_by_email(payload['email'])
        
        if not user:
            raise ValueError("User not found")
        
        if not user.get('is_active', True):
            raise ValueError("User account is deactivated")
        
        # Generate new access token
        now = timezone.now()
        access_payload = {
            'user_id': str(user['_id']),
            'email': user['email'],
            'name': user.get('name', ''),
            'exp': now + JWTService.ACCESS_TOKEN_LIFETIME,
            'iat': now,
            'token_type': 'access',
        }
        access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm='HS256')
        
        return {
            'access': access_token,
            'access_expires_in': int(JWTService.ACCESS_TOKEN_LIFETIME.total_seconds()),
        }
    
    @staticmethod
    def revoke_token(refresh_token: str) -> bool:
        """
        Revoke a refresh token.
        
        Args:
            refresh_token: The refresh token string to revoke
        
        Returns:
            bool: True if revoked successfully, False otherwise
        """
        token_service = get_token_service()
        return token_service.revoke_token(refresh_token)
    
    @staticmethod
    def revoke_all_user_tokens(email: str) -> int:
        """
        Revoke all refresh tokens for a user.
        
        Args:
            email: User's email address
        
        Returns:
            int: Number of tokens revoked
        """
        token_service = get_token_service()
        return token_service.revoke_all_user_tokens(email)
    
    @staticmethod
    def clean_expired_tokens() -> int:
        """
        Delete expired tokens from the database.
        
        Returns:
            int: Number of tokens deleted
        """
        token_service = get_token_service()
        return token_service.clean_expired_tokens()
    
    @staticmethod
    def set_tokens_in_cookies(response, tokens: dict):
        """
        Set JWT tokens in secure httpOnly cookies.
        
        Args:
            response: HTTP response object
            tokens: Dictionary containing 'access' and 'refresh' tokens
        """
        # Set access token cookie
        response.set_cookie(
            key='access_token',
            value=tokens['access'],
            max_age=int(JWTService.ACCESS_TOKEN_LIFETIME.total_seconds()),
            httponly=True,  # Prevents JavaScript access
            secure=not settings.DEBUG,  # HTTPS only in production
            samesite='Lax',  # CSRF protection
            path='/',
        )
        
        # Set refresh token cookie
        response.set_cookie(
            key='refresh_token',
            value=tokens['refresh'],
            max_age=int(JWTService.REFRESH_TOKEN_LIFETIME.total_seconds()),
            httponly=True,  # Prevents JavaScript access
            secure=not settings.DEBUG,  # HTTPS only in production
            samesite='Lax',  # CSRF protection
            path='/',
        )
    
    @staticmethod
    def clear_tokens_from_cookies(response):
        """
        Clear JWT tokens from cookies (for logout).
        
        Args:
            response: HTTP response object
        """
        response.delete_cookie('access_token', path='/')
        response.delete_cookie('refresh_token', path='/')
    
    @staticmethod
    def _get_client_ip(request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class TokenCookieAuthentication:
    """
    Custom authentication class to extract JWT from httpOnly cookies.
    """
    
    @staticmethod
    def get_access_token_from_request(request):
        """
        Extract access token from cookies.
        
        Args:
            request: HTTP request object
        
        Returns:
            str: Access token or None
        """
        return request.COOKIES.get('access_token')
    
    @staticmethod
    def get_refresh_token_from_request(request):
        """
        Extract refresh token from cookies.
        
        Args:
            request: HTTP request object
        
        Returns:
            str: Refresh token or None
        """
        return request.COOKIES.get('refresh_token')
