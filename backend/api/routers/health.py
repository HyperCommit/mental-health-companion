from fastapi import APIRouter
from backend.shared.cosmos import check_database_connection

router = APIRouter()

# Health check endpoint
@router.get("/status", response_model=dict)
def health_status():
    """Check the health status of the application"""
    db_status = check_database_connection()
    return {
        "status": "healthy",
        "database": "connected" if db_status else "disconnected"
    }