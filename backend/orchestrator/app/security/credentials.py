"""
Credential encryption and decryption utilities.

Provides secure encryption/decryption of credentials using Fernet (AES-128).

Security Rules:
- Master key MUST be stored in environment variable ORCH_CRED_KEY
- NEVER generate random keys at runtime
- NEVER log or print decrypted secrets
- NEVER include secrets in exception messages
"""

import os
import logging
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


class CredentialEncryptionError(Exception):
    """Exception raised for credential encryption/decryption errors."""
    pass


def get_crypto_key() -> bytes:
    """
    Get the master encryption key from environment.
    
    Returns:
        Master encryption key as bytes
        
    Raises:
        CredentialEncryptionError: If key is not configured
        
    Security:
        - Key MUST be set in ORCH_CRED_KEY environment variable
        - Key MUST be a valid Fernet key (44 bytes, base64-encoded)
        - NEVER generate a random key at runtime
        - NEVER hardcode the key
        
    Setup:
        To generate a new key, run:
        ```python
        from cryptography.fernet import Fernet
        key = Fernet.generate_key()
        print(key.decode())
        ```
        Then set it in .env:
        ORCH_CRED_KEY=<generated_key>
    """
    key = os.environ.get("ORCH_CRED_KEY")
    
    if not key:
        error_msg = (
            "Credential encryption key not configured. "
            "Please set ORCH_CRED_KEY environment variable. "
            "Generate a key with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
        logger.error(error_msg)
        raise CredentialEncryptionError(error_msg)
    
    try:
        # Validate key format
        key_bytes = key.encode() if isinstance(key, str) else key
        # Test if it's a valid Fernet key by creating a Fernet instance
        Fernet(key_bytes)
        return key_bytes
    except Exception as e:
        error_msg = (
            "Invalid credential encryption key format. "
            "Key must be a valid Fernet key (44 bytes, base64-encoded). "
            f"Error: {type(e).__name__}"
        )
        logger.error(error_msg)
        raise CredentialEncryptionError(error_msg)


def encrypt_secret(plain_text: str) -> str:
    """
    Encrypt a secret using Fernet encryption.
    
    Args:
        plain_text: Plain text secret to encrypt
        
    Returns:
        Encrypted secret as base64-encoded string
        
    Raises:
        CredentialEncryptionError: If encryption fails
        
    Security:
        - Uses AES-128 encryption in CBC mode with PKCS7 padding
        - Includes HMAC for authentication
        - NEVER logs the plain text
        - NEVER includes plain text in exceptions
    """
    if not plain_text:
        raise CredentialEncryptionError("Cannot encrypt empty secret")
    
    try:
        key = get_crypto_key()
        fernet = Fernet(key)
        
        # Encrypt the secret
        plain_bytes = plain_text.encode('utf-8')
        encrypted_bytes = fernet.encrypt(plain_bytes)
        encrypted_str = encrypted_bytes.decode('utf-8')
        
        logger.debug("Secret encrypted successfully")
        return encrypted_str
        
    except CredentialEncryptionError:
        # Re-raise key configuration errors
        raise
    except Exception as e:
        # NEVER include the plain text in the error message
        error_msg = f"Failed to encrypt secret: {type(e).__name__}"
        logger.error(error_msg)
        raise CredentialEncryptionError(error_msg)


def decrypt_secret(encrypted_text: str) -> str:
    """
    Decrypt a secret using Fernet decryption.
    
    Args:
        encrypted_text: Encrypted secret as base64-encoded string
        
    Returns:
        Decrypted plain text secret
        
    Raises:
        CredentialEncryptionError: If decryption fails
        
    Security:
        - NEVER logs the decrypted secret
        - NEVER includes decrypted secret in exceptions
        - Returns decrypted value only in memory
        - Caller is responsible for secure handling of decrypted value
        
    Warning:
        The decrypted secret is returned in plain text and exists in memory.
        The caller MUST:
        - Use it immediately
        - NEVER log it
        - NEVER return it in API responses
        - NEVER store it in plain text
    """
    if not encrypted_text:
        raise CredentialEncryptionError("Cannot decrypt empty secret")
    
    try:
        key = get_crypto_key()
        fernet = Fernet(key)
        
        # Decrypt the secret
        encrypted_bytes = encrypted_text.encode('utf-8')
        decrypted_bytes = fernet.decrypt(encrypted_bytes)
        decrypted_str = decrypted_bytes.decode('utf-8')
        
        logger.debug("Secret decrypted successfully")
        return decrypted_str
        
    except InvalidToken:
        # This happens if the key is wrong or data is corrupted
        error_msg = "Failed to decrypt secret: Invalid encryption key or corrupted data"
        logger.error(error_msg)
        raise CredentialEncryptionError(error_msg)
    except CredentialEncryptionError:
        # Re-raise key configuration errors
        raise
    except Exception as e:
        # NEVER include the encrypted or decrypted text in the error message
        error_msg = f"Failed to decrypt secret: {type(e).__name__}"
        logger.error(error_msg)
        raise CredentialEncryptionError(error_msg)


def mask_secret(secret: str, visible_chars: int = 4) -> str:
    """
    Mask a secret for logging purposes.
    
    Args:
        secret: Secret to mask
        visible_chars: Number of characters to show at the end
        
    Returns:
        Masked secret (e.g., "****abc123")
        
    Usage:
        For logging or display purposes only.
        Shows last N characters to help identify the credential.
    """
    if not secret:
        return "****"
    
    if len(secret) <= visible_chars:
        return "*" * len(secret)
    
    return "*" * (len(secret) - visible_chars) + secret[-visible_chars:]


def validate_credential_type(cred_type: str) -> bool:
    """
    Validate credential type.
    
    Args:
        cred_type: Credential type to validate
        
    Returns:
        True if valid, False otherwise
        
    Valid types:
        - ssh: SSH credentials
        - http_basic: HTTP Basic Auth
        - bearer_token: Bearer token
        - db_dsn: Database connection string
        - api_key: API key
        - custom: Custom credential type
    """
    valid_types = {
        "ssh",
        "http_basic",
        "bearer_token",
        "db_dsn",
        "api_key",
        "custom"
    }
    return cred_type in valid_types
