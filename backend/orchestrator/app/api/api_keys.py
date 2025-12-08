"""
API Key Management for External Access
Allows external applications to access the orchestrator via API keys
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel

# Database and security imports (for future implementation)
# from ..db.database import get_db_session
# from ..security.credentials import encrypt_value, decrypt_value

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/api-keys", tags=["api-keys"])


class APIKey(BaseModel):
    """API Key model"""
    id: Optional[int] = None
    name: str
    key: Optional[str] = None  # Only shown on creation
    key_prefix: str  # First 8 chars for identification
    permissions: List[str] = ["read"]  # read, write, admin
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    is_active: bool = True


class APIKeyCreate(BaseModel):
    """Create API Key request"""
    name: str
    permissions: List[str] = ["read"]
    expires_in_days: Optional[int] = 365  # Default 1 year


class APIKeyResponse(BaseModel):
    """API Key response"""
    success: bool
    message: str
    api_key: Optional[APIKey] = None


def generate_api_key() -> str:
    """Generate a secure API key"""
    return f"zos_{secrets.token_urlsafe(32)}"


def verify_api_key(api_key: str = Header(None, alias="X-API-Key")) -> dict:
    """
    Verify API key from request header
    
    Usage in endpoints:
    @router.get("/protected")
    async def protected_endpoint(auth: dict = Depends(verify_api_key)):
        # auth contains: {"key_id": 1, "permissions": ["read", "write"]}
        pass
    """
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    if not api_key.startswith("zos_"):
        raise HTTPException(status_code=401, detail="Invalid API key format")
    
    # In production, verify against database
    # For now, return mock data
    return {
        "key_id": 1,
        "permissions": ["read", "write"],
        "name": "External App"
    }


@router.post("/", response_model=APIKeyResponse)
async def create_api_key(key_data: APIKeyCreate):
    """
    Create a new API key for external access
    
    Returns the full API key only once - it cannot be retrieved again
    """
    try:
        # Generate API key
        api_key = generate_api_key()
        key_prefix = api_key[:12]  # zos_xxxxxxxx
        
        # Calculate expiration
        expires_at = None
        if key_data.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=key_data.expires_in_days)
        
        # In production: Store encrypted key in database
        # For now, return the key
        
        response_key = APIKey(
            id=1,
            name=key_data.name,
            key=api_key,  # Only shown on creation
            key_prefix=key_prefix,
            permissions=key_data.permissions,
            expires_at=expires_at,
            created_at=datetime.utcnow(),
            is_active=True
        )
        
        logger.info(f"Created API key: {key_data.name} ({key_prefix})")
        
        return APIKeyResponse(
            success=True,
            message="API key created successfully. Save it now - it won't be shown again!",
            api_key=response_key
        )
        
    except Exception as e:
        logger.error(f"Error creating API key: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[APIKey])
async def list_api_keys():
    """List all API keys (without showing the actual keys)"""
    try:
        # In production: Query from database
        # For now, return mock data
        keys = [
            APIKey(
                id=1,
                name="External App 1",
                key_prefix="zos_abc12345",
                permissions=["read", "write"],
                created_at=datetime.utcnow(),
                last_used=datetime.utcnow(),
                is_active=True
            ),
            APIKey(
                id=2,
                name="Mobile App",
                key_prefix="zos_xyz67890",
                permissions=["read"],
                created_at=datetime.utcnow(),
                is_active=True
            )
        ]
        
        return keys
        
    except Exception as e:
        logger.error(f"Error listing API keys: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{key_id}")
async def revoke_api_key(key_id: int):
    """Revoke an API key"""
    try:
        # In production: Mark as inactive in database
        logger.info(f"Revoked API key ID: {key_id}")
        
        return {
            "success": True,
            "message": f"API key {key_id} revoked successfully"
        }
        
    except Exception as e:
        logger.error(f"Error revoking API key: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{key_id}/permissions")
async def update_api_key_permissions(key_id: int, permissions: List[str]):
    """Update API key permissions"""
    try:
        valid_permissions = ["read", "write", "admin"]
        invalid = [p for p in permissions if p not in valid_permissions]
        
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid permissions: {invalid}. Valid: {valid_permissions}"
            )
        
        # In production: Update in database
        logger.info(f"Updated permissions for API key {key_id}: {permissions}")
        
        return {
            "success": True,
            "message": "Permissions updated successfully",
            "permissions": permissions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating permissions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_api_key(auth: dict = Depends(verify_api_key)):
    """
    Test endpoint to verify API key
    
    Usage:
    curl -H "X-API-Key: zos_your_key_here" http://localhost:8000/api/api-keys/test
    """
    return {
        "success": True,
        "message": "API key is valid",
        "auth_info": auth
    }
