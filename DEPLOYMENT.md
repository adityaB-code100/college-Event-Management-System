# Deployment Guide

This guide explains how to deploy the College Event Management System to Render (backend) and Vercel (frontend).

## Backend Deployment (Render)

### Prerequisites
1. A Render account (https://render.com)
2. A MongoDB database (you can use MongoDB Atlas for cloud hosting)

### Steps

1. **Prepare Your Repository**
   - Ensure your code is committed and pushed to a Git repository (GitHub, GitLab, or Bitbucket)
   - The repository should include:
     - `app.py` (main Flask application)
     - `requirements.txt` (dependencies)
     - `render.yaml` (deployment configuration)
     - `wsgi.py` (WSGI entry point)
     - `config.json` or environment variables for configuration

2. **Configure Environment Variables on Render**
   Navigate to your Render dashboard and set the following environment variables:
   ```
   SECRET_KEY=your-super-secret-key-change-this-in-production
   MONGODB_HOST=your-mongodb-host (e.g., cluster0.xxxxx.mongodb.net)
   MONGODB_PORT=27017
   MONGODB_DATABASE=college_events
   MONGODB_USERNAME=your-mongodb-username
   MONGODB_PASSWORD=your-mongodb-password
   ```

3. **Deploy to Render**
   - Go to your Render Dashboard
   - Click "New" → "Web Service"
   - Connect your Git repository
   - Configure the service:
     - Name: college-event-mgmt
     - Environment: Python
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `gunicorn --bind 0.0.0.0:$PORT wsgi:app`
   - Click "Create Web Service"

4. **Initialize Database (Optional)**
   After deployment, you can initialize the database with sample data by running:
   ```bash
   python init_mongodb.py
   ```

## Frontend Deployment (Vercel)

### Important Note
The current application is a monolithic Flask application that serves both backend API and frontend templates. To deploy separately to Vercel, you would need to:

1. **Create a Separate Frontend Application**
   - Build a React, Vue, or Next.js application
   - Configure it to communicate with your Render backend via API calls
   - Deploy this separate frontend application to Vercel

2. **Alternative Approach**
   If you want to keep the current monolithic structure, you can deploy the entire application to Render and it will serve both the API and frontend templates.

## Configuration Files Explanation

### render.yaml
This file tells Render how to deploy your application:
```yaml
services:
  - type: web
    name: college-event-mgmt
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "gunicorn --bind 0.0.0.0:$PORT wsgi:app"
    envVars:
      - key: PYTHON_VERSION
        value: 3.9.15
```

### wsgi.py
This is the standard entry point for WSGI applications:
```python
from app import app

if __name__ == "__main__":
    app.run()
```

### Procfile
Used by Heroku and Render for deployment:
```
web: gunicorn --bind 0.0.0.0:$PORT wsgi:app
```

## Environment Variables

The application supports configuration through both `config.json` and environment variables. For deployment, it's recommended to use environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| SECRET_KEY | Flask secret key | fallback-secret-key |
| MONGODB_HOST | MongoDB host | localhost |
| MONGODB_PORT | MongoDB port | 27017 |
| MONGODB_DATABASE | MongoDB database name | college_events |
| MONGODB_USERNAME | MongoDB username | (empty) |
| MONGODB_PASSWORD | MongoDB password | (empty) |

## MongoDB Atlas Configuration

For production deployment, it's recommended to use MongoDB Atlas:

1. Create a MongoDB Atlas account
2. Create a new cluster
3. Add your Render app's IP address to the IP whitelist
4. Create a database user
5. Get the connection string and configure the environment variables accordingly

Example connection string:
```
mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/college_events
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check MongoDB credentials and connection string
   - Ensure IP whitelisting is configured correctly
   - Verify MongoDB service is running

2. **Module Not Found Errors**
   - Ensure all dependencies are listed in `requirements.txt`
   - Check Python version compatibility

3. **Permission Denied**
   - Check file permissions
   - Ensure environment variables are correctly set

### Logs
Check the logs on Render dashboard for detailed error information:
- Go to your service on Render
- Click "Logs" tab
- Look for error messages and stack traces

## Security Considerations

1. **Change Secret Key**
   Always change the `SECRET_KEY` in production

2. **Database Security**
   - Use strong passwords
   - Enable authentication
   - Restrict IP access

3. **HTTPS**
   Render automatically provides HTTPS for your applications

4. **Environment Variables**
   Never commit sensitive information like passwords to version control

## Scaling

Render automatically handles scaling for your web services. For high-traffic applications:

1. Consider upgrading your Render plan
2. Use a managed MongoDB service like MongoDB Atlas
3. Implement caching mechanisms if needed
4. Monitor performance and adjust resources accordingly

## Support

For issues with deployment:
1. Check the Render documentation: https://render.com/docs
2. Review application logs
3. Ensure all prerequisites are met
4. Contact Render support if needed