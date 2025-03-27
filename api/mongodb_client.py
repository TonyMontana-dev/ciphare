from pymongo import MongoClient
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

# Global MongoDB client instance
_mongodb_client = None

def get_db():
    """Get the MongoDB database instance."""
    global _mongodb_client
    if _mongodb_client is None:
        try:
            # Get MongoDB URI from environment
            mongodb_uri = os.getenv('MONGODB_URI')
            if not mongodb_uri:
                raise ValueError("MONGODB_URI environment variable is not set")
            
            logger.debug(f"Attempting to connect to MongoDB with URI: {mongodb_uri}")
            
            # Initialize MongoDB client with connection timeout
            client = MongoClient(
                mongodb_uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=5000
            )
            
            # Test the connection
            client.server_info()
            logger.info("Successfully connected to MongoDB")
            
            # Get the database
            _mongodb_client = client.ciphare
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    return _mongodb_client

class MongoDBClient:
    def __init__(self):
        try:
            # Get MongoDB URI from environment
            mongodb_uri = os.getenv('MONGODB_URI')
            if not mongodb_uri:
                raise ValueError("MONGODB_URI environment variable is not set")
            
            logger.debug(f"Attempting to connect to MongoDB with URI: {mongodb_uri}")
            
            # Initialize MongoDB client with connection timeout
            self.client = MongoClient(
                mongodb_uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=5000
            )
            
            # Test the connection
            self.client.server_info()
            logger.info("Successfully connected to MongoDB")
            
            # Initialize database and collections
            self.db = self.client.ciphare
            self.files = self.db.files
            self.posts = self.db.posts
            self.comments = self.db.comments
            
            # Create indexes
            self._create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    def _create_indexes(self):
        try:
            # Files collection indexes
            self.files.create_index([("file_id", 1)], unique=True)
            self.files.create_index([("expires_at", 1)], expireAfterSeconds=0)
            
            # Posts collection indexes
            self.posts.create_index([("created_at", -1)])
            self.posts.create_index([("expires_at", 1)], expireAfterSeconds=0)
            
            # Comments collection indexes
            self.comments.create_index([("comment_id", 1)], unique=True)
            self.comments.create_index([("post_id", 1)])
            self.comments.create_index([("created_at", -1)])
            
            logger.info("Successfully created MongoDB indexes")
        except Exception as e:
            logger.error(f"Failed to create MongoDB indexes: {str(e)}")
            raise

    def store_file_metadata(self, file_id: str, metadata: Dict[str, Any]) -> bool:
        """Store file metadata in MongoDB"""
        try:
            metadata['file_id'] = file_id
            metadata['created_at'] = datetime.utcnow()
            
            # Convert TTL seconds to timedelta
            ttl_seconds = metadata.get('ttl', 0)
            metadata['expires_at'] = datetime.utcnow() + timedelta(seconds=ttl_seconds)
            
            logger.debug(f"Storing file metadata for file_id: {file_id}")
            result = self.files.insert_one(metadata)
            
            if result.inserted_id:
                logger.info(f"Successfully stored metadata for file_id: {file_id}")
                return True
            else:
                logger.error(f"Failed to store metadata for file_id: {file_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error storing file metadata: {str(e)}")
            return False

    def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve file metadata from MongoDB"""
        try:
            logger.debug(f"Retrieving metadata for file_id: {file_id}")
            metadata = self.files.find_one({"file_id": file_id})
            
            if metadata:
                logger.info(f"Successfully retrieved metadata for file_id: {file_id}")
                return metadata
            else:
                logger.warning(f"No metadata found for file_id: {file_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving file metadata: {str(e)}")
            return None

    def update_file_reads(self, file_id: str) -> bool:
        """Update the number of reads for a file"""
        try:
            logger.debug(f"Updating reads for file_id: {file_id}")
            result = self.files.update_one(
                {"file_id": file_id, "reads": {"$gt": 0}},  # Only update if reads > 0
                {"$inc": {"reads": -1}}  # Decrement reads by 1
            )
            
            if result.modified_count > 0:
                logger.info(f"Successfully updated reads for file_id: {file_id}")
                return True
            else:
                logger.warning(f"No document updated for file_id: {file_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating file reads: {str(e)}")
            return False

    def create_post(self, post_data: Dict[str, Any]) -> bool:
        """Create a new post in the community forum"""
        try:
            post_data['created_at'] = datetime.utcnow()
            post_data['likes'] = 0
            post_data['dislikes'] = 0
            
            logger.debug(f"Creating new post with data: {post_data}")
            result = self.posts.insert_one(post_data)
            
            if result.inserted_id:
                logger.info(f"Successfully created post with ID: {result.inserted_id}")
                return True
            else:
                logger.error("Failed to create post")
                return False
                
        except Exception as e:
            logger.error(f"Error creating post: {str(e)}")
            return False

    def get_posts(self, limit: int = 10, skip: int = 0) -> list:
        """Retrieve posts with pagination"""
        try:
            logger.debug(f"Retrieving posts with limit: {limit}, skip: {skip}")
            posts = list(self.posts.find().sort("created_at", -1).skip(skip).limit(limit))
            logger.info(f"Successfully retrieved {len(posts)} posts")
            return posts
        except Exception as e:
            logger.error(f"Error retrieving posts: {str(e)}")
            return []

    def create_comment(self, comment_data: Dict[str, Any]) -> bool:
        """Create a new comment on a post"""
        try:
            comment_data['created_at'] = datetime.utcnow()
            
            logger.debug(f"Creating new comment with data: {comment_data}")
            result = self.comments.insert_one(comment_data)
            
            if result.inserted_id:
                logger.info(f"Successfully created comment with ID: {result.inserted_id}")
                return True
            else:
                logger.error("Failed to create comment")
                return False
                
        except Exception as e:
            logger.error(f"Error creating comment: {str(e)}")
            return False

    def get_comments(self, post_id: str) -> list:
        """Retrieve comments for a specific post"""
        try:
            logger.debug(f"Retrieving comments for post_id: {post_id}")
            comments = list(self.comments.find({"post_id": post_id}).sort("created_at", -1))
            logger.info(f"Successfully retrieved {len(comments)} comments")
            return comments
        except Exception as e:
            logger.error(f"Error retrieving comments: {str(e)}")
            return []

    def update_post_reaction(self, post_id: str, reaction_type: str) -> bool:
        """Update post likes/dislikes"""
        try:
            update_field = "likes" if reaction_type == "like" else "dislikes"
            logger.debug(f"Updating {update_field} for post_id: {post_id}")
            
            result = self.posts.update_one(
                {"post_id": post_id},
                {"$inc": {update_field: 1}}
            )
            
            if result.modified_count > 0:
                logger.info(f"Successfully updated {update_field} for post_id: {post_id}")
                return True
            else:
                logger.warning(f"No document updated for post_id: {post_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating post reaction: {str(e)}")
            return False

# Create a singleton instance
try:
    mongodb_client = MongoDBClient()
except Exception as e:
    logger.error(f"Failed to initialize MongoDB client: {str(e)}")
    raise 