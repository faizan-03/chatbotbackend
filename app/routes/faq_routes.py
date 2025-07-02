from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from ..utils.db import faq_collection
from ..model.faq_model import FAQ
from .auth_routes import get_current_user
from datetime import datetime
import json
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

def serialize_faq(faq):
    faq["_id"] = str(faq["_id"])
    return faq

@router.get("/faqs")
def get_faqs():
    if faq_collection is None:
        raise HTTPException(status_code=503, detail="Database connection not available")
    faqs = list(faq_collection.find())
    return [serialize_faq(f) for f in faqs]

@router.post("/faqs", status_code=201)
def add_faq(faq: FAQ, current_user: dict = Depends(get_current_user)):
    # Verify admin role
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
        
    if faq_collection is None:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    # Add metadata to FAQ
    faq_doc = faq.dict()
    faq_doc.update({
        "created_by": current_user.get("name", "admin"),
        "created_at": datetime.now(),
        "source": "manual_add"
    })
    
    result = faq_collection.insert_one(faq_doc)
    logger.info(f"FAQ added by {current_user.get('name')}: {faq.question[:50]}...")
    return {"id": str(result.inserted_id)}

@router.delete("/faqs/{id}", status_code=204)
def delete_faq(id: str, current_user: dict = Depends(get_current_user)):
    # Verify admin role
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
        
    if faq_collection is None:
        raise HTTPException(status_code=503, detail="Database connection not available")
    result = faq_collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="FAQ not found")
    
    logger.info(f"FAQ deleted by {current_user.get('name')}: {id}")
