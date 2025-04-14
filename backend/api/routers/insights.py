from fastapi import APIRouter, Depends
from backend.shared.kernel import KernelService
from backend.shared.auth import get_current_user

router = APIRouter()
kernel_service = KernelService()

@router.get("/weekly", response_model=dict)
async def get_weekly_insights(current_user: str = Depends(get_current_user)):
    """Retrieve weekly insights for the current user"""
    weekly_insights = await kernel_service.get_weekly_insights(current_user.id)
    return weekly_insights

@router.get("/patterns", response_model=dict)
async def get_emotional_patterns(current_user: str = Depends(get_current_user)):
    """Retrieve emotional patterns for the current user"""
    return await kernel_service.get_emotional_patterns(current_user.id)