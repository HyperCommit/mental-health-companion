from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from shared.models.user import User
from backend.shared.cosmos import CosmosService
from jose import JWTError, jwt
from datetime import datetime, timedelta

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
cosmos_service = CosmosService()

SECRET_KEY = "your_secret_key_here"  # Replace with a secure key
ALGORITHM = "HS256"

# Placeholder for authentication-related functions
def verify_firebase_token(token):
    # Mock implementation
    return "mock_user_id"

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

async def authenticate_user(username: str, password: str):
    """Authenticate user by verifying credentials"""
    user = await cosmos_service.get_user_by_email(username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

def get_current_user(token: str = Depends(oauth2_scheme)):
    user_id = verify_firebase_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return {"user_id": user_id}

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Generate a JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt