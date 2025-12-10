"""
Authentication Web Views

Web views for rendering authentication pages.
Google SSO is the ONLY authentication method.
"""

from django.shortcuts import render, redirect
from django.views import View


class LoginView(View):
    """
    Render the login page.
    
    GET /auth/login/
    
    This page shows Google SSO button only.
    No username/password form.
    """
    
    def get(self, request):
        """Render login page."""
        # Redirect to home if already authenticated
        if request.user.is_authenticated:
            return redirect('/')
        
        return render(request, 'authentication/login.html')


class GoogleCallbackView(View):
    """
    Handle Google OAuth callback.
    
    GET /sso/google/callback/
    
    This page:
    1. Receives the Google OAuth code
    2. Verifies the code and checks if user exists
    3. If user exists: logs them in directly
    4. If new user: shows confirmation prompt
    5. On confirmation: creates account and logs in
    """
    
    def get(self, request):
        """Handle Google OAuth callback."""
        return render(request, 'authentication/google_callback.html')
