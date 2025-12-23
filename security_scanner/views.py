"""
Security Scanner API Views

Provides REST API endpoints for security scanning.
Protected by authentication.
"""
import logging
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from security_scanner.serializers import (
    SecurityScanRequestSerializer,
    SecurityScanResponseSerializer,
    ScanHistorySerializer,
)
from security_scanner.engine.orchestrator import ScanOrchestrator
from security_scanner.models import ScanHistory

logger = logging.getLogger(__name__)


class SecurityScanAPIView(APIView):
    """
    API endpoint for performing security scans on GitHub repositories.
    
    POST /api/security/scan/
    
    Request Body:
        repository_url (str, required): GitHub repository URL to scan
        include_low_confidence (bool, optional): Include low-confidence findings
        max_files (int, optional): Maximum files to scan (default: 500)
    
    Returns:
        JSON with categorized vulnerabilities (critical, high, medium, low)
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Perform a security scan on a GitHub repository.
        """
        # Validate request
        serializer = SecurityScanRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'error': 'Invalid request',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        repo_url = serializer.validated_data['repository_url']
        include_low_confidence = serializer.validated_data.get('include_low_confidence', False)
        max_files = serializer.validated_data.get('max_files', 500)
        
        logger.info(f"Security scan requested for {repo_url} by user {request.user}")
        
        # Get the actual Django User instance
        # The middleware may attach a MongoUser proxy, but we need the real User for ForeignKey
        user_instance = None
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # If request.user is a Django User, use it directly
            if hasattr(request.user, 'pk') and isinstance(request.user.pk, int):
                user_instance = request.user
            # If we have user ID or email, fetch the actual User
            elif hasattr(request.user, 'id'):
                user_instance = User.objects.filter(id=request.user.id).first()
            elif hasattr(request.user, 'email'):
                user_instance = User.objects.filter(email=request.user.email).first()
        except Exception as e:
            logger.warning(f"Could not get Django User: {e}")
        
        # Create scan history entry (user can be None if lookup fails)
        scan_history = ScanHistory.objects.create(
            user=user_instance,
            repository_url=repo_url,
            status='running'
        )
        
        try:
            # Perform the scan
            orchestrator = ScanOrchestrator()
            result = orchestrator.scan_repository(
                repo_url=repo_url,
                max_files=max_files,
                include_low_confidence=include_low_confidence
            )
            
            # Convert to dict
            result_dict = result.to_dict()
            
            # Update scan history
            scan_history.status = 'completed' if not result.error else 'failed'
            scan_history.completed_at = timezone.now()
            scan_history.duration_ms = result.scan_duration_ms
            scan_history.files_scanned = result.files_scanned
            scan_history.repository_name = result.metadata.get('repository_name', '')
            scan_history.critical_count = len(result_dict.get('critical', []))
            scan_history.high_count = len(result_dict.get('high', []))
            scan_history.medium_count = len(result_dict.get('medium', []))
            scan_history.low_count = len(result_dict.get('low', []))
            scan_history.results = result_dict
            scan_history.error_message = result.error or ''
            scan_history.save()
            
            # Check for errors
            if result.error:
                return Response(
                    {
                        'success': False,
                        'error': result.error,
                        'repository_url': repo_url
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Add success flag
            result_dict['success'] = True
            
            return Response(result_dict, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.exception(f"Scan failed: {str(e)}")
            
            # Update scan history with error
            scan_history.status = 'failed'
            scan_history.completed_at = timezone.now()
            scan_history.error_message = str(e)
            scan_history.save()
            
            return Response(
                {
                    'success': False,
                    'error': f'Scan failed: {str(e)}',
                    'repository_url': repo_url
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ScanHistoryAPIView(APIView):
    """
    API endpoint for retrieving scan history.
    
    GET /api/security/history/
    
    Returns:
        List of previous scans for the authenticated user
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get scan history for the authenticated user.
        """
        try:
            # Get the actual Django User instance
            user_instance = None
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                if hasattr(request.user, 'pk') and isinstance(request.user.pk, int):
                    user_instance = request.user
                elif hasattr(request.user, 'id'):
                    user_instance = User.objects.filter(id=request.user.id).first()
                elif hasattr(request.user, 'email'):
                    user_instance = User.objects.filter(email=request.user.email).first()
            except Exception:
                pass
            
            # Get user's scan history
            if user_instance:
                scans = ScanHistory.objects.filter(
                    user=user_instance
                ).order_by('-started_at')[:50]
            else:
                scans = []
            
            # Serialize
            history = []
            for scan in scans:
                history.append({
                    'id': scan.id,
                    'repository_url': scan.repository_url,
                    'repository_name': scan.repository_name,
                    'status': scan.status,
                    'started_at': scan.started_at.isoformat(),
                    'completed_at': scan.completed_at.isoformat() if scan.completed_at else None,
                    'duration_ms': scan.duration_ms,
                    'files_scanned': scan.files_scanned,
                    'critical_count': scan.critical_count,
                    'high_count': scan.high_count,
                    'medium_count': scan.medium_count,
                    'low_count': scan.low_count,
                    'total_vulnerabilities': scan.total_vulnerabilities,
                    'has_critical_issues': scan.has_critical_issues,
                })
            
            return Response({
                'success': True,
                'count': len(history),
                'history': history
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.exception(f"Failed to fetch scan history: {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': f'Failed to fetch history: {str(e)}'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ScanDetailAPIView(APIView):
    """
    API endpoint for retrieving a specific scan's details.
    
    GET /api/security/scan/<id>/
    
    Returns:
        Full scan details including all vulnerabilities
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, scan_id):
        """
        Get details of a specific scan.
        """
        try:
            # Get the actual Django User instance
            user_instance = None
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                if hasattr(request.user, 'pk') and isinstance(request.user.pk, int):
                    user_instance = request.user
                elif hasattr(request.user, 'id'):
                    user_instance = User.objects.filter(id=request.user.id).first()
                elif hasattr(request.user, 'email'):
                    user_instance = User.objects.filter(email=request.user.email).first()
            except Exception:
                pass
            
            # Get the scan
            scan = None
            if user_instance:
                scan = ScanHistory.objects.filter(
                    id=scan_id,
                    user=user_instance
                ).first()
            
            if not scan:
                return Response(
                    {
                        'success': False,
                        'error': 'Scan not found'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response({
                'success': True,
                'id': scan.id,
                'repository_url': scan.repository_url,
                'repository_name': scan.repository_name,
                'status': scan.status,
                'started_at': scan.started_at.isoformat(),
                'completed_at': scan.completed_at.isoformat() if scan.completed_at else None,
                'duration_ms': scan.duration_ms,
                'files_scanned': scan.files_scanned,
                'summary': {
                    'critical': scan.critical_count,
                    'high': scan.high_count,
                    'medium': scan.medium_count,
                    'low': scan.low_count,
                },
                'total_vulnerabilities': scan.total_vulnerabilities,
                'results': scan.results,
                'error_message': scan.error_message,
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.exception(f"Failed to fetch scan details: {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': f'Failed to fetch scan: {str(e)}'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
