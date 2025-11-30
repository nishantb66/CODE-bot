"""
MongoDB database connection and operations utility.
"""
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MongoDBConnection:
    """Singleton MongoDB connection manager."""
    
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBConnection, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self._connect()
    
    def _connect(self):
        """Establish MongoDB connection."""
        try:
            mongodb_uri = os.environ.get('MONGODB_URI')
            db_name = os.environ.get('MONGODB_DB_NAME', 'github_bot_db')
            
            if not mongodb_uri:
                raise ValueError("MONGODB_URI environment variable is not set")
            
            self._client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            self._db = self._client[db_name]
            
            # Test connection
            self._client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {str(e)}")
            raise
    
    @property
    def db(self):
        """Get database instance."""
        if self._db is None:
            self._connect()
        return self._db
    
    def get_collection(self, collection_name: str):
        """Get a MongoDB collection."""
        return self.db[collection_name]
    
    def close(self):
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None


def get_db():
    """Get MongoDB database instance."""
    connection = MongoDBConnection()
    return connection.db


def save_chat_log(prompt: str, response: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Save chat log to MongoDB.
    
    Args:
        prompt: User's prompt/question
        response: AI's response
        metadata: Additional metadata (optional)
    
    Returns:
        Document ID as string
    """
    try:
        db = get_db()
        collection = db["chat_logs"]
        
        document = {
            "prompt": prompt,
            "response": response,
            "timestamp": datetime.utcnow(),
            "metadata": metadata or {}
        }
        
        result = collection.insert_one(document)
        logger.info(f"Chat log saved with ID: {result.inserted_id}")
        return str(result.inserted_id)
        
    except Exception as e:
        logger.error(f"Error saving chat log: {str(e)}")
        raise


def save_request_log(request_data: Dict[str, Any], response_data: Dict[str, Any], 
                    status_code: int, duration_ms: float) -> str:
    """
    Save request/response log to MongoDB.
    
    Args:
        request_data: Request data
        response_data: Response data
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
    
    Returns:
        Document ID as string
    """
    try:
        db = get_db()
        collection = db["request_logs"]
        
        document = {
            "request": request_data,
            "response": response_data,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow()
        }
        
        result = collection.insert_one(document)
        logger.info(f"Request log saved with ID: {result.inserted_id}")
        return str(result.inserted_id)
        
    except Exception as e:
        logger.error(f"Error saving request log: {str(e)}")
        raise


def save_error_log(error_type: str, error_message: str, 
                  stack_trace: Optional[str] = None, 
                  context: Optional[Dict[str, Any]] = None) -> str:
    """
    Save error log to MongoDB.
    
    Args:
        error_type: Type of error
        error_message: Error message
        stack_trace: Stack trace (optional)
        context: Additional context (optional)
    
    Returns:
        Document ID as string
    """
    try:
        db = get_db()
        collection = db["error_logs"]
        
        document = {
            "error_type": error_type,
            "error_message": error_message,
            "stack_trace": stack_trace,
            "context": context or {},
            "timestamp": datetime.utcnow()
        }
        
        result = collection.insert_one(document)
        logger.error(f"Error log saved with ID: {result.inserted_id}")
        return str(result.inserted_id)
        
    except Exception as e:
        logger.error(f"Error saving error log: {str(e)}")
        raise


def save_conversation_message(conversation_id: str, role: str, content: str, 
                             metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Save a conversation message to MongoDB.
    
    Args:
        conversation_id: Unique conversation/session ID
        role: Message role ('user' or 'assistant')
        content: Message content
        metadata: Additional metadata (optional)
    
    Returns:
        Document ID as string
    """
    try:
        db = get_db()
        collection = db["conversations"]
        
        document = {
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow(),
            "metadata": metadata or {}
        }
        
        result = collection.insert_one(document)
        logger.debug(f"Conversation message saved with ID: {result.inserted_id}")
        return str(result.inserted_id)
        
    except Exception as e:
        logger.error(f"Error saving conversation message: {str(e)}")
        raise


def get_conversation_history(conversation_id: str, max_messages: int = 10, 
                            max_tokens_estimate: int = 2000) -> list:
    """
    Get conversation history for a given conversation ID.
    Returns messages in chronological order, limited by count and token estimate.
    
    Args:
        conversation_id: Unique conversation/session ID
        max_messages: Maximum number of messages to retrieve (default: 10)
        max_tokens_estimate: Maximum estimated tokens (rough estimate: 1 token ≈ 4 chars)
    
    Returns:
        List of message dictionaries with 'role' and 'content' keys
    """
    try:
        db = get_db()
        collection = db["conversations"]
        
        # Get recent messages for this conversation, ordered by timestamp
        cursor = collection.find(
            {"conversation_id": conversation_id}
        ).sort("timestamp", 1).limit(max_messages * 2)  # Get more to filter by tokens
        
        messages = []
        total_chars = 0
        
        for doc in cursor:
            content = doc.get("content", "")
            content_length = len(content)
            
            # Rough token estimate: 1 token ≈ 4 characters
            estimated_tokens = content_length / 4
            
            # Check if adding this message would exceed token limit
            if total_chars + content_length > max_tokens_estimate * 4:
                break
            
            messages.append({
                "role": doc.get("role", "user"),
                "content": content
            })
            
            total_chars += content_length
            
            # Also limit by message count
            if len(messages) >= max_messages:
                break
        
        logger.info(f"Retrieved {len(messages)} messages for conversation {conversation_id}")
        return messages
        
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {str(e)}")
        return []


def clear_conversation(conversation_id: str) -> bool:
    """
    Clear all messages for a conversation.
    
    Args:
        conversation_id: Unique conversation/session ID
    
    Returns:
        True if successful, False otherwise
    """
    try:
        db = get_db()
        collection = db["conversations"]
        
        result = collection.delete_many({"conversation_id": conversation_id})
        logger.info(f"Cleared {result.deleted_count} messages for conversation {conversation_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error clearing conversation: {str(e)}")
        return False

