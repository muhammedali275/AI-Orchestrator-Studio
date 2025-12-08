"""
Credentials API - REST endpoints for credential management.

Provides CRUD operations for credentials via REST API.

Security Rules:
- NEVER return secrets in API responses
- NEVER log secrets
- All secrets are encrypted before storage
- Only metadata is returned to clients
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..services.credentials_service import (
    CredentialsService,
    CredentialNotFoundError,
    CredentialValidationError
)
from ..security.credentials import CredentialEncryptionError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/credentials", tags=["credentials"])


# Request/Response Models

class CredentialCreateRequest(BaseModel):
    """Request model for creating a credential."""
    name: str = Field(..., description="Human-readable credential name", min_length=1, max_length=255)
    type: str = Field(..., description="Credential type (ssh, http_basic, bearer_token, db_dsn, api_key, custom)")
    username: Optional[str] = Field(None, description="Username (optional, depends on type)", max_length=255)
    secret: str = Field(..., description="Secret value (will be encrypted)", min_length=1)
    extra: Optional[Dict[str, Any]] = Field(None, description="Additional metadata (must not contain secrets)")


class CredentialUpdateRequest(BaseModel):
    """Request model for updating a credential."""
    name: Optional[str] = Field(None, description="New credential name", min_length=1, max_length=255)
    username: Optional[str] = Field(None, description="New username", max_length=255)
    secret: Optional[str] = Field(None, description="New secret (will be encrypted)", min_length=1)
    extra: Optional[Dict[str, Any]] = Field(None, description="New metadata")
    is_active: Optional[bool] = Field(None, description="Active status")


class CredentialResponse(BaseModel):
    """Response model for credential (without secret)."""
    id: str
    name: str
    type: str
    username: Optional[str]
    extra: Dict[str, Any]
    created_at: str
    updated_at: str
    is_active: bool


class CredentialListResponse(BaseModel):
    """Response model for credential list."""
    credentials: List[CredentialResponse]
    total: int


# API Endpoints

@router.post("", response_model=CredentialResponse, status_code=status.HTTP_201_CREATED)
async def create_credential(
    request: CredentialCreateRequest,
    db: Session = Depends(get_db)
) -> CredentialResponse:
    """
    Create a new credential.
    
    The secret will be encrypted before storage and will never be returned in responses.
    
    Args:
        request: Credential creation request
        db: Database session
        
    Returns:
        Created credential metadata (without secret)
        
    Raises:
        400: Validation error
        500: Encryption or database error
        
    Security:
        - Secret is encrypted before storage
        - Secret is NEVER returned in response
        - Only metadata is returned
    """
    try:
        service = CredentialsService(db)
        
        credential = service.create_credential(
            name=request.name,
            cred_type=request.type,
            secret=request.secret,
            username=request.username,
            extra=request.extra
        )
        
        logger.info(f"[API] Created credential: {request.name}")
        
        return CredentialResponse(**credential)
        
    except CredentialValidationError as e:
        logger.warning(f"[API] Validation error creating credential: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except CredentialEncryptionError as e:
        logger.error(f"[API] Encryption error creating credential: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to encrypt credential. Check server configuration."
        )
    except Exception as e:
        logger.error(f"[API] Error creating credential: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("", response_model=CredentialListResponse)
async def list_credentials(
    type: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
) -> CredentialListResponse:
    """
    List all credentials.
    
    Args:
        type: Optional filter by credential type
        active_only: If True, return only active credentials
        db: Database session
        
    Returns:
        List of credential metadata (without secrets)
        
    Security:
        - Secrets are NEVER returned
        - Only metadata is returned
    """
    try:
        service = CredentialsService(db)
        
        credentials = service.list_credentials(
            cred_type=type,
            active_only=active_only
        )
        
        return CredentialListResponse(
            credentials=[CredentialResponse(**cred) for cred in credentials],
            total=len(credentials)
        )
        
    except Exception as e:
        logger.error(f"[API] Error listing credentials: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{credential_id}", response_model=CredentialResponse)
async def get_credential(
    credential_id: str,
    db: Session = Depends(get_db)
) -> CredentialResponse:
    """
    Get credential by ID.
    
    Args:
        credential_id: Credential ID
        db: Database session
        
    Returns:
        Credential metadata (without secret)
        
    Raises:
        404: Credential not found
        
    Security:
        - Secret is NEVER returned
        - Only metadata is returned
    """
    try:
        service = CredentialsService(db)
        
        credential = service.get_credential(credential_id)
        
        return CredentialResponse(**credential)
        
    except CredentialNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"[API] Error getting credential: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/{credential_id}", response_model=CredentialResponse)
async def update_credential(
    credential_id: str,
    request: CredentialUpdateRequest,
    db: Session = Depends(get_db)
) -> CredentialResponse:
    """
    Update credential.
    
    Can be used to rotate secrets or update metadata.
    
    Args:
        credential_id: Credential ID
        request: Update request
        db: Database session
        
    Returns:
        Updated credential metadata (without secret)
        
    Raises:
        400: Validation error
        404: Credential not found
        500: Encryption or database error
        
    Security:
        - If secret is provided, it's encrypted before storage
        - Secret is NEVER returned in response
        - Only metadata is returned
    """
    try:
        service = CredentialsService(db)
        
        credential = service.update_credential(
            credential_id=credential_id,
            name=request.name,
            secret=request.secret,
            username=request.username,
            extra=request.extra,
            is_active=request.is_active
        )
        
        logger.info(f"[API] Updated credential: {credential_id}")
        
        return CredentialResponse(**credential)
        
    except CredentialNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except CredentialValidationError as e:
        logger.warning(f"[API] Validation error updating credential: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except CredentialEncryptionError as e:
        logger.error(f"[API] Encryption error updating credential: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to encrypt credential. Check server configuration."
        )
    except Exception as e:
        logger.error(f"[API] Error updating credential: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(
    credential_id: str,
    db: Session = Depends(get_db)
) -> None:
    """
    Delete (deactivate) credential.
    
    This performs a soft delete by setting is_active=False.
    
    Args:
        credential_id: Credential ID
        db: Database session
        
    Raises:
        404: Credential not found
    """
    try:
        service = CredentialsService(db)
        
        service.delete_credential(credential_id)
        
        logger.info(f"[API] Deleted credential: {credential_id}")
        
    except CredentialNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"[API] Error deleting credential: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/{credential_id}/test", response_model=Dict[str, Any])
async def test_credential(
    credential_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Test credential connectivity.
    
    This endpoint validates that the credential exists and is active.
    Actual connectivity testing is done by the monitoring service.
    
    Args:
        credential_id: Credential ID
        db: Database session
        
    Returns:
        Test result
        
    Raises:
        404: Credential not found
    """
    try:
        service = CredentialsService(db)
        
        credential = service.get_credential(credential_id)
        
        if not credential["is_active"]:
            return {
                "success": False,
                "message": "Credential is inactive",
                "credential_id": credential_id
            }
        
        return {
            "success": True,
            "message": "Credential is valid and active",
            "credential_id": credential_id,
            "credential_name": credential["name"],
            "credential_type": credential["type"]
        }
        
    except CredentialNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"[API] Error testing credential: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
