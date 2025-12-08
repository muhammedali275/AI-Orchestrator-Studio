"""
Security utilities for AIpanel.

Implements API key and JWT authentication for securing endpoints.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Union, List

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from .config import get_settings

settings = get_settings()

# API Key security scheme
api_key_header = APIKeyHeader(name=settings.API_KEY_HEADER, auto_error=False)

# OAuth2 security scheme for JWT
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)


class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str
    expires_at: int


class TokenData(BaseModel):
    """Token data model."""
    sub: Optional[str] = None
    scopes: List[str] = []
    exp: Optional[int] = None


class User(BaseModel):
    """User model."""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    scopes: List[str] = []


def create_access_token(
    data: Dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Data to encode in token
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


async def get_current_user_from_token(token: str = Depends(oauth2_scheme)) -> Optional[User]:
    """
    Validate JWT token and return user.
    
    Args:
        token: JWT token
        
    Returns:
        User if token is valid
        
    Raises:
        HTTPException: If token is invalid
    """
    if not token:
        return None
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            return None
        
        token_scopes = payload.get("scopes", [])
        token_exp = payload.get("exp")
        
        token_data = TokenData(
            sub=username,
            scopes=token_scopes,
            exp=token_exp
        )
    except JWTError:
        return None
    
    # In a real application, you would fetch the user from a database
    # For now, we'll create a mock user
    user = User(
        username=token_data.sub,
        email=f"{token_data.sub}@example.com",
        full_name=token_data.sub.title(),
        disabled=False,
        scopes=token_data.scopes
    )
    
    return user


async def get_api_key(api_key: str = Security(api_key_header)) -> Optional[str]:
    """
    Validate API key.
    
    Args:
        api_key: API key from header
        
    Returns:
        API key if valid
        
    Raises:
        HTTPException: If API key is invalid
    """
    if not api_key:
        return None
    
    # In a real application, you would validate the API key against a database
    # For now, we'll use a simple check
    valid_api_keys = ["test-api-key"]  # Replace with DB lookup
    
    if api_key not in valid_api_keys:
        return None
    
    return api_key


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    api_key: str = Security(api_key_header)
) -> User:
    """
    Get current user from JWT token or API key.
    
    Args:
        token: JWT token
        api_key: API key
        
    Returns:
        User if authentication is valid
        
    Raises:
        HTTPException: If authentication is invalid
    """
    # Try JWT token first
    if token:
        user = await get_current_user_from_token(token)
        if user:
            return user
    
    # Try API key
    if api_key:
        valid_api_key = await get_api_key(api_key)
        if valid_api_key:
            # Create a user from API key
            return User(
                username="api_user",
                email="api@example.com",
                full_name="API User",
                disabled=False,
                scopes=["api"]
            )
    
    # No valid authentication
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def verify_scope(required_scopes: List[str]):
    """
    Verify user has required scopes.
    
    Args:
        required_scopes: List of required scopes
        
    Returns:
        Dependency function
    """
    async def verify_user_scope(user: User = Depends(get_current_user)):
        for scope in required_scopes:
            if scope not in user.scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: missing scope '{scope}'",
                )
        return user
    
    return verify_user_scope
