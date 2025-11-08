# Migration Summary: Redis → MongoDB + R2

## Changes Applied ✅

### 1. Dependencies Updated
- ✅ Added `boto3==1.34.0` for Cloudflare R2 (S3-compatible API)
- ✅ Added `pymongo==4.6.0` for MongoDB Atlas
- ✅ Kept `redis==5.2.0` (for backward compatibility, can be removed later)

### 2. New Files Created
- ✅ `api/storage.py` - Complete storage handler for MongoDB + R2 integration

### 3. Files Modified

#### `api/encode.py`
- ✅ Removed Redis/Upstash dependencies
- ✅ Added MongoDB + R2 storage integration
- ✅ Changed file size limit from 16MB to 500MB
- ✅ Updated to store encrypted files in R2 and metadata in MongoDB

#### `api/decode.py`
- ✅ Removed Redis/Upstash dependencies
- ✅ Added MongoDB + R2 storage integration
- ✅ Updated to retrieve files from R2 and metadata from MongoDB

#### `api/app.py`
- ✅ Updated `MAX_CONTENT_LENGTH` from 16MB to 500MB
- ✅ Updated error message from "16MB" to "500MB"

#### `README.md`
- ✅ Updated tech stack description
- ✅ Updated prerequisites
- ✅ Updated environment variables section
- ✅ Updated file size limits (16MB → 500MB)
- ✅ Added storage architecture section
- ✅ Updated troubleshooting sections
- ✅ Updated project structure

#### `requirements.txt`
- ✅ Added boto3 and pymongo

## Environment Variables Required

You need to set these environment variables:

```env
# MongoDB Atlas
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority

# Cloudflare R2
R2_ACCOUNT_ID=your-account-id
R2_ACCESS_KEY_ID=your-access-key-id
R2_SECRET_ACCESS_KEY=your-secret-access-key
R2_BUCKET_NAME=your-bucket-name

# Application
DOMAIN=https://your-domain.com
CORS_ORIGINS=*
```

## Architecture Changes

### Before (Redis)
```
Encrypted File + Metadata → Redis (16MB limit)
```

### After (MongoDB + R2)
```
Encrypted File → Cloudflare R2 (up to 500MB)
Metadata → MongoDB Atlas (file_id, keys, TTL, reads)
```

## Key Features

1. **File Size Limit**: Increased from 16MB to 500MB
2. **Storage Separation**: 
   - Large files in R2 (10GB free tier)
   - Small metadata in MongoDB (512MB free tier)
3. **Automatic Cleanup**: Expired files are automatically deleted
4. **Read Count Management**: Atomic decrement in MongoDB
5. **Error Handling**: Comprehensive error handling and logging

## Next Steps

1. **Set up MongoDB Atlas**:
   - Create free M0 cluster
   - Get connection string
   - Add to environment variables

2. **Set up Cloudflare R2**:
   - Create R2 bucket
   - Create API token
   - Add credentials to environment variables

3. **Test the migration**:
   - Upload a small file (< 1MB)
   - Upload a medium file (~50MB)
   - Upload a large file (~400MB)
   - Test decryption
   - Test TTL expiration
   - Test read count limits

4. **Deploy**:
   - Update environment variables in your deployment platform
   - Deploy and test

## Breaking Changes

⚠️ **Important**: This migration is **not backward compatible** with the Redis implementation. Old files stored in Redis will not be accessible after this migration.

If you have existing files in Redis:
1. Decrypt and download all files before migration
2. Re-upload them after migration (they'll be stored in R2)

## Testing Checklist

- [ ] Small file upload (< 1MB)
- [ ] Medium file upload (~50MB)
- [ ] Large file upload (~400MB)
- [ ] File upload > 500MB (should fail)
- [ ] File decryption
- [ ] TTL expiration (wait for file to expire)
- [ ] Read count decrement
- [ ] File deletion after reads exhausted
- [ ] Error handling (invalid file_id, wrong password)

## Support

If you encounter any issues:
1. Check environment variables are set correctly
2. Verify MongoDB cluster is accessible
3. Verify R2 bucket exists and credentials are correct
4. Check application logs for detailed error messages

