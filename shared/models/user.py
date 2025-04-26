# filepath: shared/models/user.py
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Dict, Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    
class UserCreate(UserBase):
    password: str  # Add password field for registration
    password_confirm: str | None = None  # Optional confirmation field
    
    # Add validation to ensure password meets security requirements
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v
    
    # Add validation for password confirmation
    @validator('password_confirm')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    preferences: Optional[Dict] = None
    profile: Optional[Dict] = None
    subscription_tier: Optional[str] = None

class User(UserBase):
    id: str
    created_at: datetime
    hashed_password: str  # Add field for storing hashed password
    subscription_tier: str = "free"
    preferences: Dict = Field(default_factory=dict)
    profile: Dict = Field(default_factory=dict)
    
    class Config:
        from_attributes = True
        # Exclude sensitive fields when converting to dict/json
        json_exclude = {"hashed_password"}