import uvicorn
import os
from app.config import settings

if __name__ == "__main__":
    # Use PORT environment variable for Railway, fallback to settings
    port = int(os.getenv("PORT", settings.api_port))
    uvicorn.run(
        "app.main:app",  # Import string instead of app object for reload
        host="0.0.0.0",  # Railway requires 0.0.0.0
        port=port, 
        reload=settings.debug
    )
