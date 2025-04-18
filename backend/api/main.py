from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.openapi.utils import get_openapi
from backend.shared.auth import get_current_user
from backend.shared.cosmos import check_database_connection
import asyncio
from backend.shared.cosmos import CosmosService

# Enhanced documentation
app = FastAPI(
    title="Mental Health Companion API",
    description="API for mental health tracking and mindfulness exercises",
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

app.include_router(auth.router, prefix="/api/auth/user", tags=["Authentication"])
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

# Custom OpenAPI schema generation
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    # Define standard error responses
    standard_responses = {
        "400": {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {"type": "string"}
                        }
                    }
                }
            }
        },
        "401": {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {"type": "string"}
                        }
                    }
                }
            }
        },
        "404": {
            "description": "Not Found",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {"type": "string"}
                        }
                    }
                }
            }
        },
        "500": {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {"type": "string"}
                        }
                    }
                }
            }
        }
    }
    
    # Apply standard responses to each path
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if method.lower() not in ("get", "post", "put", "delete", "patch"):
                continue
            
            # Skip adding error responses to the health check endpoint
            if path == "/health/status" and method.lower() == "get":
                continue
                
            # Add relevant responses
            openapi_schema["paths"][path][method]["responses"].update({
                "400": standard_responses["400"],
                "401": standard_responses["401"],
                "500": standard_responses["500"]
            })
            
            # Add 404 to certain methods (get by ID, update, delete)
            if any(pattern in path for pattern in ["/{", "/user/"]) and method.lower() in ("get", "put", "delete"):
                openapi_schema["paths"][path][method]["responses"]["404"] = standard_responses["404"]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

def main():
    async def run():
        cosmos_service = CosmosService()
        user = await cosmos_service.get_user("sample_user_id")
        print(user)

    asyncio.run(run())

if __name__ == "__main__":
    main()