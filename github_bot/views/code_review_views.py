"""
API views for code review functionality.
"""
import logging
import time
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from github_bot.serializers import (
    CodeReviewRequestSerializer,
    FileReviewRequestSerializer,
    ImprovementRequestSerializer,
    CodeReviewResponseSerializer
)
from github_bot.utils.code_review_service import CodeReviewService
from github_bot.utils.github_service import GitHubService
from github_bot.utils.database import save_error_log

logger = logging.getLogger(__name__)


class CodeReviewAPIView(APIView):
    """
    API endpoint for reviewing code snippets.
    
    POST /api/review-code/
    {
        "code": "def hello():\n    print('Hello')",
        "language": "python",
        "context": "Optional context",
        "model_id": 2
    }
    """
    
    def post(self, request):
        """Handle code review requests."""
        start_time = time.time()
        
        try:
            # Validate request
            serializer = CodeReviewRequestSerializer(data=request.data)
            if not serializer.is_valid():
                logger.warning(f"Invalid code review request: {serializer.errors}")
                return Response({
                    "success": False,
                    "error": "Invalid request data",
                    "details": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            
            # Log request
            logger.info(f"Code review request: language={validated_data.get('language')}, code_length={len(validated_data.get('code', ''))}")
            
            # Perform code review
            review_service = CodeReviewService()
            result = review_service.review_code(
                code=validated_data["code"],
                language=validated_data.get("language", "python"),
                context=validated_data.get("context"),
                model_id=validated_data.get("model_id")
            )
            
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"Code review completed in {duration_ms:.2f}ms")
            
            # Add metadata
            if result.get("success"):
                result["metadata"] = {
                    "duration_ms": round(duration_ms, 2),
                    "timestamp": time.time()
                }
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            error_msg = f"Error in code review endpoint: {str(e)}"
            logger.error(error_msg, exc_info=True)
            save_error_log(
                error_type="CodeReviewAPIError",
                error_message=error_msg,
                context={"endpoint": "/api/review-code/"}
            )
            return Response({
                "success": False,
                "error": "An error occurred while reviewing code"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FileReviewAPIView(APIView):
    """
    API endpoint for reviewing files from GitHub repositories.
    
    POST /api/review-file/
    {
        "owner": "username",
        "repo": "repository-name",
        "file_path": "src/main.py",
        "model_id": 2
    }
    """
    
    def post(self, request):
        """Handle file review requests."""
        start_time = time.time()
        
        try:
            # Validate request
            serializer = FileReviewRequestSerializer(data=request.data)
            if not serializer.is_valid():
                logger.warning(f"Invalid file review request: {serializer.errors}")
                return Response({
                    "success": False,
                    "error": "Invalid request data",
                    "details": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            
            # Log request
            logger.info(f"File review request: {validated_data['owner']}/{validated_data['repo']}/{validated_data['file_path']}")
            
            # Fetch file from GitHub
            github_service = GitHubService()
            file_content = github_service.get_file_content(
                owner=validated_data["owner"],
                repo=validated_data["repo"],
                path=validated_data["file_path"]
            )
            
            if not file_content:
                return Response({
                    "success": False,
                    "error": "Failed to fetch file from GitHub. Please check the repository and file path."
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Review the file
            review_service = CodeReviewService()
            result = review_service.analyze_file(
                file_content=file_content,
                file_path=validated_data["file_path"],
                model_id=validated_data.get("model_id")
            )
            
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"File review completed in {duration_ms:.2f}ms")
            
            # Add metadata
            if result.get("success"):
                result["metadata"] = {
                    "duration_ms": round(duration_ms, 2),
                    "file_path": validated_data["file_path"],
                    "repository": f"{validated_data['owner']}/{validated_data['repo']}"
                }
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            error_msg = f"Error in file review endpoint: {str(e)}"
            logger.error(error_msg, exc_info=True)
            save_error_log(
                error_type="FileReviewAPIError",
                error_message=error_msg,
                context={"endpoint": "/api/review-file/"}
            )
            return Response({
                "success": False,
                "error": "An error occurred while reviewing file"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ImprovementSuggestionsAPIView(APIView):
    """
    API endpoint for getting code improvement suggestions.
    
    POST /api/suggest-improvements/
    {
        "code": "def hello():\n    print('Hello')",
        "language": "python",
        "focus_areas": ["performance", "readability"],
        "model_id": 2
    }
    """
    
    def post(self, request):
        """Handle improvement suggestion requests."""
        start_time = time.time()
        
        try:
            # Validate request
            serializer = ImprovementRequestSerializer(data=request.data)
            if not serializer.is_valid():
                logger.warning(f"Invalid improvement request: {serializer.errors}")
                return Response({
                    "success": False,
                    "error": "Invalid request data",
                    "details": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            
            # Log request
            logger.info(f"Improvement suggestions request: language={validated_data.get('language')}, focus_areas={validated_data.get('focus_areas', [])}")
            
            # Get improvement suggestions
            review_service = CodeReviewService()
            result = review_service.suggest_improvements(
                code=validated_data["code"],
                language=validated_data.get("language", "python"),
                focus_areas=validated_data.get("focus_areas"),
                model_id=validated_data.get("model_id")
            )
            
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"Improvement suggestions generated in {duration_ms:.2f}ms")
            
            # Add metadata
            if result.get("success"):
                result["metadata"] = {
                    "duration_ms": round(duration_ms, 2),
                    "timestamp": time.time()
                }
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            error_msg = f"Error in improvement suggestions endpoint: {str(e)}"
            logger.error(error_msg, exc_info=True)
            save_error_log(
                error_type="ImprovementSuggestionsAPIError",
                error_message=error_msg,
                context={"endpoint": "/api/suggest-improvements/"}
            )
            return Response({
                "success": False,
                "error": "An error occurred while generating suggestions"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
