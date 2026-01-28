"""Main FastAPI application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.routes import auth, conversations, transactions, prices, audio_cleanup, data_export, account_deletion, feedback
from app.middleware.security import (
    HTTPSRedirectMiddleware,
    SecurityHeadersMiddleware,
    TLSVersionCheckMiddleware
)
from app.services.audio_storage import AudioStorageService
from app.services.audio_storage.audio_cleanup_scheduler import (
    initialize_scheduler,
    get_scheduler
)
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting up application...")
    
    # Initialize audio storage service
    audio_storage = AudioStorageService(storage_path=settings.AUDIO_STORAGE_PATH)
    
    # Initialize and start audio cleanup scheduler
    scheduler = initialize_scheduler(
        storage_service=audio_storage,
        retention_hours=settings.AUDIO_RETENTION_HOURS,
        cleanup_interval_hours=settings.AUDIO_CLEANUP_INTERVAL_HOURS
    )
    await scheduler.start()
    logger.info("Audio cleanup scheduler started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    # Stop audio cleanup scheduler
    scheduler = get_scheduler()
    if scheduler:
        await scheduler.stop()
        logger.info("Audio cleanup scheduler stopped")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# Add security middleware (order matters - first added is outermost)
# 1. HTTPS redirect (outermost - redirects HTTP to HTTPS)
app.add_middleware(
    HTTPSRedirectMiddleware,
    enabled=not settings.DEBUG  # Disable in development
)

# 2. TLS version check (for monitoring)
app.add_middleware(TLSVersionCheckMiddleware)

# 3. Security headers (adds HSTS and other security headers)
app.add_middleware(
    SecurityHeadersMiddleware,
    hsts_enabled=not settings.DEBUG  # Enable HSTS in production only
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(conversations.router, prefix=settings.API_PREFIX)
app.include_router(transactions.router, prefix=settings.API_PREFIX)
app.include_router(prices.router, prefix=settings.API_PREFIX)
app.include_router(audio_cleanup.router, prefix=settings.API_PREFIX)
app.include_router(data_export.router, prefix=settings.API_PREFIX)
app.include_router(account_deletion.router, prefix=settings.API_PREFIX)
app.include_router(feedback.router, prefix=settings.API_PREFIX)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
