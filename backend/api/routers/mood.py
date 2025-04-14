from fastapi import APIRouter, Depends
from typing import List
from shared.models.mood import MoodLog, MoodLogCreate
from backend.shared.auth import get_current_user
from backend.shared.kernel import KernelService

router = APIRouter()
kernel_service = KernelService()

@router.post("/analyze", response_model=dict)
async def analyze_mood(
    input_text: str,
    current_user: str = Depends(get_current_user)
):
    """Analyze mood from text"""
    mood_analysis = await kernel_service.analyze_mood(input_text)
    return mood_analysis

@router.post("/log", response_model=MoodLog)
async def log_mood(
    mood_data: MoodLogCreate,
    current_user: str = Depends(get_current_user)
):
    """Log a mood entry"""
    return await kernel_service.log_mood(mood_data, current_user.id)

@router.get("/patterns", response_model=str)
async def detect_patterns(
    journal_entries: List[str],
    current_user: str = Depends(get_current_user)
):
    """Detect emotional patterns from journal entries"""
    return await kernel_service.detect_patterns(journal_entries)