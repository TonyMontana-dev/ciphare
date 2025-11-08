# Railway Deployment Guide for Ciphare

Railway is **recommended** for this project as it can run Flask as a full service, which is simpler and more performant than serverless functions.

## Architecture Options

### Option 1: Two Services (Recommended)
- **Frontend Service**: Next.js application
- **Backend Service**: Flask API

### Option 2: Single Service
- Combined Next.js + Flask using concurrently

This guide covers **Option 1** (two services) as it's more scalable and cleaner.

## Prerequisites

1. Railway account (sign up at https://railway.app)
2. GitHub repository connected to Railway
3. Upstash Redis account

## Deployment Steps

### Step 1: Create Railway Project

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository

### Step 2: Create Backend Service (Flask)

1. In your Railway project, click "New Service"
2. Select "GitHub Repo" and choose your repository
3. Railway will auto-detect Python

**Configure the service:**

1. Go to **Settings** → **Service Settings**
2. Set **Root Directory**: Leave empty (root directory)
3. Set **Start Command** to:
   ```
   gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 api.app:flask_app
   ```

**Environment Variables:**
Add these in **Variables** tab:
```
UPSTASH_REDIS_URL=https://your-redis-instance.upstash.io
UPSTASH_REDIS_PASSWORD=your-redis-password
DOMAIN=https://your-backend.railway.app
CORS_ORIGINS=https://your-frontend.railway.app
FLASK_DEBUG=False
```

**Generate Public URL:**
1. Go to **Settings** → **Networking**
2. Click "Generate Domain"
3. Copy the generated URL (e.g., `https://your-backend.railway.app`)
4. Update `DOMAIN` and `CORS_ORIGINS` with this URL

### Step 3: Create Frontend Service (Next.js)

1. In the same Railway project, click "New Service"
2. Select "GitHub Repo" and choose your repository
3. Railway will auto-detect Node.js

**Configure the service:**

1. Go to **Settings** → **Service Settings**
2. Set **Root Directory**: Leave empty (root directory)
3. Set **Build Command** to: `npm install && npm run build`
4. Set **Start Command** to: `npm start`

**Environment Variables:**
Add these in **Variables** tab:
```
NODE_ENV=production
NEXT_PUBLIC_API_BASE_URL=https://your-backend.railway.app
```

Replace `your-backend.railway.app` with the actual backend URL from Step 2.

**Generate Public URL:**
1. Go to **Settings** → **Networking**
2. Click "Generate Domain"
3. Copy the generated URL

### Step 4: Update Next.js Configuration

Update `next.config.ts` to proxy API requests in production:

```typescript
import { NextConfig } from 'next';

const nextConfig: NextConfig = {
    // For Railway: proxy API requests to Flask backend
    ...(process.env.NEXT_PUBLIC_API_BASE_URL && {
        rewrites: async () => {
            return [
                {
                    source: '/api/:path*',
                    destination: `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/:path*`,
                },
            ];
        },
    }),
    // For local development
    ...(process.env.NODE_ENV === 'development' && {
        rewrites: async () => {
            return [
                {
                    source: '/api/:path*',
                    destination: 'http://127.0.0.1:5328/api/:path*',
                },
            ];
        },
    }),
};

export default nextConfig;
```

### Step 5: Update Backend CORS

Make sure your backend's `CORS_ORIGINS` includes your frontend URL:
```
CORS_ORIGINS=https://your-frontend.railway.app
```

## Alternative: Single Service Deployment

If you prefer a single service, you can use the `railway.json` configuration:

1. Create one service in Railway
2. Set **Start Command** to:
   ```
   npm run prod
   ```
3. This will run both Next.js and Flask using `concurrently`

**Note**: This approach uses more resources and is less scalable, but simpler to set up.

## Monitoring

1. **Logs**: View logs in Railway dashboard for each service
2. **Metrics**: Monitor CPU, memory, and network usage
3. **Health Checks**: Use `/health` endpoint to verify backend is running

## Troubleshooting

### Backend not starting
- Check logs in Railway dashboard
- Verify `gunicorn` is in `requirements.txt`
- Ensure `api.app:flask_app` is the correct import path

### CORS errors
- Verify `CORS_ORIGINS` includes your frontend URL exactly
- Check that URLs include `https://` protocol

### API requests failing
- Verify `NEXT_PUBLIC_API_BASE_URL` is set correctly
- Check that backend service is running and accessible
- Test backend directly: `https://your-backend.railway.app/health`

### Build failures
- Check Node.js version (should be 18+)
- Verify all dependencies are in `package.json`
- Check build logs for specific errors

## Cost Considerations

Railway pricing:
- **Hobby Plan**: $5/month + usage
- **Pro Plan**: $20/month + usage
- Includes generous free tier for testing

## Custom Domains

1. Go to service **Settings** → **Networking**
2. Click "Custom Domain"
3. Add your domain and configure DNS

## Environment Variables Reference

### Backend Service
```
UPSTASH_REDIS_URL=          # Upstash Redis REST URL
UPSTASH_REDIS_PASSWORD=     # Upstash Redis REST token
DOMAIN=                     # Backend public URL
CORS_ORIGINS=               # Frontend URL(s), comma-separated
FLASK_DEBUG=False           # Always False in production
PORT=                       # Auto-set by Railway
```

### Frontend Service
```
NODE_ENV=production
NEXT_PUBLIC_API_BASE_URL=   # Backend public URL
PORT=                       # Auto-set by Railway
```

## Next Steps

1. Set up monitoring and alerts
2. Configure custom domains
3. Set up CI/CD (Railway auto-deploys on git push)
4. Consider adding rate limiting
5. Set up database backups if needed

