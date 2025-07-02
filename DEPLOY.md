# 🚀 Railway Deployment Checklist

## ✅ Pre-deployment Setup
- [x] Procfile created
- [x] railway.json configured 
- [x] requirements.txt updated with all dependencies
- [x] runtime.txt specifies Python version
- [x] .railwayignore excludes unnecessary files
- [x] Config supports Railway environment variables
- [x] CORS configured for Railway domains

## 🌐 Railway Deployment Steps

### 1. Repository Setup
1. **Push Backend folder to GitHub**
   ```bash
   git add Backend/
   git commit -m "Prepare backend for Railway deployment"
   git push origin main
   ```

### 2. Railway Project Creation
1. Go to [railway.app](https://railway.app)
2. Sign in with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository
6. Select **only the Backend folder** as root directory

### 3. Environment Variables
Set these in Railway dashboard under "Variables":
```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/university_bot
DB_NAME=university_bot
USERS_COLLECTION=users
FAQS_COLLECTION=faqs
JWT_SECRET_KEY=your-super-secure-secret-key-change-this
DEBUG=false
ENVIRONMENT=production
```

### 4. Deployment
- Railway will automatically:
  - Detect Python app
  - Install from requirements.txt
  - Run using Procfile
  - Assign a domain

### 5. Test Deployment
Your app will be available at: `https://your-app-name.up.railway.app`

Test endpoints:
- Health: `https://your-domain.railway.app/`
- Docs: `https://your-domain.railway.app/docs`

### 6. Update Flutter App
Update your Flutter app config with the Railway domain:
```dart
static const String baseUrl = 'https://your-app-name.up.railway.app';
```

## 🔄 Auto-deployment
- Any push to GitHub will automatically trigger Railway deployment
- Check deployment logs in Railway dashboard
- Monitor app health and performance

## 📝 Notes
- Railway provides free tier with 512MB RAM
- Automatic HTTPS certificates
- Environment variables are encrypted
- Logs available in Railway dashboard
