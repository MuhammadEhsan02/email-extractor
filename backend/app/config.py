import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Global Application Configuration.
    
    Reads values from environment variables (e.g., .env file) or uses defaults.
    Centralizes paths, security keys, and scraping constraints.
    """

    # --- Project Info ---
    PROJECT_NAME: str = "Email Extraction System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # --- Security ---
    # WARNING: In production, strictly set this via environment variable!
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev_secret_key_change_in_production")
    
    # CORS: Allow frontend to communicate with backend
    # In production, specify the exact frontend domain (e.g., ["http://internal-tool.local"])
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # --- Directory Hierarchy (Absolute Paths) ---
    # backend/app/
    BASE_DIR: Path = Path(__file__).resolve().parent
    
    # backend/app/storage/
    STORAGE_DIR: Path = BASE_DIR / "storage"
    
    # backend/app/storage/temp_html/
    TEMP_HTML_DIR: Path = STORAGE_DIR / "temp_html"
    
    # backend/app/storage/encrypted_files/
    ENCRYPTED_DIR: Path = STORAGE_DIR / "encrypted_files"
    
    # backend/app/storage/decrypted_files/ (Internal Use Only)
    DECRYPTED_DIR: Path = STORAGE_DIR / "decrypted_files"
    
    # backend/app/logs/
    LOG_DIR: Path = BASE_DIR / "logs"
    LOG_FILE: Path = LOG_DIR / "app.log"
    
    # --- Logging Settings ---
    LOG_LEVEL: str = "INFO"

    # --- Scraping & Extraction Limits (Safety Guardrails) ---
    # Maximum concurrent scraping tasks to prevent server overload
    MAX_CONCURRENT_TASKS: int = 5
    
    # Default timeout for a single HTTP request (seconds)
    DEFAULT_REQUEST_TIMEOUT: int = 30
    
    # Max size of a single page to download (10 MB)
    MAX_PAGE_SIZE_BYTES: int = 10 * 1024 * 1024
    
    # Global hard limit on pages per job to prevent runaway scraping
    MAX_TOTAL_PAGES_LIMIT: int = 100

    class Config:
        case_sensitive = True
        # Loads .env file if present
        env_file = ".env"

# Instantiate settings
settings = Settings()

# --- Initialization Logic ---
# Ensure all critical directories exist immediately upon startup
def ensure_directories():
    dirs = [
        settings.STORAGE_DIR,
        settings.TEMP_HTML_DIR,
        settings.ENCRYPTED_DIR,
        settings.DECRYPTED_DIR,
        settings.LOG_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

ensure_directories()