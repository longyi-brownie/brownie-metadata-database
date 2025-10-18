"""Main application entry point for Brownie Metadata Database."""

import sys
import os
from contextlib import asynccontextmanager

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from database.connection import get_database_manager
from database.models import Organization, Team, User, Incident, AgentConfig, Stats
from app_logging.setup import configure_logging, get_logger
from metrics.setup import configure_metrics
from backup.config import BackupConfig
from backup.api import create_backup_router


# Configure logging
configure_logging()
logger = get_logger(__name__)

# Configure metrics
metrics_collector = configure_metrics()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Brownie Metadata Database service")
    
    # Initialize database
    db_manager = get_database_manager()
    try:
        db_manager.create_engine()
        logger.info("Database connection established")
    except Exception as e:
        logger.error("Failed to connect to database", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Brownie Metadata Database service")
    db_manager.close()


# Create FastAPI app
app = FastAPI(
    title="Brownie Metadata Database",
    description="Enterprise metadata database service for Brownie incident assistant",
    version="0.1.0",
    lifespan=lifespan
)

# Add backup API router
backup_config = BackupConfig.from_env()
backup_router = create_backup_router(backup_config)
app.include_router(backup_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "brownie-metadata-db"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    metrics_data = metrics_collector.get_metrics()
    return PlainTextResponse(metrics_data, media_type=CONTENT_TYPE_LATEST)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Brownie Metadata Database",
        "version": "0.1.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
