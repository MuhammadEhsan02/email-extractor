import logging
import os
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import FileResponse
from pydantic import ValidationError

# Import Schemas
from app.models.decrypt_request import DecryptRequest

# Import Service
from app.services.encryption_service import EncryptionService
from app.services.file_service import FileService

# Initialize Router
router = APIRouter()
logger = logging.getLogger(__name__)

@router.post(
    "/",
    response_class=FileResponse,
    summary="Decrypt and Download File",
    description="Decrypts an encrypted output file and streams the result back to the user."
)
async def decrypt_file(
    request: DecryptRequest,
    encryption_service: EncryptionService = Depends(EncryptionService),
    file_service: FileService = Depends(FileService)
):
    """
    Decryption endpoint.
    
    Flow:
    1. Validate request (File ID + Passphrase/Key).
    2. Locate the encrypted file in storage.
    3. Perform AES-256 decryption.
    4. Stream the decrypted file to the client.
    """
    temp_decrypted_path = None
    
    try:
        logger.info(f"Decryption request received for File ID: {request.file_id}")

        # 1. Verify file existence
        encrypted_path = file_service.get_encrypted_file_path(request.file_id)
        if not os.path.exists(encrypted_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Encrypted file '{request.file_id}' not found."
            )

        # 2. Perform Decryption
        # Returns path to a temporary decrypted file
        temp_decrypted_path = encryption_service.decrypt_file(
            file_path=encrypted_path,
            passphrase=request.passphrase
        )

        if not temp_decrypted_path or not os.path.exists(temp_decrypted_path):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Decryption failed. Output file was not generated."
            )

        # 3. Determine filename for download (e.g., results.xlsx)
        filename = "extracted_contacts.xlsx"

        # 4. Return FileResponse
        # background=file_service.cleanup matches FastAPI's way to run code after response
        return FileResponse(
            path=temp_decrypted_path,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            background=file_service.create_cleanup_task(temp_decrypted_path)
        )

    except ValueError as ve:
        # Usually invalid passphrase or corrupted data
        logger.warning(f"Decryption validation error: {str(ve)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Decryption failed. Invalid passphrase or corrupted file."
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Critical error during decryption: {str(e)}", exc_info=True)
        # Attempt immediate cleanup if error occurred
        if temp_decrypted_path and os.path.exists(temp_decrypted_path):
            os.remove(temp_decrypted_path)
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while decrypting the file."
        )