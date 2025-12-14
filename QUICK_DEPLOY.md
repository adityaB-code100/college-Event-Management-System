# Quick Deployment Guide

## Backend on Render (5 minutes)

### 1. Prepare MongoDB Atlas
- Create account at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
- Create cluster → Create database user → Whitelist IP (0.0.0.0/0)
- Copy connection string: `mongodb+srv://user:pass@cluster.mongodb.net/db`

### 2. Deploy to Render
1. Go to [dashboard.render.com](https://dashboard.render.com)
2. New → Web Service → Connect GitHub repo
3. Configure:
   - **Name**: `college-event-mgmt`
   - **Build**: `pip install -r requirements.txt`
   - **Start**: `gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 wsgi:app`
4. Add Environment Variables:
   ```
   SECRET_KEY=<generate-random-key>
   MONGODB_URI=<your-mongodb-connection-string>
   FRONTEND_URL=<your-vercel-url-if-separate>
   FLASK_ENV=production
   ```
5. Deploy!

**Generate SECRET_KEY**: 
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Frontend Options

### Option 1: Keep on Render (Easiest)
- Your Flask app already serves templates
- No separate frontend needed
- Just deploy to Render as above

### Option 2: Deploy to Vercel
- Create separate React/Next.js frontend
- Point API calls to Render backend
- Deploy to Vercel with `REACT_APP_API_URL` env var

## Environment Variables Checklist

**Render Backend:**
- ✅ `SECRET_KEY` - Random 32+ character string
- ✅ `MONGODB_URI` - Full MongoDB Atlas connection string
- ✅ `FRONTEND_URL` - Your Vercel frontend URL (if separate)
- ✅ `FLASK_ENV=production`

**Vercel Frontend (if separate):**
- ✅ `REACT_APP_API_URL` - Your Render backend URL

## Post-Deployment

1. Test backend: Visit `https://your-app.onrender.com`
2. Test login/registration
3. Create an event
4. Check logs for errors

## Troubleshooting

**Database connection fails:**
- Check MONGODB_URI format
- Verify IP whitelist in MongoDB Atlas
- Check user credentials

**App crashes:**
- Check Render logs
- Verify all env vars are set
- Check requirements.txt

**CORS errors:**
- Verify FRONTEND_URL matches Vercel URL
- Check CORS config in app.py

## Full Guide

See `DEPLOYMENT_GUIDE.md` for detailed instructions.

