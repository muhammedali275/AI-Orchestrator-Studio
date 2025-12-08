"""
Register Chat UI router directly.

This script directly registers the chat_ui router with the FastAPI app.
"""

import logging
import asyncio
from fastapi import FastAPI
from app.api.chat_ui import router as chat_ui_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def register_router():
    """Register the chat_ui router with the FastAPI app."""
    from app.main import app
    
    # Check if the router is already registered
    for route in app.routes:
        if getattr(route, "tags", None) == ["chat-ui"]:
            logger.info("Chat UI router is already registered")
            return True
    
    # Register the router
    logger.info("Registering Chat UI router...")
    app.include_router(chat_ui_router)
    logger.info("Chat UI router registered successfully")
    
    # Print all available routes
    logger.info("Available routes:")
    for route in app.routes:
        logger.info(f"  {route.path} [{','.join(getattr(route, 'methods', []))}]")
    
    return True

def main():
    """Run the registration."""
    logger.info("=" * 80)
    logger.info("CHAT UI ROUTER REGISTRATION")
    logger.info("=" * 80)
    
    asyncio.run(register_router())
    
    logger.info("=" * 80)
    logger.info("Registration complete")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
