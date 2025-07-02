from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from bson import ObjectId
from ..utils.db import db
from ..routes.auth_routes import get_current_user
from datetime import datetime
from typing import List, Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Get reviews collection
reviews_collection = db["reviews"] if db is not None else None

class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    feedback: str = Field(..., min_length=1, max_length=500, description="Review feedback")
    
class ReviewResponse(BaseModel):
    id: str
    user_name: str
    user_email: str
    rating: int
    feedback: str
    created_at: str

class ReviewStats(BaseModel):
    total_reviews: int
    average_rating: float
    rating_distribution: dict

def serialize_review(review):
    """Convert MongoDB document to ReviewResponse format"""
    return {
        "id": str(review["_id"]),
        "user_name": review.get("user_name", "Anonymous"),
        "user_email": review.get("user_email", ""),
        "rating": review.get("rating", 0),
        "feedback": review.get("feedback", ""),
        "created_at": review.get("created_at").isoformat() if review.get("created_at") else datetime.now().isoformat()
    }

@router.post("/reviews", status_code=201)
def create_review(review: ReviewCreate, current_user: dict = Depends(get_current_user)):
    """Create a new review"""
    try:
        if reviews_collection is None:
            raise HTTPException(status_code=503, detail="Database connection not available")
        
        # Check if user already has a review
        existing_review = reviews_collection.find_one({"user_id": current_user.get("user_id")})
        if existing_review:
            raise HTTPException(status_code=400, detail="You have already submitted a review")
        
        # Validate rating
        if review.rating < 1 or review.rating > 5:
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
        
        # Create review document
        review_doc = {
            "user_id": current_user.get("user_id"),
            "user_name": current_user.get("name"),
            "user_email": current_user.get("sub"),  # email from JWT
            "rating": review.rating,
            "feedback": review.feedback.strip(),
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Insert review into database
        result = reviews_collection.insert_one(review_doc)
        
        if result.inserted_id:
            logger.info(f"Review created with ID: {result.inserted_id} by user: {current_user.get('name')}")
            return {
                "message": "Review submitted successfully",
                "review_id": str(result.inserted_id)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to submit review")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating review: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/reviews", response_model=List[ReviewResponse])
def get_reviews(
    limit: int = Query(20, ge=1, le=100, description="Number of reviews to return"),
    skip: int = Query(0, ge=0, description="Number of reviews to skip"),
    sort_by: str = Query("created_at", description="Sort field (created_at, rating)"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)")
):
    """Get all reviews with pagination and sorting"""
    try:
        if reviews_collection is None:
            raise HTTPException(status_code=503, detail="Database connection not available")
        
        # Determine sort direction
        sort_direction = -1 if sort_order.lower() == "desc" else 1
        
        # Validate sort field
        valid_sort_fields = ["created_at", "rating", "user_name"]
        if sort_by not in valid_sort_fields:
            sort_by = "created_at"
        
        # Get reviews from database with pagination and sorting
        reviews_cursor = reviews_collection.find().sort(sort_by, sort_direction).skip(skip).limit(limit)
        reviews = []
        
        for review in reviews_cursor:
            reviews.append(serialize_review(review))
        
        logger.info(f"Retrieved {len(reviews)} reviews with skip={skip}, limit={limit}")
        return reviews
    
    except Exception as e:
        logger.error(f"Error getting reviews: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/reviews/stats", response_model=ReviewStats)
def get_review_stats():
    """Get review statistics"""
    try:
        if reviews_collection is None:
            raise HTTPException(status_code=503, detail="Database connection not available")
        
        # Get total count
        total_reviews = reviews_collection.count_documents({})
        
        if total_reviews == 0:
            return ReviewStats(
                total_reviews=0,
                average_rating=0.0,
                rating_distribution={"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
            )
        
        # Calculate average rating using aggregation
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "average_rating": {"$avg": "$rating"},
                    "ratings": {"$push": "$rating"}
                }
            }
        ]
        
        result = list(reviews_collection.aggregate(pipeline))
        average_rating = result[0]["average_rating"] if result else 0.0
        
        # Calculate rating distribution
        rating_distribution = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
        if result:
            for rating in result[0]["ratings"]:
                rating_distribution[str(rating)] += 1
        
        return ReviewStats(
            total_reviews=total_reviews,
            average_rating=round(average_rating, 2),
            rating_distribution=rating_distribution
        )
    
    except Exception as e:
        logger.error(f"Error getting review stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/reviews/my-review")
def get_my_review(current_user: dict = Depends(get_current_user)):
    """Get current user's review"""
    try:
        if reviews_collection is None:
            raise HTTPException(status_code=503, detail="Database connection not available")
        
        user_review = reviews_collection.find_one({"user_id": current_user.get("user_id")})
        
        if not user_review:
            return {"has_review": False}
        
        return {
            "has_review": True,
            "review": serialize_review(user_review)
        }
    
    except Exception as e:
        logger.error(f"Error getting user review: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.put("/reviews/my-review")
def update_my_review(review: ReviewCreate, current_user: dict = Depends(get_current_user)):
    """Update current user's review"""
    try:
        if reviews_collection is None:
            raise HTTPException(status_code=503, detail="Database connection not available")
        
        # Validate rating
        if review.rating < 1 or review.rating > 5:
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
        
        # Update the review
        result = reviews_collection.update_one(
            {"user_id": current_user.get("user_id")},
            {
                "$set": {
                    "rating": review.rating,
                    "feedback": review.feedback.strip(),
                    "updated_at": datetime.now()
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Review not found")
        
        logger.info(f"Review updated by user: {current_user.get('name')}")
        return {"message": "Review updated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating review: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.delete("/reviews/{review_id}")
def delete_review(review_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a review (admin only or own review)"""
    try:
        if reviews_collection is None:
            raise HTTPException(status_code=503, detail="Database connection not available")
        
        # Check if review exists
        review = reviews_collection.find_one({"_id": ObjectId(review_id)})
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        
        # Check permissions (admin or own review)
        user_role = current_user.get("role", "")
        user_id = current_user.get("user_id", "")
        
        if user_role != "admin" and review.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # Delete the review
        result = reviews_collection.delete_one({"_id": ObjectId(review_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Review not found")
        
        logger.info(f"Review {review_id} deleted by user: {current_user.get('name')}")
        return {"message": "Review deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting review: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
