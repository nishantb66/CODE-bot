"""
Repository Report Views
Handles PDF report generation and preview
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from github_bot.utils.report_generator import generate_repo_report
import logging
import base64

logger = logging.getLogger(__name__)


@api_view(['POST'])
def generate_report(request):
    """
    Generate a PDF report for a GitHub repository
    
    Request body:
    {
        "repo_url": "https://github.com/owner/repo"
    }
    
    Returns:
        PDF file as base64 for preview and download
    """
    try:
        repo_url = request.data.get('repo_url', '').strip()
        
        if not repo_url:
            return Response({
                'error': 'Repository URL is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate URL format
        if 'github.com' not in repo_url:
            return Response({
                'error': 'Please provide a valid GitHub repository URL'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Generating report for repository: {repo_url}")
        
        # Generate PDF
        pdf_buffer = generate_repo_report(repo_url)
        pdf_data = pdf_buffer.getvalue()
        
        # Convert to base64 for preview
        pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
        
        # Extract repo name for filename
        repo_name = repo_url.rstrip('/').split('/')[-1]
        filename = f"{repo_name}_report.pdf"
        
        return Response({
            'success': True,
            'pdf_base64': pdf_base64,
            'filename': filename,
            'message': 'Report generated successfully'
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return Response({
            'error': 'Failed to generate report. Please check the repository URL and try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def download_report(request):
    """
    Download PDF report directly
    
    Request body:
    {
        "repo_url": "https://github.com/owner/repo"
    }
    
    Returns:
        PDF file for download
    """
    try:
        repo_url = request.data.get('repo_url', '').strip()
        
        if not repo_url:
            return HttpResponse('Repository URL is required', status=400)
        
        logger.info(f"Downloading report for repository: {repo_url}")
        
        # Generate PDF
        pdf_buffer = generate_repo_report(repo_url)
        
        # Extract repo name for filename
        repo_name = repo_url.rstrip('/').split('/')[-1]
        filename = f"{repo_name}_report.pdf"
        
        # Create response
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}")
        return HttpResponse('Failed to generate report', status=500)
