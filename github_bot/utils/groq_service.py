"""
Groq AI service utility for chat functionality.
"""
import os
from groq import Groq
from groq.types.chat import ChatCompletion
import logging
from typing import Optional, Dict, Any, List
from github_bot.utils.database import save_error_log
from github_bot.constants import SYSTEM_INSTRUCTION, GROQ_MODELS, DEFAULT_GROQ_MODEL

logger = logging.getLogger(__name__)


class GroqServiceError(Exception):
    """Custom exception for Groq service errors."""
    pass


class GroqService:
    """Service for interacting with Groq AI with improved error handling and resilience."""
    
    def __init__(self):
        self.api_key = os.environ.get('GROQ_API_KEY')
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self) -> bool:
        """
        Initialize Groq client with error handling.
        
        Returns:
            True if client initialized successfully, False otherwise
        """
        if not self.api_key:
            logger.warning("Groq API key not found in environment variables")
            return False
        
        try:
            self.client = Groq(api_key=self.api_key)
            logger.info("Successfully initialized Groq client")
            return True
        except Exception as e:
            logger.error(f"Error initializing Groq client: {str(e)}")
            self.client = None
            return False
    
    def _get_model_name(self, model_id: Optional[int] = None) -> str:
        """
        Get model name from model_id with validation.
        
        Args:
            model_id: Model ID (1 or 2), defaults to DEFAULT_GROQ_MODEL
        
        Returns:
            Model name string
        
        Raises:
            GroqServiceError: If model_id is invalid
        """
        if model_id is None:
            model_id = DEFAULT_GROQ_MODEL
        
        if model_id not in GROQ_MODELS:
            available = ", ".join([f"{k}={v}" for k, v in GROQ_MODELS.items()])
            raise GroqServiceError(f"Invalid model_id: {model_id}. Available: {available}")
        
        return GROQ_MODELS[model_id]
    
    def _handle_error(self, error: Exception, prompt: str, model_id: Optional[int] = None) -> str:
        """
        Handle errors with appropriate logging and user-friendly messages.
        
        Args:
            error: The exception that occurred
            prompt: User's prompt (for logging)
            model_id: Model ID used (for logging)
        
        Returns:
            User-friendly error message
        """
        error_msg = str(error)
        error_lower = error_msg.lower()
        model_name = self._get_model_name(model_id) if model_id else "unknown"
        
        # Log the error first
        logger.error(f"Groq API error (model: {model_name}): {error_msg}")
        
        # Determine error type and context for saving log
        error_type = "GroqAPIError"
        user_message = "An error occurred while processing your request. Please try again."
        context = {
            "prompt": prompt[:100],
            "model_id": model_id,
            "model_name": model_name
        }

        if any(keyword in error_lower for keyword in ["quota", "429", "rate limit", "too many requests"]):
            error_type = "GroqQuotaError"
            user_message = "I've reached my API quota limit. Please try again later or check your Groq API usage limits."
        
        elif any(keyword in error_lower for keyword in ["decommissioned", "no longer supported", "model_decommissioned"]):
            error_type = "GroqModelDecommissioned"
            replacement_model = GROQ_MODELS.get(DEFAULT_GROQ_MODEL)
            context["replacement_model"] = replacement_model
            user_message = f"The model '{model_name}' has been decommissioned. Please use model_id {DEFAULT_GROQ_MODEL} ({replacement_model}) instead."
        
        elif any(keyword in error_lower for keyword in ["404", "not found", "invalid model", "model not available"]):
            error_type = "GroqModelError"
            user_message = f"The AI model '{model_name}' is currently unavailable. Please try a different model or try again later."
        
        elif any(keyword in error_lower for keyword in ["401", "unauthorized", "authentication", "invalid api key"]):
            error_type = "GroqAuthError"
            user_message = "API authentication failed. Please check your API key configuration."
        
        elif any(keyword in error_lower for keyword in ["timeout", "timed out", "connection"]):
            error_type = "GroqConnectionError"
            user_message = "Connection to AI service timed out. Please try again."

        # Save error log
        save_error_log(
            error_type=error_type,
            error_message=error_msg,
            context=context
        )
        
        return user_message
    
    def _validate_client(self) -> bool:
        """
        Validate that client is initialized.
        
        Returns:
            True if client is ready, False otherwise
        """
        if not self.api_key:
            logger.warning("Groq API key not configured")
            return False
        
        if not self.client:
            # Try to reinitialize
            if not self._initialize_client():
                logger.error("Failed to initialize Groq client")
                return False
        
        return True
    
    def chat(
        self, 
        prompt: str, 
        repository_context: Optional[str] = None,
        model_id: Optional[int] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        system_instruction: Optional[str] = None
    ) -> Optional[str]:
        """
        Send a chat message to Groq AI.
        
        Args:
            prompt: User's prompt/question
            repository_context: Context about user's repositories
            model_id: Model ID to use (1 or 2), defaults to DEFAULT_GROQ_MODEL
            conversation_history: List of previous messages with 'role' and 'content' keys
            system_instruction: Optional custom system instruction (defaults to constant)
        
        Returns:
            AI response as string or None if error
        """
        if not self._validate_client():
            return "Groq service is not properly configured. Please check your API key."
        
        try:
            model_name = self._get_model_name(model_id)
            
            # Build system message
            base_system_message = system_instruction or SYSTEM_INSTRUCTION
            if repository_context:
                base_system_message += f"\n\n{repository_context}"
            
            # Build messages array
            messages = [{"role": "system", "content": base_system_message}]
            
            # Add conversation history if available
            if conversation_history:
                for msg in conversation_history:
                    if msg.get("role") in ["user", "assistant"]:
                        messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
            
            # Add current user prompt
            messages.append({"role": "user", "content": prompt})
            
            # Generate response
            response: ChatCompletion = self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
            )
            
            # Validate response
            if not response or not response.choices:
                logger.warning("Empty response from Groq")
                return "I apologize, but I couldn't generate a response. Please try again."
            
            content = response.choices[0].message.content
            if not content:
                logger.warning("Empty content in Groq response")
                return "I apologize, but I couldn't generate a response. Please try again."
            
            return content.strip()
                
        except Exception as e:
            return self._handle_error(e, prompt, model_id)
    
    def chat_stream(
        self, 
        prompt: str, 
        repository_context: Optional[str] = None,
        model_id: Optional[int] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        system_instruction: Optional[str] = None
    ):
        """
        Stream chat responses from Groq AI in real-time.
        Yields chunks of text as they arrive.
        """
        if not self._validate_client():
            yield "Groq service is not properly configured. Please check your API key."
            return
        
        try:
            model_name = self._get_model_name(model_id)
            
            # Build system message
            base_system_message = system_instruction or SYSTEM_INSTRUCTION
            if repository_context:
                base_system_message += f"\n\n{repository_context}"
            
            # Build messages array
            messages = [{"role": "system", "content": base_system_message}]
            
            # Add conversation history
            if conversation_history:
                for msg in conversation_history:
                    if msg.get("role") in ["user", "assistant"]:
                        messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
            
            # Add current prompt
            messages.append({"role": "user", "content": prompt})
            
            # Create streaming completion
            stream = self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                stream=True  # Enable streaming
            )
            
            # Yield chunks as they arrive
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            error_msg = self._handle_error(e, prompt, model_id)
            yield error_msg

