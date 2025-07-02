# University Chatbot Backend API

FastAPI backend for the University of Gujrat Chatbot system with FAQ management and analytics.

## 🚀 Quick Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template-id)

### 1. One-Click Deploy
- Click the Railway button above
- Connect your GitHub account
- Set environment variables
- Deploy automatically

### 2. Manual Deploy
1. Fork this repository
2. Connect to Railway
3. Set environment variables in Railway dashboard
4. Deploy

## 🔧 Environment Variables

Set these in Railway dashboard:

```bash
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/university_bot
DB_NAME=university_bot
USERS_COLLECTION=users
FAQS_COLLECTION=faqs
JWT_SECRET_KEY=your-super-secure-secret-key
DEBUG=false
ENVIRONMENT=production
```

## 🌐 API Endpoints

- **Health Check**: `GET /`
- **API Documentation**: `GET /docs`
- **Authentication**: `POST /login`, `POST /register`
- **FAQ Management**: `GET /faqs`, `POST /faqs`, `PUT /faqs/{id}`, `DELETE /faqs/{id}`
- **Chatbot**: `POST /chat`
- **Analytics**: `GET /analytics/*`

## 🏃‍♂️ Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your values

# Run the server
python run.py
```

Visit: `http://localhost:8000`

## 📦 Tech Stack

- **Framework**: FastAPI
- **Database**: MongoDB
- **Authentication**: JWT
- **Vector Search**: FAISS
- **Embeddings**: Sentence Transformers
- **Deployment**: Railway

## 🔗 Frontend

This backend is designed to work with the University Chatbot Flutter app:
[University Chatbot Frontend](https://github.com/your-username/University_bot_Frontend)

## � License

MIT License
