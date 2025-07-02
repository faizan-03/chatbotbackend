# 🚀 Quick Railway Deployment Guide

## Step-by-Step Instructions:

### 1. Create New GitHub Repository
1. Go to [GitHub.com](https://github.com)
2. Click "New Repository"
3. Name: `university-chatbot-backend`
4. Description: "University Chatbot Backend API - FastAPI with MongoDB"
5. Set to **Public** (for easier Railway deployment)
6. Don't initialize with README (we already have one)
7. Click "Create Repository"

### 2. Push Your Backend Code
```bash
# In your backend directory
git remote add origin https://github.com/YOUR_USERNAME/university-chatbot-backend.git
git push -u origin main
```

### 3. Deploy on Railway
1. Go to [railway.app](https://railway.app)
2. Sign in with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose `university-chatbot-backend`
6. Railway will auto-detect Python and deploy

### 4. Set Environment Variables in Railway
```
MONGODB_URI=mongodb+srv://chatbot:UMtMgUGZzlBKyp4b@cluster0.t32lw.mongodb.net/university_bot?retryWrites=true&w=majority&appName=Cluster0
DB_NAME=university_bot
USERS_COLLECTION=users
FAQS_COLLECTION=faqs
JWT_SECRET_KEY=UniversityBot-2025-SecureKey-MongoDB-Production-JWT-Token-SigningKey-ForMobileApp
DEBUG=false
ENVIRONMENT=production
```

### 5. Get Your Domain
- Railway will provide: `https://your-app-name.up.railway.app`
- Test with: `https://your-domain.up.railway.app/docs`

### 6. Update Flutter App
```dart
static const String baseUrl = 'https://your-app-name.up.railway.app';
```

## ✅ That's it! Your backend will be live and auto-deploy on every push.

## 🔧 Troubleshooting
- Check Railway logs if deployment fails
- Ensure all environment variables are set
- Verify MongoDB connection string is correct
