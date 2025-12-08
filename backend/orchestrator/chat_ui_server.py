"""
Standalone Chat UI API server.

This script creates a standalone FastAPI server for the Chat UI API endpoints.
"""

import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat_ui import router as chat_ui_router
from app.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Chat Studio API",
    description="API for Chat Studio",
    version="1.0.0"
)

# Get settings
settings = get_settings()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include router
app.include_router(chat_ui_router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Chat Studio API",
        "version": "1.0.0",
        "endpoints": [
            "/api/chat/ui/conversations",
            "/api/chat/ui/profiles",
            "/api/chat/ui/models"
        ]
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Chat Studio API"
    }

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("CHAT STUDIO API SERVER")
    logger.info("=" * 80)
    
    # Print all available routes
    logger.info("Available routes:")
    for route in app.routes:
        logger.info(f"  {route.path} [{','.join(getattr(route, 'methods', []))}]")
    
    logger.info("=" * 80)
    logger.info("Starting server...")
    logger.info("=" * 80)
    
    # Run server
    uvicorn.run(
        "chat_ui_server:app",
        host="0.0.0.0",
        port=8001,  # Use a different port to avoid conflicts
        reload=True
    )
