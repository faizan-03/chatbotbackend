# University Chatbot Backend - Railway Deployment

## 🚀 Quick Railway Deployment

### 1. Connect GitHub Repository
- Go to [Railway](https://railway.app)
- Sign in with GitHub
- Click "New Project" → "Deploy from GitHub repo"
- Select this repository
- Choose only the `Backend` folder

### 2. Set Environment Variables
Add these environment variables in Railway dashboard:

```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/university_bot
DB_NAME=university_bot
USERS_COLLECTION=users
FAQS_COLLECTION=faqs
JWT_SECRET_KEY=your-super-secure-secret-key
DEBUG=false
ENVIRONMENT=production
```

### 3. Deploy
- Railway will automatically detect the Python app
- It will install dependencies from `requirements.txt`
- Start the app using the `Procfile`

### 4. Get Your Domain
- After successful deployment, you'll get a domain like: `https://your-app-name.up.railway.app`
- Use this domain in your Flutter app configuration

## 🔗 API Endpoints
- Health Check: `https://your-domain.railway.app/`
- API Docs: `https://your-domain.railway.app/docs`
- Login: `https://your-domain.railway.app/login`
- Register: `https://your-domain.railway.app/register`

## 🛠️ Local Development
```bash
cd Backend
pip install -r requirements.txt
python run.py
```

Visit: `http://localhost:8000`
