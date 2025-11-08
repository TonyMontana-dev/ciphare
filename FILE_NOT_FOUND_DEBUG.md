# Debugging "File Not Found or Expired" Error

## Issue Analysis

If you successfully encrypted a file but get "File not found or expired" when trying to decrypt, here are the most common causes and fixes:

## Common Causes

### 1. **File ID Mismatch (Most Common)**

**Problem:** The file_id in the share link doesn't match what's stored in the database.

**Symptoms:**
- Encryption succeeds
- Share link is generated
- Decryption fails with "File not found or expired"

**Debugging Steps:**

1. **Check Flask server logs** when encrypting:
   ```
   INFO:api.encode:Generated file_id: <file_id>
   INFO:api.storage:Stored metadata in MongoDB for file_id: <file_id>
   ```

2. **Check Flask server logs** when decrypting:
   ```
   INFO:api.decode:Looking up file_id: <file_id>
   WARNING:api.storage:File not found in MongoDB: <file_id>
   ```

3. **Compare the file_ids** - they should match exactly (case-sensitive, no extra spaces)

**Fixes:**
- ✅ Fixed: Share link now uses query parameter format: `/decode?id={file_id}`
- ✅ Fixed: Decode page now extracts file_id from path, query params, or hash
- ✅ Fixed: Added URL decoding to handle encoded characters

### 2. **URL Encoding Issues**

**Problem:** Special characters in file_id get URL encoded/decoded incorrectly.

**Solution:** The code now properly decodes URL-encoded file_ids using `decodeURIComponent()`.

### 3. **File Expired Immediately**

**Problem:** TTL is set too short or there's a timezone issue.

**Check:**
- Look at the TTL value when encrypting
- Check MongoDB document `expires_at` field
- Verify server time is correct

**Fix:** Ensure TTL is at least 60 seconds (minimum enforced).

### 4. **MongoDB Connection Issues**

**Problem:** File was stored but MongoDB connection fails when retrieving.

**Check Flask logs for:**
```
ERROR:api.storage:Error getting metadata for <file_id>
```

**Solution:** Verify MongoDB connection is stable.

### 5. **R2 File Missing**

**Problem:** Metadata exists in MongoDB but file is missing from R2.

**Check Flask logs for:**
```
ERROR:api.storage:File not found in R2 for file_id: <file_id>
```

**Solution:** Check R2 bucket and verify file exists.

## Enhanced Logging

The code now includes detailed logging to help diagnose issues:

### When Encrypting:
```
INFO:api.encode:Generated file_id: <file_id>
INFO:api.storage:Stored metadata in MongoDB for file_id: <file_id>
DEBUG:api.storage:Verified file_id stored: <file_id>
```

### When Decrypting:
```
INFO:api.decode:Looking up file_id: '<file_id>' (length: X)
DEBUG:api.storage:Looking up metadata for file_id: <file_id> (type: <class 'str'>, length: X)
WARNING:api.storage:File not found in MongoDB: <file_id>
DEBUG:api.storage:Sample file_ids in database: [<sample_ids>]
```

## How to Debug

### Step 1: Check Flask Server Logs

When you try to decrypt, look for these log messages:

```bash
# In the terminal where you ran `npm run dev`, look for Flask output (marked with [1])
[1] INFO:api.decode:Looking up file_id: 'abc123...'
[1] DEBUG:api.storage:Looking up metadata for file_id: abc123...
[1] WARNING:api.storage:File not found in MongoDB: abc123...
```

### Step 2: Verify File Was Stored

Check if the file_id from encryption matches what's being looked up:

**Encryption log:**
```
[1] INFO:api.encode:Generated file_id: abc123xyz
[1] INFO:api.storage:Stored metadata in MongoDB for file_id: abc123xyz
```

**Decryption log:**
```
[1] INFO:api.decode:Looking up file_id: 'abc123xyz'
```

If they don't match exactly, that's the problem!

### Step 3: Check MongoDB Directly (Optional)

If you have MongoDB Compass or CLI access:

```javascript
// Connect to your MongoDB cluster
use ciphare
db.files.find({}, {file_id: 1, created_at: 1, expires_at: 1}).limit(5)
```

This will show you what file_ids are actually in the database.

### Step 4: Check Browser Console

Open browser DevTools (F12) → Console:
- Check if file_id is being extracted correctly from URL
- Look for any JavaScript errors

### Step 5: Test with Direct API Call

Test the decode endpoint directly:

```bash
curl -X POST http://localhost:5328/api/decode/ \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "YOUR_FILE_ID_HERE",
    "password": "your_password",
    "algorithm": "AES256"
  }'
```

Replace `YOUR_FILE_ID_HERE` with the actual file_id from the encryption response.

## Quick Fix Checklist

- [ ] Share link format is `/decode?id={file_id}` (query parameter)
- [ ] File_id in share link matches file_id from encryption response
- [ ] No extra spaces or characters in file_id
- [ ] TTL is at least 60 seconds
- [ ] MongoDB connection is working
- [ ] R2 connection is working
- [ ] Check Flask server logs for detailed error messages

## Still Having Issues?

1. **Copy the exact file_id** from the encryption response
2. **Check Flask server logs** for the exact error
3. **Verify the file_id exists** in MongoDB (if you have access)
4. **Check if file expired** by looking at `expires_at` in MongoDB
5. **Try with a fresh encryption** and immediately decrypt (before any TTL expires)

The enhanced logging should now show you exactly what's happening at each step!

