# Quick Start: Deploy to Railway or Netlify

## 🚂 Railway (Recommended - 5 minutes)

### Why Railway?
- ✅ Best for Flask applications
- ✅ Simple setup
- ✅ Better performance
- ✅ One platform for everything

### Steps:

1. **Sign up**: https://railway.app
2. **Create Project** → "Deploy from GitHub repo"
3. **Create Backend Service**:
   - New Service → GitHub Repo
   - Settings → Start Command: `gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 api.app:flask_app`
   - Variables → Add:
     ```
     UPSTASH_REDIS_URL=your-redis-url
     UPSTASH_REDIS_PASSWORD=your-redis-password
     DOMAIN=https://your-backend.railway.app
     CORS_ORIGINS=https://your-frontend.railway.app
     ```
   - Networking → Generate Domain (copy URL)
4. **Create Frontend Service**:
   - New Service → GitHub Repo
   - Settings → Build: `npm install && npm run build`
   - Settings → Start: `npm start`
   - Variables → Add:
     ```
     NEXT_PUBLIC_API_BASE_URL=https://your-backend.railway.app
     ```
   - Networking → Generate Domain
5. **Done!** 🎉

**Full Guide**: See [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md)

---

## 🌐 Netlify (Alternative - 10 minutes)

### Why Netlify?
- ⚠️ Requires external Flask backend
- ⚠️ More complex setup
- ✅ Good for static sites

### Steps:

1. **Deploy Flask to Railway first** (follow Railway steps above)
2. **Sign up**: https://netlify.com
3. **Deploy Next.js**:
   - Add new site → Import from GitHub
   - Build: `npm run build`
   - Publish: `.next`
   - Variables:
     ```
     FLASK_BACKEND_URL=https://your-backend.railway.app
     NEXT_PUBLIC_API_BASE_URL=https://your-backend.railway.app
     ```
4. **Done!** 🎉

**Full Guide**: See [NETLIFY_DEPLOYMENT.md](./NETLIFY_DEPLOYMENT.md)

---

## 📊 Which Should I Choose?

| Feature | Railway | Netlify |
|---------|---------|---------|
| Setup Time | 5 min | 10 min |
| Flask Support | ✅ Excellent | ⚠️ Requires workaround |
| Performance | ✅ Better | ⚠️ Slower (proxy) |
| Cost | $5-20/month | $19+/month |
| Complexity | ✅ Simple | ⚠️ More complex |

**Recommendation**: Choose **Railway** unless you have specific Netlify requirements.

**Full Comparison**: See [DEPLOYMENT_COMPARISON.md](./DEPLOYMENT_COMPARISON.md)

---

## 🆘 Need Help?

- **Railway Issues**: Check [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md) troubleshooting
- **Netlify Issues**: Check [NETLIFY_DEPLOYMENT.md](./NETLIFY_DEPLOYMENT.md) troubleshooting
- **General Questions**: Check main [README.md](./README.md)

