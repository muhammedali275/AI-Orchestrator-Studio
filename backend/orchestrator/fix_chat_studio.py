"""
Fix Chat Studio API endpoints by ensuring database tables are created
and default data is seeded.
"""

import sys
import logging
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from app.db.database import init_db, SessionLocal
from app.db.models import Base, Conversation, Message, PromptProfile, ChatMetric, Credential

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_default_data():
    """Seed default data into database if empty."""
    try:
        db = SessionLocal()
        try:
            # Check if we have any prompt profiles
            existing_profiles = db.query(PromptProfile).count()
            
            if existing_profiles == 0:
                logger.info("Seeding default prompt profiles...")
                
                # Create default profiles
                default_profiles = [
                    {
                        "name": "General Assistant",
                        "description": "A helpful, harmless, and honest AI assistant",
                        "system_prompt": "You are a helpful AI assistant. Provide clear, accurate, and concise responses to user queries.",
                        "is_active": True
                    },
                    {
                        "name": "Code Assistant",
                        "description": "Specialized in programming and software development",
                        "system_prompt": "You are an expert programming assistant. Help users with code, debugging, and software development best practices.",
                        "is_active": True
                    },
                    {
                        "name": "Data Analyst",
                        "description": "Specialized in data analysis and insights",
                        "system_prompt": "You are a data analysis expert. Help users understand data, create queries, and derive insights.",
                        "is_active": True
                    }
                ]
                
                for profile_data in default_profiles:
                    profile = PromptProfile(**profile_data)
                    db.add(profile)
                
                db.commit()
                logger.info(f"✓ Seeded {len(default_profiles)} default prompt profiles")
            else:
                logger.info(f"✓ Found {existing_profiles} existing prompt profiles")
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error seeding default data: {str(e)}")

def create_tables_directly():
    """Create tables directly using SQLAlchemy."""
    try:
        from sqlalchemy import create_engine
        from app.db.database import DATABASE_URL
        
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("✓ Tables created directly")
        return True
    except Exception as e:
        logger.error(f"✗ Error creating tables directly: {str(e)}")
        return False

async def main():
    """Initialize database and seed default data."""
    logger.info("=" * 80)
    logger.info("CHAT STUDIO FIX")
    logger.info("=" * 80)
    
    # Initialize database
    db_initialized = False
    try:
        logger.info("Initializing database...")
        db_initialized = init_db()
        if db_initialized:
            logger.info("✓ Database initialized successfully")
        else:
            logger.warning("✗ Database initialization failed, trying direct table creation")
            db_initialized = create_tables_directly()
    except Exception as e:
        logger.error(f"✗ Error initializing database: {str(e)}")
        logger.warning("Trying direct table creation...")
        db_initialized = create_tables_directly()
    
    if db_initialized:
        # Seed default data
        logger.info("Seeding default data...")
        await seed_default_data()
        
        logger.info("=" * 80)
        logger.info("✓ Chat Studio fix completed successfully")
        logger.info("=" * 80)
        return True
    else:
        logger.error("=" * 80)
        logger.error("✗ Failed to initialize database")
        logger.error("=" * 80)
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
