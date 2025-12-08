"""
Test script for Chat UI API endpoints.

This script directly tests the Chat UI API endpoints without going through the FastAPI app.
"""

import asyncio
import logging
from app.api.chat_ui import list_routing_profiles, list_models
from app.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_profiles():
    """Test the profiles endpoint."""
    logger.info("Testing profiles endpoint...")
    try:
        result = await list_routing_profiles()
        logger.info(f"Profiles result: {result}")
        return True
    except Exception as e:
        logger.error(f"Error testing profiles: {str(e)}")
        return False

async def test_models():
    """Test the models endpoint."""
    logger.info("Testing models endpoint...")
    try:
        settings = get_settings()
        result = await list_models(settings)
        logger.info(f"Models result: {result}")
        return True
    except Exception as e:
        logger.error(f"Error testing models: {str(e)}")
        return False

async def main():
    """Run all tests."""
    logger.info("=" * 80)
    logger.info("CHAT UI API TEST")
    logger.info("=" * 80)
    
    profiles_success = await test_profiles()
    models_success = await test_models()
    
    logger.info("=" * 80)
    logger.info(f"Profiles test: {'✓ Success' if profiles_success else '✗ Failed'}")
    logger.info(f"Models test: {'✓ Success' if models_success else '✗ Failed'}")
    logger.info("=" * 80)
    
    return profiles_success and models_success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
