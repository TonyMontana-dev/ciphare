# Troubleshooting Guide - Encryption Failures

## Common Encryption Errors & Solutions

### 1. "Storage service unavailable"

**Error Message:**
```
Storage service unavailable. Please check MongoDB and R2 configuration.
```

**Causes:**
- Missing environment variables
- MongoDB connection failed
- R2 connection failed
- Dependencies not installed

**Solutions:**

1. **Check environment variables:**
   ```bash
   # Verify .env file exists and has all required variables
   cat .env | grep -E "MONGODB_URI|R2_"
   ```

2. **Install Python dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Test MongoDB connection:**
   ```bash
   python3 -c "from pymongo import MongoClient; import os; from dotenv import load_dotenv; load_dotenv(); client = MongoClient(os.getenv('MONGODB_URI')); print('✅ MongoDB connected')"
   ```

4. **Test R2 connection:**
   ```bash
   python3 -c "import boto3; import os; from dotenv import load_dotenv; load_dotenv(); client = boto3.client('s3', endpoint_url=f'https://{os.getenv(\"R2_ACCOUNT_ID\")}.r2.cloudflarestorage.com', aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'), aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY')); print('✅ R2 connected')"
   ```

### 2. "Database connection failed"

**Error Message:**
```
Database connection failed. Please check MongoDB configuration.
```

**Causes:**
- Invalid MongoDB URI
- Network access not configured
- Wrong username/password
- Cluster is paused

**Solutions:**

1. **Verify MongoDB URI format:**
   ```
   mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
   ```

2. **Check network access:**
   - Go to MongoDB Atlas → Network Access
   - Add your IP address (or `0.0.0.0/0` for testing)
   - Wait a few minutes for changes

3. **Verify credentials:**
   - Check username and password are correct
   - Ensure special characters in password are URL-encoded

4. **Check cluster status:**
   - Ensure cluster is running (not paused)
   - Free tier clusters may pause after inactivity

### 3. "File storage connection failed"

**Error Message:**
```
File storage connection failed. Please check R2 configuration.
```

**Causes:**
- Invalid R2 credentials
- Bucket doesn't exist
- Wrong Account ID
- API token expired or revoked

**Solutions:**

1. **Verify R2 credentials:**
   - Check all 4 variables are set:
     - `R2_ACCOUNT_ID`
     - `R2_ACCESS_KEY_ID`
     - `R2_SECRET_ACCESS_KEY`
     - `R2_BUCKET_NAME`

2. **Verify bucket exists:**
   - Go to Cloudflare R2 dashboard
   - Check bucket name matches exactly (case-sensitive)

3. **Check API token:**
   - Go to R2 → Manage R2 API Tokens
   - Verify token is active
   - Check token has Object Read & Write permissions

4. **Verify Account ID:**
   - Found in R2 dashboard URL or settings
   - Should be a long alphanumeric string

### 4. "Invalid Base64 file_data"

**Error Message:**
```
Invalid Base64 file_data
```

**Causes:**
- File encoding issue in frontend
- Corrupted file data
- Network transmission error

**Solutions:**

1. **Check browser console:**
   - Look for JavaScript errors
   - Verify file is being read correctly

2. **Test with small file:**
   - Try uploading a small text file first
   - If small files work, issue might be with large files

3. **Check network:**
   - Verify request is reaching backend
   - Check for CORS errors

### 5. "File size exceeds 500MB limit"

**Error Message:**
```
File size exceeds 500MB limit. File size: XXX.XXMB
```

**Solutions:**
- Use a file smaller than 500MB
- Compress the file before uploading
- Split large files into smaller parts

### 6. "Password is required"

**Error Message:**
```
Password is required
```

**Solutions:**
- Ensure password field is filled
- Check password is not empty string
- Verify password is being sent in request

### 7. "ModuleNotFoundError: No module named 'boto3'"

**Error Message:**
```
ModuleNotFoundError: No module named 'boto3'
```

**Solutions:**
```bash
pip3 install -r requirements.txt
```

### 8. "ModuleNotFoundError: No module named 'pymongo'"

**Error Message:**
```
ModuleNotFoundError: No module named 'pymongo'
```

**Solutions:**
```bash
pip3 install -r requirements.txt
```

## Debugging Steps

### Step 1: Check Flask Server Logs

When running `npm run dev`, look for Flask server output (usually marked with `[1]`):

```
[1] ERROR:api.storage:Failed to initialize storage: ...
[1] ERROR:api.encode:Error during encoding: ...
```

### Step 2: Check Browser Console

Open browser DevTools (F12) → Console tab:
- Look for JavaScript errors
- Check network requests to `/api/encode`
- Verify request/response payloads

### Step 3: Check Network Tab

In browser DevTools → Network tab:
- Find the `/api/encode` request
- Check request payload
- Check response status and body
- Look for error messages in response

### Step 4: Test Storage Initialization

```bash
python3 -c "
from dotenv import load_dotenv
load_dotenv()
from api.storage import Storage
try:
    s = Storage()
    print('✅ Storage initialized successfully')
except Exception as e:
    print(f'❌ Storage initialization failed: {e}')
"
```

### Step 5: Test API Endpoint Directly

```bash
# Test with curl
curl -X POST http://localhost:5328/api/encode/ \
  -H "Content-Type: application/json" \
  -d '{
    "file_data": "SGVsbG8gV29ybGQ=",
    "file_name": "test.txt",
    "file_type": "text/plain",
    "password": "test123",
    "reads": 1,
    "ttl": 3600,
    "algorithm": "AES256"
  }'
```

## Quick Diagnostic Checklist

- [ ] `.env` file exists in root directory
- [ ] All required environment variables are set
- [ ] Python dependencies installed: `pip3 install -r requirements.txt`
- [ ] Node.js dependencies installed: `npm install`
- [ ] MongoDB cluster is running (not paused)
- [ ] MongoDB network access allows your IP
- [ ] R2 bucket exists and is accessible
- [ ] R2 API token is active with correct permissions
- [ ] Flask server is running on port 5328
- [ ] Next.js server is running on port 3000
- [ ] No port conflicts
- [ ] Browser console shows no errors

## Getting More Detailed Error Messages

The error handling has been improved to show actual error messages from the backend. Check:

1. **Browser console** - Shows the actual error message
2. **Flask server logs** - Shows detailed Python errors
3. **Network tab** - Shows API response with error details

## Still Having Issues?

1. Check the Flask server terminal output for detailed error messages
2. Check browser console for JavaScript errors
3. Verify all environment variables are set correctly
4. Test storage initialization separately (see Step 4 above)
5. Try with a very small file first to isolate the issue

