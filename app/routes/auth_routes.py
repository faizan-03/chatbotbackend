from fastapi import APIRouter, HTTPException, status, Depends, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from ..utils.db import db
from ..utils.jwt_utils import create_access_token, verify_token, get_token_expiry_time
from ..config import settings
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import logging

router = APIRouter()
security = HTTPBearer()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get users collection
users_collection = db["users"] if db is not None else None

## CORS preflight requests are handled by FastAPI's CORS middleware in main.py

# Request models
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str  # "student" or "admin"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    email: str
    name: str
    expires_at: str

class TokenValidationResponse(BaseModel):
    valid: bool
    role: str
    email: str
    name: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user: UserRegister):
    """Register a new user"""
    try:
        if users_collection is None:
            raise HTTPException(
                status_code=500, 
                detail="Database connection not available"
            )
        
        logger.info(f"Registering user with email: {user.email}")
        
        # Check if user already exists
        existing_user = users_collection.find_one({"email": user.email})
        if existing_user:
            logger.warning(f"User with email {user.email} already exists")
            raise HTTPException(
                status_code=400, 
                detail="User with this email already exists"
            )
        
        # Validate role
        if user.role not in ["student", "admin"]:
            raise HTTPException(
                status_code=400, 
                detail="Role must be either 'student' or 'admin'"
            )
        
        # Hash password
        hashed_password = generate_password_hash(user.password)
        
        # Create user document
        user_doc = {
            "name": user.name,
            "email": user.email,
            "password": hashed_password,
            "role": user.role,
            "created_at": datetime.now(),
            "is_active": True
        }
        
        # Insert user into database
        result = users_collection.insert_one(user_doc)
        
        if result.inserted_id:
            logger.info(f"User {user.email} registered successfully with ID: {result.inserted_id}")
            return {
                "message": "User registered successfully",
                "user_id": str(result.inserted_id),
                "email": user.email,
                "role": user.role
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail="Failed to register user"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during user registration: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=LoginResponse)
def login_user(user: UserLogin):
    """Login user and return JWT token"""
    try:
        if users_collection is None:
            raise HTTPException(
                status_code=500, 
                detail="Database connection not available"
            )
        
        logger.info(f"Login attempt for email: {user.email}")
        
        # Find user by email
        user_doc = users_collection.find_one({"email": user.email})
        if not user_doc:
            logger.warning(f"User with email {user.email} not found")
            raise HTTPException(
                status_code=401, 
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user_doc.get("is_active", True):
            logger.warning(f"Inactive user attempted login: {user.email}")
            raise HTTPException(
                status_code=401, 
                detail="Account is deactivated"
            )
        
        # Verify password
        if not check_password_hash(user_doc["password"], user.password):
            logger.warning(f"Invalid password for user: {user.email}")
            raise HTTPException(
                status_code=401, 
                detail="Invalid email or password"
            )
        
        # Create JWT token
        token_data = {
            "sub": user_doc["email"],
            "role": user_doc["role"],
            "name": user_doc["name"],
            "user_id": str(user_doc["_id"])
        }
        access_token = create_access_token(data=token_data)
        expires_at = get_token_expiry_time()
        
        # Update last login time
        users_collection.update_one(
            {"_id": user_doc["_id"]},
            {"$set": {"last_login": datetime.now()}}
        )
        
        logger.info(f"User {user.email} logged in successfully")
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            role=user_doc["role"],
            email=user_doc["email"],
            name=user_doc["name"],
            expires_at=expires_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Login failed: {str(e)}"
        )

@router.get("/users")
def get_all_users():
    """Get all users (admin only - add authentication later)"""
    try:
        if users_collection is None:
            raise HTTPException(
                status_code=500, 
                detail="Database connection not available"
            )
        
        users = list(users_collection.find(
            {},
            {"password": 0}  # Exclude password from response
        ))
        
        # Convert ObjectId to string
        for user in users:
            user["_id"] = str(user["_id"])
        
        return users
        
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch users: {str(e)}"
        )

@router.get("/users/count")
def get_user_count():
    """Get total number of registered users"""
    try:
        if users_collection is None:
            return {"total_users": 0, "message": "Database not available"}
        
        total_users = users_collection.count_documents({})
        active_users = users_collection.count_documents({"is_active": True})
        admin_users = users_collection.count_documents({"role": "admin"})
        student_users = users_collection.count_documents({"role": "student"})
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "admin_users": admin_users,
            "student_users": student_users
        }
        
    except Exception as e:
        logger.error(f"Error getting user count: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get user count: {str(e)}"
        )

# JWT Token validation and user authentication
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
    token = credentials.credentials
    payload = verify_token(token)
    return payload

@router.post("/validate-token", response_model=TokenValidationResponse)
def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate JWT token and return user info"""
    try:
        payload = verify_token(credentials.credentials)
        
        # Optional: Check if user still exists in database
        if users_collection is not None:
            user_doc = users_collection.find_one({"email": payload["sub"]})
            if not user_doc or not user_doc.get("is_active", True):
                raise HTTPException(
                    status_code=401,
                    detail="User account no longer active"
                )
        
        return TokenValidationResponse(
            valid=True,
            role=payload["role"],
            email=payload["sub"],
            name=payload["name"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

@router.post("/logout")
def logout_user():
    """Logout user (client should clear the token)"""
    return {"message": "Logged out successfully. Please clear your token."}

@router.get("/protected-test")
def protected_route(current_user: dict = Depends(get_current_user)):
    """Test route to verify JWT authentication works"""
    return {
        "message": "This is a protected route",
        "user": current_user["sub"],
        "role": current_user["role"]
    }
