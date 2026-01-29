"""
Decrypt Response Schema

Defines metadata about a decrypted file. 
Note: The actual file content is returned as a binary stream, not via this JSON model.
This model is primarily used for metadata checks or status reports.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DecryptMetadataResponse(BaseModel):
    """
    Metadata information about a file available for decryption.
    """
    file_id: str = Field(
        ..., 
        description="The unique identifier of the file."
    )
    filename: str = Field(
        ..., 
        description="Original filename of the exported data (e.g., results.csv)."
    )
    size_bytes: int = Field(
        ..., 
        description="Size of the encrypted file in bytes."
    )
    generated_at: datetime = Field(
        ..., 
        description="Timestamp when the file was originally created."
    )
    is_ready: bool = Field(
        True, 
        description="Whether the file is ready for download."
    )
    
    class Config:
        schema_extra = {
            "example": {
                "file_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "filename": "emails_20231027.csv",
                "size_bytes": 1048576,
                "generated_at": "2023-10-27T10:05:00Z",
                "is_ready": True
            }
        }