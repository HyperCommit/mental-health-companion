from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.shared.auth import get_current_user

# Create FastAPI application
app = FastAPI(
    title="Mental Health Companion API",
    description="Backend API for the Mental Health Companion application",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers from the routers directory
from backend.api.routers import auth, journal, mood, mindfulness, insights

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(
    journal.router, 
    prefix="/api/journal", 
    tags=["Journal"], 
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    mood.router, 
    prefix="/api/mood", 
    tags=["Mood"], 
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    mindfulness.router, 
    prefix="/api/mindfulness", 
    tags=["Mindfulness"], 
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    insights.router, 
    prefix="/api/insights", 
    tags=["Insights"], 
    dependencies=[Depends(get_current_user)]
)

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}