"""
Main chat service that orchestrates GitHub and Groq AI services.
"""
import logging
import time
import uuid
from typing import Dict, Any, Optional, List
from github_bot.utils.github_service import GitHubService
from github_bot.utils.groq_service import GroqService
from github_bot.utils.database import (
    save_chat_log, 
    save_error_log,
    save_conversation_message,
    get_conversation_history,
    clear_conversation
)
from github_bot.constants import MAX_CONVERSATION_MESSAGES, MAX_CONVERSATION_TOKENS

logger = logging.getLogger(__name__)


class ChatService:
    """Service for handling chat interactions with GitHub bot."""
    
    def __init__(self):
        self.github_service = GitHubService()
        self.groq_service = GroqService()
    
    def _get_or_create_conversation_id(self, conversation_id: Optional[str]) -> str:
        """Get existing conversation ID or generate a new one."""
        if not conversation_id:
            new_id = str(uuid.uuid4())
            logger.info(f"Generated new conversation_id: {new_id}")
            return new_id
        logger.info(f"Using existing conversation_id: {conversation_id}")
        return conversation_id

    def _handle_history_clearing(self, conversation_id: str, should_clear: bool) -> None:
        """Clear conversation history if requested."""
        if should_clear and conversation_id:
            try:
                clear_conversation(conversation_id)
                logger.info(f"Cleared conversation history for: {conversation_id}")
            except Exception as e:
                logger.warning(f"Failed to clear conversation history: {str(e)}")

    def _get_conversation_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """Retrieve conversation history with error handling."""
        try:
            history = get_conversation_history(
                conversation_id=conversation_id,
                max_messages=MAX_CONVERSATION_MESSAGES,
                max_tokens_estimate=MAX_CONVERSATION_TOKENS
            )
            logger.info(f"Retrieved {len(history)} previous messages")
            return history
        except Exception as e:
            logger.warning(f"Failed to retrieve conversation history: {str(e)}")
            return []

    def _get_repository_context(self, prompt: str) -> Optional[str]:
        """Fetch repository context based on prompt with smart detection."""
        logger.info("Fetching repository context...")
        try:
            # Check if user is asking about a specific repository
            repos = self.github_service.get_user_repositories()
            specific_repo = None
            prompt_lower = prompt.lower()
            
            # Try to identify if user is asking about a specific repo
            for repo in repos:
                repo_name_lower = repo['name'].lower()
                # Check for exact or partial match
                if repo_name_lower in prompt_lower or any(
                    word == repo_name_lower for word in prompt_lower.split()
                ):
                    specific_repo = repo
                    break
            
            # If specific repo detected, use smart context
            if specific_repo:
                owner = specific_repo.get('owner', {}).get('login', '')
                repo_name = specific_repo['name']
                
                if owner and repo_name:
                    logger.info(f"Detected specific repository query: {owner}/{repo_name}")
                    context = self.github_service.get_smart_repository_context(
                        query=prompt,
                        owner=owner,
                        repo=repo_name
                    )
                    logger.info(f"Smart context size: {len(context)} characters")
                    return context
            
            # Otherwise, use general repository context
            context = self.github_service.get_repository_context_for_query(
                query=prompt,
                max_repos=5  # Limit to 5 most relevant repos
            )
            logger.info(f"Context size: {len(context)} characters")
            return context
            
        except Exception as e:
            logger.warning(f"Failed to fetch repository context: {str(e)}")
            return "Repository information temporarily unavailable."

    def _save_interaction(self, conversation_id: str, prompt: str, response: str, model_id: Optional[int], context_exists: bool, history_length: int) -> None:
        """Save the interaction to database (conversation and chat logs)."""
        # Save conversation messages
        try:
            save_conversation_message(
                conversation_id=conversation_id,
                role="user",
                content=prompt,
                metadata={"model_id": model_id}
            )
            save_conversation_message(
                conversation_id=conversation_id,
                role="assistant",
                content=response,
                metadata={"model_id": model_id}
            )
        except Exception as e:
            logger.warning(f"Failed to save conversation messages: {str(e)}")
        
        # Save chat log
        try:
            save_chat_log(
                prompt=prompt,
                response=response,
                metadata={
                    "has_repository_context": context_exists,
                    "response_length": len(response),
                    "model_id": model_id,
                    "conversation_id": conversation_id,
                    "history_length": history_length
                }
            )
        except Exception as e:
            logger.warning(f"Failed to save chat log: {str(e)}")

    def process_chat(
        self, 
        prompt: str, 
        model_id: Optional[int] = None,
        conversation_id: Optional[str] = None,
        clear_history: bool = False
    ) -> Dict[str, Any]:
        """
        Process a chat request with the GitHub bot.
        
        Args:
            prompt: User's prompt/question
            model_id: Model ID to use (1 or 2), defaults to DEFAULT_GROQ_MODEL
            conversation_id: Optional conversation ID for maintaining chat history
            clear_history: If True, clear conversation history for the given conversation_id
        
        Returns:
            Dictionary with response and metadata
        """
        start_time = time.time()
        
        try:
            # Validate prompt
            if not prompt or not prompt.strip():
                return {
                    "success": False,
                    "response": "Prompt cannot be empty.",
                    "error": "INVALID_PROMPT",
                    "metadata": {
                        "duration_ms": round((time.time() - start_time) * 1000, 2)
                    }
                }
            
            # Setup conversation
            conversation_id = self._get_or_create_conversation_id(conversation_id)
            self._handle_history_clearing(conversation_id, clear_history)
            
            # Get context and history
            conversation_history = self._get_conversation_history(conversation_id)
            repository_context = self._get_repository_context(prompt)
            
            # Get AI response
            logger.info(f"Generating AI response with model_id: {model_id}")
            ai_response = self.groq_service.chat(
                prompt=prompt,
                repository_context=repository_context,
                model_id=model_id,
                conversation_history=conversation_history
            )
            
            if ai_response is None:
                return {
                    "success": False,
                    "response": "Failed to generate response. Please try again.",
                    "error": "GROQ_ERROR",
                    "metadata": {
                        "duration_ms": round((time.time() - start_time) * 1000, 2),
                        "model_id": model_id
                    }
                }
            
            # Check for error messages in response
            if ai_response.startswith(("I've reached", "The AI model", "API authentication", "Connection", "An error occurred")):
                return {
                    "success": False,
                    "response": ai_response,
                    "error": "GROQ_ERROR",
                    "metadata": {
                        "duration_ms": round((time.time() - start_time) * 1000, 2),
                        "model_id": model_id
                    }
                }
            
            # Save interaction
            self._save_interaction(
                conversation_id=conversation_id,
                prompt=prompt,
                response=ai_response,
                model_id=model_id,
                context_exists=bool(repository_context),
                history_length=len(conversation_history)
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "response": ai_response,
                "conversation_id": conversation_id,
                "metadata": {
                    "duration_ms": round(duration_ms, 2),
                    "prompt_length": len(prompt),
                    "response_length": len(ai_response),
                    "model_id": model_id,
                    "history_messages": len(conversation_history)
                }
            }
            
        except Exception as e:
            error_msg = f"Error processing chat: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            save_error_log(
                error_type="ChatServiceError",
                error_message=error_msg,
                context={
                    "prompt": prompt[:100] if prompt else None,
                    "model_id": model_id,
                    "conversation_id": conversation_id
                }
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            return {
                "success": False,
                "response": "An unexpected error occurred while processing your request. Please try again.",
                "error": "INTERNAL_ERROR",
                "metadata": {
                    "duration_ms": round(duration_ms, 2),
                    "model_id": model_id
                }
            }

    def process_chat_stream(self, prompt: str, model_id: Optional[int] = None, 
                           conversation_id: Optional[str] = None, 
                           clear_history: bool = False):
        """
        Process chat with streaming responses.
        Yields chunks of the AI response as they arrive.
        """
        try:
            # Get or create conversation ID
            conversation_id = self._get_or_create_conversation_id(conversation_id)
            
            # Yield conversation ID first
            yield {
                "type": "conversation_id",
                "conversation_id": conversation_id
            }
            
            # Handle history clearing
            self._handle_history_clearing(conversation_id, clear_history)
            
            # Get conversation history
            conversation_history = self._get_conversation_history(conversation_id)
            
            # Get repository context
            repository_context = self._get_repository_context(prompt)
            
            # Save user message
            save_conversation_message(
                conversation_id=conversation_id,
                role="user",
                content=prompt
            )
            
            # Stream AI response
            full_response = ""
            for chunk in self.groq_service.chat_stream(
                prompt=prompt,
                repository_context=repository_context,
                model_id=model_id,
                conversation_history=conversation_history
            ):
                full_response += chunk
                yield {
                    "type": "content",
                    "content": chunk
                }
            
            # Save assistant message
            save_conversation_message(
                conversation_id=conversation_id,
                role="assistant",
                content=full_response
            )
            
            # Save to chat logs
            save_chat_log(
                prompt=prompt,
                response=full_response,
                metadata={
                    "model_id": model_id,
                    "conversation_id": conversation_id,
                    "has_context": bool(repository_context),
                    "history_length": len(conversation_history)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in streaming chat: {str(e)}", exc_info=True)
            yield {
                "type": "error",
                "error": str(e)
            }

