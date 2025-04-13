# filepath: shared/models/mood.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

class MoodLogBase(BaseModel):
    mood_score: int = Field(..., ge=1, le=10)
    mood_labels: List[str] = Field(default_factory=list)
    context: Optional[str] = None
    factors: Optional[List[str]] = None

class MoodLogCreate(MoodLogBase):
    pass

class MoodLogInDB(MoodLogBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    location: Optional[str] = None
    
    class Config:
        from_attributes = True

class MoodLog(MoodLogInDB):
    pass