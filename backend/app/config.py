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
    # PyInstaller Path Resolution
    # When frozen, files are extracted to sys._MEIPASS.
    # Otherwise, we use the normal development structure.
    @property
    def BASE_DIR(self) -> Path:
        import sys
        if hasattr(sys, '_MEIPASS'):
            return Path(sys._MEIPASS)
        return Path(__file__).resolve().parent
    
    # Store settings in a persistent user directory when frozen
    @property
    def USER_DATA_DIR(self) -> Path:
        import sys
        if hasattr(sys, '_MEIPASS'):
            return Path.home() / ".email-extractor-tool"
        return self.BASE_DIR

    # backend/app/storage/
    @property
    def STORAGE_DIR(self) -> Path:
        return self.USER_DATA_DIR / "storage"
    
    # backend/app/storage/temp_html/
    @property
    def TEMP_HTML_DIR(self) -> Path:
        return self.STORAGE_DIR / "temp_html"
    
    # backend/app/storage/encrypted_files/
    @property
    def ENCRYPTED_DIR(self) -> Path:
        return self.STORAGE_DIR / "encrypted_files"
    
    # backend/app/storage/decrypted_files/ (Internal Use Only)
    @property
    def DECRYPTED_DIR(self) -> Path:
        return self.STORAGE_DIR / "decrypted_files"
    
    # backend/app/logs/
    @property
    def LOG_DIR(self) -> Path:
        return self.USER_DATA_DIR / "logs"

    @property
    def LOG_FILE(self) -> Path:
        return self.LOG_DIR / "app.log"
    
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