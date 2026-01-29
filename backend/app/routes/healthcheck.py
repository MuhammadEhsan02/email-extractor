import logging
import platform
import shutil
from datetime import datetime
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

# Initialize Router
router = APIRouter()
logger = logging.getLogger(__name__)

# Track startup time
START_TIME = datetime.now()

@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="System Health Check",
    description="Returns the operational status of the Email Extraction System."
)
async def health_check():
    """
    Simple health check endpoint for monitoring tools (e.g., Docker healthcheck).
    """
    uptime = datetime.now() - START_TIME
    
    # Check disk space (critical for file generation)
    total, used, free = shutil.disk_usage("/")
    free_mb = free // (1024 * 1024)
    
    health_status = {
        "status": "healthy",
        "service": "Email Extraction System",
        "timestamp": datetime.now().isoformat(),
        "uptime": str(uptime),
        "system_info": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "disk_free_mb": free_mb
        },
        "components": {
            "api": "operational",
            # Future: Add checks for DB or Proxy connection here
            "storage": "writable" if free_mb > 500 else "critical"
        }
    }

    # If disk space is critically low, return 503
    if free_mb < 100:
        logger.critical("System running out of disk space!")
        health_status["status"] = "unhealthy"
        health_status["components"]["storage"] = "full"
        return JSONResponse(
            content=health_status, 
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    return health_status