from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.openapi.utils import get_openapi
from backend.shared.auth import get_current_user
from backend.shared.cosmos import check_database_connection
import asyncio
from backend.shared.cosmos import CosmosService
import uuid
import logging
from datetime import datetime
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

# Middleware to add correlation ID
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    correlation_id = str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    
    try:
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}", extra={
            "correlation_id": correlation_id,
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc()
        })
        return JSONResponse(
            status_code=500,
            content={
                "message": "An unexpected error occurred.",
                "correlation_id": correlation_id,
                "timestamp": datetime.now().isoformat()
            },
        )

# Global error handler for unexpected exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    
    logger.error(f"Unhandled exception: {str(exc)}", extra={
        "correlation_id": correlation_id,
        "path": request.url.path,
        "method": request.method,
        "traceback": traceback.format_exc()
    })
    
    return JSONResponse(
        status_code=500,
        content={
            "message": "An unexpected error occurred.",
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat()
        },
    )

# Global error handler for HTTP exceptions
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    
    # Log based on status code severity
    if exc.status_code >= 500:
        logger.error(f"Server error: {exc.detail}", extra={
            "correlation_id": correlation_id,
            "status_code": exc.status_code,
            "path": request.url.path
        })
    elif exc.status_code >= 400:
        logger.warning(f"Client error: {exc.detail}", extra={
            "correlation_id": correlation_id,
            "status_code": exc.status_code,
            "path": request.url.path
        })
    
    error_response = {
        "message": exc.detail,
        "correlation_id": correlation_id,
        "timestamp": datetime.now().isoformat()
    }
    
    # Add specific information for certain status codes
    if exc.status_code == 401:
        error_response["auth_required"] = True
    elif exc.status_code == 403:
        error_response["permission_required"] = True
    elif exc.status_code == 404:
        error_response["resource"] = request.url.path
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
        headers=exc.headers,
    )

# Global error handler for validation errors (422)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    
    # Extract field information for clearer error messages
    error_details = []
    for error in exc.errors():
        error_details.append({
            "field": error.get("loc", ["unknown"])[-1],
            "type": error.get("type"),
            "msg": error.get("msg")
        })
    
    logger.warning(f"Validation error at {request.url.path}", extra={
        "correlation_id": correlation_id,
        "validation_errors": error_details
    })
    
    return JSONResponse(
        status_code=422,
        content={
            "message": "Validation error",
            "details": error_details,
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat()
        },
    )

# Custom 403 Forbidden handler
@app.exception_handler(403)
async def forbidden_exception_handler(request: Request, exc):
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    
    logger.warning(f"Forbidden access: {request.url.path}", extra={
        "correlation_id": correlation_id,
        "path": request.url.path,
        "method": request.method
    })
    
    return JSONResponse(
        status_code=403,
        content={
            "message": "You don't have permission to access this resource",
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat()
        },
    )

# Custom 400 Bad Request handler
@app.exception_handler(400)
async def bad_request_exception_handler(request: Request, exc):
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    
    logger.warning(f"Bad request: {request.url.path}", extra={
        "correlation_id": correlation_id,
        "path": request.url.path,
        "method": request.method
    })
    
    return JSONResponse(
        status_code=400,
        content={
            "message": str(exc) if hasattr(exc, '__str__') else "Bad request",
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat()
        },
    )

# Enhanced health check endpoint
@app.get("/api/health")
async def health_check():
    db_status = check_database_connection()
    return {
        "status": "healthy",
        "database": "connected" if db_status else "disconnected",
        "timestamp": datetime.now().isoformat()
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
    
    # Define standard error responses with enhanced details
    standard_responses = {
        "400": {
            "description": "Bad Request - The request is malformed or contains invalid parameters",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"},
                            "correlation_id": {"type": "string"},
                            "timestamp": {"type": "string", "format": "date-time"}
                        }
                    },
                    "example": {
                        "message": "Invalid request parameters",
                        "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
                        "timestamp": "2025-04-18T12:34:56.789Z"
                    }
                }
            }
        },
        "401": {
            "description": "Unauthorized - Authentication is required or has failed",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"},
                            "correlation_id": {"type": "string"},
                            "timestamp": {"type": "string", "format": "date-time"},
                            "auth_required": {"type": "boolean"}
                        }
                    },
                    "example": {
                        "message": "Not authenticated",
                        "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
                        "timestamp": "2025-04-18T12:34:56.789Z",
                        "auth_required": True
                    }
                }
            }
        },
        "403": {
            "description": "Forbidden - You don't have permission to access this resource",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"},
                            "correlation_id": {"type": "string"},
                            "timestamp": {"type": "string", "format": "date-time"},
                            "permission_required": {"type": "boolean"}
                        }
                    },
                    "example": {
                        "message": "You don't have permission to access this resource",
                        "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
                        "timestamp": "2025-04-18T12:34:56.789Z",
                        "permission_required": True
                    }
                }
            }
        },
        "404": {
            "description": "Not Found - The requested resource does not exist",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"},
                            "correlation_id": {"type": "string"},
                            "timestamp": {"type": "string", "format": "date-time"},
                            "resource": {"type": "string"}
                        }
                    },
                    "example": {
                        "message": "Resource not found",
                        "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
                        "timestamp": "2025-04-18T12:34:56.789Z",
                        "resource": "/api/journal/12345"
                    }
                }
            }
        },
        "422": {
            "description": "Unprocessable Entity - Validation error",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"},
                            "details": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "field": {"type": "string"},
                                        "type": {"type": "string"},
                                        "msg": {"type": "string"}
                                    }
                                }
                            },
                            "correlation_id": {"type": "string"},
                            "timestamp": {"type": "string", "format": "date-time"}
                        }
                    },
                    "example": {
                        "message": "Validation error",
                        "details": [
                            {
                                "field": "email",
                                "type": "value_error.email",
                                "msg": "value is not a valid email address"
                            }
                        ],
                        "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
                        "timestamp": "2025-04-18T12:34:56.789Z"
                    }
                }
            }
        },
        "500": {
            "description": "Internal Server Error - An unexpected error occurred",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"},
                            "correlation_id": {"type": "string"},
                            "timestamp": {"type": "string", "format": "date-time"}
                        }
                    },
                    "example": {
                        "message": "An unexpected error occurred.",
                        "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
                        "timestamp": "2025-04-18T12:34:56.789Z"
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
            if path == "/api/health" and method.lower() == "get":
                continue
                
            # Add relevant responses
            openapi_schema["paths"][path][method]["responses"].update({
                "400": standard_responses["400"],
                "401": standard_responses["401"],
                "403": standard_responses["403"],
                "500": standard_responses["500"]
            })
            
            # Add 422 to endpoints that accept request bodies
            if method.lower() in ("post", "put", "patch"):
                openapi_schema["paths"][path][method]["responses"]["422"] = standard_responses["422"]
            
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