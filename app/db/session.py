"""
Database connection and session management.

Provides SQLAlchemy engine and session factory.
"""

import logging
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from ..config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Create SQLAlchemy engine
engine = create_engine(
    settings.DB_CONNECTION_STRING,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=settings.DEBUG
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Get database session.
    
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
    Initialize database.
    
    Creates all tables defined in models.
    
    Returns:
        True if successful, False otherwise
    """
    from .models import Base
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Verify tables were created
        db = SessionLocal()
        try:
            # Try to query each table to verify it exists
            from .models import (
                LLMConnection, Tool, Agent, Credential,
                DataSource, ChatSession, Message, ServiceCheck
            )
            
            db.query(LLMConnection).first()
            db.query(Tool).first()
            db.query(Agent).first()
            db.query(Credential).first()
            db.query(DataSource).first()
            db.query(ChatSession).first()
            db.query(Message).first()
            db.query(ServiceCheck).first()
            
            logger.info("✓ Database tables initialized and verified successfully")
            logger.info(f"✓ Using database: {settings.DB_CONNECTION_STRING}")
            return True
        finally:
            db.close()
    except Exception as e:
        logger.error(f"✗ Error initializing database: {str(e)}")
        logger.warning("⚠ Application will continue but database features may not work")
        return False
