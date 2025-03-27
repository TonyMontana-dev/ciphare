import boto3
from botocore.config import Config
import os
from typing import Optional, BinaryIO
from datetime import datetime, timedelta
import uuid
from dotenv import load_dotenv

load_dotenv()

class StorageService:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=os.getenv('DO_SPACES_ENDPOINT'),
            aws_access_key_id=os.getenv('DO_SPACES_KEY'),
            aws_secret_access_key=os.getenv('DO_SPACES_SECRET'),
            region_name=os.getenv('DO_SPACES_REGION'),
            config=Config(signature_version='s3v4')
        )
        self.bucket_name = os.getenv('DO_SPACES_BUCKET')
        
    def upload_file(self, file: BinaryIO, original_filename: str) -> Optional[str]:
        """Upload a file to DigitalOcean Spaces and return the file ID"""
        try:
            # Generate a unique file ID
            file_id = str(uuid.uuid4())
            
            # Get file extension from original filename
            file_extension = os.path.splitext(original_filename)[1]
            
            # Create the object key (path in the bucket)
            object_key = f"{file_id}{file_extension}"
            
            # Upload the file
            self.s3_client.upload_fileobj(
                file,
                self.bucket_name,
                object_key,
                ExtraArgs={
                    'ContentType': file.content_type if hasattr(file, 'content_type') else 'application/octet-stream',
                    'ACL': 'private'
                }
            )
            
            return file_id
        except Exception as e:
            print(f"Error uploading file: {e}")
            return None
    
    def get_file(self, file_id: str, file_extension: str) -> Optional[BinaryIO]:
        """Retrieve a file from DigitalOcean Spaces"""
        try:
            object_key = f"{file_id}{file_extension}"
            
            # Get the file object
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            return response['Body']
        except Exception as e:
            print(f"Error retrieving file: {e}")
            return None
    
    def delete_file(self, file_id: str, file_extension: str) -> bool:
        """Delete a file from DigitalOcean Spaces"""
        try:
            object_key = f"{file_id}{file_extension}"
            
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            return True
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
    
    def generate_presigned_url(self, file_id: str, file_extension: str, expires_in: int = 3600) -> Optional[str]:
        """Generate a presigned URL for temporary file access"""
        try:
            object_key = f"{file_id}{file_extension}"
            
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expires_in
            )
            
            return url
        except Exception as e:
            print(f"Error generating presigned URL: {e}")
            return None

# Create a singleton instance
storage_service = StorageService() 