"""
Encryptor Module

Implements AES-256 encryption/decryption for output files.
Uses industry-standard encryption practices.

Author: Email Extraction System
"""

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import base64
from typing import Optional, Tuple
import logging
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class EncryptedData:
    """Container for encrypted data and metadata."""
    ciphertext: bytes
    salt: bytes
    iv: bytes  # Initialization vector
    tag: bytes  # Authentication tag (for GCM mode)
    metadata: dict = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'ciphertext': base64.b64encode(self.ciphertext).decode('utf-8'),
            'salt': base64.b64encode(self.salt).decode('utf-8'),
            'iv': base64.b64encode(self.iv).decode('utf-8'),
            'tag': base64.b64encode(self.tag).decode('utf-8'),
            'metadata': self.metadata or {}
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'EncryptedData':
        """Create from dictionary."""
        return cls(
            ciphertext=base64.b64decode(data['ciphertext']),
            salt=base64.b64decode(data['salt']),
            iv=base64.b64decode(data['iv']),
            tag=base64.b64decode(data['tag']),
            metadata=data.get('metadata', {})
        )


class AESEncryptor:
    """
    AES-256 encryption/decryption using GCM mode (Galois/Counter Mode).
    GCM provides both confidentiality and authenticity.
    """
    
    # Constants
    KEY_SIZE = 32  # 256 bits
    SALT_SIZE = 16  # 128 bits
    IV_SIZE = 12  # 96 bits (recommended for GCM)
    TAG_SIZE = 16  # 128 bits
    ITERATIONS = 100000  # PBKDF2 iterations
    
    def __init__(self, passphrase: Optional[str] = None):
        """
        Initialize encryptor.
        
        Args:
            passphrase: Encryption passphrase (if None, generates random key)
        """
        self.passphrase = passphrase
        self.backend = default_backend()
    
    def _derive_key(self, passphrase: str, salt: bytes) -> bytes:
        """
        Derive encryption key from passphrase using PBKDF2.
        
        Args:
            passphrase: User passphrase
            salt: Salt for key derivation
            
        Returns:
            Derived key (32 bytes)
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_SIZE,
            salt=salt,
            iterations=self.ITERATIONS,
            backend=self.backend
        )
        
        key = kdf.derive(passphrase.encode('utf-8'))
        return key
    
    def encrypt(self, 
                plaintext: bytes, 
                passphrase: Optional[str] = None,
                metadata: Optional[dict] = None) -> EncryptedData:
        """
        Encrypt data using AES-256-GCM.
        
        Args:
            plaintext: Data to encrypt
            passphrase: Encryption passphrase (uses instance passphrase if None)
            metadata: Optional metadata to include (not encrypted)
            
        Returns:
            EncryptedData object
        """
        # Use provided passphrase or instance passphrase
        pwd = passphrase or self.passphrase
        if not pwd:
            raise ValueError("No passphrase provided for encryption")
        
        try:
            # Generate random salt and IV
            salt = os.urandom(self.SALT_SIZE)
            iv = os.urandom(self.IV_SIZE)
            
            # Derive key from passphrase
            key = self._derive_key(pwd, salt)
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(iv),
                backend=self.backend
            )
            
            encryptor = cipher.encryptor()
            
            # Encrypt the data
            ciphertext = encryptor.update(plaintext) + encryptor.finalize()
            
            # Get authentication tag
            tag = encryptor.tag
            
            encrypted_data = EncryptedData(
                ciphertext=ciphertext,
                salt=salt,
                iv=iv,
                tag=tag,
                metadata=metadata
            )
            
            logger.info(f"Successfully encrypted {len(plaintext)} bytes")
            return encrypted_data
            
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise
    
    def decrypt(self, 
                encrypted_data: EncryptedData, 
                passphrase: Optional[str] = None) -> bytes:
        """
        Decrypt data using AES-256-GCM.
        
        Args:
            encrypted_data: EncryptedData object
            passphrase: Decryption passphrase (uses instance passphrase if None)
            
        Returns:
            Decrypted plaintext bytes
        """
        # Use provided passphrase or instance passphrase
        pwd = passphrase or self.passphrase
        if not pwd:
            raise ValueError("No passphrase provided for decryption")
        
        try:
            # Derive key from passphrase
            key = self._derive_key(pwd, encrypted_data.salt)
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(encrypted_data.iv, encrypted_data.tag),
                backend=self.backend
            )
            
            decryptor = cipher.decryptor()
            
            # Decrypt the data
            plaintext = decryptor.update(encrypted_data.ciphertext) + decryptor.finalize()
            
            logger.info(f"Successfully decrypted {len(plaintext)} bytes")
            return plaintext
            
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise
    
    def encrypt_file(self, 
                    input_path: str, 
                    output_path: str, 
                    passphrase: Optional[str] = None,
                    metadata: Optional[dict] = None) -> EncryptedData:
        """
        Encrypt a file.
        
        Args:
            input_path: Path to file to encrypt
            output_path: Path for encrypted output
            passphrase: Encryption passphrase
            metadata: Optional metadata
            
        Returns:
            EncryptedData object
        """
        try:
            # Read input file
            with open(input_path, 'rb') as f:
                plaintext = f.read()
            
            logger.info(f"Read {len(plaintext)} bytes from {input_path}")
            
            # Encrypt
            encrypted_data = self.encrypt(plaintext, passphrase, metadata)
            
            # Write encrypted data to file (as JSON)
            output_dict = encrypted_data.to_dict()
            with open(output_path, 'w') as f:
                json.dump(output_dict, f, indent=2)
            
            logger.info(f"Encrypted file saved to {output_path}")
            return encrypted_data
            
        except Exception as e:
            logger.error(f"File encryption failed: {str(e)}")
            raise
    
    def decrypt_file(self, 
                    input_path: str, 
                    output_path: str, 
                    passphrase: Optional[str] = None) -> bytes:
        """
        Decrypt a file.
        
        Args:
            input_path: Path to encrypted file
            output_path: Path for decrypted output
            passphrase: Decryption passphrase
            
        Returns:
            Decrypted data
        """
        try:
            # Read encrypted file
            with open(input_path, 'r') as f:
                encrypted_dict = json.load(f)
            
            encrypted_data = EncryptedData.from_dict(encrypted_dict)
            
            logger.info(f"Read encrypted data from {input_path}")
            
            # Decrypt
            plaintext = self.decrypt(encrypted_data, passphrase)
            
            # Write decrypted data to file
            with open(output_path, 'wb') as f:
                f.write(plaintext)
            
            logger.info(f"Decrypted file saved to {output_path}")
            return plaintext
            
        except Exception as e:
            logger.error(f"File decryption failed: {str(e)}")
            raise
    
    def encrypt_string(self, 
                      plaintext: str, 
                      passphrase: Optional[str] = None,
                      encoding: str = 'utf-8') -> str:
        """
        Encrypt a string and return base64-encoded result.
        
        Args:
            plaintext: String to encrypt
            passphrase: Encryption passphrase
            encoding: String encoding
            
        Returns:
            Base64-encoded encrypted data (JSON)
        """
        encrypted_data = self.encrypt(plaintext.encode(encoding), passphrase)
        return json.dumps(encrypted_data.to_dict())
    
    def decrypt_string(self, 
                      encrypted_json: str, 
                      passphrase: Optional[str] = None,
                      encoding: str = 'utf-8') -> str:
        """
        Decrypt a base64-encoded encrypted string.
        
        Args:
            encrypted_json: JSON string containing encrypted data
            passphrase: Decryption passphrase
            encoding: String encoding
            
        Returns:
            Decrypted string
        """
        encrypted_dict = json.loads(encrypted_json)
        encrypted_data = EncryptedData.from_dict(encrypted_dict)
        plaintext_bytes = self.decrypt(encrypted_data, passphrase)
        return plaintext_bytes.decode(encoding)
    
    @staticmethod
    def generate_passphrase(length: int = 32) -> str:
        """
        Generate a random secure passphrase.
        
        Args:
            length: Length of passphrase
            
        Returns:
            Base64-encoded random passphrase
        """
        random_bytes = os.urandom(length)
        passphrase = base64.urlsafe_b64encode(random_bytes).decode('utf-8')
        logger.info(f"Generated random passphrase ({length} bytes)")
        return passphrase
    
    @staticmethod
    def verify_passphrase(passphrase: str) -> bool:
        """
        Verify passphrase meets minimum requirements.
        
        Args:
            passphrase: Passphrase to verify
            
        Returns:
            True if passphrase is acceptable
        """
        # Minimum length check
        if len(passphrase) < 8:
            logger.warning("Passphrase too short (minimum 8 characters)")
            return False
        
        return True


class FileEncryptor:
    """
    Higher-level file encryption with key management.
    """
    
    def __init__(self, key_file: Optional[str] = None):
        """
        Initialize file encryptor.
        
        Args:
            key_file: Path to file containing encryption key
        """
        self.key_file = key_file
        self._passphrase = None
        
        if key_file and os.path.exists(key_file):
            self._load_key()
    
    def _load_key(self):
        """Load encryption key from file."""
        try:
            with open(self.key_file, 'r') as f:
                self._passphrase = f.read().strip()
            logger.info(f"Loaded encryption key from {self.key_file}")
        except Exception as e:
            logger.error(f"Failed to load key: {str(e)}")
            raise
    
    def _save_key(self, passphrase: str):
        """Save encryption key to file."""
        try:
            with open(self.key_file, 'w') as f:
                f.write(passphrase)
            # Set restrictive permissions (Unix only)
            if os.name != 'nt':  # Not Windows
                os.chmod(self.key_file, 0o600)
            logger.info(f"Saved encryption key to {self.key_file}")
        except Exception as e:
            logger.error(f"Failed to save key: {str(e)}")
            raise
    
    def initialize_key(self, passphrase: Optional[str] = None):
        """
        Initialize encryption key (generate if not provided).
        
        Args:
            passphrase: Encryption passphrase (generates if None)
        """
        if passphrase:
            if not AESEncryptor.verify_passphrase(passphrase):
                raise ValueError("Passphrase does not meet requirements")
            self._passphrase = passphrase
        else:
            self._passphrase = AESEncryptor.generate_passphrase()
        
        if self.key_file:
            self._save_key(self._passphrase)
    
    def encrypt(self, input_path: str, output_path: str, metadata: Optional[dict] = None):
        """
        Encrypt a file.
        
        Args:
            input_path: Input file path
            output_path: Output file path
            metadata: Optional metadata
        """
        if not self._passphrase:
            raise ValueError("No encryption key available")
        
        encryptor = AESEncryptor(self._passphrase)
        return encryptor.encrypt_file(input_path, output_path, metadata=metadata)
    
    def decrypt(self, input_path: str, output_path: str):
        """
        Decrypt a file.
        
        Args:
            input_path: Input file path
            output_path: Output file path
        """
        if not self._passphrase:
            raise ValueError("No encryption key available")
        
        encryptor = AESEncryptor(self._passphrase)
        return encryptor.decrypt_file(input_path, output_path)
    
    def get_passphrase(self) -> Optional[str]:
        """Get the current passphrase (use with caution)."""
        return self._passphrase


# Convenience functions
def encrypt_data(data: bytes, passphrase: str) -> EncryptedData:
    """
    Convenience function to encrypt data.
    
    Args:
        data: Data to encrypt
        passphrase: Encryption passphrase
        
    Returns:
        EncryptedData object
    """
    encryptor = AESEncryptor(passphrase)
    return encryptor.encrypt(data)


def decrypt_data(encrypted_data: EncryptedData, passphrase: str) -> bytes:
    """
    Convenience function to decrypt data.
    
    Args:
        encrypted_data: EncryptedData object
        passphrase: Decryption passphrase
        
    Returns:
        Decrypted data
    """
    encryptor = AESEncryptor(passphrase)
    return encryptor.decrypt(encrypted_data)