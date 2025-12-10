"""
Authentication Middleware

Custom middleware for JWT cookie-based authentication with MongoDB.
"""

from django.utils.functional import SimpleLazyObject
from authentication.services import JWTService, TokenCookieAuthentication, get_user_service
import logging

logger = logging.getLogger(__name__)


class MongoUser:
    """
    A user-like object for MongoDB users.
    Provides compatibility with Django's authentication system.
    """
    
    def __init__(self, user_data):
        self._data = user_data
        self.id = str(user_data.get('_id', ''))
        self.email = user_data.get('email', '')
        self.name = user_data.get('name', '')
        self.first_name = user_data.get('first_name', '')
        self.last_name = user_data.get('last_name', '')
        self.profile_picture = user_data.get('profile_picture', '')
        self.is_active = user_data.get('is_active', True)
        self.is_authenticated = True
        self.is_anonymous = False
    
    def __str__(self):
        return self.email
    
    def get(self, key, default=None):
        return self._data.get(key, default)


class AnonymousUser:
    """
    Anonymous user for unauthenticated requests.
    """
    
    id = None
    email = ''
    name = ''
    is_authenticated = False
    is_anonymous = True
    is_active = False
    
    def __str__(self):
        return 'AnonymousUser'


class JWTCookieAuthenticationMiddleware:
    """
    Middleware to authenticate users via JWT tokens stored in httpOnly cookies.
    Uses MongoDB for user storage.
    
    This middleware extracts the access token from cookies and authenticates the user
    automatically for each request.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        """
        Process the request and authenticate user if valid token is present.
        """
        # Use SimpleLazyObject to defer user lookup until needed
        request.user = SimpleLazyObject(lambda: self._get_user_from_token(request))
        
        # Also set user_email on request for easy access
        def get_user_email():
            user = request.user
            return user.email if hasattr(user, 'email') and user.email else None
        
        request.user_email = SimpleLazyObject(get_user_email)
        
        response = self.get_response(request)
        return response
    
    def _get_user_from_token(self, request):
        """
        Get user from JWT token in cookies.
        
        Args:
            request: HTTP request object
        
        Returns:
            MongoUser instance or AnonymousUser
        """
        # Get access token from cookies
        access_token = TokenCookieAuthentication.get_access_token_from_request(request)
        
        if not access_token:
            return AnonymousUser()
        
        try:
            # Validate and decode the token
            payload = JWTService.verify_access_token(access_token)
            
            # Get email from token
            email = payload.get('email')
            
            if not email:
                return AnonymousUser()
            
            # Fetch user from MongoDB
            user_service = get_user_service()
            user_data = user_service.find_user_by_email(email)
            
            if not user_data:
                logger.warning(f"User with email {email} not found in MongoDB")
                return AnonymousUser()
            
            if not user_data.get('is_active', True):
                logger.warning(f"User {email} is inactive")
                return AnonymousUser()
            
            return MongoUser(user_data)
            
        except ValueError as e:
            # Token is invalid or expired
            logger.debug(f"Token validation failed: {str(e)}")
            return AnonymousUser()
        except Exception as e:
            # Any other error
            logger.error(f"Unexpected error in authentication: {str(e)}")
            return AnonymousUser()
