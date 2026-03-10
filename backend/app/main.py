from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging

from app.config import settings
from app.routes import api_router

# Configure Logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
    )

    # Set all CORS enabled origins
    if settings.BACKEND_CORS_ORIGINS:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Include API Routes
    application.include_router(api_router, prefix=settings.API_V1_STR)

    # --- MOUNT FRONTEND (The Fix) ---
    import sys
    from pathlib import Path
    
    # This securely resolves the correct path when running via uvicorn directly or pyinstaller exe
    if hasattr(sys, '_MEIPASS'):
        frontend_path = os.path.join(sys._MEIPASS, "frontend")
    else:
        current_dir = os.path.dirname(os.path.realpath(__file__))
        frontend_path = os.path.join(current_dir, "../../frontend")
    
    # Mount the frontend to the root "/" so it loads index.html
    if os.path.exists(frontend_path):
        application.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
        logger.info(f"Frontend mounted successfully from {frontend_path}")
    else:
        logger.warning(f"Frontend directory not found at {frontend_path}")

    return application

app = create_application()