"""
Authentication Required Middleware

Redirects unauthenticated users to login page.
Only Google SSO and callback endpoints are exempt.
"""

from django.shortcuts import redirect
from django.http import JsonResponse
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class LoginRequiredMiddleware:
    """
    Middleware that requires authentication for all views except whitelisted paths.
    
    Unauthenticated users are:
    - Redirected to login page for web requests
    - Returned 401 Unauthorized for API requests
    """
    
    # Paths that don't require authentication
    EXEMPT_PATHS = [
        # Login page
        '/auth/login/',
        
        # Google SSO callback
        '/auth/google/callback/',
        '/sso/google/callback/',
        
        # Google SSO API endpoints (for initiating and completing auth)
        '/api/auth/api/google/login/',
        '/api/auth/api/google/verify/',
        '/api/auth/api/google/',
        '/api/auth/api/google/signup/',
        '/api/auth/api/refresh/',
        
        # Django admin (has its own auth)
        '/admin/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Get the request path
        path = request.path
        
        # Check if path is exempt from authentication
        if self.is_exempt(path):
            return self.get_response(request)
        
        # Check if user is authenticated
        if not request.user.is_authenticated:
            # Check if this is an API request
            if self.is_api_request(request):
                return JsonResponse(
                    {'error': 'Authentication required', 'code': 'UNAUTHORIZED'},
                    status=401
                )
            
            # Redirect to login page, preserving the original URL
            login_url = '/auth/login/'
            
            # Don't redirect if already on login
            if path != login_url:
                # Add 'next' parameter to redirect back after login
                return redirect(f'{login_url}?next={path}')
        
        return self.get_response(request)
    
    def is_exempt(self, path):
        """
        Check if the path is exempt from authentication requirement.
        
        Args:
            path: Request path
        
        Returns:
            bool: True if path is exempt, False otherwise
        """
        # Check exact matches
        if path in self.EXEMPT_PATHS:
            return True
        
        # Check if path starts with any exempt path
        for exempt_path in self.EXEMPT_PATHS:
            if path.startswith(exempt_path):
                return True
        
        # Check if it's a static or media file
        if hasattr(settings, 'STATIC_URL') and path.startswith(settings.STATIC_URL):
            return True
        if hasattr(settings, 'MEDIA_URL') and path.startswith(settings.MEDIA_URL):
            return True
        
        return False
    
    def is_api_request(self, request):
        """
        Check if the request is an API request.
        
        Args:
            request: HTTP request object
        
        Returns:
            bool: True if API request, False otherwise
        """
        # Check URL path
        if request.path.startswith('/api/'):
            return True
        
        # Check Accept header
        accept = request.META.get('HTTP_ACCEPT', '')
        if 'application/json' in accept:
            return True
        
        # Check Content-Type header
        content_type = request.META.get('CONTENT_TYPE', '')
        if 'application/json' in content_type:
            return True
        
        return False
