import logging
from fastapi import APIRouter
from app.routes import extract, decrypt, healthcheck

# Initialize the main API router
api_router = APIRouter()

# Register sub-routers for specific functional areas
# Prefix: /api/v1/extract
api_router.include_router(
    extract.router, 
    prefix="/extract", 
    tags=["Extraction"]
)

# Prefix: /api/v1/decrypt
api_router.include_router(
    decrypt.router, 
    prefix="/decrypt", 
    tags=["Decryption"]
)

# Prefix: /api/v1/health
api_router.include_router(
    healthcheck.router, 
    prefix="/health", 
    tags=["System"]
)

logger = logging.getLogger(__name__)
logger.info("Routes initialized and registered.")