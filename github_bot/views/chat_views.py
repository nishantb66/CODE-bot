"""
API views for GitHub Bot chat functionality.
"""
import time
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from github_bot.serializers import ChatRequestSerializer, ChatResponseSerializer
from github_bot.utils.chat_service import ChatService
from github_bot.utils.database import save_request_log, save_error_log

logger = logging.getLogger(__name__)


class ChatAPIView(APIView):
    """
    API endpoint for chatting with the GitHub bot.
    
    POST /api/chat/
    Request body: {"prompt": "your question here"}
    """
    
    def post(self, request):
        """
        Handle chat request.
        
        Request body:
        {
            "prompt": "What repositories do I have?",
            "model_id": 2,  # Optional: 1 = llama-3.1-8b-instant, 2 = llama-3.3-70b-versatile (default: 2)
            "conversation_id": "optional-conversation-id",  # Optional: For maintaining chat history
            "clear_history": false  # Optional: Set to true to clear conversation history
        }
        
        Response:
        {
            "success": true,
            "response": "You have access to...",
            "conversation_id": "uuid-or-provided-id",
            "metadata": {
                "duration_ms": 1234.56,
                "prompt_length": 25,
                "response_length": 150,
                "history_messages": 3
            }
        }
        """
        start_time = time.time()
        request_data = request.data
        
        # Validate request
        serializer = ChatRequestSerializer(data=request_data)
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "response": "Invalid request data.",
                    "error": "VALIDATION_ERROR",
                    "details": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        prompt = serializer.validated_data['prompt']
        model_id = serializer.validated_data.get('model_id')
        conversation_id = serializer.validated_data.get('conversation_id')
        clear_history = serializer.validated_data.get('clear_history', False)
        
        try:
            # Process chat request
            chat_service = ChatService()
            result = chat_service.process_chat(
                prompt=prompt, 
                model_id=model_id,
                conversation_id=conversation_id,
                clear_history=clear_history
            )
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Prepare response
            response_data = {
                "success": result.get("success", False),
                "response": result.get("response", ""),
                "error": result.get("error"),
                "conversation_id": result.get("conversation_id"),
                "metadata": {
                    **result.get("metadata", {}),
                    "duration_ms": round(duration_ms, 2)
                }
            }
            
            # Save request log
            try:
                save_request_log(
                    request_data={
                        "prompt": prompt, 
                        "model_id": model_id,
                        "conversation_id": conversation_id,
                        "clear_history": clear_history
                    },
                    response_data=response_data,
                    status_code=status.HTTP_200_OK if result.get("success") else status.HTTP_500_INTERNAL_SERVER_ERROR,
                    duration_ms=duration_ms
                )
            except Exception as e:
                logger.warning(f"Failed to save request log: {str(e)}")
            
            # Return response
            response_serializer = ChatResponseSerializer(data=response_data)
            if response_serializer.is_valid():
                http_status = status.HTTP_200_OK if result.get("success") else status.HTTP_500_INTERNAL_SERVER_ERROR
                return Response(response_serializer.validated_data, status=http_status)
            else:
                return Response(response_data, status=status.HTTP_200_OK)
                
        except Exception as e:
            error_msg = f"Unexpected error in chat API: {str(e)}"
            logger.error(error_msg)
            
            save_error_log(
                error_type="ChatAPIError",
                error_message=error_msg,
                context={"prompt": prompt[:100]}
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            return Response(
                {
                    "success": False,
                    "response": "An unexpected error occurred. Please try again.",
                    "error": "INTERNAL_ERROR",
                    "metadata": {
                        "duration_ms": round(duration_ms, 2)
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

