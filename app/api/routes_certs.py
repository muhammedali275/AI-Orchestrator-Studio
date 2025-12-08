"""
Certificate management API routes for AIpanel.

Implements endpoints for managing TLS certificates.
"""

import logging
import os
import shutil
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..config import get_settings, Settings
from ..db.session import get_db
from ..security import get_current_user, User, verify_scope

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/certs", tags=["certificates"])


class CertificateInfo(BaseModel):
    """Certificate information model."""
    tls_enabled: bool = Field(..., description="TLS enabled status")
    cert_path: Optional[str] = Field(None, description="Certificate path")
    key_path: Optional[str] = Field(None, description="Key path")
    cert_exists: bool = Field(False, description="Certificate exists")
    key_exists: bool = Field(False, description="Key exists")


@router.get("", response_model=CertificateInfo)
async def get_certificate_info(
    user: User = Depends(verify_scope(["admin"])),
    db: Session = Depends(get_db)
) -> CertificateInfo:
    """
    Get certificate information.
    
    Args:
        user: Authenticated user with admin scope
        db: Database session
        
    Returns:
        Certificate information
    """
    logger.info("[API:Certs] Get certificate info")
    
    try:
        # Get certificate info
        cert_path = settings.TLS_CERT_PATH
        key_path = settings.TLS_KEY_PATH
        
        # Check if files exist
        cert_exists = cert_path and os.path.isfile(cert_path)
        key_exists = key_path and os.path.isfile(key_path)
        
        return CertificateInfo(
            tls_enabled=settings.TLS_ENABLED,
            cert_path=cert_path,
            key_path=key_path,
            cert_exists=cert_exists,
            key_exists=key_exists
        )
        
    except Exception as e:
        logger.error(f"[API:Certs] Error getting certificate info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting certificate info: {str(e)}"
        )


@router.post("/upload", response_model=Dict[str, Any])
async def upload_certificates(
    cert_file: UploadFile = File(...),
    key_file: UploadFile = File(...),
    user: User = Depends(verify_scope(["admin"])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upload TLS certificates.
    
    Args:
        cert_file: Certificate file
        key_file: Key file
        user: Authenticated user with admin scope
        db: Database session
        
    Returns:
        Success status
    """
    logger.info("[API:Certs] Upload certificates")
    
    try:
        # Create certificates directory if it doesn't exist
        certs_dir = os.path.join(os.getcwd(), "certs")
        os.makedirs(certs_dir, exist_ok=True)
        
        # Save certificate file
        cert_path = os.path.join(certs_dir, "server.crt")
        with open(cert_path, "wb") as f:
            shutil.copyfileobj(cert_file.file, f)
        
        # Save key file
        key_path = os.path.join(certs_dir, "server.key")
        with open(key_path, "wb") as f:
            shutil.copyfileobj(key_file.file, f)
        
        # Update settings
        # In a real application, this would update the database or environment variables
        # For now, we'll just update the in-memory settings
        
        # Update settings in database or configuration store
        from ..db.models import Credential
        
        # Check if TLS settings credential exists
        tls_settings = db.query(Credential).filter(
            Credential.name == "tls_settings"
        ).first()
        
        if tls_settings:
            # Update existing credential
            tls_settings.data = {
                "tls_enabled": True,
                "cert_path": cert_path,
                "key_path": key_path
            }
        else:
            # Create new credential
            tls_settings = Credential(
                name="tls_settings",
                type="config",
                secret=str({
                    "tls_enabled": True,
                    "cert_path": cert_path,
                    "key_path": key_path
                })
            )
            db.add(tls_settings)
        
        db.commit()
        
        return {
            "success": True,
            "message": "Certificates uploaded successfully",
            "cert_path": cert_path,
            "key_path": key_path
        }
        
    except Exception as e:
        logger.error(f"[API:Certs] Error uploading certificates: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading certificates: {str(e)}"
        )


@router.post("/enable", response_model=Dict[str, Any])
async def enable_tls(
    user: User = Depends(verify_scope(["admin"])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Enable TLS.
    
    Args:
        user: Authenticated user with admin scope
        db: Database session
        
    Returns:
        Success status
    """
    logger.info("[API:Certs] Enable TLS")
    
    try:
        # Get certificate info
        cert_path = settings.TLS_CERT_PATH
        key_path = settings.TLS_KEY_PATH
        
        # Check if files exist
        if not cert_path or not os.path.isfile(cert_path):
            raise HTTPException(
                status_code=400,
                detail="Certificate file not found"
            )
        
        if not key_path or not os.path.isfile(key_path):
            raise HTTPException(
                status_code=400,
                detail="Key file not found"
            )
        
        # Update settings in database or configuration store
        from ..db.models import Credential
        
        # Check if TLS settings credential exists
        tls_settings = db.query(Credential).filter(
            Credential.name == "tls_settings"
        ).first()
        
        if tls_settings:
            # Update existing credential
            tls_settings.data = {
                "tls_enabled": True,
                "cert_path": cert_path,
                "key_path": key_path
            }
        else:
            # Create new credential
            tls_settings = Credential(
                name="tls_settings",
                type="config",
                secret=str({
                    "tls_enabled": True,
                    "cert_path": cert_path,
                    "key_path": key_path
                })
            )
            db.add(tls_settings)
        
        db.commit()
        
        return {
            "success": True,
            "message": "TLS enabled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API:Certs] Error enabling TLS: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error enabling TLS: {str(e)}"
        )


@router.post("/disable", response_model=Dict[str, Any])
async def disable_tls(
    user: User = Depends(verify_scope(["admin"])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Disable TLS.
    
    Args:
        user: Authenticated user with admin scope
        db: Database session
        
    Returns:
        Success status
    """
    logger.info("[API:Certs] Disable TLS")
    
    try:
        # Update settings in database or configuration store
        from ..db.models import Credential
        
        # Check if TLS settings credential exists
        tls_settings = db.query(Credential).filter(
            Credential.name == "tls_settings"
        ).first()
        
        if tls_settings:
            # Update existing credential
            tls_settings.data = {
                "tls_enabled": False,
                "cert_path": settings.TLS_CERT_PATH,
                "key_path": settings.TLS_KEY_PATH
            }
            
            db.commit()
        
        return {
            "success": True,
            "message": "TLS disabled successfully"
        }
        
    except Exception as e:
        logger.error(f"[API:Certs] Error disabling TLS: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error disabling TLS: {str(e)}"
        )
