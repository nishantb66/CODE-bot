"""JWT Debugger API URL configuration."""
from django.urls import path
from .views import (
    JWTDecodeAPIView,
    JWTEncodeAPIView,
    KeyGeneratorAPIView,
    CodeGeneratorAPIView,
    SecurityScannerAPIView,
    JWKSIntegrationAPIView,
)

app_name = 'jwt_debugger'

urlpatterns = [
    path('inspect/', JWTDecodeAPIView.as_view(), name='inspect'),
    path('sign/', JWTEncodeAPIView.as_view(), name='sign'),
    path('generate-key/', KeyGeneratorAPIView.as_view(), name='generate_key'),
    path('generate-code/', CodeGeneratorAPIView.as_view(), name='generate_code'),
    path('security-scan/', SecurityScannerAPIView.as_view(), name='security_scan'),
    path('jwks/', JWKSIntegrationAPIView.as_view(), name='jwks'),
]
