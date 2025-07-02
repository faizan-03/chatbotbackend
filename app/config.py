import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # MongoDB Configuration
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/university_bot")
    db_name: str = os.getenv("DB_NAME", "university_bot")
    users_collection: str = os.getenv("USERS_COLLECTION", "users")
    faqs_collection: str = os.getenv("FAQS_COLLECTION", "faqs")
    
    # JWT Configuration
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "fallback-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # API Configuration
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))
    
    # CORS Configuration
    cors_origins: list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080"
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Handle CORS_ORIGINS from environment variable
        cors_env = os.getenv("CORS_ORIGINS")
        if cors_env:
            try:
                import json
                self.cors_origins = json.loads(cors_env)
            except json.JSONDecodeError:
                # Fallback: split by comma if not valid JSON
                self.cors_origins = [origin.strip() for origin in cors_env.split(',')]
        
        # Add Railway domain to CORS if available
        railway_domain = os.getenv("RAILWAY_STATIC_URL")
        if railway_domain and railway_domain not in self.cors_origins:
            self.cors_origins.append(f"https://{railway_domain}")
    
    # Development Settings
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields to be ignored

# Global settings instance
settings = Settings()
