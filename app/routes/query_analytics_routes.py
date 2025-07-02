from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from datetime import datetime
from ..utils.db import db
from ..routes.auth_routes import get_current_user
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Collections
if db is not None:
    queries_collection = db["queries"]
    faq_collection = db["faqs"]
else:
    queries_collection = None
    faq_collection = None

class QueryRequest(BaseModel):
    question: str
    user_id: str
    response_found: bool
    response: str = ""
    response_time: float = 0.0

class ConvertToFAQRequest(BaseModel):
    question: str
    suggested_answer: str = ""
    category: str = "general"

@router.post("/analytics/log-query")
def log_query(query_data: QueryRequest):
    """Log a query for analytics tracking"""
    try:
        if not queries_collection:
            return {"status": "skipped", "message": "Database not available"}
        
        # Create query document
        query_doc = {
            "question": query_data.question,
            "user_id": query_data.user_id,
            "response_found": query_data.response_found,
            "response": query_data.response,
            "response_time": query_data.response_time,
            "timestamp": datetime.now(),
            "attempts": 1
        }
        
        # Check if similar query exists to increment attempts
        existing_query = queries_collection.find_one({
            "question": query_data.question,
            "user_id": query_data.user_id,
            "response_found": False
        })
        
        if existing_query:
            # Update attempts count
            queries_collection.update_one(
                {"_id": existing_query["_id"]},
                {"$inc": {"attempts": 1}, "$set": {"timestamp": datetime.now()}}
            )
        else:
            # Insert new query
            result = queries_collection.insert_one(query_doc)
            logger.info(f"Query logged with ID: {result.inserted_id}")
        
        return {"status": "logged", "message": "Query logged successfully"}
        
    except Exception as e:
        logger.error(f"Error logging query: {str(e)}")
        return {"status": "error", "message": f"Failed to log query: {str(e)}"}

@router.post("/analytics/convert-to-faq")
def convert_failed_query_to_faq(
    convert_data: ConvertToFAQRequest,
    current_user: dict = Depends(get_current_user)
):
    """Convert a failed query to an FAQ entry"""
    try:
        if not faq_collection:
            raise HTTPException(
                status_code=500,
                detail="Database not available"
            )
        
        # Check if FAQ already exists
        existing_faq = faq_collection.find_one({
            "question": {"$regex": convert_data.question, "$options": "i"}
        })
        
        if existing_faq:
            return {
                "status": "exists",
                "message": "Similar FAQ already exists",
                "faq_id": str(existing_faq["_id"])
            }
        
        # Create new FAQ entry
        faq_doc = {
            "question": convert_data.question,
            "answer": convert_data.suggested_answer or "Answer pending - to be filled by admin",
            "category": convert_data.category,
            "keywords": convert_data.question.lower().split(),
            "created_by": current_user.get("email", "system"),
            "created_at": datetime.now(),
            "status": "pending" if not convert_data.suggested_answer else "active",
            "source": "failed_query",
            "usage_count": 0
        }
        
        result = faq_collection.insert_one(faq_doc)
        
        # Mark the failed query as converted (if it exists in queries collection)
        if queries_collection:
            queries_collection.update_many(
                {"question": convert_data.question, "response_found": False},
                {"$set": {"converted_to_faq": True, "faq_id": str(result.inserted_id)}}
            )
        
        logger.info(f"Failed query converted to FAQ with ID: {result.inserted_id}")
        
        return {
            "status": "created",
            "message": "Failed query successfully converted to FAQ",
            "faq_id": str(result.inserted_id),
            "needs_answer": not convert_data.suggested_answer
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error converting query to FAQ: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to convert query to FAQ: {str(e)}"
        )

@router.delete("/analytics/dismiss-failed-query")
def dismiss_failed_query(
    question: str,
    current_user: dict = Depends(get_current_user)
):
    """Dismiss a failed query (mark as resolved without creating FAQ)"""
    try:
        if not queries_collection:
            raise HTTPException(
                status_code=500,
                detail="Database not available"
            )
        
        # Mark query as dismissed
        result = queries_collection.update_many(
            {"question": question, "response_found": False},
            {"$set": {"dismissed": True, "dismissed_by": current_user.get("email", "system")}}
        )
        
        return {
            "status": "dismissed",
            "message": f"Dismissed {result.modified_count} failed queries",
            "modified_count": result.modified_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error dismissing query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to dismiss query: {str(e)}"
        )
