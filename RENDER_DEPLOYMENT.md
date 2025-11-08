# Render Deployment Guide for Ciphare

**Render is the best FREE option** for deploying Ciphare - no credit card required, generous free tier!

## Why Render?

✅ **Completely Free** - No credit card required  
✅ **Full Flask Service** - Runs Flask as a proper service (not serverless)  
✅ **No Function Limits** - Unlike Vercel's 12 function limit  
✅ **Auto-Deploy** - Deploys automatically from GitHub  
✅ **Free SSL** - Automatic HTTPS certificates  
✅ **Simple Setup** - Easy configuration  

**Limitations (Free Tier):**
- ⚠️ Spins down after 15 minutes of inactivity (cold start ~30 seconds)
- ⚠️ 512MB RAM per service
- ⚠️ Suitable for personal projects and low-medium traffic

## Architecture: Separated Services (Recommended)

We deploy **two separate services** for optimal performance on the free tier:

- **Backend Service**: Flask API (Web Service) - 512MB RAM dedicated
- **Frontend Service**: Next.js (Static Site) - Served from CDN, instant loading

**Why Separated?**
- Each service gets dedicated 512MB RAM (1GB total)
- Frontend served from CDN (faster than web service)
- Independent scaling and debugging
- Better reliability (if one crashes, other stays up)

## Prerequisites

1. Render account (sign up at https://render.com - **no credit card needed**)
2. GitHub repository with your code
3. MongoDB Atlas account (free M0 tier)
4. Cloudflare R2 account (free tier)

## Step 1: Deploy Flask Backend

### 1.1 Create Web Service

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Select your repository

### 1.2 Configure Backend Service

**Basic Settings:**
- **Name**: `ciphare-backend` (or any name you prefer)
- **Region**: Choose closest to you
- **Branch**: `main` (or your default branch)
- **Root Directory**: Leave empty (root directory)
- **Runtime**: `Python 3`
- **Build Command**: 
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command**: 
  ```bash
  gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 api.app:flask_app
  ```

**Instance Type:**
- Select **"Free"** tier

### 1.3 Add Environment Variables

Go to **Environment** tab and add:

```env
# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority

# Cloudflare R2 Configuration
R2_ACCOUNT_ID=your-account-id
R2_ACCESS_KEY_ID=your-access-key-id
R2_SECRET_ACCESS_KEY=your-secret-access-key
R2_BUCKET_NAME=your-bucket-name

# Application Configuration
DOMAIN=https://your-frontend-url.onrender.com
CORS_ORIGINS=https://your-frontend-url.onrender.com
FLASK_DEBUG=False

# Optional: Community Posts (Redis)
UPSTASH_REDIS_URL=https://your-redis-instance.upstash.io
UPSTASH_REDIS_PASSWORD=your-redis-password
```

**Note:** You'll update `DOMAIN` and `CORS_ORIGINS` after deploying the frontend.

### 1.4 Deploy

1. Click **"Create Web Service"**
2. Render will start building and deploying
3. Wait for deployment to complete (usually 2-5 minutes)
4. Copy your service URL (e.g., `https://ciphare-backend.onrender.com`)

**Important:** Note this URL - you'll need it for the frontend!

---

## Step 2: Deploy Next.js Frontend

### 2.1 Create Static Site

1. In Render dashboard, click **"New +"** → **"Static Site"**
2. Connect your GitHub repository (same repo)
3. Select your repository

### 2.2 Configure Frontend Service

**Basic Settings:**
- **Name**: `ciphare-frontend` (or any name you prefer)
- **Branch**: `main` (or your default branch)
- **Root Directory**: Leave empty
- **Build Command**: 
  ```bash
  npm install && npm run build
  ```
- **Publish Directory**: 
  ```
  .next
  ```

**Note:** If `.next` doesn't work, try using a Web Service instead (see Alternative below).

### 2.3 Add Environment Variables

Go to **Environment** tab and add:

```env
# API Base URL (your backend service URL from Step 1)
NEXT_PUBLIC_API_BASE_URL=https://ciphare-backend.onrender.com
```

### 2.4 Deploy

1. Click **"Create Static Site"**
2. Render will build and deploy
3. Wait for deployment (usually 3-5 minutes)
4. Copy your frontend URL (e.g., `https://ciphare-frontend.onrender.com`)

### Alternative: Frontend as Web Service

If Static Site doesn't work (e.g., Next.js routing issues), use Web Service:

1. **New +** → **Web Service**
2. Same settings, but:
   - **Start Command**: `npm start`
   - **Publish Directory**: Not needed
   - Same environment variables

---

## Step 3: Update Backend CORS and Domain

After getting your frontend URL, update the backend environment variables:

1. Go to your **Backend Service** → **Environment**
2. Update:
   ```env
   DOMAIN=https://your-frontend-url.onrender.com
   CORS_ORIGINS=https://your-frontend-url.onrender.com
   ```
3. Click **"Save Changes"** - Render will automatically redeploy

---

## Step 4: Test Your Deployment

1. **Visit your frontend URL**: `https://your-frontend.onrender.com`
2. **Test encryption**: Upload a file and encrypt it
3. **Test decryption**: Use the share link to decrypt
4. **Check backend logs**: Go to Backend Service → Logs tab

---

## Troubleshooting

### Backend Issues

**Problem: Service won't start**
- Check logs in Render dashboard
- Verify `gunicorn` is in `requirements.txt`
- Check start command is correct

**Problem: "Module not found" errors**
- Verify all dependencies are in `requirements.txt`
- Check build logs for installation errors

**Problem: Database connection errors**
- Verify `MONGODB_URI` is correct
- Check MongoDB network access allows Render IPs (or use `0.0.0.0/0` for testing)
- Verify R2 credentials are correct

**Problem: CORS errors**
- Update `CORS_ORIGINS` to include your frontend URL
- Ensure `DOMAIN` is set correctly

### Frontend Issues

**Problem: Build fails**
- Check build logs
- Verify Node.js version (Render uses Node 18+)
- Check for TypeScript errors

**Problem: API calls fail**
- Verify `NEXT_PUBLIC_API_BASE_URL` is set correctly
- Check backend is running (visit backend URL directly)
- Check browser console for errors

**Problem: Static export issues**
- If using static export, ensure all routes are pre-rendered
- Consider using Web Service instead of Static Site

### Cold Start Issues

**Problem: First request is slow**
- This is normal on free tier (15-minute spin-down)
- First request after inactivity takes ~30 seconds
- Subsequent requests are fast
- Consider upgrading to paid plan for always-on

---

## Alternative: Single Service Deployment (Not Recommended)

If you prefer to run both frontend and backend together (not recommended for free tier):

### Configuration

1. Create **Web Service** (not Static Site)
2. **Build Command**: 
   ```bash
   npm install && npm run build && pip install -r requirements.txt
   ```
3. **Start Command**: 
   ```bash
   concurrently "npm start" "gunicorn --bind 0.0.0.0:$PORT api.app:flask_app"
   ```

**Note:** This requires `concurrently` in `package.json` (already included).

**Why Not Recommended:**
- Shares 512MB RAM between Next.js and Flask (can be tight)
- Port conflicts (both need ports, Render provides one)
- Slower cold starts (both spin up together)
- Less reliable (one crash takes both down)

---

## Custom Domain (Optional)

1. Go to your service → **Settings** → **Custom Domains**
2. Add your domain
3. Follow DNS configuration instructions
4. Render provides free SSL automatically

---

## Monitoring & Logs

- **View Logs**: Service → Logs tab (real-time)
- **Metrics**: Service → Metrics tab (CPU, memory, requests)
- **Deployments**: Service → Deployments tab (deployment history)

---

## Free Tier Limits

- **Web Services**: 750 hours/month per service (enough for always-on)
- **Static Sites**: Unlimited (free forever)
- **Bandwidth**: 100GB/month
- **Build Time**: 500 minutes/month
- **Spins down**: After 15 minutes of inactivity (web services only)

**Upgrade to Paid ($7/month)** for:
- Always-on (no spin-down)
- More resources
- Better performance
- Priority support

---

## Cost Comparison

| Platform | Free Tier | Paid Tier |
|----------|-----------|-----------|
| **Render** | ✅ Yes (with spin-down) | $7/month (always-on) |
| **Railway** | ❌ No (trial only) | $5/month |
| **Vercel** | ✅ Yes (12 function limit) | $20/month |
| **Netlify** | ✅ Yes (limited) | $19/month |

**Render is the best free option** for your Flask + Next.js app!

---

## Quick Checklist

- [ ] Render account created
- [ ] Backend service deployed
- [ ] Backend environment variables set
- [ ] Backend URL copied
- [ ] Frontend service deployed
- [ ] Frontend environment variables set (with backend URL)
- [ ] Backend CORS updated with frontend URL
- [ ] Tested encryption/decryption
- [ ] Checked logs for errors

---

## Next Steps

1. Follow Step 1 to deploy backend
2. Follow Step 2 to deploy frontend
3. Update backend CORS with frontend URL
4. Test everything
5. (Optional) Add custom domain

**Need help?** Check the troubleshooting section or Render's documentation.

---

## Local Development

Your local development setup remains unchanged:

```bash
# Run both frontend and backend concurrently (local dev)
npm run dev

# Or run separately:
npm run next-dev      # Frontend only
npm run flask-dev     # Backend only
```

These commands are for **local development only** and don't affect Render deployment.

