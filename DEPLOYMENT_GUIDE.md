# Deployment Guide - Backend (Render) & Frontend (Vercel)

This guide will help you deploy the College Event Management System with backend on Render and frontend on Vercel.

## Prerequisites

1. **GitHub Account** - Your code should be in a GitHub repository
2. **Render Account** - Sign up at [render.com](https://render.com)
3. **Vercel Account** - Sign up at [vercel.com](https://vercel.com)
4. **MongoDB Atlas Account** - For database hosting

## Part 1: Backend Deployment on Render

### Step 1: Prepare MongoDB Atlas

1. Create a MongoDB Atlas account at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Create a new cluster (free tier is fine)
3. Create a database user:
   - Go to Database Access → Add New Database User
   - Create username and password (save these!)
4. Whitelist IP addresses:
   - Go to Network Access → Add IP Address
   - Add `0.0.0.0/0` to allow all IPs (or Render's IP ranges)
5. Get your connection string:
   - Go to Clusters → Connect → Connect your application
   - Copy the connection string (format: `mongodb+srv://username:password@cluster.mongodb.net/database`)

### Step 2: Deploy to Render

1. **Connect Repository**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Select the repository containing your code

2. **Configure Service**
   - **Name**: `college-event-mgmt` (or your preferred name)
   - **Environment**: `Python 3`
   - **Region**: Choose closest to your users
   - **Branch**: `main` (or your default branch)
   - **Root Directory**: Leave empty (or specify if code is in subdirectory)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 wsgi:app`

3. **Set Environment Variables**
   Click "Advanced" → "Add Environment Variable" and add:
   ```
   SECRET_KEY=your-super-secret-key-here-generate-a-random-one
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/college_events?retryWrites=true&w=majority
   FRONTEND_URL=https://your-frontend-url.vercel.app
   FLASK_ENV=production
   PORT=10000
   ```
   
   **Important**: 
   - Generate a secure SECRET_KEY (you can use: `python -c "import secrets; print(secrets.token_hex(32))"`)
   - Replace `username`, `password`, and `cluster` in MONGODB_URI with your actual values
   - Update FRONTEND_URL after deploying frontend

4. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy your application
   - Wait for deployment to complete (usually 2-5 minutes)
   - Your backend URL will be: `https://your-app-name.onrender.com`

### Step 3: Test Backend

1. Visit your Render service URL
2. You should see the login page or be redirected to login
3. Check Render logs for any errors

## Part 2: Frontend Deployment on Vercel

### Option A: Deploy Current Flask Templates (Monolithic)

If you want to keep the current structure where Flask serves templates:

**Note**: Vercel doesn't natively support Python/Flask for server-side rendering. You have two options:

1. **Keep everything on Render** (Recommended for now)
   - Your Flask app already serves both API and frontend templates
   - Just deploy to Render as described above
   - No separate frontend deployment needed

2. **Create a separate frontend** (React/Next.js/Vue)
   - Build a new frontend application
   - Connect to your Render backend API
   - Deploy frontend to Vercel

### Option B: Create Separate Frontend (Recommended for Vercel)

If you want to deploy a separate frontend to Vercel:

1. **Create a new frontend project** (React, Next.js, or Vue)
2. **Configure API calls** to point to your Render backend
3. **Deploy to Vercel**:
   - Connect your GitHub repository
   - Vercel will auto-detect the framework
   - Set environment variable: `REACT_APP_API_URL=https://your-backend.onrender.com`
   - Deploy

## Environment Variables Summary

### Render (Backend)
```
SECRET_KEY=your-secret-key
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/db
FRONTEND_URL=https://your-frontend.vercel.app
FLASK_ENV=production
PORT=10000
```

### Vercel (Frontend - if separate)
```
REACT_APP_API_URL=https://your-backend.onrender.com
```

## Post-Deployment Checklist

- [ ] Backend is accessible at Render URL
- [ ] Database connection is working
- [ ] Can login and create events
- [ ] CORS is configured correctly (if using separate frontend)
- [ ] Environment variables are set correctly
- [ ] HTTPS is enabled (automatic on Render/Vercel)
- [ ] Error logging is working

## Troubleshooting

### Backend Issues

1. **Database Connection Failed**
   - Check MONGODB_URI format
   - Verify IP whitelist in MongoDB Atlas
   - Check database user credentials

2. **Application Crashes**
   - Check Render logs for error messages
   - Verify all environment variables are set
   - Check requirements.txt has all dependencies

3. **CORS Errors** (if using separate frontend)
   - Verify FRONTEND_URL matches your Vercel URL
   - Check CORS configuration in app.py

### Frontend Issues

1. **API Calls Failing**
   - Verify REACT_APP_API_URL is correct
   - Check CORS settings on backend
   - Verify backend is accessible

## Security Notes

1. **Never commit sensitive data**:
   - config.json is in .gitignore
   - Use environment variables in production

2. **SECRET_KEY**:
   - Must be unique and random
   - Never share or commit

3. **MongoDB Credentials**:
   - Keep connection string secure
   - Use strong passwords
   - Regularly rotate credentials

## Monitoring

- **Render**: Check logs in Render dashboard
- **Vercel**: Check logs in Vercel dashboard
- **MongoDB Atlas**: Monitor database usage and performance

## Scaling

- **Render**: Upgrade plan for more resources
- **MongoDB Atlas**: Upgrade cluster for more capacity
- **Vercel**: Automatically scales with traffic

## Support

- Render Docs: https://render.com/docs
- Vercel Docs: https://vercel.com/docs
- MongoDB Atlas Docs: https://docs.atlas.mongodb.com

