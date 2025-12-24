"""
URL configuration for analyzer project.

This module defines the root URL patterns for the application.
Routes are organized as follows:
- /admin/ - Django admin interface
- /api/auth/ - Authentication API endpoints
- /auth/ - Authentication web pages
- /sso/ - SSO callbacks
- /api/ - GitHub Bot API endpoints
- / - GitHub Bot web pages
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),
    
    # Authentication - API endpoints (e.g., /api/auth/api/google/)
    path('api/auth/', include(('authentication.urls', 'authentication'), namespace='auth_api')),
    
    # Authentication - Web pages (e.g., /auth/login/)
    path('auth/', include(('authentication.urls', 'authentication'), namespace='auth_pages')),
    
    # Authentication - SSO callbacks (e.g., /sso/google/callback/)
    path('sso/', include(('authentication.urls', 'authentication'), namespace='auth_sso')),
    
    # JWT Debugger - API endpoints
    path('api/jwt/', include(('jwt_debugger.urls', 'jwt_debugger'), namespace='jwt_debugger_api')),
    # JWT Debugger - Web page
    path('jwt-debugger/', include(('jwt_debugger.web_urls', 'jwt_debugger'), namespace='jwt_debugger_pages')),
    
    # GitHub Bot - API endpoints (e.g., /api/chat/, /api/review-code/)
    path('api/', include(('github_bot.urls', 'github_bot'), namespace='github_bot_api')),
    
    # Security Scanner - API endpoints (e.g., /api/security/scan/)
    path('api/security/', include(('security_scanner.urls', 'security_scanner'), namespace='security_scanner_api')),
    
    # Security Scanner - Web page (e.g., /security/)
    path('security/', include(('security_scanner.web_urls', 'security_scanner'), namespace='security_scanner_pages')),
    
    # GitHub Bot - Web pages (e.g., /, /code-review/)
    path('', include(('github_bot.urls', 'github_bot'), namespace='github_bot_pages')),
]

