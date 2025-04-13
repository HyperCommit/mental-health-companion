import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_settings():
    """Get application settings from environment variables with validation"""
    cosmos_conn = os.getenv("COSMOS_CONNECTION_STRING")
    if not cosmos_conn:
        raise ValueError("COSMOS_CONNECTION_STRING environment variable is required")
        
    cosmos_db = os.getenv("COSMOS_DATABASE_NAME")
    if not cosmos_db:
        raise ValueError("COSMOS_DATABASE_NAME environment variable is required")
    
    return {
        "app_name": "Mental Health Companion",
        "version": "1.0.0",
        "cosmos_connection_string": cosmos_conn,
        "cosmos_database_name": cosmos_db,
    }