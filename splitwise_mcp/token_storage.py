#!/usr/bin/env python3
"""Secure token storage and management for OAuth tokens."""

import os
import json
import base64
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger("splitwise-token-storage")


class TokenStorage:
    """Secure storage for OAuth tokens."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize token storage.
        
        Args:
            storage_dir: Directory to store encrypted tokens (default: ~/.splitwise-mcp)
        """
        if storage_dir is None:
            storage_dir = os.path.expanduser("~/.splitwise-mcp")
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.tokens_file = self.storage_dir / "oauth_tokens.json"
        self.key_file = self.storage_dir / "encryption.key"
        
        # Initialize encryption key
        self._encryption_key = self._get_or_create_encryption_key()
        self._fernet = Fernet(self._encryption_key)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for token storage."""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            
            # Set restrictive permissions
            os.chmod(self.key_file, 0o600)
            return key
    
    def _derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def store_token(self, user_id: str, access_token: str, 
                   token_type: str = "Bearer", expires_in: Optional[int] = None,
                   refresh_token: Optional[str] = None) -> bool:
        """
        Store OAuth token securely.
        
        Args:
            user_id: Unique identifier for the user
            access_token: OAuth access token
            token_type: Type of token (default: Bearer)
            expires_in: Token expiration time in seconds
            refresh_token: Optional refresh token
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load existing tokens
            tokens = self._load_tokens()
            
            # Create token data
            token_data = {
                "access_token": access_token,
                "token_type": token_type,
                "expires_in": expires_in,
                "refresh_token": refresh_token,
                "created_at": int(os.time())
            }
            
            # Encrypt token data
            encrypted_data = self._fernet.encrypt(json.dumps(token_data).encode())
            
            # Store encrypted token
            tokens[user_id] = base64.b64encode(encrypted_data).decode()
            
            # Save to file
            self._save_tokens(tokens)
            
            logger.info(f"Stored OAuth token for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing token: {e}")
            return False
    
    def get_token(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve OAuth token for user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Token data dictionary or None if not found
        """
        try:
            tokens = self._load_tokens()
            
            if user_id not in tokens:
                return None
            
            # Decrypt token data
            encrypted_data = base64.b64decode(tokens[user_id])
            decrypted_data = self._fernet.decrypt(encrypted_data)
            token_data = json.loads(decrypted_data.decode())
            
            # Check if token is expired
            if self._is_token_expired(token_data):
                logger.warning(f"Token expired for user: {user_id}")
                return None
            
            return token_data
            
        except Exception as e:
            logger.error(f"Error retrieving token: {e}")
            return None
    
    def revoke_token(self, user_id: str) -> bool:
        """
        Revoke and remove OAuth token for user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            True if successful, False otherwise
        """
        try:
            tokens = self._load_tokens()
            
            if user_id in tokens:
                del tokens[user_id]
                self._save_tokens(tokens)
                logger.info(f"Revoked token for user: {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error revoking token: {e}")
            return False
    
    def list_users(self) -> list:
        """
        List all users with stored tokens.
        
        Returns:
            List of user IDs with stored tokens
        """
        try:
            tokens = self._load_tokens()
            return list(tokens.keys())
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []
    
    def clear_all_tokens(self) -> bool:
        """
        Clear all stored tokens.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self._save_tokens({})
            logger.info("Cleared all stored tokens")
            return True
        except Exception as e:
            logger.error(f"Error clearing tokens: {e}")
            return False
    
    def _load_tokens(self) -> Dict[str, str]:
        """Load encrypted tokens from file."""
        if not self.tokens_file.exists():
            return {}
        
        with open(self.tokens_file, 'r') as f:
            return json.load(f)
    
    def _save_tokens(self, tokens: Dict[str, str]) -> None:
        """Save encrypted tokens to file."""
        with open(self.tokens_file, 'w') as f:
            json.dump(tokens, f, indent=2)
        
        # Set restrictive permissions
        os.chmod(self.tokens_file, 0o600)
    
    def _is_token_expired(self, token_data: Dict[str, Any]) -> bool:
        """Check if token is expired."""
        if not token_data.get("expires_in"):
            return False  # No expiration info, assume valid
        
        created_at = token_data.get("created_at", 0)
        expires_in = token_data.get("expires_in", 0)
        
        current_time = int(os.time())
        return current_time > (created_at + expires_in)
    
    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get information about token storage.
        
        Returns:
            Dictionary with storage information
        """
        try:
            tokens = self._load_tokens()
            users = list(tokens.keys())
            
            return {
                "storage_dir": str(self.storage_dir),
                "tokens_file": str(self.tokens_file),
                "key_file": str(self.key_file),
                "user_count": len(users),
                "users": users
            }
        except Exception as e:
            logger.error(f"Error getting storage info: {e}")
            return {"error": str(e)}


# Global token storage instance
_token_storage: Optional[TokenStorage] = None


def get_token_storage() -> TokenStorage:
    """Get the global token storage instance."""
    global _token_storage
    if _token_storage is None:
        _token_storage = TokenStorage()
    return _token_storage


def store_oauth_token(user_id: str, access_token: str, **kwargs) -> bool:
    """Convenience function to store OAuth token."""
    return get_token_storage().store_token(user_id, access_token, **kwargs)


def get_oauth_token(user_id: str) -> Optional[Dict[str, Any]]:
    """Convenience function to get OAuth token."""
    return get_token_storage().get_token(user_id)


def revoke_oauth_token(user_id: str) -> bool:
    """Convenience function to revoke OAuth token."""
    return get_token_storage().revoke_token(user_id)


if __name__ == "__main__":
    # Example usage
    storage = TokenStorage()
    
    # Store a token
    success = storage.store_token(
        user_id="test_user",
        access_token="test_access_token",
        token_type="Bearer",
        expires_in=3600
    )
    print(f"Token stored: {success}")
    
    # Retrieve token
    token_data = storage.get_token("test_user")
    print(f"Retrieved token: {token_data}")
    
    # List users
    users = storage.list_users()
    print(f"Users with tokens: {users}")
    
    # Revoke token
    revoked = storage.revoke_token("test_user")
    print(f"Token revoked: {revoked}")
