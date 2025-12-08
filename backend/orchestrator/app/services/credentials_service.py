"""
Credentials Service - Business logic for credential management.

Provides CRUD operations for credentials with encryption/decryption.

Security Rules:
- All secrets MUST be encrypted before storage
- Decrypted secrets MUST NEVER be returned in responses
- Decrypted secrets MUST NEVER be logged
- Only metadata is returned to API layer
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..db.models import Credential
from ..security.credentials import (
    encrypt_secret,
    decrypt_secret,
    validate_credential_type,
    CredentialEncryptionError
)

logger = logging.getLogger(__name__)


class CredentialNotFoundError(Exception):
    """Exception raised when credential is not found."""
    pass


class CredentialValidationError(Exception):
    """Exception raised when credential validation fails."""
    pass


class CredentialsService:
    """
    Service for managing credentials.
    
    Handles CRUD operations with automatic encryption/decryption.
    """
    
    def __init__(self, db: Session):
        """
        Initialize credentials service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create_credential(
        self,
        name: str,
        cred_type: str,
        secret: str,
        username: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new credential.
        
        Args:
            name: Human-readable credential name
            cred_type: Credential type (ssh, http_basic, bearer_token, db_dsn, api_key, custom)
            secret: Plain text secret (will be encrypted)
            username: Optional username
            extra: Optional metadata (must not contain secrets)
            
        Returns:
            Credential metadata (without secret)
            
        Raises:
            CredentialValidationError: If validation fails
            CredentialEncryptionError: If encryption fails
            
        Security:
            - Secret is encrypted before storage
            - Returns metadata only, never the secret
        """
        # Validate inputs
        if not name or not name.strip():
            raise CredentialValidationError("Credential name is required")
        
        if not cred_type or not validate_credential_type(cred_type):
            raise CredentialValidationError(
                f"Invalid credential type: {cred_type}. "
                f"Valid types: ssh, http_basic, bearer_token, db_dsn, api_key, custom"
            )
        
        if not secret or not secret.strip():
            raise CredentialValidationError("Secret is required")
        
        # Validate extra doesn't contain sensitive keys
        if extra:
            sensitive_keys = {"password", "secret", "token", "key", "credential"}
            found_sensitive = [k for k in extra.keys() if any(s in k.lower() for s in sensitive_keys)]
            if found_sensitive:
                raise CredentialValidationError(
                    f"Extra metadata must not contain sensitive keys: {found_sensitive}"
                )
        
        try:
            # Encrypt the secret
            encrypted_secret = encrypt_secret(secret)
            
            # Create credential
            credential = Credential(
                name=name.strip(),
                type=cred_type,
                username=username.strip() if username else None,
                secret=encrypted_secret,
                extra=extra or {},
                is_active=True
            )
            
            self.db.add(credential)
            self.db.commit()
            self.db.refresh(credential)
            
            logger.info(f"Created credential: {credential.name} (type: {credential.type})")
            
            # Return safe metadata only
            return credential.to_safe_dict()
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Credential with name '{name}' already exists")
            raise CredentialValidationError(f"Credential with name '{name}' already exists")
        except CredentialEncryptionError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating credential: {str(e)}")
            raise
    
    def get_credential(self, credential_id: str) -> Dict[str, Any]:
        """
        Get credential metadata by ID.
        
        Args:
            credential_id: Credential ID
            
        Returns:
            Credential metadata (without secret)
            
        Raises:
            CredentialNotFoundError: If credential not found
            
        Security:
            - Returns metadata only, never the secret
        """
        credential = self.db.query(Credential).filter(Credential.id == credential_id).first()
        
        if not credential:
            raise CredentialNotFoundError(f"Credential not found: {credential_id}")
        
        return credential.to_safe_dict()
    
    def get_credential_by_name(self, name: str) -> Dict[str, Any]:
        """
        Get credential metadata by name.
        
        Args:
            name: Credential name
            
        Returns:
            Credential metadata (without secret)
            
        Raises:
            CredentialNotFoundError: If credential not found
            
        Security:
            - Returns metadata only, never the secret
        """
        credential = self.db.query(Credential).filter(Credential.name == name).first()
        
        if not credential:
            raise CredentialNotFoundError(f"Credential not found: {name}")
        
        return credential.to_safe_dict()
    
    def list_credentials(
        self,
        cred_type: Optional[str] = None,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List all credentials.
        
        Args:
            cred_type: Optional filter by credential type
            active_only: If True, return only active credentials
            
        Returns:
            List of credential metadata (without secrets)
            
        Security:
            - Returns metadata only, never secrets
        """
        query = self.db.query(Credential)
        
        if cred_type:
            query = query.filter(Credential.type == cred_type)
        
        if active_only:
            query = query.filter(Credential.is_active == True)
        
        credentials = query.order_by(Credential.created_at.desc()).all()
        
        return [cred.to_safe_dict() for cred in credentials]
    
    def update_credential(
        self,
        credential_id: str,
        name: Optional[str] = None,
        secret: Optional[str] = None,
        username: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Update credential.
        
        Args:
            credential_id: Credential ID
            name: New name (optional)
            secret: New secret (optional, will be encrypted)
            username: New username (optional)
            extra: New metadata (optional)
            is_active: New active status (optional)
            
        Returns:
            Updated credential metadata (without secret)
            
        Raises:
            CredentialNotFoundError: If credential not found
            CredentialValidationError: If validation fails
            
        Security:
            - If secret is provided, it's encrypted before storage
            - Returns metadata only, never the secret
        """
        credential = self.db.query(Credential).filter(Credential.id == credential_id).first()
        
        if not credential:
            raise CredentialNotFoundError(f"Credential not found: {credential_id}")
        
        try:
            # Update fields
            if name is not None:
                if not name.strip():
                    raise CredentialValidationError("Credential name cannot be empty")
                credential.name = name.strip()
            
            if secret is not None:
                if not secret.strip():
                    raise CredentialValidationError("Secret cannot be empty")
                # Encrypt new secret
                credential.secret = encrypt_secret(secret)
                logger.info(f"Rotated secret for credential: {credential.name}")
            
            if username is not None:
                credential.username = username.strip() if username else None
            
            if extra is not None:
                # Validate extra doesn't contain sensitive keys
                sensitive_keys = {"password", "secret", "token", "key", "credential"}
                found_sensitive = [k for k in extra.keys() if any(s in k.lower() for s in sensitive_keys)]
                if found_sensitive:
                    raise CredentialValidationError(
                        f"Extra metadata must not contain sensitive keys: {found_sensitive}"
                    )
                credential.extra = extra
            
            if is_active is not None:
                credential.is_active = is_active
            
            credential.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(credential)
            
            logger.info(f"Updated credential: {credential.name}")
            
            return credential.to_safe_dict()
            
        except IntegrityError:
            self.db.rollback()
            raise CredentialValidationError(f"Credential with name '{name}' already exists")
        except (CredentialValidationError, CredentialEncryptionError):
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating credential: {str(e)}")
            raise
    
    def delete_credential(self, credential_id: str) -> bool:
        """
        Delete (soft delete) a credential.
        
        Args:
            credential_id: Credential ID
            
        Returns:
            True if deleted
            
        Raises:
            CredentialNotFoundError: If credential not found
        """
        credential = self.db.query(Credential).filter(Credential.id == credential_id).first()
        
        if not credential:
            raise CredentialNotFoundError(f"Credential not found: {credential_id}")
        
        # Soft delete
        credential.is_active = False
        credential.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        logger.info(f"Deactivated credential: {credential.name}")
        
        return True
    
    def get_credential_for_use(self, credential_id: str) -> Dict[str, Any]:
        """
        Get credential with decrypted secret for internal use.
        
        Args:
            credential_id: Credential ID
            
        Returns:
            Dictionary with decrypted secret and metadata
            
        Raises:
            CredentialNotFoundError: If credential not found
            CredentialEncryptionError: If decryption fails
            
        Security:
            - This method MUST ONLY be used internally by clients/services
            - The returned dictionary contains the decrypted secret
            - NEVER return this dictionary in API responses
            - NEVER log the returned dictionary
            - Use the decrypted secret immediately and don't store it
            
        Warning:
            This is a security-sensitive method. The decrypted secret
            exists in memory and must be handled with extreme care.
        """
        credential = self.db.query(Credential).filter(
            Credential.id == credential_id,
            Credential.is_active == True
        ).first()
        
        if not credential:
            raise CredentialNotFoundError(f"Active credential not found: {credential_id}")
        
        try:
            # Decrypt the secret
            decrypted_secret = decrypt_secret(credential.secret)
            
            # Return credential data with decrypted secret
            # WARNING: This contains sensitive data!
            return {
                "id": credential.id,
                "name": credential.name,
                "type": credential.type,
                "username": credential.username,
                "secret": decrypted_secret,  # DECRYPTED - Handle with care!
                "extra": credential.extra or {}
            }
            
        except CredentialEncryptionError:
            logger.error(f"Failed to decrypt credential: {credential.name}")
            raise
