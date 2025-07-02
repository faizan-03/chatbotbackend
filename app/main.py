from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .chatbot import query_bot
from .routes.faq_routes import router as faq_router
from .routes.retrain_route import router as retrain_router
from .routes.auth_routes import router as auth_router
from .routes.analytics_routes import router as analytics_router
from .routes.query_collection_routes import router as query_collection_router
from .routes.questionnaire_routes import router as questionnaire_router
from .config import settings

app = FastAPI(
    title="University Chatbot API",
    description="A comprehensive university chatbot system with FAQ management and analytics",
    version="1.0.0"
)

# Enable CORS for frontend access using settings
# More permissive CORS for mobile apps and development
cors_origins = settings.cors_origins.copy()
if settings.debug:
    # In debug mode, be more permissive for mobile apps
    cors_origins.extend(["*"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400
)

# Request schema for chatbot queries
class QuestionRequest(BaseModel):
    question: str

# Root check route
@app.get("/")
def root():
    return {"message": "🎓 University Chatbot API is live!"}

# Health check endpoint for Railway
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "University Chatbot API is running",
        "environment": settings.environment,
        "debug": settings.debug
    }

# Advanced health check with database connectivity
@app.get("/health/detailed")
def detailed_health_check():
    try:
        from .utils.db import client
        if client is None:
            return {
                "status": "unhealthy",
                "message": "Database connection failed",
                "database": "disconnected",
                "error": "MongoDB client is None",
                "environment": settings.environment
            }
        
        # Test MongoDB connection
        client.admin.command('ping')
        return {
            "status": "healthy",
            "message": "University Chatbot API is running",
            "database": "connected",
            "environment": settings.environment,
            "debug": settings.debug
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": "Database connection failed",
            "database": "disconnected",
            "error": str(e),
            "environment": settings.environment
        }

# Chatbot interaction route
@app.post("/query")
def get_response(query: QuestionRequest):
    answer = query_bot(query.question)
    return {"answer": answer}

# Admin routes
app.include_router(faq_router)
app.include_router(retrain_router)

# Authentication routes
app.include_router(auth_router)

# Review routes
from .routes.review_routes import router as review_router
app.include_router(review_router)

# Analytics routes
app.include_router(analytics_router)

# Query collection routes
app.include_router(query_collection_router)

# Questionnaire routes
app.include_router(questionnaire_router)
