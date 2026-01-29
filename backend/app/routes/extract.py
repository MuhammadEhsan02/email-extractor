import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, status, Depends
from typing import Dict, Any

# Import Schemas
from app.models.extract_request import ExtractRequest
from app.models.extract_response import ExtractResponse

# Import Service
from app.services.extraction_service import ExtractionService

# Initialize Router
router = APIRouter()
logger = logging.getLogger(__name__)

@router.post(
    "/",
    response_model=ExtractResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Initiate Email Extraction",
    description="Accepts text or URLs, extracts emails from target websites, and returns a job ID."
)
async def extract_emails(
    request: ExtractRequest,
    background_tasks: BackgroundTasks,
    service: ExtractionService = Depends(ExtractionService)
):
    """
    Main extraction endpoint.
    """
    try:
        logger.info(f"Received extraction request. Mode: {request.mode}")

        if not request.input_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Input data cannot be empty."
            )

        job_id = await service.create_job(request)
        
        # Add the heavy processing to background tasks
        background_tasks.add_task(service.process_extraction, job_id, request)

        logger.info(f"Job {job_id} queued successfully.")

        return ExtractResponse(
            job_id=job_id,
            status="queued",
            message="Extraction started in the background."
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error in extraction route: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing the request."
        )

# --- THIS WAS MISSING BEFORE ---
@router.get(
    "/{job_id}",
    status_code=status.HTTP_200_OK,
    summary="Get Job Status",
    description="Polls the status of a specific extraction job."
)
async def get_job_status(
    job_id: str,
    service: ExtractionService = Depends(ExtractionService)
) -> Dict[str, Any]:
    """
    Returns the current status and results (if ready) of a job.
    """
    job = service.get_job_status(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found."
        )
    
    # We return the dictionary directly so the frontend can access 
    # dynamic fields like 'result_summary' and 'passphrase'
    return job