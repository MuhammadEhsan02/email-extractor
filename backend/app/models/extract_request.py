"""
Extract Request Schema

Defines the structure and validation rules for initiating an email extraction job.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class ExtractionMode(str, Enum):
    """
    Defines the operation mode.
    """
    QUICK = "quick"
    DEEP = "deep"
    CUSTOM = "custom"

class OutputFormat(str, Enum):
    CSV = "csv"
    EXCEL = "xlsx"
    JSON = "json"

class ExtractionConfig(BaseModel):
    """
    Fine-grained configuration for the extraction process.
    """
    max_urls_per_domain: int = Field(
        default=10, 
        ge=1, 
        le=50, 
        description="Max pages to visit per domain."
    )
    max_depth: int = Field(
        default=2, 
        ge=1, 
        le=5, 
        description="Recursion depth for crawling."
    )
    request_timeout: int = Field(
        default=30, 
        ge=5, 
        le=60, 
        description="Timeout in seconds per request."
    )
    respect_robots_txt: bool = Field(
        default=True, 
        description="Whether to strictly follow robots.txt rules."
    )
    user_agent_alias: str = Field(
        default="generic_desktop",
        description="Alias for the user agent string to use."
    )

class AIConfig(BaseModel):
    """
    Configuration for optional AI components.
    """
    enabled: bool = Field(
        default=False, 
        description="Enable AI-based categorization and filtering."
    )
    min_confidence: float = Field(
        default=0.7, 
        ge=0.0, 
        le=1.0, 
        description="Minimum confidence score to retain an email."
    )
    categorize_emails: bool = Field(
        default=True,
        description="Attempt to categorize emails (e.g., 'Sales', 'Support')."
    )

class ExtractRequest(BaseModel):
    """
    Main request payload for the /extract endpoint.
    """
    input_data: str = Field(
        ..., 
        min_length=5, 
        description="Raw text containing URLs or search results to parse."
    )
    mode: ExtractionMode = Field(
        default=ExtractionMode.QUICK, 
        description="Scraping intensity mode."
    )
    output_formats: List[OutputFormat] = Field(
        default=[OutputFormat.CSV], 
        description="List of desired output formats."
    )
    config: Optional[ExtractionConfig] = Field(
        default_factory=ExtractionConfig, 
        description="Technical constraints for the scraper."
    )
    ai_settings: Optional[AIConfig] = Field(
        default_factory=AIConfig, 
        description="Settings for AI analysis."
    )
    
    # Pydantic V2 Config
    model_config = {
        "json_schema_extra": {
            "example": {
                "input_data": "Check out https://example.com and www.test-site.org for leads.",
                "mode": "quick",
                "output_formats": ["csv", "xlsx"],
                "config": {
                    "max_urls_per_domain": 5,
                    "respect_robots_txt": True
                },
                "ai_settings": {
                    "enabled": False
                }
            }
        }
    }