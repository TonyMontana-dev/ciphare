"""
Storage module for MongoDB (metadata) and Cloudflare R2 (files)
"""
import boto3
from pymongo import MongoClient
from datetime import datetime, timedelta
import os
import logging
import base64

logger = logging.getLogger(__name__)

class Storage:
    """Handles storage operations for MongoDB (metadata) and R2 (files)"""
    
    def __init__(self):
        # MongoDB setup
        mongodb_uri = os.getenv("MONGODB_URI")
        if not mongodb_uri:
            raise ValueError("MONGODB_URI environment variable must be set")
        
        self.mongo_client = MongoClient(mongodb_uri)
        self.db = self.mongo_client['ciphare']
        self.files_collection = self.db['files']
        
        # Create indexes for better performance
        try:
            self.files_collection.create_index("file_id", unique=True)
            self.files_collection.create_index("expires_at")
        except Exception as e:
            logger.warning(f"Index creation warning (may already exist): {e}")
        
        # R2 (S3-compatible) setup
        r2_account_id = os.getenv("R2_ACCOUNT_ID")
        r2_access_key_id = os.getenv("R2_ACCESS_KEY_ID")
        r2_secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY")
        r2_bucket_name = os.getenv("R2_BUCKET_NAME")
        
        if not all([r2_account_id, r2_access_key_id, r2_secret_access_key, r2_bucket_name]):
            raise ValueError("R2 environment variables must be set: R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME")
        
        self.r2_client = boto3.client(
            's3',
            endpoint_url=f'https://{r2_account_id}.r2.cloudflarestorage.com',
            aws_access_key_id=r2_access_key_id,
            aws_secret_access_key=r2_secret_access_key
        )
        self.bucket_name = r2_bucket_name
        
        logger.info("Storage initialized: MongoDB + R2")
    
    def store_file(self, file_id, encrypted_data, metadata):
        """
        Store encrypted file in R2 and metadata in MongoDB
        
        Args:
            file_id: Unique file identifier
            encrypted_data: Encrypted file bytes
            metadata: Dict containing file_name, file_type, iv, salt, tag, reads, ttl_seconds
        """
        try:
            # Store encrypted file in R2
            r2_key = f"encrypted/{file_id}.bin"
            self.r2_client.put_object(
                Bucket=self.bucket_name,
                Key=r2_key,
                Body=encrypted_data,
                ContentType='application/octet-stream'
            )
            logger.debug(f"Stored file in R2: {r2_key}")
            
            # Calculate expiration
            expires_at = datetime.utcnow() + timedelta(seconds=metadata['ttl_seconds'])
            
            # Store metadata in MongoDB
            doc = {
                'file_id': file_id,
                'file_name': metadata['file_name'],
                'file_type': metadata['file_type'],
                'iv': metadata['iv'],  # Base64 encoded
                'salt': metadata['salt'],  # Base64 encoded
                'tag': metadata['tag'],  # Base64 encoded
                'reads': metadata['reads'],
                'ttl_seconds': metadata['ttl_seconds'],
                'created_at': datetime.utcnow(),
                'expires_at': expires_at,
                'r2_key': r2_key
            }
            
            self.files_collection.insert_one(doc)
            logger.info(f"Stored metadata in MongoDB for file_id: {file_id}")
            
            # Verify the insert was successful
            verify_doc = self.files_collection.find_one({'file_id': file_id})
            if verify_doc:
                logger.debug(f"Verified file_id stored: {file_id}")
            else:
                logger.error(f"WARNING: File_id {file_id} was not found after insert!")
            
        except Exception as e:
            logger.error(f"Error storing file {file_id}: {str(e)}", exc_info=True)
            # Cleanup: try to delete from R2 if MongoDB insert failed
            try:
                self.r2_client.delete_object(Bucket=self.bucket_name, Key=r2_key)
            except:
                pass
            raise
    
    def get_metadata(self, file_id):
        """
        Get file metadata from MongoDB
        
        Args:
            file_id: Unique file identifier
            
        Returns:
            Dict with metadata or None if not found
        """
        try:
            logger.debug(f"Looking up metadata for file_id: {file_id} (type: {type(file_id)}, length: {len(file_id) if file_id else 0})")
            doc = self.files_collection.find_one({'file_id': file_id})
            if not doc:
                # Try to find any similar file_ids for debugging
                logger.warning(f"File not found in MongoDB: {file_id}")
                # Log a sample of existing file_ids for debugging (limit to 5)
                sample_docs = list(self.files_collection.find({}, {'file_id': 1}).limit(5))
                if sample_docs:
                    sample_ids = [d.get('file_id') for d in sample_docs]
                    logger.debug(f"Sample file_ids in database: {sample_ids}")
                return None
            
            logger.debug(f"Found metadata for file_id: {file_id}")
            
            # Check if expired
            if doc.get('expires_at') and datetime.utcnow() > doc['expires_at']:
                logger.info(f"File {file_id} has expired, deleting...")
                self.delete_file(file_id)
                return None
            
            # Convert ObjectId to string and datetime to ISO string for JSON serialization
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
            if 'created_at' in doc and isinstance(doc['created_at'], datetime):
                doc['created_at'] = doc['created_at'].isoformat()
            if 'expires_at' in doc and isinstance(doc['expires_at'], datetime):
                doc['expires_at'] = doc['expires_at'].isoformat()
            
            return doc
        except Exception as e:
            logger.error(f"Error getting metadata for {file_id}: {str(e)}", exc_info=True)
            return None
    
    def get_file(self, file_id):
        """
        Get encrypted file from R2
        
        Args:
            file_id: Unique file identifier
            
        Returns:
            Encrypted file bytes or None if not found
        """
        try:
            # Get metadata to find R2 key
            logger.debug(f"Getting file from R2 for file_id: {file_id}")
            metadata = self.get_metadata(file_id)
            if not metadata:
                logger.warning(f"Cannot get file from R2: metadata not found for file_id: {file_id}")
                return None
            
            r2_key = metadata.get('r2_key', f"encrypted/{file_id}.bin")
            logger.debug(f"Retrieving file from R2 with key: {r2_key}")
            
            # Get file from R2
            response = self.r2_client.get_object(
                Bucket=self.bucket_name,
                Key=r2_key
            )
            
            file_data = response['Body'].read()
            logger.info(f"Retrieved file from R2: {r2_key}, size: {len(file_data)} bytes")
            return file_data
            
        except self.r2_client.exceptions.NoSuchKey:
            logger.error(f"File not found in R2 for file_id: {file_id}, r2_key: {r2_key if 'r2_key' in locals() else 'unknown'}")
            return None
        except Exception as e:
            logger.error(f"Error getting file {file_id} from R2: {str(e)}", exc_info=True)
            return None
    
    def decrement_reads(self, file_id):
        """
        Decrement read count for a file
        
        Args:
            file_id: Unique file identifier
            
        Returns:
            New read count or None if file not found
        """
        try:
            result = self.files_collection.find_one_and_update(
                {'file_id': file_id},
                {'$inc': {'reads': -1}},
                return_document=True
            )
            
            if not result:
                return None
            
            remaining_reads = result['reads']
            logger.debug(f"Decremented reads for {file_id}, remaining: {remaining_reads}")
            
            # Delete if reads exhausted
            if remaining_reads <= 0:
                logger.info(f"Reads exhausted for {file_id}, deleting...")
                self.delete_file(file_id)
            
            return remaining_reads
            
        except Exception as e:
            logger.error(f"Error decrementing reads for {file_id}: {str(e)}", exc_info=True)
            return None
    
    def delete_file(self, file_id):
        """
        Delete file from both R2 and MongoDB
        
        Args:
            file_id: Unique file identifier
        """
        try:
            # Get metadata to find R2 key
            metadata = self.files_collection.find_one({'file_id': file_id})
            if metadata:
                r2_key = metadata.get('r2_key', f"encrypted/{file_id}.bin")
                
                # Delete from R2
                try:
                    self.r2_client.delete_object(
                        Bucket=self.bucket_name,
                        Key=r2_key
                    )
                    logger.debug(f"Deleted file from R2: {r2_key}")
                except Exception as e:
                    logger.warning(f"Error deleting from R2: {str(e)}")
                
                # Delete from MongoDB
                self.files_collection.delete_one({'file_id': file_id})
                logger.debug(f"Deleted metadata from MongoDB: {file_id}")
            else:
                logger.warning(f"File {file_id} not found in MongoDB, skipping deletion")
                
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {str(e)}", exc_info=True)
    
    def cleanup_expired(self):
        """
        Cleanup expired files (can be called by a background job)
        """
        try:
            now = datetime.utcnow()
            expired = self.files_collection.find({'expires_at': {'$lt': now}})
            
            count = 0
            for doc in expired:
                self.delete_file(doc['file_id'])
                count += 1
            
            logger.info(f"Cleaned up {count} expired files")
            return count
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}", exc_info=True)
            return 0

