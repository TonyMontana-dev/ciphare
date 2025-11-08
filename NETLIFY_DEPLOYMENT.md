# Netlify Deployment Guide for Ciphare

**Note**: Netlify is less ideal for this project because:
- Python serverless functions have limitations
- Flask works better as a full service
- Requires additional setup for API proxying

**Recommendation**: Use Railway instead (see `RAILWAY_DEPLOYMENT.md`)

However, if you must use Netlify, this guide provides a workaround using an external Flask backend.

## Architecture

Since Netlify's Python functions are limited, we'll use:
- **Netlify**: Next.js frontend + API proxy functions
- **External Backend**: Flask API on Railway/Render/Heroku (separate deployment)

## Prerequisites

1. Netlify account
2. External Flask backend (deploy Flask separately on Railway/Render)
3. Upstash Redis account

## Deployment Steps

### Step 1: Deploy Flask Backend Separately

First, deploy your Flask backend to Railway or Render:

**On Railway:**
- Follow the backend service setup from `RAILWAY_DEPLOYMENT.md`
- Get the public URL (e.g., `https://your-backend.railway.app`)

**On Render:**
- Create a new Web Service
- Use the `Procfile` or set start command: `gunicorn --bind 0.0.0.0:$PORT api.app:flask_app`
- Add environment variables
- Get the public URL

### Step 2: Deploy Next.js to Netlify

1. Go to https://app.netlify.com
2. Click "Add new site" → "Import an existing project"
3. Connect your GitHub repository
4. Configure build settings:

**Build Settings:**
- **Base directory**: Leave empty (root directory)
- **Build command**: `npm run build`
- **Publish directory**: `.next`

**Environment Variables:**
Add in **Site settings** → **Environment variables**:
```
NODE_ENV=production
FLASK_BACKEND_URL=https://your-backend.railway.app
NEXT_PUBLIC_API_BASE_URL=https://your-backend.railway.app
```

Replace with your actual Flask backend URL.

### Step 3: Configure Netlify Functions

The `netlify.toml` file is already configured. The API proxy function (`netlify/functions/api-proxy.js`) will forward requests to your Flask backend.

**Update the proxy function** if needed:
- Edit `netlify/functions/api-proxy.js`
- Ensure it correctly forwards to your Flask backend URL

### Step 4: Update Next.js Configuration

Update `next.config.ts`:

```typescript
import { NextConfig } from 'next';

const nextConfig: NextConfig = {
    // For Netlify: use relative API paths (handled by netlify.toml redirects)
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

### Step 5: Update Frontend API Calls

The frontend should use relative URLs in production (already configured):
```typescript
const API_BASE_URL = 
  typeof window !== 'undefined' && window.location.hostname === 'localhost'
    ? process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:3000"
    : ""; // Empty string means relative URLs
```

## Alternative: Netlify Python Functions (Limited)

If you want to try Netlify's Python functions directly:

1. Create `netlify/functions/encode.py`:
```python
from serverless_wsgi import handle_request
from api.app import flask_app

def handler(event, context):
    return handle_request(flask_app, event, context)
```

2. Repeat for `decode.py` and `posts.py`

**Limitations:**
- 10-second execution timeout
- 50MB memory limit
- Cold starts can be slow
- Limited Python package support

## Troubleshooting

### API requests failing
- Verify `FLASK_BACKEND_URL` is set correctly
- Check Netlify function logs
- Test Flask backend directly: `https://your-backend.railway.app/health`

### CORS errors
- Ensure Flask backend's `CORS_ORIGINS` includes your Netlify domain
- Check Netlify function response headers

### Build failures
- Check Node.js version (Netlify uses 18 by default)
- Verify all dependencies are in `package.json`
- Check build logs in Netlify dashboard

### Function timeouts
- Netlify functions have 10-second timeout
- For large file operations, consider increasing timeout or using background jobs

## Cost Considerations

Netlify pricing:
- **Starter**: Free (limited functions)
- **Pro**: $19/month (more functions, better performance)
- **Business**: $99/month

## Custom Domains

1. Go to **Site settings** → **Domain management**
2. Add custom domain
3. Configure DNS as instructed

## Environment Variables Reference

```
NODE_ENV=production
FLASK_BACKEND_URL=          # External Flask backend URL
NEXT_PUBLIC_API_BASE_URL=   # Same as FLASK_BACKEND_URL
```

## Why Railway is Better

1. **Simpler**: One platform for both frontend and backend
2. **Better Performance**: Full Flask service vs serverless functions
3. **No Cold Starts**: Always-on service
4. **Better Python Support**: Full package ecosystem
5. **Easier Debugging**: Direct access to Flask logs
6. **Cost**: Similar pricing, better value

## Recommendation

**Use Railway** for this project. See `RAILWAY_DEPLOYMENT.md` for the recommended deployment approach.

