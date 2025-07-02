from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from bson import ObjectId
from ..utils.db import db
from ..routes.auth_routes import get_current_user
from datetime import datetime
from typing import List, Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Get questionnaires collection
questionnaires_collection = db["questionnaires"] if db is not None else None

class QuestionnaireSubmission(BaseModel):
    question: str = Field(..., min_length=10, max_length=2000)
    category: str = Field(default="general")
    priority: str = Field(default="normal")
    context: Optional[str] = Field(default=None, max_length=1000)

class QuestionnaireReply(BaseModel):
    answer: str = Field(..., min_length=1, max_length=2000)
    add_to_faq: bool = Field(default=True)

class QuestionnaireResponse(BaseModel):
    id: str
    question: str
    category: str
    priority: str
    status: str
    user_name: str
    user_email: str
    context: Optional[str] = None
    created_at: str
    admin_answer: Optional[str] = None
    answered_at: Optional[str] = None
    answered_by: Optional[str] = None
    is_read_by_user: bool = False

@router.post("/questionnaire")
async def submit_questionnaire(
    questionnaire: QuestionnaireSubmission,
    current_user: dict = Depends(get_current_user)
):
    """Submit a questionnaire to admin"""
    try:
        if questionnaires_collection is None:
            raise HTTPException(status_code=503, detail="Database connection not available")
        
        # Create questionnaire document
        questionnaire_doc = {
            "question": questionnaire.question.strip(),
            "category": questionnaire.category,
            "priority": questionnaire.priority,
            "context": questionnaire.context.strip() if questionnaire.context else None,
            "status": "pending",
            "user_id": str(current_user.get("user_id")),
            "user_name": current_user.get("name", "Anonymous"),
            "user_email": current_user.get("email", ""),
            "created_at": datetime.now(),
            "admin_answer": None,
            "answered_at": None,
            "answered_by": None,
            "is_read_by_user": False
        }
        
        result = questionnaires_collection.insert_one(questionnaire_doc)
        
        if result.inserted_id:
            logger.info(f"Questionnaire submitted by {current_user.get('name')}: {questionnaire.question[:50]}...")
            return {
                "success": True, 
                "message": "Question submitted successfully", 
                "questionnaire_id": str(result.inserted_id)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to submit questionnaire")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting questionnaire: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/my-questionnaires")
async def get_my_questionnaires(current_user: dict = Depends(get_current_user)):
    """Get user's questionnaires"""
    try:
        if questionnaires_collection is None:
            raise HTTPException(status_code=503, detail="Database connection not available")
        
        user_id = str(current_user.get("user_id"))
        questionnaires_cursor = questionnaires_collection.find({"user_id": user_id}).sort("created_at", -1)
        
        questionnaires = []
        for q in questionnaires_cursor:
            questionnaires.append(QuestionnaireResponse(
                id=str(q["_id"]),
                question=q.get("question", ""),
                category=q.get("category", "general"),
                priority=q.get("priority", "normal"),
                status=q.get("status", "pending"),
                user_name=q.get("user_name", ""),
                user_email=q.get("user_email", ""),
                context=q.get("context"),
                created_at=q.get("created_at").isoformat() if q.get("created_at") else "",
                admin_answer=q.get("admin_answer"),
                answered_at=q.get("answered_at").isoformat() if q.get("answered_at") else None,
                answered_by=q.get("answered_by"),
                is_read_by_user=q.get("is_read_by_user", False)
            ))
        
        return questionnaires
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting questionnaires: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/admin/questionnaires")
async def get_all_questionnaires(
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Get all questionnaires (Admin only)"""
    try:
        # Verify admin role
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
            
        if questionnaires_collection is None:
            raise HTTPException(status_code=503, detail="Database connection not available")
        
        # Build query filter
        query_filter = {}
        if status:
            query_filter["status"] = status
        if category:
            query_filter["category"] = category
        if priority:
            query_filter["priority"] = priority
        
        questionnaires_cursor = questionnaires_collection.find(query_filter).sort("created_at", -1).skip(skip).limit(limit)
        
        questionnaires = []
        for q in questionnaires_cursor:
            questionnaires.append(QuestionnaireResponse(
                id=str(q["_id"]),
                question=q.get("question", ""),
                category=q.get("category", "general"),
                priority=q.get("priority", "normal"),
                status=q.get("status", "pending"),
                user_name=q.get("user_name", ""),
                user_email=q.get("user_email", ""),
                context=q.get("context"),
                created_at=q.get("created_at").isoformat() if q.get("created_at") else "",
                admin_answer=q.get("admin_answer"),
                answered_at=q.get("answered_at").isoformat() if q.get("answered_at") else None,
                answered_by=q.get("answered_by"),
                is_read_by_user=q.get("is_read_by_user", False)
            ))
        
        return questionnaires
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting questionnaires: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/admin/questionnaires/{questionnaire_id}/answer")
async def answer_questionnaire(
    questionnaire_id: str,
    answer: QuestionnaireReply,
    current_user: dict = Depends(get_current_user)
):
    """Answer a questionnaire and optionally add to FAQ (Admin only)"""
    try:
        # Verify admin role
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
            
        if questionnaires_collection is None:
            raise HTTPException(status_code=503, detail="Database connection not available")
        
        # Validate ObjectId
        try:
            object_id = ObjectId(questionnaire_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid questionnaire ID")
        
        # Update questionnaire with answer
        update_doc = {
            "$set": {
                "admin_answer": answer.answer.strip(),
                "status": "answered",
                "answered_at": datetime.now(),
                "answered_by": current_user.get("name", "Admin"),
                "is_read_by_user": False  # User hasn't read the answer yet
            }
        }
        
        result = questionnaires_collection.update_one({"_id": object_id}, update_doc)
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Questionnaire not found")
        
        # If requested, add to FAQ
        if answer.add_to_faq:
            try:
                # Get the original questionnaire to use as FAQ question
                original_questionnaire = questionnaires_collection.find_one({"_id": object_id})
                if original_questionnaire:
                    faqs_collection = db["faqs"]
                    faq_doc = {
                        "question": original_questionnaire.get("question", ""),
                        "answer": answer.answer.strip(),
                        "created_by": current_user.get("name", "Admin"),
                        "created_at": datetime.now(),
                        "category": original_questionnaire.get("category", "general"),
                        "is_active": True,
                        "source": "questionnaire",
                        "source_id": str(object_id)
                    }
                    faqs_collection.insert_one(faq_doc)
                    logger.info(f"FAQ added from questionnaire {questionnaire_id}")
            except Exception as e:
                logger.error(f"Error adding FAQ from questionnaire: {str(e)}")
                # Don't fail the answer if FAQ addition fails
        
        logger.info(f"Questionnaire {questionnaire_id} answered by {current_user.get('name')}")
        return {
            "success": True, 
            "message": "Answer submitted successfully" + (" and added to FAQ" if answer.add_to_faq else "")
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error answering questionnaire: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/questionnaires/{questionnaire_id}/mark-read")
async def mark_questionnaire_as_read(
    questionnaire_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark questionnaire answer as read by user"""
    try:
        if questionnaires_collection is None:
            raise HTTPException(status_code=503, detail="Database connection not available")
        
        # Validate ObjectId
        try:
            object_id = ObjectId(questionnaire_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid questionnaire ID")
        
        user_id = str(current_user.get("user_id"))
        
        result = questionnaires_collection.update_one(
            {"_id": object_id, "user_id": user_id},
            {"$set": {"is_read_by_user": True}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Questionnaire not found")
        
        return {"success": True, "message": "Marked as read"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking questionnaire as read: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/unread-answers-count")
async def get_unread_answers_count(current_user: dict = Depends(get_current_user)):
    """Get count of unread admin answers for current user"""
    try:
        if questionnaires_collection is None:
            return {"count": 0}
        
        user_id = str(current_user.get("user_id"))
        count = questionnaires_collection.count_documents({
            "user_id": user_id,
            "status": "answered",
            "is_read_by_user": False
        })
        
        return {"count": count}
    
    except Exception as e:
        logger.error(f"Error getting unread answers count: {str(e)}")
        return {"count": 0}

@router.delete("/questionnaires/{questionnaire_id}")
async def delete_questionnaire(
    questionnaire_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a questionnaire (User can delete their own, Admin can delete any)"""
    try:
        if questionnaires_collection is None:
            raise HTTPException(status_code=503, detail="Database connection not available")
        
        # Validate ObjectId
        try:
            object_id = ObjectId(questionnaire_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid questionnaire ID")
        
        # Build query based on user role
        user_id = str(current_user.get("user_id"))
        user_role = current_user.get("role")
        
        if user_role == "admin":
            # Admin can delete any questionnaire
            query = {"_id": object_id}
        else:
            # User can only delete their own questionnaires
            query = {"_id": object_id, "user_id": user_id}
        
        result = questionnaires_collection.delete_one(query)
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Questionnaire not found or access denied")
        
        logger.info(f"Questionnaire {questionnaire_id} deleted by {current_user.get('name')}")
        return {"success": True, "message": "Questionnaire deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting questionnaire: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/questionnaires/stats")
async def get_questionnaire_stats(current_user: dict = Depends(get_current_user)):
    """Get questionnaire statistics"""
    try:
        if questionnaires_collection is None:
            return {"total": 0, "pending": 0, "answered": 0}
        
        user_id = str(current_user.get("user_id"))
        user_role = current_user.get("role")
        
        if user_role == "admin":
            # Admin sees all questionnaires
            total = questionnaires_collection.count_documents({})
            pending = questionnaires_collection.count_documents({"status": "pending"})
            answered = questionnaires_collection.count_documents({"status": "answered"})
        else:
            # User sees only their questionnaires
            total = questionnaires_collection.count_documents({"user_id": user_id})
            pending = questionnaires_collection.count_documents({"user_id": user_id, "status": "pending"})
            answered = questionnaires_collection.count_documents({"user_id": user_id, "status": "answered"})
        
        return {
            "total": total,
            "pending": pending,
            "answered": answered
        }
    
    except Exception as e:
        logger.error(f"Error getting questionnaire stats: {str(e)}")
        return {"total": 0, "pending": 0, "answered": 0}


@router.get("/admin/unread-questionnaires-count")
async def get_admin_unread_questionnaires_count(current_user: dict = Depends(get_current_user)):
    """Get count of unread questionnaires for admin notifications"""
    try:
        if questionnaires_collection is None:
            return {"count": 0}
        
        user_role = current_user.get("role")
        if user_role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Count pending questionnaires (unread by admin)
        unread_count = questionnaires_collection.count_documents({"status": "pending"})
        
        return {"count": unread_count}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting admin unread questionnaires count: {str(e)}")
        return {"count": 0}

@router.put("/admin/questionnaires/mark-read")
async def mark_questionnaires_as_read(current_user: dict = Depends(get_current_user)):
    """Mark all pending questionnaires as read by admin (for notification purposes)"""
    try:
        if questionnaires_collection is None:
            raise HTTPException(status_code=503, detail="Database connection not available")
        
        user_role = current_user.get("role")
        if user_role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Note: This doesn't change the status, just marks them as "seen" by admin
        # You could add a separate "is_read_by_admin" field if needed
        # For now, we'll consider visiting the questionnaire screen as "reading"
        
        return {"success": True, "message": "Questionnaires marked as read"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking questionnaires as read: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/user/unread-answers-count")
async def get_user_unread_answers_count(current_user: dict = Depends(get_current_user)):
    """Get count of unread admin answers for user notifications"""
    try:
        if questionnaires_collection is None:
            return {"count": 0}
        
        user_id = str(current_user.get("user_id"))
        
        # Count answered questionnaires that haven't been read by the user
        unread_count = questionnaires_collection.count_documents({
            "user_id": user_id,
            "status": "answered",
            "is_read_by_user": False
        })
        
        return {"count": unread_count}
    
    except Exception as e:
        logger.error(f"Error getting user unread answers count: {str(e)}")
        return {"count": 0}
