"""
Security Scanner Web URL Configuration

Defines URL patterns for the security scanner web pages.
"""
from django.urls import path
from security_scanner.web_views import security_scan_view

app_name = 'security_scanner'

urlpatterns = [
    # Security scanner page
    path('', security_scan_view, name='scan'),
]
