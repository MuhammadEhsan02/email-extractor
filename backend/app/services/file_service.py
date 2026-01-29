import os
import shutil
import logging
import uuid
from pathlib import Path
from typing import Optional, List
from datetime import datetime

# FIXED: Import 'settings' (lowercase) instead of 'SETTINGS'
from app.config import settings

logger = logging.getLogger(__name__)

class FileService:
    """
    Manages file storage, retrieval, and cleanup for the application.
    Enforces strict separation between temporary and encrypted storage.
    """

    def __init__(self):
        # Use paths from the centralized config
        self.temp_dir = settings.TEMP_HTML_DIR
        self.encrypted_dir = settings.ENCRYPTED_DIR
        self.decrypted_dir = settings.DECRYPTED_DIR

        # Ensure all directories exist
        self._ensure_directories()

    def _ensure_directories(self):
        """Creates necessary storage directories if they don't exist."""
        for directory in [self.temp_dir, self.encrypted_dir, self.decrypted_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def generate_file_id(self) -> str:
        """Generates a unique identifier for a file/job."""
        return str(uuid.uuid4())

    def get_temp_path(self, filename: str) -> str:
        """Returns full path for a temporary file."""
        return str(self.temp_dir / filename)

    def get_encrypted_file_path(self, file_id: str) -> str:
        """
        Resolves the path for an encrypted output file.
        Format: {file_id}.enc
        """
        return str(self.encrypted_dir / f"{file_id}.enc")

    def get_decrypted_file_path(self, file_id: str, original_extension: str = "csv") -> str:
        """
        Resolves the path for a decrypted file (internal use only).
        """
        return str(self.decrypted_dir / f"{file_id}_decrypted.{original_extension}")

    async def save_temp_content(self, content: str, filename: str) -> str:
        """Saves string content to a temporary file."""
        path = self.get_temp_path(filename)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return path
        except IOError as e:
            logger.error(f"Failed to save temp file {filename}: {e}")
            raise

    def cleanup_file(self, file_path: str):
        """Safely removes a file if it exists."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Cleaned up file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup file {file_path}: {e}")

    async def create_cleanup_task(self, file_path: str):
        """
        Callable for BackgroundTasks to clean up files after response is sent.
        """
        self.cleanup_file(file_path)

    def list_encrypted_files(self) -> List[str]:
        """Returns a list of all available encrypted file IDs."""
        return [f.stem for f in self.encrypted_dir.glob("*.enc")]