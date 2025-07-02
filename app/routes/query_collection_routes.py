from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from bson import ObjectId
from ..utils.db import db
from ..routes.auth_routes import get_current_user
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import logging
import csv
from io import StringIO
import jwt
from ..config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Get queries collection
queries_collection = db["queries"] if db is not None else None

class UserQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)

class QueryReply(BaseModel):
    answer: str = Field(..., min_length=1, max_length=2000)
    
class QueryResponse(BaseModel):
    success: bool
    message: str

class CollectedQuery(BaseModel):
    id: str
    query: str
    user_name: str
    user_email: str
    timestamp: str
    used_for_training: bool
    user_agent: str

# Optional authentication dependency
async def get_optional_user(request: Request):
    """Get current user or None if not authenticated"""
    try:
        # Try to get authorization header
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return None
            
        token = authorization.split(" ")[1]
        
        # Decode token
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            return None
            
        # Get user from database
        from ..utils.db import db
        users_collection = db["users"] if db is not None else None
        if users_collection is None:
            return None
            
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if user:
            return {
                "user_id": str(user["_id"]),
                "name": user.get("name", "Anonymous"),
                "email": user.get("email", ""),
                "role": user.get("role", "student")
            }
        return None
    except Exception:
        return None

@router.post("/collect-query", response_model=QueryResponse)
async def collect_query(
    user_query: UserQuery, 
    request: Request,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """Store user query for future training"""
    try:
        if queries_collection is None:
            logger.warning("Database connection not available for query collection")
            return QueryResponse(success=True, message="Query processed")
        
        # Get user agent and IP
        user_agent = request.headers.get("User-Agent", "unknown")
        client_ip = request.client.host if request.client else "unknown"
        
        # Create query document
        query_doc = {
            "query": user_query.query.strip(),
            "timestamp": datetime.now(),
            "used_for_training": False,
            "user_agent": user_agent,
            "ip_address": client_ip
        }
        
        # Add user info if available
        if current_user:
            query_doc.update({
                "user_id": current_user.get("user_id", ""),
                "user_name": current_user.get("name", "Anonymous"),
                "user_email": current_user.get("email", "")
            })
        else:
            query_doc.update({
                "user_name": "Anonymous",
                "user_email": ""
            })
        
        # Insert into database
        result = queries_collection.insert_one(query_doc)
        
        if result.inserted_id:
            logger.info(f"Query collected: {user_query.query[:50]}... from {query_doc['user_name']}")
        else:
            logger.warning("Failed to store query in database")
            
        # Always return success to maintain smooth UX
        return QueryResponse(success=True, message="Query processed")
    
    except Exception as e:
        logger.error(f"Error collecting query: {str(e)}")
        # Don't expose internal errors to client
        return QueryResponse(success=True, message="Query processed")

@router.get("/admin/collected-queries", response_model=List[CollectedQuery])
async def get_collected_queries(
    limit: int = 100,
    skip: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Get all collected queries (Admin only)"""
    try:
        # Verify admin role
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
            
        if queries_collection is None:
            raise HTTPException(status_code=503, detail="Database connection not available")
        
        # Get queries with pagination
        queries_cursor = queries_collection.find().sort("timestamp", -1).skip(skip).limit(limit)
        queries = []
        
        for query in queries_cursor:
            queries.append(CollectedQuery(
                id=str(query["_id"]),
                query=query.get("query", ""),
                user_name=query.get("user_name", "Anonymous"),
                user_email=query.get("user_email", ""),
                timestamp=query.get("timestamp").isoformat() if query.get("timestamp") else "",
                used_for_training=query.get("used_for_training", False),
                user_agent=query.get("user_agent", "unknown")
            ))
        
        logger.info(f"Retrieved {len(queries)} collected queries for admin {current_user.get('name')}")
        return queries
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collected queries: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/admin/collected-queries/{query_id}/mark-used")
async def mark_query_as_used(
    query_id: str, 
    current_user: dict = Depends(get_current_user)
):
    """Mark a query as used for training (Admin only)"""
    try:
        # Verify admin role
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
            
        if queries_collection is None:
            raise HTTPException(status_code=503, detail="Database connection not available")
        
        # Validate ObjectId
        try:
            object_id = ObjectId(query_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid query ID")
        
        result = queries_collection.update_one(
            {"_id": object_id},
            {"$set": {
                "used_for_training": True, 
                "marked_by": current_user.get("name", "admin"),
                "marked_at": datetime.now()
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Query not found")
        
        logger.info(f"Query {query_id} marked as used by {current_user.get('name')}")
        return {"success": True, "message": "Query marked as used for training"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking query as used: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/admin/collected-queries/{query_id}")
async def delete_query(
    query_id: str, 
    current_user: dict = Depends(get_current_user)
):
    """Delete a collected query (Admin only)"""
    try:
        # Verify admin role
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
            
        if queries_collection is None:
            raise HTTPException(status_code=503, detail="Database connection not available")
        
        # Validate ObjectId
        try:
            object_id = ObjectId(query_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid query ID")
        
        result = queries_collection.delete_one({"_id": object_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Query not found")
        
        logger.info(f"Query {query_id} deleted by {current_user.get('name')}")
        return {"success": True, "message": "Query deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting query: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/admin/collected-queries/export")
async def export_collected_queries(current_user: dict = Depends(get_current_user)):
    """Export collected queries as CSV (Admin only)"""
    try:
        # Verify admin role
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
            
        if queries_collection is None:
            raise HTTPException(status_code=503, detail="Database connection not available")
        
        # Get all queries
        queries_cursor = queries_collection.find().sort("timestamp", -1)
        
        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Query", "User Name", "User Email", "Timestamp", 
            "Used For Training", "User Agent", "IP Address"
        ])
        
        # Write data
        for query in queries_cursor:
            writer.writerow([
                query.get("query", ""),
                query.get("user_name", "Anonymous"),
                query.get("user_email", ""),
                query.get("timestamp", "").isoformat() if query.get("timestamp") else "",
                "Yes" if query.get("used_for_training", False) else "No",
                query.get("user_agent", "unknown"),
                query.get("ip_address", "unknown")
            ])
        
        # Return CSV file
        output.seek(0)
        filename = f"collected_queries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        logger.info(f"CSV export generated by {current_user.get('name')}")
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting queries: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/admin/collected-queries/stats")
async def get_query_stats(current_user: dict = Depends(get_current_user)):
    """Get statistics about collected queries (Admin only)"""
    try:
        # Verify admin role
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
            
        if queries_collection is None:
            raise HTTPException(status_code=503, detail="Database connection not available")
        
        # Get statistics
        total_queries = queries_collection.count_documents({})
        used_for_training = queries_collection.count_documents({"used_for_training": True})
        unused_for_training = total_queries - used_for_training
        
        # Get queries from last 7 days
        week_ago = datetime.now() - timedelta(days=7)
        recent_queries = queries_collection.count_documents({
            "timestamp": {"$gte": week_ago}
        })
        
        return {
            "total_queries": total_queries,
            "used_for_training": used_for_training,
            "unused_for_training": unused_for_training,
            "recent_queries": recent_queries
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting query stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/admin/collected-queries/{query_id}/reply-and-add-faq")
async def reply_to_query_and_add_faq(
    query_id: str,
    reply: QueryReply,
    current_user: dict = Depends(get_current_user)
):
    """Reply to a query and add it to FAQ database (Admin only)"""
    try:
        # Verify admin role
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
            
        if queries_collection is None:
            raise HTTPException(status_code=503, detail="Database connection not available")
        
        # Validate ObjectId
        try:
            object_id = ObjectId(query_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid query ID")
        
        # Get the query
        query_doc = queries_collection.find_one({"_id": object_id})
        if not query_doc:
            raise HTTPException(status_code=404, detail="Query not found")
        
        # Add to FAQ collection
        from ..utils.db import faq_collection
        if faq_collection is None:
            raise HTTPException(status_code=503, detail="FAQ database connection not available")
        
        faq_doc = {
            "question": query_doc.get("query", ""),
            "answer": reply.answer.strip(),
            "created_by": current_user.get("name", "admin"),
            "created_at": datetime.now(),
            "source": "query_reply",
            "source_query_id": str(query_doc["_id"])
        }
        
        faq_result = faq_collection.insert_one(faq_doc)
        
        # Mark query as used for training
        queries_collection.update_one(
            {"_id": object_id},
            {"$set": {
                "used_for_training": True,
                "replied_by": current_user.get("name", "admin"),
                "replied_at": datetime.now(),
                "added_to_faq": True,
                "faq_id": str(faq_result.inserted_id)
            }}
        )
        
        logger.info(f"Query {query_id} replied to and added to FAQ by {current_user.get('name')}")
        return {
            "success": True, 
            "message": "Query replied to and added to FAQ successfully",
            "faq_id": str(faq_result.inserted_id)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error replying to query and adding FAQ: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
