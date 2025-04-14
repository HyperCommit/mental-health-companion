from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Placeholder for authentication-related functions
def verify_firebase_token(token):
    # Mock implementation
    return "mock_user_id"

def get_current_user(token: str = Depends(oauth2_scheme)):
    user_id = verify_firebase_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return {"user_id": user_id}