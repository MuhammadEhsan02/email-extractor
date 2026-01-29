import logging
import sys
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import Configuration
from app.config import settings

# Import Routes
from app.routes import api_router

# --- 1. Logging Configuration ---
# Configure the root logger to write to both Console and File
logger = logging.getLogger()
logger.setLevel(settings.LOG_LEVEL)

# Formatter: timestamp - module - level - message
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Handler A: Console (stdout)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# Handler B: File (backend/app/logs/app.log)
file_handler = logging.FileHandler(settings.LOG_FILE)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


# --- 2. Application Factory ---
def create_application() -> FastAPI:
    """
    Initialize and configure the FastAPI application.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        description="Secure, internal-only email extraction tool."
    )

    # --- Middleware: CORS ---
    # Required for the frontend to fetch data from the backend
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # --- Middleware: Process Timer (Optional but useful for debugging) ---
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

    # --- Register Routes ---
    # Includes /extract, /decrypt, /health under /api/v1
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app

# Create the app instance
app = create_application()

# --- 3. Lifecycle Events ---
@app.on_event("startup")
async def startup_event():
    """
    Executed when the server starts.
    """
    logging.info("--- Email Extraction System Starting Up ---")
    logging.info(f"Storage Root: {settings.STORAGE_DIR}")
    logging.info(f"Logs Path:    {settings.LOG_FILE}")
    logging.info("System Ready.")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Executed when the server shuts down.
    """
    logging.info("--- Email Extraction System Shutting Down ---")

# --- Root Endpoint (Sanity Check) ---
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Email Extraction System API is running.",
        "docs": f"{settings.API_V1_STR}/docs"
    }