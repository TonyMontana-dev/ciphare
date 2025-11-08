#!/usr/bin/env python3
"""
Diagnostic script to test Ciphare setup
Run this to check if your environment is configured correctly
"""

import os
import sys
from dotenv import load_dotenv

def check_env_file():
    """Check if .env file exists"""
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("   Create it by copying env.example: cp env.example .env")
        return False
    print("✅ .env file exists")
    return True

def check_env_vars():
    """Check if required environment variables are set"""
    load_dotenv()
    
    required_vars = {
        'MONGODB_URI': 'MongoDB Atlas connection string',
        'R2_ACCOUNT_ID': 'Cloudflare R2 account ID',
        'R2_ACCESS_KEY_ID': 'R2 API access key ID',
        'R2_SECRET_ACCESS_KEY': 'R2 API secret access key',
        'R2_BUCKET_NAME': 'R2 bucket name',
    }
    
    missing = []
    for var, desc in required_vars.items():
        value = os.getenv(var)
        if not value or value.startswith('your-') or value.startswith('username'):
            print(f"❌ {var} not set or using placeholder value")
            print(f"   Description: {desc}")
            missing.append(var)
        else:
            # Mask sensitive values
            if 'SECRET' in var or 'PASSWORD' in var:
                masked = value[:4] + '...' + value[-4:] if len(value) > 8 else '***'
                print(f"✅ {var} is set ({masked})")
            else:
                print(f"✅ {var} is set")
    
    return len(missing) == 0

def check_python_dependencies():
    """Check if Python dependencies are installed"""
    required_modules = ['flask', 'boto3', 'pymongo', 'cryptography']
    missing = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} is installed")
        except ImportError:
            print(f"❌ {module} is NOT installed")
            missing.append(module)
    
    if missing:
        print(f"\n   Install missing modules: pip3 install {' '.join(missing)}")
        print(f"   Or install all: pip3 install -r requirements.txt")
    
    return len(missing) == 0

def test_mongodb_connection():
    """Test MongoDB connection"""
    try:
        from pymongo import MongoClient
        load_dotenv()
        uri = os.getenv('MONGODB_URI')
        
        if not uri:
            print("❌ MONGODB_URI not set, skipping MongoDB test")
            return False
        
        print("\n🔍 Testing MongoDB connection...")
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        # Try to ping the server
        client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        
        # Test database access
        db = client['ciphare']
        collections = db.list_collection_names()
        print(f"✅ Database 'ciphare' accessible (collections: {len(collections)})")
        return True
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {str(e)}")
        print("   Check:")
        print("   - MongoDB URI is correct")
        print("   - Network access allows your IP")
        print("   - Cluster is running (not paused)")
        return False

def test_r2_connection():
    """Test R2 connection"""
    try:
        import boto3
        load_dotenv()
        
        account_id = os.getenv('R2_ACCOUNT_ID')
        access_key = os.getenv('R2_ACCESS_KEY_ID')
        secret_key = os.getenv('R2_SECRET_ACCESS_KEY')
        bucket_name = os.getenv('R2_BUCKET_NAME')
        
        if not all([account_id, access_key, secret_key, bucket_name]):
            print("❌ R2 credentials not set, skipping R2 test")
            return False
        
        print("\n🔍 Testing R2 connection...")
        client = boto3.client(
            's3',
            endpoint_url=f'https://{account_id}.r2.cloudflarestorage.com',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        
        # Try to list buckets or head bucket
        try:
            client.head_bucket(Bucket=bucket_name)
            print(f"✅ R2 connection successful!")
            print(f"✅ Bucket '{bucket_name}' exists and is accessible")
            return True
        except client.exceptions.NoSuchBucket:
            print(f"❌ Bucket '{bucket_name}' does not exist")
            print("   Create it in Cloudflare R2 dashboard")
            return False
        except Exception as e:
            print(f"❌ R2 bucket access failed: {str(e)}")
            print("   Check:")
            print("   - Bucket name is correct")
            print("   - API token has correct permissions")
            print("   - Account ID is correct")
            return False
            
    except ImportError:
        print("❌ boto3 not installed, skipping R2 test")
        return False
    except Exception as e:
        print(f"❌ R2 connection failed: {str(e)}")
        return False

def test_storage_initialization():
    """Test storage module initialization"""
    try:
        print("\n🔍 Testing storage module...")
        from api.storage import Storage
        storage = Storage()
        print("✅ Storage module initialized successfully!")
        return True
    except Exception as e:
        print(f"❌ Storage initialization failed: {str(e)}")
        return False

def main():
    """Run all diagnostic checks"""
    print("=" * 60)
    print("Ciphare Diagnostic Script")
    print("=" * 60)
    print()
    
    results = []
    
    print("1. Checking .env file...")
    results.append(check_env_file())
    print()
    
    print("2. Checking environment variables...")
    results.append(check_env_vars())
    print()
    
    print("3. Checking Python dependencies...")
    results.append(check_python_dependencies())
    print()
    
    if all(results[:3]):  # Only test connections if basic setup is OK
        print("4. Testing MongoDB connection...")
        results.append(test_mongodb_connection())
        print()
        
        print("5. Testing R2 connection...")
        results.append(test_r2_connection())
        print()
        
        print("6. Testing storage initialization...")
        results.append(test_storage_initialization())
        print()
    
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    if all(results):
        print("✅ All checks passed! Your setup is ready.")
        print("\nYou can now run: npm run dev")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\nSee TROUBLESHOOTING.md for detailed solutions.")
    
    return 0 if all(results) else 1

if __name__ == "__main__":
    sys.exit(main())

