"""
Main application entry point for AIpanel.

Initializes FastAPI app and includes all routers.
"""

import logging
import os
from typing import Dict, Any

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .config import get_settings
from .db.session import get_db, init_db
from .security import get_current_user, User
from .api.routes_chat import router as chat_router
from .api.routes_topology import router as topology_router
from .api.routes_config import router as config_router
from .api.routes_certs import router as certs_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="AIpanel",
    description="Enterprise AI Orchestrator",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router)
app.include_router(topology_router)
app.include_router(config_router)
app.include_router(certs_router)


@app.on_event("startup")
async def startup_event():
    """
    Startup event handler.
    
    Initializes database and other resources.
    """
    logger.info("Starting AIpanel...")
    
    # Initialize database
    init_db()
    
    logger.info(f"AIpanel started on port {settings.AIPANEL_PORT}")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event handler.
    
    Cleans up resources.
    """
    logger.info("Shutting down AIpanel...")


@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
    }


@app.get("/api/me")
async def get_current_user_info(
    user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current user information.
    
    Args:
        user: Authenticated user
        
    Returns:
        User information
    """
    return {
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "scopes": user.scopes,
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler.
    
    Args:
        request: Request
        exc: Exception
        
    Returns:
        Error response
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred",
            "error": str(exc),
        },
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.AIPANEL_PORT,
        reload=settings.DEBUG,
        ssl_keyfile=settings.TLS_KEY_PATH if settings.TLS_ENABLED else None,
        ssl_certfile=settings.TLS_CERT_PATH if settings.TLS_ENABLED else None,
    )
