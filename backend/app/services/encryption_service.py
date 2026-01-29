import logging
import os
import json
from typing import Optional

# Import Core Logic
from app.core.encryptor import AESEncryptor, EncryptedData

logger = logging.getLogger(__name__)

class EncryptionService:
    """
    Service responsible for encrypting output files and managing decryption requests.
    """

    def __init__(self):
        # In a real production system, you might fetch a Master Key from HashiCorp Vault
        # or AWS Secrets Manager here. For this internal tool, we generate per-file keys.
        pass

    def encrypt_output_file(self, input_path: str, output_path: str, passphrase: str) -> bool:
        """
        Encrypts a generated file (CSV/Excel) and saves it to the secure storage.
        
        Args:
            input_path: Path to the raw (unencrypted) file.
            output_path: Destination path for the .enc file.
            passphrase: The key used to encrypt this specific file.
        """
        encryptor = AESEncryptor(passphrase=passphrase)
        
        try:
            logger.info(f"Starting encryption for {input_path}")
            
            # [cite_start]Use the core encryptor module to handle the AES-256-GCM logic [cite: 23]
            # This saves the file as a JSON structure containing {ciphertext, iv, salt, tag}
            encryptor.encrypt_file(input_path, output_path)
            
            # Verify the output exists
            if not os.path.exists(output_path):
                raise FileNotFoundError("Encryption completed but output file not found.")
                
            logger.info(f"File encrypted successfully to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Encryption service failed: {str(e)}")
            # Ensure no partial files are left
            if os.path.exists(output_path):
                os.remove(output_path)
            raise e

    def decrypt_file(self, file_path: str, passphrase: str) -> Optional[str]:
        """
        Decrypts a file for temporary access.
        
        Args:
            file_path: Path to the .enc file.
            passphrase: The key provided by the user.
            
        Returns:
            Path to the temporary decrypted file (which must be cleaned up later).
        """
        encryptor = AESEncryptor(passphrase=passphrase)
        
        # Determine output path (remove .enc extension)
        # file_path is like ".../uuid.enc" -> output is ".../uuid_decrypted"
        # We need to peek at metadata to know the real extension, 
        # but for now, we'll assume the system knows or appends it.
        # Let's save it to a temp location with a generic suffix to be renamed by the controller if needed.
        temp_output_path = file_path.replace(".enc", ".decrypted.tmp")

        try:
            logger.info(f"Attempting decryption for {file_path}")
            
            # Core decryption logic
            encryptor.decrypt_file(file_path, temp_output_path)
            
            logger.info(f"Decryption successful. Temp file at {temp_output_path}")
            return temp_output_path

        except Exception as e:
            logger.error(f"Decryption service failed: {str(e)}")
            if os.path.exists(temp_output_path):
                os.remove(temp_output_path)
            raise ValueError("Invalid passphrase or corrupted file.")