import faiss
import json
import numpy as np
import os
from .model.embed_model import get_embedding

# Get the directory of this file to build absolute paths
current_dir = os.path.dirname(os.path.abspath(__file__))


# Global variables for index and faq_data
index = None
faq_data = None

def load_faiss_and_faq():
    global index, faq_data
    index_path = os.path.join(current_dir, "data", "faiss_index.index")
    lookup_path = os.path.join(current_dir, "data", "faq_data.json")
    index = faiss.read_index(index_path)
    with open(lookup_path, "r", encoding="utf-8") as f:
        faq_data = json.load(f)

# Initial load
load_faiss_and_faq()


def query_bot(user_question: str) -> str:
    try:
        if index is None or faq_data is None:
            load_faiss_and_faq()
        embedding = np.array([get_embedding(user_question)]).astype("float32")
        D, I = index.search(embedding, k=1)
        matched_index = I[0][0]
        distance = D[0][0]
        # Set a distance threshold for smooth fallback (tune as needed)
        DISTANCE_THRESHOLD = 1.0
        if matched_index < 0 or matched_index >= len(faq_data) or distance > DISTANCE_THRESHOLD:
            return "I'm sorry, I couldn't find a relevant answer to your question. Please try rephrasing or contact support."
        return faq_data[matched_index]["answer"]
    except Exception as e:
        print(f"Error in query_bot: {e}")
        return "I'm sorry, I couldn't find a relevant answer to your question. Please try rephrasing or contact support."

# Function to reload index and faq_data after retrain
def reload_faiss_and_faq():
    load_faiss_and_faq()
