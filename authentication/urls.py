"""
Authentication URL Configuration

This module defines URL patterns for Google SSO authentication endpoints.
Google SSO is the ONLY authentication method.
"""

from django.urls import path
from authentication.views import (
    GoogleLoginInitView,
    GoogleAuthView,
    GoogleSignupView,
    LogoutView,
    RefreshTokenView,
    MeView,
    RevokeAllTokensView,
)
from authentication.web_views import (
    LoginView,
    GoogleCallbackView,
)

app_name = 'authentication'

urlpatterns = [
    # API endpoints - Google SSO only
    path('api/google/login/', GoogleLoginInitView.as_view(), name='api-google-login-init'),
    path('api/google/', GoogleAuthView.as_view(), name='api-google-auth'),
    path('api/google/signup/', GoogleSignupView.as_view(), name='api-google-signup'),
    path('api/logout/', LogoutView.as_view(), name='api-logout'),
    path('api/refresh/', RefreshTokenView.as_view(), name='api-refresh'),
    path('api/me/', MeView.as_view(), name='api-me'),
    path('api/revoke-all/', RevokeAllTokensView.as_view(), name='api-revoke-all'),
    
    # Web pages
    path('login/', LoginView.as_view(), name='login'),
    path('google/callback/', GoogleCallbackView.as_view(), name='google-callback'),
]
