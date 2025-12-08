"""
Database connection and session management.

Provides SQLAlchemy engine and session factory for credential storage.
"""

import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from ..config import get_settings

logger = logging.getLogger(__name__)

# Get database URL from settings
settings = get_settings()
DATABASE_URL = settings.get_postgres_dsn()

# If no PostgreSQL configured, use SQLite for credentials
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./credentials.db"
    logger.warning("No PostgreSQL configured, using SQLite for credential storage")
    # SQLite specific configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
else:
    # PostgreSQL configuration
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database session.
    
    Yields:
        Database session
        
    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # Use db session
            pass
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> bool:
    """
    Initialize database tables.
    
    Creates all tables defined in models if they don't exist.
    Should be called on application startup.
    
    Returns:
        True if initialization was successful, False otherwise
    """
    from .models import Base
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Verify tables were created by checking if we can query them
        db = SessionLocal()
        try:
            # Try to query each table to verify it exists
            from .models import Credential, Conversation, Message, PromptProfile, ChatMetric
            db.query(Credential).first()
            db.query(Conversation).first()
            db.query(Message).first()
            db.query(PromptProfile).first()
            db.query(ChatMetric).first()
            
            logger.info("✓ Database tables initialized and verified successfully")
            logger.info(f"✓ Using database: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
            return True
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"✗ Error initializing database: {str(e)}")
        logger.warning("⚠ Application will continue but database features may not work")
        return False
