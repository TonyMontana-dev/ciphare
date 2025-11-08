# Deployment Checklist for Ciphare

## Pre-Deployment Checklist

### ✅ Code Improvements Completed

1. **Vercel Serverless Function Structure**
   - ✅ Created proper serverless function handlers in `api/encode/index.py`, `api/decode/index.py`, `api/posts/index.py`
   - ✅ Updated `vercel.json` with correct Python serverless function configuration
   - ✅ Removed incorrect handler implementations from blueprint files

2. **Security Enhancements**
   - ✅ Added input validation for all API endpoints
   - ✅ Added request timeouts (10 seconds) to prevent hanging requests
   - ✅ Improved error handling with proper logging
   - ✅ Added file size limits (16MB max)
   - ✅ Added TTL validation (1 minute to 90 days)
   - ✅ Added read limits validation (1 to 100)
   - ✅ Improved CORS configuration for production

3. **Environment Variable Handling**
   - ✅ Added validation for required environment variables
   - ✅ Improved error messages for missing configuration
   - ✅ Updated frontend to use relative URLs in production

4. **Code Quality**
   - ✅ Fixed registry.py to handle missing algorithms gracefully
   - ✅ Improved logging throughout the application
   - ✅ Added proper error handlers in Flask app
   - ✅ Fixed frontend API calls to work in both dev and production

5. **Documentation**
   - ✅ Updated README with comprehensive deployment instructions
   - ✅ Added API documentation
   - ✅ Added troubleshooting section

## Vercel Deployment Steps

### 1. Environment Variables Setup

In your Vercel project settings, configure these environment variables:

```
UPSTASH_REDIS_URL=https://your-redis-instance.upstash.io
UPSTASH_REDIS_PASSWORD=your-redis-password
DOMAIN=https://your-app.vercel.app
CORS_ORIGINS=https://your-app.vercel.app
```

**Important**: 
- Replace `your-redis-instance` with your actual Upstash Redis URL
- Replace `your-app.vercel.app` with your actual Vercel domain
- For production, set `CORS_ORIGINS` to your specific domain (not `*`)

### 2. Verify Configuration Files

- ✅ `vercel.json` is correctly configured
- ✅ `requirements.txt` includes `serverless-wsgi`
- ✅ `package.json` has correct build scripts
- ✅ `next.config.ts` is configured for production

### 3. Deploy

```bash
# Install Vercel CLI if needed
npm i -g vercel

# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

### 4. Post-Deployment Verification

After deployment, verify:

1. **Health Check**: Visit `https://your-app.vercel.app/health`
   - Should return: `{"status": "running", "service": "ciphare"}`

2. **API Endpoints**:
   - Test `/api/encode` with a small file
   - Test `/api/decode` with the returned file_id
   - Test `/api/posts` GET and POST

3. **Frontend Pages**:
   - Home page loads
   - Encode page works
   - Decode page works
   - Community page works

## Common Issues & Solutions

### Issue: Python functions return 500 errors

**Solution**: 
- Check Vercel function logs
- Verify environment variables are set
- Ensure `serverless-wsgi` is in `requirements.txt`
- Check that Python version is compatible (3.8+)

### Issue: CORS errors in browser

**Solution**:
- Verify `CORS_ORIGINS` environment variable includes your domain
- Check that the domain matches exactly (including https://)
- For development, you can temporarily set to `*`

### Issue: Redis connection errors

**Solution**:
- Verify `UPSTASH_REDIS_URL` is correct (should be REST URL, not Redis URL)
- Verify `UPSTASH_REDIS_PASSWORD` is the REST token, not Redis password
- Check Upstash dashboard for connection limits

### Issue: Files not encrypting/decrypting

**Solution**:
- Check file size (max 16MB)
- Verify password is being sent correctly
- Check browser console for errors
- Verify API endpoints are returning correct responses

## Security Considerations

1. **Environment Variables**: Never commit `.env` file
2. **CORS**: In production, restrict `CORS_ORIGINS` to your domain only
3. **Rate Limiting**: Consider adding rate limiting for production (Vercel Pro plan includes this)
4. **HTTPS**: Vercel automatically provides HTTPS
5. **Secrets**: Use Vercel's environment variable encryption for sensitive data

## Monitoring

After deployment, monitor:

1. **Vercel Function Logs**: Check for errors in Vercel dashboard
2. **Upstash Redis**: Monitor usage and connection limits
3. **Error Rates**: Watch for 500 errors in Vercel analytics
4. **Performance**: Monitor function execution times

## Rollback Plan

If deployment fails:

1. Check Vercel deployment logs
2. Verify environment variables
3. Test locally with production environment variables
4. Rollback to previous deployment in Vercel dashboard if needed

## Next Steps

After successful deployment:

1. Set up custom domain (optional)
2. Configure monitoring and alerts
3. Set up CI/CD for automatic deployments
4. Consider adding rate limiting
5. Set up backup strategy for Redis data (if needed)

