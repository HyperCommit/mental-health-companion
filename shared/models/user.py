# filepath: shared/models/user.py
from pydantic import BaseModel, Field, EmailStr
from typing import Dict, Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    
class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    preferences: Optional[Dict] = None
    profile: Optional[Dict] = None
    subscription_tier: Optional[str] = None

class User(UserBase):
    id: str
    created_at: datetime
    subscription_tier: str = "free"
    preferences: Dict = Field(default_factory=dict)
    profile: Dict = Field(default_factory=dict)
    
    class Config:
        from_attributes = True