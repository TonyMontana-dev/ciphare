# Render Quick Start Guide - 5 Minutes to Deploy

## Fastest Way to Deploy (Separated Services)

1. **Sign up**: https://render.com (no credit card needed)

2. **Deploy Backend**:
   - Dashboard → "New +" → "Web Service"
   - Connect GitHub repo
   - **Settings**:
     - Build: `pip install -r requirements.txt`
     - Start: `gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 api.app:flask_app`
     - Plan: **Free**
   - **Environment Variables** (see list below)
   - **Create** → Copy URL

3. **Deploy Frontend**:
   - Dashboard → "New +" → "Static Site"
   - Connect GitHub repo
   - **Settings**:
     - Build: `npm install && npm run build`
     - Publish: `.next`
   - **Environment Variables**:
     - `NEXT_PUBLIC_API_BASE_URL=https://your-backend.onrender.com`
   - **Create** → Copy URL

4. **Update Backend CORS**:
   - Backend → Environment
   - Set `DOMAIN` and `CORS_ORIGINS` to frontend URL
   - Save → Auto-redeploys

5. **Done!** Your app is live 🎉

---

## Required Environment Variables

### Backend (Flask)

```env
# Required
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority
R2_ACCOUNT_ID=your-account-id
R2_ACCESS_KEY_ID=your-access-key-id
R2_SECRET_ACCESS_KEY=your-secret-access-key
R2_BUCKET_NAME=your-bucket-name
DOMAIN=https://your-frontend.onrender.com
CORS_ORIGINS=https://your-frontend.onrender.com
FLASK_DEBUG=False

# Optional (for community posts)
UPSTASH_REDIS_URL=https://your-redis.upstash.io
UPSTASH_REDIS_PASSWORD=your-redis-password
```

### Frontend (Next.js)

```env
# Required
NEXT_PUBLIC_API_BASE_URL=https://your-backend.onrender.com
```

---

## Architecture

```
┌─────────────────────┐
│  Frontend (Static)  │  ← Static Site (instant, CDN)
│  Next.js Build      │    512MB RAM
└──────────┬──────────┘    750 hours/month
           │
           │ API Calls
           │
┌──────────▼──────────┐
│  Backend (Web)       │  ← Web Service (Flask)
│  Flask API           │    512MB RAM
└──────────────────────┘    750 hours/month
```

**Total: 2 services = 1,500 hours/month** (more than enough!)

---

## Testing

1. Visit your frontend URL
2. Try encrypting a file
3. Try decrypting with the share link
4. Check backend logs if issues occur

---

## Troubleshooting

**Backend won't start?**
- Check logs → Look for Python errors
- Verify `gunicorn` in `requirements.txt`
- Check start command is correct

**Frontend can't reach backend?**
- Verify `NEXT_PUBLIC_API_BASE_URL` is correct
- Check backend is running (visit backend URL)
- Check CORS settings in backend

**Cold start slow?**
- Normal on free tier (15 min spin-down)
- First request takes ~30 seconds
- Subsequent requests are fast

**Static Site build fails?**
- Try using Web Service instead
- Check Next.js build logs
- Verify Node.js version

---

## Local Development (Unchanged)

```bash
# Run both concurrently (local dev)
npm run dev

# Or separately:
npm run next-dev      # Frontend only
npm run flask-dev     # Backend only
```

These commands are for **local development only** and don't affect Render deployment.

---

## That's It!

Your app should now be live on Render! 🚀

For detailed instructions, see `RENDER_DEPLOYMENT.md`

