"""
Google OAuth Service

This module handles Google OAuth authentication flow.
Google SSO is the ONLY authentication method.
"""

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google_auth_oauthlib.flow import Flow
from django.conf import settings
from authentication.services.mongodb_user_service import get_user_service
import logging

logger = logging.getLogger(__name__)


class GoogleOAuthService:
    """
    Service class for handling Google OAuth authentication.
    
    Features:
    - OAuth flow initialization
    - Token exchange
    - User profile retrieval
    - User creation/update in MongoDB
    """
    
    SCOPES = [
        'openid',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile',
    ]
    
    @staticmethod
    def get_authorization_url(redirect_uri: str) -> str:
        """
        Generate Google OAuth authorization URL.
        
        Args:
            redirect_uri: The redirect URI for OAuth callback
        
        Returns:
            str: Authorization URL
        """
        flow = Flow.from_client_config(
            client_config={
                'web': {
                    'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
                    'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
                    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                    'token_uri': 'https://oauth2.googleapis.com/token',
                    'redirect_uris': [redirect_uri],
                }
            },
            scopes=GoogleOAuthService.SCOPES
        )
        
        flow.redirect_uri = redirect_uri
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        return authorization_url
    
    @staticmethod
    def exchange_code_for_token(code: str, redirect_uri: str) -> dict:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from Google
            redirect_uri: The redirect URI used in OAuth flow
        
        Returns:
            dict: Token information
        
        Raises:
            ValueError: If token exchange fails
        """
        try:
            flow = Flow.from_client_config(
                client_config={
                    'web': {
                        'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
                        'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
                        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                        'token_uri': 'https://oauth2.googleapis.com/token',
                        'redirect_uris': [redirect_uri],
                    }
                },
                scopes=GoogleOAuthService.SCOPES
            )
            
            flow.redirect_uri = redirect_uri
            flow.fetch_token(code=code)
            
            credentials = flow.credentials
            
            return {
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'id_token': credentials.id_token,
            }
            
        except Exception as e:
            logger.error(f"Failed to exchange code for token: {str(e)}")
            raise ValueError(f"Token exchange failed: {str(e)}")
    
    @staticmethod
    def verify_and_get_user_info(id_token_str: str) -> dict:
        """
        Verify ID token and extract user information.
        
        Args:
            id_token_str: The ID token from Google
        
        Returns:
            dict: User information including:
                - google_id
                - email
                - email_verified
                - first_name
                - last_name
                - name (full name)
                - profile_picture
        
        Raises:
            ValueError: If token verification fails
        """
        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                id_token_str,
                google_requests.Request(),
                settings.GOOGLE_OAUTH_CLIENT_ID
            )
            
            # Verify the issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Invalid token issuer')
            
            return {
                'google_id': idinfo['sub'],
                'email': idinfo.get('email', ''),
                'email_verified': idinfo.get('email_verified', False),
                'first_name': idinfo.get('given_name', ''),
                'last_name': idinfo.get('family_name', ''),
                'name': idinfo.get('name', ''),
                'profile_picture': idinfo.get('picture', ''),
            }
            
        except ValueError as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise ValueError(f"Invalid token: {str(e)}")
    
    @staticmethod
    def get_user_info_from_code(code: str, redirect_uri: str) -> dict:
        """
        Exchange code for token and get user info.
        This is used to get user info before deciding whether to create a user.
        
        Args:
            code: Authorization code from Google
            redirect_uri: The redirect URI used in OAuth flow
        
        Returns:
            dict: User information from Google
        
        Raises:
            ValueError: If authentication fails
        """
        # Exchange code for token
        tokens = GoogleOAuthService.exchange_code_for_token(code, redirect_uri)
        
        # Verify token and get user info
        user_info = GoogleOAuthService.verify_and_get_user_info(tokens['id_token'])
        
        return user_info
    
    @staticmethod
    def check_user_exists(email: str) -> bool:
        """
        Check if a user with the given email exists in MongoDB.
        
        Args:
            email: User's email address
        
        Returns:
            bool: True if user exists, False otherwise
        """
        user_service = get_user_service()
        return user_service.user_exists(email)
    
    @staticmethod
    def authenticate_existing_user(email: str) -> dict:
        """
        Authenticate an existing user by email.
        Updates the last_login timestamp.
        
        Args:
            email: User's email address
        
        Returns:
            dict: User document from MongoDB
        
        Raises:
            ValueError: If user doesn't exist
        """
        user_service = get_user_service()
        user = user_service.update_user_login(email)
        
        if not user:
            raise ValueError(f"User with email {email} not found")
        
        logger.info(f"User authenticated: {email}")
        return user
    
    @staticmethod
    def create_new_user(user_info: dict) -> dict:
        """
        Create a new user in MongoDB from Google SSO info.
        
        Args:
            user_info: User information from Google OAuth containing:
                - email (required)
                - name
                - google_id
                - first_name
                - last_name
                - profile_picture
        
        Returns:
            dict: Created user document
        
        Raises:
            ValueError: If user creation fails
        """
        user_service = get_user_service()
        
        try:
            user = user_service.create_user(user_info)
            logger.info(f"New user created via Google SSO: {user_info['email']}")
            return user
        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
            raise ValueError(f"Failed to create user: {str(e)}")
    
    @staticmethod
    def get_user_by_email(email: str) -> dict:
        """
        Get a user by email from MongoDB.
        
        Args:
            email: User's email address
        
        Returns:
            dict: User document or None
        """
        user_service = get_user_service()
        return user_service.find_user_by_email(email)
