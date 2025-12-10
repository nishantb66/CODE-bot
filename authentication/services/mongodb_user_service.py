"""
MongoDB User Service

This module handles user operations in MongoDB for Google SSO authentication.
Users are stored in the 'users' collection.
"""

import os
import certifi
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, DuplicateKeyError
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class MongoDBUserService:
    """
    Service class for managing users in MongoDB.
    
    All authentication is Google SSO only.
    Users are stored in the 'users' collection.
    """
    
    _instance = None
    _client = None
    _db = None
    
    COLLECTION_NAME = 'users'
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBUserService, cls).__new__(cls)
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
            
            # Use certifi for SSL certificate verification
            self._client = MongoClient(
                mongodb_uri, 
                serverSelectionTimeoutMS=5000,
                tlsCAFile=certifi.where()
            )
            self._db = self._client[db_name]
            
            # Test connection
            self._client.admin.command('ping')
            logger.info("MongoDB User Service: Successfully connected to MongoDB")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB User Service: Failed to connect to MongoDB: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"MongoDB User Service: Unexpected error connecting to MongoDB: {str(e)}")
            raise
    
    def _ensure_indexes(self):
        """Create necessary indexes on the users collection."""
        try:
            collection = self._db[self.COLLECTION_NAME]
            
            # Create unique index on email
            collection.create_index('email', unique=True)
            
            # Create index on google_id for faster lookups
            collection.create_index('google_id', unique=True, sparse=True)
            
            logger.info("MongoDB User Service: Indexes created successfully")
            
        except Exception as e:
            logger.error(f"MongoDB User Service: Error creating indexes: {str(e)}")
    
    @property
    def collection(self):
        """Get the users collection."""
        if self._db is None:
            self._connect()
        return self._db[self.COLLECTION_NAME]
    
    def find_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Find a user by email address.
        
        Args:
            email: User's email address (case-insensitive)
        
        Returns:
            User document or None if not found
        """
        try:
            user = self.collection.find_one({'email': email.lower()})
            return user
        except Exception as e:
            logger.error(f"Error finding user by email: {str(e)}")
            return None
    
    def find_user_by_google_id(self, google_id: str) -> Optional[Dict[str, Any]]:
        """
        Find a user by Google ID.
        
        Args:
            google_id: Google OAuth user ID
        
        Returns:
            User document or None if not found
        """
        try:
            user = self.collection.find_one({'google_id': google_id})
            return user
        except Exception as e:
            logger.error(f"Error finding user by Google ID: {str(e)}")
            return None
    
    def find_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Find a user by MongoDB _id.
        
        Args:
            user_id: MongoDB document ID as string
        
        Returns:
            User document or None if not found
        """
        try:
            from bson import ObjectId
            user = self.collection.find_one({'_id': ObjectId(user_id)})
            return user
        except Exception as e:
            logger.error(f"Error finding user by ID: {str(e)}")
            return None
    
    def user_exists(self, email: str) -> bool:
        """
        Check if a user exists by email.
        
        Args:
            email: User's email address
        
        Returns:
            True if user exists, False otherwise
        """
        return self.find_user_by_email(email) is not None
    
    def create_user(self, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user from Google SSO user info.
        
        Args:
            user_info: User information from Google OAuth containing:
                - email: User's email
                - name: User's display name
                - google_id: Google OAuth user ID
                - first_name: (optional) First name
                - last_name: (optional) Last name
                - profile_picture: (optional) Profile picture URL
        
        Returns:
            Created user document
        
        Raises:
            DuplicateKeyError: If user with email already exists
        """
        try:
            now = datetime.utcnow()
            
            user_doc = {
                'email': user_info['email'].lower(),
                'name': user_info.get('name', ''),
                'first_name': user_info.get('first_name', ''),
                'last_name': user_info.get('last_name', ''),
                'google_id': user_info.get('google_id'),
                'profile_picture': user_info.get('profile_picture', ''),
                'auth_provider': 'google',
                'is_active': True,
                'is_email_verified': user_info.get('email_verified', True),
                'created_at': now,
                'updated_at': now,
                'last_login': now,
            }
            
            result = self.collection.insert_one(user_doc)
            user_doc['_id'] = result.inserted_id
            
            logger.info(f"MongoDB User Service: Created new user with email: {user_doc['email']}")
            return user_doc
            
        except DuplicateKeyError:
            logger.warning(f"MongoDB User Service: User with email {user_info['email']} already exists")
            raise
        except Exception as e:
            logger.error(f"MongoDB User Service: Error creating user: {str(e)}")
            raise
    
    def update_user_login(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Update user's last login timestamp.
        
        Args:
            email: User's email address
        
        Returns:
            Updated user document or None
        """
        try:
            result = self.collection.find_one_and_update(
                {'email': email.lower()},
                {
                    '$set': {
                        'last_login': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    }
                },
                return_document=True
            )
            return result
        except Exception as e:
            logger.error(f"MongoDB User Service: Error updating user login: {str(e)}")
            return None
    
    def update_user(self, email: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update user data.
        
        Args:
            email: User's email address
            update_data: Dictionary of fields to update
        
        Returns:
            Updated user document or None
        """
        try:
            update_data['updated_at'] = datetime.utcnow()
            
            result = self.collection.find_one_and_update(
                {'email': email.lower()},
                {'$set': update_data},
                return_document=True
            )
            return result
        except Exception as e:
            logger.error(f"MongoDB User Service: Error updating user: {str(e)}")
            return None


# Singleton instance getter
def get_user_service() -> MongoDBUserService:
    """Get the MongoDB User Service instance."""
    return MongoDBUserService()
