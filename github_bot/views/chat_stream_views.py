"""
Streaming API view for real-time chat responses.
"""
import json
import logging
from django.http import StreamingHttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from github_bot.utils.chat_service import ChatService

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class ChatStreamView(View):
    """
    Streaming endpoint for real-time AI responses.
    Uses Server-Sent Events (SSE) for streaming.
    """
    
    def post(self, request):
        """Handle streaming chat request."""
        try:
            # Parse request body
            body = json.loads(request.body)
            prompt = body.get('prompt', '').strip()
            model_id = body.get('model_id', 2)
            conversation_id = body.get('conversation_id')
            clear_history = body.get('clear_history', False)
            
            if not prompt:
                return StreamingHttpResponse(
                    self._error_stream('Prompt is required'),
                    content_type='text/event-stream'
                )
            
            # Create streaming response
            response = StreamingHttpResponse(
                self._stream_chat(prompt, model_id, conversation_id, clear_history),
                content_type='text/event-stream'
            )
            response['Cache-Control'] = 'no-cache'
            response['X-Accel-Buffering'] = 'no'
            return response
            
        except Exception as e:
            logger.error(f"Error in streaming chat: {str(e)}", exc_info=True)
            return StreamingHttpResponse(
                self._error_stream(str(e)),
                content_type='text/event-stream'
            )
    
    def _stream_chat(self, prompt, model_id, conversation_id, clear_history):
        """Generator for streaming chat responses."""
        try:
            chat_service = ChatService()
            
            # Process chat with streaming
            for chunk in chat_service.process_chat_stream(
                prompt=prompt,
                model_id=model_id,
                conversation_id=conversation_id,
                clear_history=clear_history
            ):
                # Send chunk as SSE
                yield f"data: {json.dumps(chunk)}\n\n"
            
            # Send completion signal
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            logger.error(f"Error streaming chat: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    def _error_stream(self, error_message):
        """Generate error stream."""
        yield f"data: {json.dumps({'error': error_message})}\n\n"
