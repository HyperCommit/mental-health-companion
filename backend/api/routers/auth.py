from fastapi import APIRouter, Depends, HTTPException
from shared.models.user import User, UserCreate, UserUpdate
from backend.shared.auth import get_current_user
from backend.shared.cosmos import CosmosService

router = APIRouter()
cosmos_service = CosmosService()


@router.get("/me", response_model=User)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Retrieve the current user's profile"""
    return current_user

@router.post("/register", response_model=User)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    return await cosmos_service.create_user(id=user_data.id, email=user_data.email)

@router.put("/update", response_model=User)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update the current user's profile"""
    updated_user = await cosmos_service.update_user(current_user.id, user_update.dict(exclude_unset=True))
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user