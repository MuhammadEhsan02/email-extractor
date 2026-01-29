"""
Decrypt Request Schema

Defines the inputs required to request a decrypted file.
"""

from pydantic import BaseModel, Field

class DecryptRequest(BaseModel):
    """
    Request payload for the /decrypt endpoint.
    """
    file_id: str = Field(
        ..., 
        min_length=1,
        description="The unique identifier of the encrypted file (usually the Job ID)."
    )
    passphrase: str = Field(
        ..., 
        min_length=8, 
        description="The secure passphrase used to decrypt the AES-256 file."
    )
    
    class Config:
        schema_extra = {
            "example": {
                "file_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "passphrase": "correct-horse-battery-staple"
            }
        }