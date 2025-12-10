"""
Authentication Views

This module contains API views for Google SSO authentication.
This is the ONLY authentication method - no username/password.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.conf import settings
from authentication.services import (
    JWTService,
    GoogleOAuthService,
    TokenCookieAuthentication,
    get_user_service,
)
import logging

logger = logging.getLogger(__name__)


class GoogleLoginInitView(APIView):
    """
    API endpoint to get Google OAuth login URL.
    
    GET /api/auth/google/login/
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Get Google OAuth authorization URL.
        
        Returns:
            200: Authorization URL
        """
        try:
            redirect_uri = settings.GOOGLE_OAUTH_REDIRECT_URI
            auth_url = GoogleOAuthService.get_authorization_url(redirect_uri)
            
            return Response(
                {'authorization_url': auth_url},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Failed to generate Google auth URL: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to initialize Google login'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GoogleAuthView(APIView):
    """
    API endpoint for Google OAuth authentication.
    
    POST /api/auth/google/
    
    This endpoint handles the complete authentication flow:
    1. Exchanges the Google auth code for user info
    2. Checks if user exists in MongoDB
    3. Returns appropriate response based on user existence
    
    For existing users: Logs them in and returns tokens
    For new users: Returns user_info with requires_confirmation=True
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Process Google OAuth code.
        
        Request Body:
            code: str (required) - Authorization code from Google
            redirect_uri: str (optional) - Redirect URI used in OAuth flow
            confirm_signup: bool (optional) - If true and user doesn't exist, create account
        
        Returns:
            200: For existing users - tokens and user info
            200: For new users (no confirm_signup) - requires_confirmation with user_info
            201: For new users (with confirm_signup=true) - account created with tokens
            400: Invalid request
            401: Authentication failed
        """
        code = request.data.get('code')
        redirect_uri = request.data.get('redirect_uri', settings.GOOGLE_OAUTH_REDIRECT_URI)
        confirm_signup = request.data.get('confirm_signup', False)
        
        if not code:
            return Response(
                {'error': 'Authorization code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get user info from Google
            user_info = GoogleOAuthService.get_user_info_from_code(code, redirect_uri)
            email = user_info['email']
            
            # Check if user exists
            user_exists = GoogleOAuthService.check_user_exists(email)
            
            if user_exists:
                # Existing user - log them in
                user = GoogleOAuthService.authenticate_existing_user(email)
                
                # Generate JWT tokens
                tokens = JWTService.generate_tokens(user, request)
                
                # Prepare response
                response_data = {
                    'message': 'Login successful',
                    'user_exists': True,
                    'user': {
                        'id': str(user['_id']),
                        'email': user['email'],
                        'name': user.get('name', ''),
                        'first_name': user.get('first_name', ''),
                        'last_name': user.get('last_name', ''),
                        'profile_picture': user.get('profile_picture', ''),
                    },
                }
                
                response = Response(response_data, status=status.HTTP_200_OK)
                
                # Set tokens in secure httpOnly cookies
                JWTService.set_tokens_in_cookies(response, tokens)
                
                logger.info(f"User logged in via Google: {email}")
                return response
            
            else:
                # New user
                if confirm_signup:
                    # User has confirmed - create account
                    user = GoogleOAuthService.create_new_user(user_info)
                    
                    # Generate JWT tokens
                    tokens = JWTService.generate_tokens(user, request)
                    
                    # Prepare response
                    response_data = {
                        'message': 'Account created successfully',
                        'user_exists': False,
                        'account_created': True,
                        'user': {
                            'id': str(user['_id']),
                            'email': user['email'],
                            'name': user.get('name', ''),
                            'first_name': user.get('first_name', ''),
                            'last_name': user.get('last_name', ''),
                            'profile_picture': user.get('profile_picture', ''),
                        },
                    }
                    
                    response = Response(response_data, status=status.HTTP_201_CREATED)
                    
                    # Set tokens in secure httpOnly cookies
                    JWTService.set_tokens_in_cookies(response, tokens)
                    
                    logger.info(f"New user created via Google SSO: {email}")
                    return response
                
                else:
                    # User hasn't confirmed - return user info for confirmation prompt
                    return Response({
                        'message': 'Account not found. Please confirm to create account.',
                        'user_exists': False,
                        'requires_confirmation': True,
                        'user_info': {
                            'email': user_info['email'],
                            'name': user_info.get('name', ''),
                            'first_name': user_info.get('first_name', ''),
                            'last_name': user_info.get('last_name', ''),
                            'google_id': user_info.get('google_id', ''),
                            'profile_picture': user_info.get('profile_picture', ''),
                        }
                    }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.warning(f"Google auth failed: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            logger.error(f"Google auth error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Google authentication failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GoogleSignupView(APIView):
    """
    API endpoint for creating new user after confirmation.
    
    POST /api/auth/google/signup/
    
    This endpoint creates a new user using stored user_info.
    Should only be called after user confirms account creation.
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Create new user with confirmed user info.
        
        Request Body:
            user_info: dict (required) - User info from previous Google auth response
        
        Returns:
            201: User created successfully with tokens
            400: Invalid request
            409: User already exists
        """
        user_info = request.data.get('user_info')
        
        if not user_info or not user_info.get('email'):
            return Response(
                {'error': 'User information with email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email = user_info['email']
        
        try:
            # Check if user was created in the meantime (race condition)
            if GoogleOAuthService.check_user_exists(email):
                # User already exists - just log them in
                user = GoogleOAuthService.authenticate_existing_user(email)
                
                tokens = JWTService.generate_tokens(user, request)
                
                response_data = {
                    'message': 'Login successful (account already exists)',
                    'user': {
                        'id': str(user['_id']),
                        'email': user['email'],
                        'name': user.get('name', ''),
                        'first_name': user.get('first_name', ''),
                        'last_name': user.get('last_name', ''),
                        'profile_picture': user.get('profile_picture', ''),
                    },
                }
                
                response = Response(response_data, status=status.HTTP_200_OK)
                JWTService.set_tokens_in_cookies(response, tokens)
                
                return response
            
            # Create new user
            user = GoogleOAuthService.create_new_user(user_info)
            
            # Generate JWT tokens
            tokens = JWTService.generate_tokens(user, request)
            
            # Prepare response
            response_data = {
                'message': 'Account created successfully',
                'user': {
                    'id': str(user['_id']),
                    'email': user['email'],
                    'name': user.get('name', ''),
                    'first_name': user.get('first_name', ''),
                    'last_name': user.get('last_name', ''),
                    'profile_picture': user.get('profile_picture', ''),
                },
            }
            
            response = Response(response_data, status=status.HTTP_201_CREATED)
            
            # Set tokens in secure httpOnly cookies
            JWTService.set_tokens_in_cookies(response, tokens)
            
            logger.info(f"New user created via Google SSO: {email}")
            return response
            
        except Exception as e:
            logger.error(f"Google signup error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to create account. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LogoutView(APIView):
    """
    API endpoint for user logout.
    
    POST /api/auth/logout/
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Logout user by revoking refresh token and clearing cookies.
        
        Returns:
            200: Logout successful
        """
        try:
            # Get refresh token from cookies
            refresh_token = TokenCookieAuthentication.get_refresh_token_from_request(request)
            
            if refresh_token:
                # Revoke the refresh token
                JWTService.revoke_token(refresh_token)
            
            # Prepare response
            response = Response(
                {'message': 'Logout successful'},
                status=status.HTTP_200_OK
            )
            
            # Clear tokens from cookies
            JWTService.clear_tokens_from_cookies(response)
            
            # Get user email from request if available
            user_email = getattr(request, 'user_email', 'unknown')
            logger.info(f"User logged out: {user_email}")
            return response
            
        except Exception as e:
            logger.error(f"Logout error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Logout failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RefreshTokenView(APIView):
    """
    API endpoint for refreshing access token.
    
    POST /api/auth/refresh/
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Generate a new access token using refresh token from cookies.
        
        Returns:
            200: New access token generated
            401: Invalid or expired refresh token
        """
        try:
            # Get refresh token from cookies
            refresh_token = TokenCookieAuthentication.get_refresh_token_from_request(request)
            
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token not found'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Generate new access token
            tokens = JWTService.refresh_access_token(refresh_token)
            
            # Prepare response
            response = Response(
                {'message': 'Token refreshed successfully'},
                status=status.HTTP_200_OK
            )
            
            # Set new access token in cookie
            response.set_cookie(
                key='access_token',
                value=tokens['access'],
                max_age=tokens['access_expires_in'],
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                path='/',
            )
            
            logger.debug("Access token refreshed")
            return response
            
        except ValueError as e:
            logger.warning(f"Token refresh failed: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Token refresh failed. Please login again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MeView(APIView):
    """
    API endpoint to get current user information.
    
    GET /api/auth/me/
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get current authenticated user's information.
        
        Returns:
            200: User information
            401: Not authenticated
        """
        try:
            # Get user email from the request (set by middleware)
            user_email = getattr(request, 'user_email', None)
            
            if not user_email:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Get user from MongoDB
            user_service = get_user_service()
            user = user_service.find_user_by_email(user_email)
            
            if not user:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            return Response({
                'id': str(user['_id']),
                'email': user['email'],
                'name': user.get('name', ''),
                'first_name': user.get('first_name', ''),
                'last_name': user.get('last_name', ''),
                'profile_picture': user.get('profile_picture', ''),
                'auth_provider': user.get('auth_provider', 'google'),
                'created_at': user.get('created_at'),
                'last_login': user.get('last_login'),
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to get user information'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RevokeAllTokensView(APIView):
    """
    API endpoint to revoke all refresh tokens for the current user.
    
    POST /api/auth/revoke-all/
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Revoke all refresh tokens (logout from all devices).
        
        Returns:
            200: All tokens revoked
        """
        try:
            user_email = getattr(request, 'user_email', None)
            
            if not user_email:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            count = JWTService.revoke_all_user_tokens(user_email)
            
            response = Response(
                {
                    'message': f'Successfully revoked {count} tokens',
                    'tokens_revoked': count
                },
                status=status.HTTP_200_OK
            )
            
            # Clear tokens from current session
            JWTService.clear_tokens_from_cookies(response)
            
            logger.info(f"All tokens revoked for user: {user_email}")
            return response
            
        except Exception as e:
            logger.error(f"Token revocation error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to revoke tokens. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
