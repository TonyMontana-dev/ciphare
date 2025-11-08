# Ciphare - Local Setup & Testing Guide

## Quick Start

### Step 1: Install Dependencies

```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Install Node.js dependencies (if not already installed)
npm install
```

### Step 2: Configure Environment Variables

1. **Copy the example environment file:**
   ```bash
   cp env.example .env
   ```

2. **Edit `.env` file and add your credentials:**

   **MongoDB Atlas:**
   - Go to https://cloud.mongodb.com
   - Select your cluster → Connect → Connect your application
   - Copy the connection string
   - Replace `<password>` and `<username>` with your credentials
   - Add to `.env`:
     ```env
     MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
     ```

   **Cloudflare R2:**
   - Go to https://dash.cloudflare.com → R2
   - Create a bucket (if needed)
   - Go to "Manage R2 API Tokens" → Create API Token
   - Copy the credentials
   - Get your Account ID from the dashboard
   - Add to `.env`:
     ```env
     R2_ACCOUNT_ID=your-account-id
     R2_ACCESS_KEY_ID=your-access-key-id
     R2_SECRET_ACCESS_KEY=your-secret-access-key
     R2_BUCKET_NAME=your-bucket-name
     ```

   **Application Settings:**
   ```env
   DOMAIN=http://localhost:3000
   CORS_ORIGINS=*
   FLASK_DEBUG=True
   NEXT_PUBLIC_API_BASE_URL=http://localhost:3000
   ```

### Step 3: Verify MongoDB Network Access

1. Go to MongoDB Atlas → Network Access
2. Add your IP address (or `0.0.0.0/0` for testing)
3. Wait a few minutes for changes to propagate

### Step 4: Test the Setup

```bash
# Test Python imports (should work after pip install)
python3 -c "from api.storage import Storage; print('✅ Storage module OK')"

# Start development servers
npm run dev
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Flask API**: http://localhost:5328

## Troubleshooting

### "MONGODB_URI environment variable must be set"
- Check `.env` file exists in root directory
- Verify `MONGODB_URI` is set correctly
- Make sure you're running from the project root

### "R2 environment variables must be set"
- Check all 4 R2 variables are in `.env`:
  - `R2_ACCOUNT_ID`
  - `R2_ACCESS_KEY_ID`
  - `R2_SECRET_ACCESS_KEY`
  - `R2_BUCKET_NAME`

### MongoDB Connection Errors
- Verify network access allows your IP
- Check username/password are correct
- Ensure cluster is running (not paused)

### R2 Connection Errors
- Verify bucket name exists
- Check API token has correct permissions
- Verify Account ID is correct

### ModuleNotFoundError
- Run `pip3 install -r requirements.txt`
- Make sure you're using Python 3.8+

### Port Already in Use
- Change ports in `package.json` if 3000 or 5328 are taken
- Or kill the process using those ports

## Testing Checklist

After setup, test these features:

- [ ] **Health Check**: Visit http://localhost:3000/health
- [ ] **Upload Small File**: Upload a file < 1MB
- [ ] **Upload Medium File**: Upload a file ~50MB
- [ ] **Upload Large File**: Upload a file ~400MB (near 500MB limit)
- [ ] **Test File Size Limit**: Try uploading > 500MB (should fail)
- [ ] **Decrypt File**: Use the share link to decrypt
- [ ] **Test TTL**: Wait for file to expire (if testing with short TTL)
- [ ] **Test Read Limits**: Decrypt file multiple times until reads exhausted

## Production Deployment

Before deploying to production:

1. **Update `.env` for production:**
   ```env
   DOMAIN=https://your-domain.com
   CORS_ORIGINS=https://your-domain.com
   FLASK_DEBUG=False
   ```

2. **Set environment variables in your deployment platform:**
   - Vercel: Project Settings → Environment Variables
   - Railway: Service Settings → Variables
   - Netlify: Site Settings → Environment Variables

3. **Verify all credentials are set correctly**

4. **Test production deployment:**
   - Health check endpoint
   - File upload/download
   - All features working

## Environment Variables Reference

### Required (Core Features)
- `MONGODB_URI` - MongoDB Atlas connection string
- `R2_ACCOUNT_ID` - Cloudflare R2 account ID
- `R2_ACCESS_KEY_ID` - R2 API access key
- `R2_SECRET_ACCESS_KEY` - R2 API secret key
- `R2_BUCKET_NAME` - R2 bucket name

### Required (Application)
- `DOMAIN` - Your application domain

### Optional
- `CORS_ORIGINS` - CORS allowed origins (default: *)
- `FLASK_DEBUG` - Flask debug mode (default: False)
- `NEXT_PUBLIC_API_BASE_URL` - API base URL for frontend (default: empty for relative URLs)

### Optional (Community Posts)
- `UPSTASH_REDIS_URL` - Upstash Redis URL (only if using community posts)
- `UPSTASH_REDIS_PASSWORD` - Upstash Redis password (only if using community posts)

## Next Steps

1. ✅ Install dependencies
2. ✅ Configure `.env` file
3. ✅ Test locally
4. ✅ Deploy to production
5. ✅ Monitor and maintain

For deployment instructions, see:
- `RAILWAY_DEPLOYMENT.md` (Recommended)
- `NETLIFY_DEPLOYMENT.md`
- `DEPLOYMENT_CHECKLIST.md`

