from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from shared.models.user import User, UserCreate, UserUpdate
from backend.shared.auth import get_current_user, authenticate_user, create_access_token, get_password_hash
from backend.shared.cosmos import CosmosService
import uuid

router = APIRouter()
cosmos_service = CosmosService()

ACCESS_TOKEN_EXPIRE_MINUTES = 30

@router.get("/login", response_model=User)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Retrieve the current user's profile"""
    return current_user

@router.post("/register", response_model=User)
async def register_user(user_data: UserCreate):
    """
    Register a new user with secure password hashing.
    
    Args:
        user_data: User registration data including email and password
        
    Returns:
        Newly created user object
        
    Raises:
        HTTPException: If email is already registered or other creation errors
    """
    # Check if user already exists
    existing_user = await cosmos_service.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Generate a unique ID for the user
    user_id = str(uuid.uuid4())
    
    # Hash the password securely
    hashed_password = get_password_hash(user_data.password)
    
    # Create user with email and hashed password
    return await cosmos_service.create_user(
        id=user_id,
        email=user_data.email,
        hashed_password=hashed_password
    )

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

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return a JWT token"""
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}