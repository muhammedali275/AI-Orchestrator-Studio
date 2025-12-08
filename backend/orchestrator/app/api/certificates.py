"""
Certificates API - Endpoints for TLS certificate management.

Provides endpoints for uploading, enabling, and managing TLS certificates.
"""

import logging
import os
import shutil
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/certs", tags=["certificates"])


class CertificateInfo(BaseModel):
    """Certificate information model."""
    tls_enabled: bool = Field(..., description="TLS enabled status")
    cert_path: Optional[str] = Field(None, description="Certificate path")
    key_path: Optional[str] = Field(None, description="Key path")
    cert_exists: bool = Field(False, description="Certificate exists")
    key_exists: bool = Field(False, description="Key exists")


# Default certificate paths
CERT_DIR = os.path.join(os.getcwd(), "certs")
CERT_PATH = os.path.join(CERT_DIR, "certificate.pem")
KEY_PATH = os.path.join(CERT_DIR, "private_key.pem")

# Ensure certs directory exists
os.makedirs(CERT_DIR, exist_ok=True)


@router.get("", response_model=CertificateInfo)
async def get_certificate_info() -> CertificateInfo:
    """
    Get certificate information.
    
    Returns:
        Certificate information including status and paths
    """
    logger.info("[Certificates API] Get certificate info")
    
    try:
        # Check if files exist
        cert_exists = os.path.isfile(CERT_PATH)
        key_exists = os.path.isfile(KEY_PATH)
        
        # TLS is enabled if both files exist
        tls_enabled = cert_exists and key_exists
        
        return CertificateInfo(
            tls_enabled=tls_enabled,
            cert_path=CERT_PATH if cert_exists else None,
            key_path=KEY_PATH if key_exists else None,
            cert_exists=cert_exists,
            key_exists=key_exists
        )
        
    except Exception as e:
        logger.error(f"[Certificates API] Error getting certificate info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting certificate info: {str(e)}"
        )


@router.post("/upload")
async def upload_certificates(
    cert_file: UploadFile = File(..., description="Certificate file (certificate.pem)"),
    key_file: UploadFile = File(..., description="Private key file (private_key.pem)")
) -> Dict[str, Any]:
    """
    Upload TLS certificates.
    
    Args:
        cert_file: Certificate file
        key_file: Private key file
        
    Returns:
        Success status and file paths
    """
    logger.info("[Certificates API] Upload certificates")
    
    try:
        # Validate file extensions
        if not cert_file.filename.endswith('.pem'):
            raise HTTPException(
                status_code=400,
                detail="Certificate file must be a .pem file"
            )
        
        if not key_file.filename.endswith('.pem'):
            raise HTTPException(
                status_code=400,
                detail="Private key file must be a .pem file"
            )
        
        # Save certificate file
        with open(CERT_PATH, "wb") as f:
            content = await cert_file.read()
            f.write(content)
        
        logger.info(f"[Certificates API] Saved certificate to {CERT_PATH}")
        
        # Save private key file
        with open(KEY_PATH, "wb") as f:
            content = await key_file.read()
            f.write(content)
        
        logger.info(f"[Certificates API] Saved private key to {KEY_PATH}")
        
        # Set appropriate permissions (read-only for owner)
        os.chmod(CERT_PATH, 0o400)
        os.chmod(KEY_PATH, 0o400)
        
        return {
            "success": True,
            "message": "Certificates uploaded successfully",
            "cert_path": CERT_PATH,
            "key_path": KEY_PATH,
            "tls_enabled": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Certificates API] Error uploading certificates: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading certificates: {str(e)}"
        )


@router.post("/enable")
async def enable_tls() -> Dict[str, Any]:
    """
    Enable TLS.
    
    Returns:
        Success status
    """
    logger.info("[Certificates API] Enable TLS")
    
    try:
        # Check if certificates exist
        if not os.path.isfile(CERT_PATH) or not os.path.isfile(KEY_PATH):
            raise HTTPException(
                status_code=400,
                detail="Certificates not found. Please upload certificates first."
            )
        
        # In a real implementation, this would update the server configuration
        # For now, we just verify the files exist
        
        return {
            "success": True,
            "message": "TLS enabled successfully",
            "tls_enabled": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Certificates API] Error enabling TLS: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error enabling TLS: {str(e)}"
        )


@router.post("/disable")
async def disable_tls() -> Dict[str, Any]:
    """
    Disable TLS.
    
    Returns:
        Success status
    """
    logger.info("[Certificates API] Disable TLS")
    
    try:
        # In a real implementation, this would update the server configuration
        # For now, we just return success
        
        return {
            "success": True,
            "message": "TLS disabled successfully",
            "tls_enabled": False
        }
        
    except Exception as e:
        logger.error(f"[Certificates API] Error disabling TLS: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error disabling TLS: {str(e)}"
        )


@router.delete("")
async def delete_certificates() -> Dict[str, Any]:
    """
    Delete uploaded certificates.
    
    Returns:
        Success status
    """
    logger.info("[Certificates API] Delete certificates")
    
    try:
        deleted = []
        
        # Delete certificate file
        if os.path.isfile(CERT_PATH):
            os.remove(CERT_PATH)
            deleted.append("certificate.pem")
            logger.info(f"[Certificates API] Deleted {CERT_PATH}")
        
        # Delete private key file
        if os.path.isfile(KEY_PATH):
            os.remove(KEY_PATH)
            deleted.append("private_key.pem")
            logger.info(f"[Certificates API] Deleted {KEY_PATH}")
        
        if not deleted:
            return {
                "success": True,
                "message": "No certificates to delete",
                "deleted": []
            }
        
        return {
            "success": True,
            "message": f"Deleted {len(deleted)} certificate file(s)",
            "deleted": deleted
        }
        
    except Exception as e:
        logger.error(f"[Certificates API] Error deleting certificates: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting certificates: {str(e)}"
        )
