# Deployment Readiness Checklist

Use this checklist to ensure your Ciphare application is ready for production deployment.

## Pre-Deployment Checklist

### ✅ Code Quality
- [x] All files migrated from Redis to MongoDB + R2
- [x] File size limit updated to 500MB
- [x] Error handling implemented
- [x] Logging configured
- [x] No linter errors
- [x] All imports working correctly

### ✅ Dependencies
- [x] `requirements.txt` includes boto3 and pymongo
- [x] `package.json` scripts are correct
- [x] All Node.js dependencies installed
- [x] All Python dependencies listed

### ✅ Configuration Files
- [x] `env.example` created with all required variables
- [x] `.gitignore` excludes `.env` files
- [x] `vercel.json` configured (if using Vercel)
- [x] `railway.json` configured (if using Railway)
- [x] `netlify.toml` configured (if using Netlify)

### ✅ Environment Variables

**Required for Core Features:**
- [ ] `MONGODB_URI` - MongoDB Atlas connection string
- [ ] `R2_ACCOUNT_ID` - Cloudflare R2 account ID
- [ ] `R2_ACCESS_KEY_ID` - R2 API access key
- [ ] `R2_SECRET_ACCESS_KEY` - R2 API secret key
- [ ] `R2_BUCKET_NAME` - R2 bucket name
- [ ] `DOMAIN` - Your production domain

**Optional but Recommended:**
- [ ] `CORS_ORIGINS` - Your production domain (not `*`)
- [ ] `FLASK_DEBUG=False` - Disable debug mode in production

**Optional (Community Posts):**
- [ ] `UPSTASH_REDIS_URL` - Only if using community posts
- [ ] `UPSTASH_REDIS_PASSWORD` - Only if using community posts

## Local Testing Checklist

Before deploying, test locally:

### Basic Functionality
- [ ] Application starts without errors
- [ ] Health check endpoint works (`/health`)
- [ ] Frontend loads at http://localhost:3000
- [ ] Flask API responds at http://localhost:5328

### File Encryption/Decryption
- [ ] Upload small file (< 1MB) - SUCCESS
- [ ] Upload medium file (~50MB) - SUCCESS
- [ ] Upload large file (~400MB) - SUCCESS
- [ ] Upload file > 500MB - FAILS with proper error
- [ ] Decrypt file with correct password - SUCCESS
- [ ] Decrypt file with wrong password - FAILS with proper error
- [ ] Share link generation works
- [ ] File download after decryption works

### TTL and Read Limits
- [ ] File expires after TTL (test with short TTL like 60 seconds)
- [ ] File deleted after reads exhausted
- [ ] Read count decrements correctly

### Error Handling
- [ ] Invalid file ID returns 404
- [ ] Missing password returns 400
- [ ] Invalid Base64 returns 400
- [ ] Network errors handled gracefully

## Production Deployment Checklist

### Before Deployment
- [ ] All environment variables set in deployment platform
- [ ] MongoDB network access configured (allow deployment platform IPs)
- [ ] R2 bucket created and accessible
- [ ] Domain configured (if using custom domain)
- [ ] CORS origins set to production domain

### Deployment Steps
1. [ ] Push code to repository
2. [ ] Configure environment variables in deployment platform
3. [ ] Deploy application
4. [ ] Verify deployment succeeded

### Post-Deployment Testing
- [ ] Health check: `https://your-domain.com/health`
- [ ] Upload test file
- [ ] Decrypt test file
- [ ] Verify share links work
- [ ] Check application logs for errors
- [ ] Test from different network/IP

## Security Checklist

- [ ] `FLASK_DEBUG=False` in production
- [ ] `CORS_ORIGINS` restricted to your domain (not `*`)
- [ ] MongoDB network access restricted (not `0.0.0.0/0` in production)
- [ ] R2 API tokens have minimal required permissions
- [ ] Environment variables not exposed in logs
- [ ] `.env` file not committed to git

## Monitoring Checklist

- [ ] Application logs accessible
- [ ] Error tracking configured (optional)
- [ ] Usage metrics available (optional)
- [ ] MongoDB connection monitoring
- [ ] R2 storage usage monitoring

## Rollback Plan

If deployment fails:
- [ ] Previous deployment version available
- [ ] Environment variables documented
- [ ] Database backups available (if needed)
- [ ] Rollback procedure tested

## Support Resources

- **Setup Guide**: See `SETUP_GUIDE.md`
- **Deployment Guides**: 
  - `RAILWAY_DEPLOYMENT.md` (Recommended)
  - `NETLIFY_DEPLOYMENT.md`
  - `DEPLOYMENT_CHECKLIST.md`
- **Troubleshooting**: See `README.md` troubleshooting section

## Quick Test Commands

```bash
# Test storage module
python3 -c "from api.storage import Storage; print('✅ Storage OK')"

# Test Flask app
python3 -c "from api.app import flask_app; print('✅ Flask app OK')"

# Test blueprints
python3 -c "from api.encode import encode_bp; from api.decode import decode_bp; print('✅ Blueprints OK')"

# Start dev servers
npm run dev
```

## Common Issues & Solutions

### Issue: "MONGODB_URI environment variable must be set"
**Solution**: Check `.env` file exists and has `MONGODB_URI` set

### Issue: "R2 environment variables must be set"
**Solution**: Verify all 4 R2 variables are in `.env`

### Issue: MongoDB connection timeout
**Solution**: Check network access allows your IP in MongoDB Atlas

### Issue: R2 access denied
**Solution**: Verify API token has correct permissions and bucket exists

### Issue: File upload fails
**Solution**: Check file size is under 500MB and Flask MAX_CONTENT_LENGTH is set correctly

---

**Status**: ✅ Code is ready for deployment. Fill in environment variables and test locally first!

