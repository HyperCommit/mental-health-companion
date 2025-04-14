from fastapi import APIRouter, Depends
from typing import Dict
from backend.shared.auth import get_current_user
from backend.shared.kernel import KernelService

router = APIRouter()
kernel_service = KernelService()


@router.get("/exercise", response_model=str)
async def guide_exercise(
    exercise_type: str,
    current_user: str = Depends(get_current_user)
):
    """Guide a mindfulness exercise"""
    return await kernel_service.guide_exercise(exercise_type)

@router.post("/track", response_model=str)
async def track_progress(
    session_data: Dict,
    current_user: str = Depends(get_current_user)
):
    """Track mindfulness progress"""
    return await kernel_service.track_progress(session_data)

@router.get("/statistics", response_model=Dict)
async def get_statistics(
    current_user: str = Depends(get_current_user)
):
    """Get mindfulness statistics"""
    return await kernel_service.get_statistics()