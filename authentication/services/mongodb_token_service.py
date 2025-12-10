"""
MongoDB Refresh Token Service

This module handles JWT refresh token storage in MongoDB.
"""

import os
import certifi
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import uuid

logger = logging.getLogger(__name__)


class MongoDBTokenService:
    """
    Service class for managing JWT refresh tokens in MongoDB.
    
    Tokens are stored in the 'refresh_tokens' collection.
    """
    
    _instance = None
    _client = None
    _db = None
    
    COLLECTION_NAME = 'refresh_tokens'
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBTokenService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self._connect()
            self._ensure_indexes()
    
    def _connect(self):
        """Establish MongoDB connection."""
        try:
            mongodb_uri = os.environ.get('MONGODB_URI')
            db_name = os.environ.get('MONGODB_DB_NAME', 'github_bot_db')
            
            if not mongodb_uri:
                raise ValueError("MONGODB_URI environment variable is not set")
            
            self._client = MongoClient(
                mongodb_uri, 
                serverSelectionTimeoutMS=5000,
                tlsCAFile=certifi.where()
            )
            self._db = self._client[db_name]
            
            self._client.admin.command('ping')
            logger.info("MongoDB Token Service: Successfully connected to MongoDB")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB Token Service: Failed to connect: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"MongoDB Token Service: Unexpected error: {str(e)}")
            raise
    
    def _ensure_indexes(self):
        """Create necessary indexes on the refresh_tokens collection."""
        try:
            collection = self._db[self.COLLECTION_NAME]
            
            # Index on jti for fast lookups
            collection.create_index('jti', unique=True)
            
            # Index on user_email for finding all user tokens
            collection.create_index('user_email')
            
            # Index on expires_at for cleanup
            collection.create_index('expires_at')
            
            # Compound index for token validation
            collection.create_index([('jti', 1), ('is_revoked', 1)])
            
            logger.info("MongoDB Token Service: Indexes created successfully")
            
        except Exception as e:
            logger.error(f"MongoDB Token Service: Error creating indexes: {str(e)}")
    
    @property
    def collection(self):
        """Get the refresh_tokens collection."""
        if self._db is None:
            self._connect()
        return self._db[self.COLLECTION_NAME]
    
    def store_refresh_token(
        self,
        user_email: str,
        token: str,
        jti: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: str = ''
    ) -> Dict[str, Any]:
        """
        Store a new refresh token.
        
        Args:
            user_email: User's email address
            token: The refresh token string
            jti: JWT ID for token identification
            expires_at: Token expiration datetime
            ip_address: Client IP address (optional)
            user_agent: Client user agent string
        
        Returns:
            Created token document
        """
        try:
            token_doc = {
                'user_email': user_email.lower(),
                'token': token,
                'jti': jti,
                'created_at': datetime.utcnow(),
                'expires_at': expires_at,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'is_revoked': False,
                'revoked_at': None,
            }
            
            result = self.collection.insert_one(token_doc)
            token_doc['_id'] = result.inserted_id
            
            logger.debug(f"Stored refresh token for user: {user_email}")
            return token_doc
            
        except Exception as e:
            logger.error(f"Error storing refresh token: {str(e)}")
            raise
    
    def find_token_by_jti(self, jti: str) -> Optional[Dict[str, Any]]:
        """
        Find a refresh token by JTI.
        
        Args:
            jti: JWT ID
        
        Returns:
            Token document or None
        """
        try:
            return self.collection.find_one({'jti': jti})
        except Exception as e:
            logger.error(f"Error finding token by JTI: {str(e)}")
            return None
    
    def find_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Find a refresh token by token string.
        
        Args:
            token: The refresh token string
        
        Returns:
            Token document or None
        """
        try:
            return self.collection.find_one({'token': token})
        except Exception as e:
            logger.error(f"Error finding token: {str(e)}")
            return None
    
    def is_token_valid(self, jti: str) -> bool:
        """
        Check if a token is valid (exists, not revoked, not expired).
        
        Args:
            jti: JWT ID
        
        Returns:
            True if token is valid, False otherwise
        """
        try:
            token = self.collection.find_one({
                'jti': jti,
                'is_revoked': False,
                'expires_at': {'$gt': datetime.utcnow()}
            })
            return token is not None
        except Exception as e:
            logger.error(f"Error checking token validity: {str(e)}")
            return False
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke a refresh token.
        
        Args:
            token: The refresh token string
        
        Returns:
            True if revoked successfully, False otherwise
        """
        try:
            result = self.collection.update_one(
                {'token': token},
                {
                    '$set': {
                        'is_revoked': True,
                        'revoked_at': datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error revoking token: {str(e)}")
            return False
    
    def revoke_token_by_jti(self, jti: str) -> bool:
        """
        Revoke a refresh token by JTI.
        
        Args:
            jti: JWT ID
        
        Returns:
            True if revoked successfully, False otherwise
        """
        try:
            result = self.collection.update_one(
                {'jti': jti},
                {
                    '$set': {
                        'is_revoked': True,
                        'revoked_at': datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error revoking token by JTI: {str(e)}")
            return False
    
    def revoke_all_user_tokens(self, user_email: str) -> int:
        """
        Revoke all refresh tokens for a user.
        
        Args:
            user_email: User's email address
        
        Returns:
            Number of tokens revoked
        """
        try:
            result = self.collection.update_many(
                {'user_email': user_email.lower(), 'is_revoked': False},
                {
                    '$set': {
                        'is_revoked': True,
                        'revoked_at': datetime.utcnow()
                    }
                }
            )
            logger.info(f"Revoked {result.modified_count} tokens for user: {user_email}")
            return result.modified_count
        except Exception as e:
            logger.error(f"Error revoking all user tokens: {str(e)}")
            return 0
    
    def clean_expired_tokens(self) -> int:
        """
        Delete expired tokens from the database.
        
        Returns:
            Number of tokens deleted
        """
        try:
            result = self.collection.delete_many({
                'expires_at': {'$lt': datetime.utcnow()}
            })
            logger.info(f"Cleaned up {result.deleted_count} expired tokens")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error cleaning expired tokens: {str(e)}")
            return 0


# Singleton instance getter
def get_token_service() -> MongoDBTokenService:
    """Get the MongoDB Token Service instance."""
    return MongoDBTokenService()
