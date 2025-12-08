"""
Test script for API endpoints.
"""

import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

def test_endpoint(endpoint, expected_status=200):
    """Test an API endpoint."""
    url = f"{BASE_URL}{endpoint}"
    logger.info(f"Testing endpoint: {url}")
    
    try:
        response = requests.get(url)
        status = response.status_code
        
        if status == expected_status:
            logger.info(f"✓ Success: {status}")
            try:
                data = response.json()
                logger.info(f"Response: {json.dumps(data, indent=2)}")
            except:
                logger.info(f"Response: {response.text[:100]}...")
            return True
        else:
            logger.error(f"✗ Failed: {status}")
            logger.error(f"Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"✗ Error: {str(e)}")
        return False

def main():
    """Run all tests."""
    logger.info("=" * 80)
    logger.info("API ENDPOINT TEST")
    logger.info("=" * 80)
    
    # Test basic endpoints
    test_endpoint("/health")
    test_endpoint("/")
    test_endpoint("/docs")
    
    # Test file endpoints
    test_endpoint("/api/files/list")
    
    # Test chat UI endpoints
    test_endpoint("/api/chat/ui/conversations")
    test_endpoint("/api/chat/ui/profiles")
    test_endpoint("/api/chat/ui/models")
    
    # Test other endpoints
    test_endpoint("/api/llm/models")
    
    logger.info("=" * 80)
    logger.info("Test complete")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
