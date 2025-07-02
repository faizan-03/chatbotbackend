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

# Simple CORS configuration for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request schema for chatbot queries
class QuestionRequest(BaseModel):
    question: str

# Root check route
@app.get("/")
def root():
    return {"message": "🎓 University Chatbot API is live!"}

# Simple health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "API is running"}

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
