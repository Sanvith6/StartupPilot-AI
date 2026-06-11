"""
StartupPilot AI — Backend Entrypoint

Initializes the FastAPI application, configures CORS, mounts endpoints,
and handles lifespan startup/shutdown events.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import router
from config import get_settings, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
from workflows.graph_runner import load_active_analyses_backup


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events handler for the FastAPI application."""
    logger.info("Initializing StartupPilot AI Backend...")
    
    # Ensure all directories exist
    ensure_directories()
    logger.info("Data directories verified and created.")
    
    # Load backup of active analyses
    load_active_analyses_backup()
    
    yield
    
    logger.info("Shutting down StartupPilot AI Backend...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="StartupPilot AI API",
        description="Enterprise-ready Multi-Agent Startup Intelligence Platform",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Configure CORS (Cross-Origin Resource Sharing)
    # Allows frontend (Streamlit) to talk to the backend API
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify actual origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include application routes
    app.include_router(router)
    
    logger.info("FastAPI application configuration complete.")
    return app


app = create_app()
