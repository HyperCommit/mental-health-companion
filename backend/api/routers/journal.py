from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from shared.models.journal import JournalEntry, JournalEntryCreate, JournalEntryUpdate
from shared.models.user import User
from backend.shared.auth import get_current_user
from backend.shared.cosmos import CosmosService
from backend.shared.kernel import KernelService

router = APIRouter()
cosmos_service = CosmosService()
kernel_service = KernelService()

@router.get("/", response_model=List[JournalEntry])
async def get_journal_entries(
    skip: int = 0, 
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Get all journal entries for the current user"""
    return await cosmos_service.get_journal_entries(current_user.id, skip, limit)

@router.post("/", response_model=JournalEntry)
async def create_journal_entry(
    entry: JournalEntryCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new journal entry"""
    insights = await kernel_service.analyze_journal_entry(entry.content)
    return await cosmos_service.create_journal_entry(
        user_id=current_user.id,
        content=entry.content,
        mood_indicators=entry.mood_indicators,
        mood_score=entry.mood_score,
        ai_insights=insights
    )

@router.get("/{entry_id}", response_model=JournalEntry)
async def get_journal_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific journal entry"""
    entry = await cosmos_service.get_journal_entry(entry_id)
    if not entry or entry.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return entry

@router.put("/{entry_id}", response_model=JournalEntry)
async def update_journal_entry(
    entry_id: str,
    entry_update: JournalEntryUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a journal entry"""
    existing_entry = await cosmos_service.get_journal_entry(entry_id)
    if not existing_entry or existing_entry.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    updated_entry = await cosmos_service.update_journal_entry(
        entry_id=entry_id,
        user_id=current_user.id,
        update_data=entry_update.dict(exclude_unset=True)
    )
    return updated_entry

@router.delete("/{entry_id}")
async def delete_journal_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a journal entry"""
    existing_entry = await cosmos_service.get_journal_entry(entry_id)
    if not existing_entry or existing_entry.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    await cosmos_service.delete_journal_entry(entry_id, current_user.id)
    return {"message": "Entry deleted successfully"}

@router.post("/prompt", response_model=dict)
async def generate_journal_prompt(
    mood: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Generate a journaling prompt based on mood"""
    prompt = await kernel_service.generate_journal_prompt(mood)
    return {"prompt": prompt}