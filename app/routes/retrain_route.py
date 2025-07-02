from fastapi import APIRouter, HTTPException
from ..utils.db import faq_collection
from ..model.embed_model import get_embedding_model
import faiss
import json
import os
import logging
from datetime import datetime

router = APIRouter()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .. import chatbot

@router.post("/retrain")
def retrain_index():
    try:
        logger.info("Starting FAISS index retraining...")
        
        # Check if database connection is available
        if faq_collection is None:
            raise HTTPException(status_code=503, detail="Database connection not available")
        
        # Fetch FAQs from database
        faqs = list(faq_collection.find())
        if not faqs:
            logger.warning("No FAQs found in database")
            return {"status": "No data to retrain", "count": 0}
        
        texts = [f["question"] for f in faqs]
        answers = [f["answer"] for f in faqs]
        logger.info(f"Found {len(texts)} FAQs to process")

        # Generate embeddings
        model = get_embedding_model()
        logger.info("Generating embeddings...")
        vectors = model.encode(texts).astype("float32")
        logger.info(f"Generated vectors shape: {vectors.shape}")

        # Create and save FAISS index
        index = faiss.IndexFlatL2(vectors.shape[1])
        index.add(vectors)
        
        index_path = "app/data/faiss_index.index"
        faiss.write_index(index, index_path)
        logger.info(f"FAISS index saved to {index_path}")

        # Save lookup data in the new format for backwards compatibility
        lookup_data = {
            "questions": texts, 
            "answers": answers,
            "last_updated": datetime.now().isoformat(),
            "total_faqs": len(texts)
        }
        
        lookup_path = "app/data/faq_lookup.json"
        with open(lookup_path, "w", encoding="utf-8") as f:
            json.dump(lookup_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Lookup data saved to {lookup_path}")

        # Also save data in the format expected by the chatbot
        faq_data = []
        for i in range(len(texts)):
            faq_data.append({
                "question": texts[i],
                "answer": answers[i]
            })
        
        faq_data_path = "app/data/faq_data.json"
        with open(faq_data_path, "w", encoding="utf-8") as f:
            json.dump(faq_data, f, indent=2, ensure_ascii=False)
        logger.info(f"FAQ data saved to {faq_data_path}")

        # Verify files were created
        index_exists = os.path.exists(index_path)
        lookup_exists = os.path.exists(lookup_path)
        faq_data_exists = os.path.exists(faq_data_path)
        
        logger.info("Retraining completed successfully!")
        # Reload FAISS index and FAQ data in memory
        chatbot.reload_faiss_and_faq()
        logger.info("In-memory FAISS index and FAQ data reloaded.")
        return {
            "status": "success",
            "message": "Index retrained successfully and in-memory data reloaded",
            "count": len(texts),
            "files_created": {
                "index": index_exists,
                "lookup": lookup_exists,
                "faq_data": faq_data_exists
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error during retraining: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Retraining failed: {str(e)}")

@router.get("/retrain/status")
def get_retrain_status():
    """Get the current status of the training data"""
    try:
        index_path = "app/data/faiss_index.index"
        lookup_path = "app/data/faq_lookup.json"
        
        status = {
            "index_exists": os.path.exists(index_path),
            "lookup_exists": os.path.exists(lookup_path),
        }
        
        if os.path.exists(lookup_path):
            with open(lookup_path, "r", encoding="utf-8") as f:
                lookup_data = json.load(f)
                status.update({
                    "total_faqs": lookup_data.get("total_faqs", 0),
                    "last_updated": lookup_data.get("last_updated", "unknown")
                })
        
        if os.path.exists(index_path):
            # Get file modification time
            mod_time = os.path.getmtime(index_path)
            status["index_last_modified"] = datetime.fromtimestamp(mod_time).isoformat()
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting retrain status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")
