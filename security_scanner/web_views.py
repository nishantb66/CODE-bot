"""
Security Scanner Web Views

Renders the security scanner web pages.
"""
from django.shortcuts import render


def security_scan_view(request):
    """
    Render the security scanner page.
    
    GET /security/
    
    This page allows users to:
    - Enter a GitHub repository URL
    - Initiate a security scan
    - View vulnerability results
    """
    return render(request, 'security_scanner/scan.html')
