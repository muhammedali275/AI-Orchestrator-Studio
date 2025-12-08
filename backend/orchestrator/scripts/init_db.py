import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.db.database import init_db
from app.db.models import Base, Conversation, Message, PromptProfile, ChatMetric, Credential
from app.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Initialize database tables and verify they exist."""
    logger.info("Starting database initialization...")
    
    # Initialize database
    success = init_db()
    
    if success:
        logger.info("✓ Database initialized successfully")
        logger.info("✓ The following tables are available:")
        logger.info("  - conversations")
        logger.info("  - messages")
        logger.info("  - prompt_profiles")
        logger.info("  - chat_metrics")
        logger.info("  - credentials")
    else:
        logger.error("✗ Database initialization failed")
        logger.info("Trying to create tables directly...")
        
        try:
            from sqlalchemy import create_engine
            from app.db.database import DATABASE_URL
            
            # Create engine
            engine = create_engine(DATABASE_URL)
            
            # Create tables
            Base.metadata.create_all(bind=engine)
            
            logger.info("✓ Tables created directly")
        except Exception as e:
            logger.error(f"✗ Error creating tables directly: {str(e)}")
            logger.error("Please check your database configuration")
            return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
