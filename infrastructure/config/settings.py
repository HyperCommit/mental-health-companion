import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_settings():
    """Get database settings from environment variables with validation"""
    cosmos_conn = os.getenv("COSMOS_CONNECTION_STRING")
    if not cosmos_conn:
        raise ValueError("COSMOS_CONNECTION_STRING environment variable is required")
        
    cosmos_db = os.getenv("COSMOS_DATABASE_NAME")
    if not cosmos_db:
        raise ValueError("COSMOS_DATABASE_NAME environment variable is required")
    
    """Get huggingface settings from environment variables with validation"""
    
    huggingface_token = os.getenv("HUGGINGFACE_API_TOKEN")
    if not huggingface_token:
        raise ValueError("HUGGINGFACE_API_TOKEN environment variable is required")

    # Model configuration
    primary_model = os.getenv("PRIMARY_MODEL", "gpt2")  # Default to gpt2 if not specified
    sentiment_model = os.getenv("SENTIMENT_MODEL", "distilbert-base-uncased-finetuned-sst-2-english")
    
    return {
        "app_name": "Mental Health Companion",
        "version": "1.0.0",
        "cosmos_connection_string": cosmos_conn,
        "cosmos_database_name": cosmos_db,
        "primary_model": primary_model,
        "sentiment_model": sentiment_model
    }