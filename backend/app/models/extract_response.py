"""
Extract Response Schema

Defines the standard response format after initiating an extraction job.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ExtractResponse(BaseModel):
    """
    Response model for the initial POST /extract request.
    """
    job_id: str = Field(
        ..., 
        description="Unique UUID for tracking the background extraction job."
    )
    status: JobStatus = Field(
        default=JobStatus.QUEUED, 
        description="Current status of the job."
    )
    message: str = Field(
        ..., 
        description="Human-readable status message."
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the request was accepted."
    )
    estimated_completion_seconds: Optional[int] = Field(
        None, 
        description="Rough estimate of time to completion based on URL count."
    )

    # Pydantic V2 Config
    model_config = {
        "json_schema_extra": {
            "example": {
                "job_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "status": "queued",
                "message": "Extraction started in the background.",
                "created_at": "2023-10-27T10:00:00Z",
                "estimated_completion_seconds": 45
            }
        }
    }