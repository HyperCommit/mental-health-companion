from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from backend.shared.auth import get_current_user
from backend.shared.cosmos import check_database_connection
import asyncio
from backend.shared.cosmos import CosmosService

# Enhanced documentation
app = FastAPI(
    title="Mental Health Companion API",
    description="Backend API for the Mental Health Companion application.\n\nThis API provides endpoints for authentication, journaling, mood tracking, mindfulness exercises, and insights.",
    version="1.0.0",
    openapi_tags=[
        {"name": "Authentication", "description": "Endpoints related to user authentication."},
        {"name": "Journal", "description": "Endpoints for journaling activities."},
        {"name": "Mood", "description": "Endpoints for mood tracking."},
        {"name": "Mindfulness", "description": "Endpoints for mindfulness exercises."},
        {"name": "Insights", "description": "Endpoints for generating insights."}
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global error handler for unexpected exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred."},
    )

# Global error handler for HTTP exceptions
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )

# Global error handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"message": "Validation error", "details": exc.errors()},
    )

# Enhanced health check endpoint
@app.get("/api/health")
async def health_check():
    db_status = check_database_connection()
    return {
        "status": "healthy",
        "database": "connected" if db_status else "disconnected"
    }

# Reusable dependency for authenticated routes
authenticated_dependency = [Depends(get_current_user)]

# Updated router imports and usage
from backend.api.routers import auth, journal, mood, mindfulness, insights

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(
    journal.router, 
    prefix="/api/journal", 
    tags=["Journal"], 
    dependencies=authenticated_dependency
)
app.include_router(
    mood.router, 
    prefix="/api/mood", 
    tags=["Mood"], 
    dependencies=authenticated_dependency
)
app.include_router(
    mindfulness.router, 
    prefix="/api/mindfulness", 
    tags=["Mindfulness"], 
    dependencies=authenticated_dependency
)
app.include_router(
    insights.router, 
    prefix="/api/insights", 
    tags=["Insights"], 
    dependencies=authenticated_dependency
)

def main():
    async def run():
        cosmos_service = CosmosService()
        user = await cosmos_service.get_user("sample_user_id")
        print(user)

    asyncio.run(run())

if __name__ == "__main__":
    main()