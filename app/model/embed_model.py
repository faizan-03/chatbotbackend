from sentence_transformers import SentenceTransformer

# Load the MiniLM model once
model = SentenceTransformer("all-MiniLM-L6-v2")

def get_embedding(text):
    return model.encode([text])[0]

def get_embedding_model():
    """Return the SentenceTransformer model for batch processing"""
    return model
