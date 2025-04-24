import uvicorn
import os
from dotenv import load_dotenv
from daystrigger import app

# Load environment variables
load_dotenv()

def main():
    print("Starting Resume Atlas API...")
    
    # Get port from environment variable (Render sets this automatically)
    port = int(os.getenv("PORT", 8000))
    
    # Check if we're in development or production
    is_development = os.getenv("ENVIRONMENT", "production").lower() == "development"
    
    print(f"API documentation will be available at port {port}")
    
    # Start the API server
    uvicorn.run(
        "api:app", 
        host="0.0.0.0", 
        port=port, 
        reload=is_development,  # Only enable reload in development
        log_level="info"
    )

if __name__ == "__main__":
    main()