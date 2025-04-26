import os
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt
from opencensus.ext.azure.log_exporter import AzureLogHandler

from shared.models.user import User
from backend.shared.cosmos import CosmosService

# Configure logging with Azure Application Insights
logger = logging.getLogger(__name__)
if os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING"):
    logger.addHandler(AzureLogHandler())

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize Cosmos DB service
cosmos_service = CosmosService()

# Load JWT configuration from environment variables with fallbacks
SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
if not SECRET_KEY:
    logger.warning("JWT_SECRET_KEY not found in environment variables. Using insecure default for development.")
    SECRET_KEY = "insecure-dev-only-key"  # Development fallback
    
ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRATION_MINUTES", 30))


def get_password_hash(password: str) -> str:
    """
    Hash a password securely using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Securely hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


async def authenticate_user(username: str, password: str) -> Optional[User]:
    """
    Authenticate user by verifying credentials.
    
    Args:
        username: User's email address
        password: User's password
        
    Returns:
        User object if authentication succeeds, None otherwise
    """
    try:
        user = await cosmos_service.get_user_by_email(username)
        if not user:
            logger.info(f"Authentication failed: User {username} not found")
            return None
        if not verify_password(password, user.hashed_password):
            logger.info(f"Authentication failed: Invalid password for user {username}")
            return None
        return user
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}", exc_info=True)
        return None


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Generate a JWT access token.
    
    Args:
        data: Payload to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Validate JWT token and return the current user.
    
    Args:
        token: JWT token from authorization header
        
    Returns:
        Authenticated user object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Token validation failed: Missing subject claim")
            raise credentials_exception
        
        # Fetch user from database
        user = await cosmos_service.get_user_by_email(username)
        if user is None:
            logger.warning(f"Token validation failed: User {username} not found")
            raise credentials_exception
            
        return user
    except JWTError as e:
        logger.warning(f"Token validation failed: {str(e)}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}", exc_info=True)
        raise credentials_exception