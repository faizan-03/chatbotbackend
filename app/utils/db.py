from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from ..config import settings

try:
    # Create MongoDB client with timeout using settings
    client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
    
    # Test the connection
    client.admin.command('ping')
    print("✅ MongoDB connection successful!")
    
    # Set up database and collections using settings
    db = client[settings.db_name]
    faq_collection = db[settings.faqs_collection]
    users_collection = db[settings.users_collection]
    
except (ConnectionFailure, ServerSelectionTimeoutError) as e:
    print(f"❌ MongoDB connection failed: {e}")
    print("🔧 Falling back to file-based storage...")
    client = None
    db = None
    faq_collection = None
    users_collection = None
    
except Exception as e:
    print(f"❌ Unexpected error connecting to MongoDB: {e}")
    client = None
    db = None
    faq_collection = None
    users_collection = None
