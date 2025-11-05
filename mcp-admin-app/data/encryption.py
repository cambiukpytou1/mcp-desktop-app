"""
Encryption and Credential Management
===================================

Secure encryption and decryption utilities for sensitive data like API keys.
Uses only Python standard library components for core functionality.
"""

import os
import base64
import hashlib
import hmac
import secrets
import logging
from typing import Optional, Tuple


class CredentialEncryption:
    """Handles encryption and decryption of sensitive credentials using standard library."""
    
    def __init__(self, master_key: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self._master_key = master_key
        self._derived_key = None
        
        if master_key:
            self._initialize_encryption(master_key)
    
    def _initialize_encryption(self, master_key: str):
        """Initialize encryption with master key."""
        try:
            # Derive encryption key from master key using PBKDF2
            salt = b'mcp_admin_salt_2024'  # In production, use random salt per installation
            self._derived_key = hashlib.pbkdf2_hmac(
                'sha256', 
                master_key.encode(), 
                salt, 
                100000  # iterations
            )
            self.logger.info("Encryption initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize encryption: {e}")
            raise
    
    def generate_master_key(self) -> str:
        """Generate a new master key for encryption."""
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
    
    def _xor_encrypt_decrypt(self, data: bytes, key: bytes) -> bytes:
        """Simple XOR encryption/decryption with key stretching."""
        result = bytearray()
        key_len = len(key)
        
        for i, byte in enumerate(data):
            # Use HMAC to stretch the key for each position
            position_key = hmac.new(
                key, 
                i.to_bytes(4, 'big'), 
                hashlib.sha256
            ).digest()
            result.append(byte ^ position_key[i % len(position_key)])
        
        return bytes(result)
    
    def encrypt_credential(self, credential: str) -> Tuple[bytes, str]:
        """
        Encrypt a credential string.
        
        Returns:
            Tuple of (encrypted_bytes, encryption_method)
        """
        if not self._derived_key:
            raise ValueError("Encryption not initialized")
        
        try:
            # Add random nonce for additional security
            nonce = secrets.token_bytes(16)
            credential_bytes = credential.encode('utf-8')
            
            # Create encryption key from derived key and nonce
            encryption_key = hmac.new(
                self._derived_key, 
                nonce, 
                hashlib.sha256
            ).digest()
            
            # Encrypt the credential
            encrypted_data = self._xor_encrypt_decrypt(credential_bytes, encryption_key)
            
            # Combine nonce and encrypted data
            final_data = nonce + encrypted_data
            
            return final_data, "xor_hmac_pbkdf2"
        except Exception as e:
            self.logger.error(f"Failed to encrypt credential: {e}")
            raise
    
    def decrypt_credential(self, encrypted_data: bytes, encryption_method: str) -> str:
        """
        Decrypt a credential.
        
        Args:
            encrypted_data: The encrypted credential bytes
            encryption_method: The encryption method used
            
        Returns:
            Decrypted credential string
        """
        if not self._derived_key:
            raise ValueError("Encryption not initialized")
        
        if encryption_method != "xor_hmac_pbkdf2":
            raise ValueError(f"Unsupported encryption method: {encryption_method}")
        
        try:
            # Extract nonce and encrypted data
            nonce = encrypted_data[:16]
            encrypted_credential = encrypted_data[16:]
            
            # Recreate encryption key from derived key and nonce
            encryption_key = hmac.new(
                self._derived_key, 
                nonce, 
                hashlib.sha256
            ).digest()
            
            # Decrypt the credential
            decrypted_bytes = self._xor_encrypt_decrypt(encrypted_credential, encryption_key)
            
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            self.logger.error(f"Failed to decrypt credential: {e}")
            raise
    
    def hash_credential(self, credential: str) -> str:
        """Create a hash of the credential for verification purposes."""
        return hashlib.sha256(credential.encode()).hexdigest()
    
    def verify_credential_hash(self, credential: str, expected_hash: str) -> bool:
        """Verify a credential against its hash."""
        return self.hash_credential(credential) == expected_hash


class CredentialManager:
    """Manages encrypted credentials with database integration."""
    
    def __init__(self, db_manager, encryption: CredentialEncryption):
        self.db_manager = db_manager
        self.encryption = encryption
        self.logger = logging.getLogger(__name__)
    
    def store_credential(self, provider_id: str, credential_type: str, 
                        credential_value: str, expires_at: Optional[str] = None) -> bool:
        """Store an encrypted credential in the database."""
        try:
            encrypted_data, encryption_method = self.encryption.encrypt_credential(credential_value)
            
            with self.db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO encrypted_credentials 
                    (provider_id, credential_type, encrypted_value, encryption_method, 
                     created_at, expires_at)
                    VALUES (?, ?, ?, ?, datetime('now'), ?)
                """, (provider_id, credential_type, encrypted_data, encryption_method, expires_at))
                
                conn.commit()
                self.logger.info(f"Stored credential for provider {provider_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to store credential: {e}")
            return False
    
    def retrieve_credential(self, provider_id: str, credential_type: str) -> Optional[str]:
        """Retrieve and decrypt a credential from the database."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT encrypted_value, encryption_method 
                    FROM encrypted_credentials 
                    WHERE provider_id = ? AND credential_type = ?
                    AND (expires_at IS NULL OR expires_at > datetime('now'))
                """, (provider_id, credential_type))
                
                result = cursor.fetchone()
                if not result:
                    return None
                
                encrypted_data, encryption_method = result
                decrypted_credential = self.encryption.decrypt_credential(
                    encrypted_data, encryption_method
                )
                
                # Update last_used timestamp
                conn.execute("""
                    UPDATE encrypted_credentials 
                    SET last_used = datetime('now')
                    WHERE provider_id = ? AND credential_type = ?
                """, (provider_id, credential_type))
                conn.commit()
                
                return decrypted_credential
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve credential: {e}")
            return None
    
    def delete_credential(self, provider_id: str, credential_type: str) -> bool:
        """Delete a credential from the database."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    DELETE FROM encrypted_credentials 
                    WHERE provider_id = ? AND credential_type = ?
                """, (provider_id, credential_type))
                
                conn.commit()
                deleted_count = cursor.rowcount
                
                if deleted_count > 0:
                    self.logger.info(f"Deleted credential for provider {provider_id}")
                    return True
                else:
                    self.logger.warning(f"No credential found to delete for provider {provider_id}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to delete credential: {e}")
            return False
    
    def list_credentials(self, provider_id: str) -> list:
        """List all credential types for a provider (without values)."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT credential_type, created_at, expires_at, last_used
                    FROM encrypted_credentials 
                    WHERE provider_id = ?
                    ORDER BY created_at DESC
                """, (provider_id,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Failed to list credentials: {e}")
            return []
    
    def cleanup_expired_credentials(self) -> int:
        """Remove expired credentials from the database."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    DELETE FROM encrypted_credentials 
                    WHERE expires_at IS NOT NULL AND expires_at <= datetime('now')
                """)
                
                conn.commit()
                deleted_count = cursor.rowcount
                
                if deleted_count > 0:
                    self.logger.info(f"Cleaned up {deleted_count} expired credentials")
                
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired credentials: {e}")
            return 0