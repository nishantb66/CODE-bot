"""
Security Scanner URL Configuration

Defines URL patterns for the security scanner API.
"""
from django.urls import path
from security_scanner.views import (
    SecurityScanAPIView,
    ScanHistoryAPIView,
    ScanDetailAPIView,
)
from security_scanner.code_scan_views import DirectCodeScanAPIView

app_name = 'security_scanner'

urlpatterns = [
    # API endpoints
    path('scan/', SecurityScanAPIView.as_view(), name='scan'),
    path('scan-code/', DirectCodeScanAPIView.as_view(), name='scan_code'),
    path('history/', ScanHistoryAPIView.as_view(), name='history'),
    path('scan/<int:scan_id>/', ScanDetailAPIView.as_view(), name='scan_detail'),
]
