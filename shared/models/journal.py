# filepath: shared/models/journal.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import uuid

class JournalEntryBase(BaseModel):
    content: str = Field(..., min_length=1)
    mood_indicators: List[str] = Field(default_factory=list)
    mood_score: Optional[int] = Field(None, ge=1, le=10)

class JournalEntryCreate(JournalEntryBase):
    pass

class JournalEntryUpdate(JournalEntryBase):
    content: Optional[str] = None
    mood_indicators: Optional[List[str]] = None
    mood_score: Optional[int] = None

class JournalEntryInDB(JournalEntryBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    ai_insights: Optional[Dict] = None
    sentiment_score: Optional[float] = None
    
    class Config:
        from_attributes = True

class JournalEntry(JournalEntryInDB):
    pass