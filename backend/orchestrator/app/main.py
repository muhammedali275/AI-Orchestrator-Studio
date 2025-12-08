"""
ZainOne Orchestrator Studio - Main FastAPI Application

Entry point for the orchestration backend.
Uses Settings from config - NO hard-coded values.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .api.chat import router as chat_router
from .api.chat_ui import router as chat_ui_router
from .api.llm import router as llm_router
from .api.agents import router as agents_router
from .api.datasources import router as datasources_router
from .api.tools import router as tools_router
from .api.monitoring import router as monitoring_router
from .api.memory import router as memory_router
from .api.credentials import router as credentials_router
from .api.certificates import router as certificates_router
from .api.config_management import router as config_router
from .api.topology_execution import router as topology_router
from .api.files import router as files_router
from .api.api_keys import router as api_keys_router
from .db.database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    settings = get_settings()
    logger.info("=" * 80)
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info("=" * 80)
    
    # Initialize database tables
    db_initialized = False
    try:
        db_initialized = init_db()
        if db_initialized:
            # Seed default data if database is empty
            await seed_default_data()
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        logger.warning("⚠ Application will continue but database features may not work")
    
    # Validate component availability
    logger.info("\n" + "=" * 80)
    logger.info("Component Status:")
    logger.info("=" * 80)
    
    # Check LLM configuration
    if settings.llm_base_url:
        logger.info(f"✓ LLM Server: {settings.llm_base_url}")
        if settings.llm_default_model:
            logger.info(f"  └─ Default Model: {settings.llm_default_model}")
    else:
        logger.warning("✗ LLM Server: Not configured")
        logger.warning("  └─ Chat will not work without LLM configuration")
    
    # Check External Agent configuration
    if settings.external_agent_base_url:
        logger.info(f"✓ External Agent: {settings.external_agent_base_url}")
    else:
        logger.info("○ External Agent: Not configured (optional)")
    
    # Check Data Source configuration
    if settings.datasource_base_url:
        logger.info(f"✓ Data Source: {settings.datasource_base_url}")
    else:
        logger.info("○ Data Source: Not configured (optional)")
    
    # Check Database
    if db_initialized:
        logger.info("✓ Database: Initialized")
    else:
        logger.warning("✗ Database: Failed to initialize")
    
    # Check Redis
    if settings.get_redis_url():
        logger.info(f"✓ Redis: {settings.redis_host}:{settings.redis_port}")
    else:
        logger.info("○ Redis: Not configured (using in-memory cache)")
    
    # Check Tools
    tool_count = len(settings.tools)
    if tool_count > 0:
        logger.info(f"✓ Tools: {tool_count} configured")
    else:
        logger.info("○ Tools: None configured (optional)")
    
    logger.info("=" * 80)
    logger.info("Application started successfully!")
    logger.info(f"API available at: http://{settings.api_host}:{settings.api_port}")
    logger.info(f"Documentation: http://{settings.api_host}:{settings.api_port}/docs")
    logger.info("=" * 80 + "\n")
    
    yield
    
    logger.info("Shutting down application")


async def seed_default_data():
    """Seed default data into database if empty."""
    from .db.database import SessionLocal
    from .db.models import PromptProfile
    
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


# Create FastAPI app
app = FastAPI(
    title="AI Orchestrator Studio",
    description="Modular orchestration backend with graph-based execution flow",
    version="1.0.0",
    lifespan=lifespan
)

# Get settings
settings = get_settings()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router)
app.include_router(chat_ui_router)
app.include_router(llm_router)
app.include_router(agents_router)
app.include_router(datasources_router)
app.include_router(tools_router)
app.include_router(monitoring_router)
app.include_router(memory_router)
app.include_router(credentials_router)
app.include_router(certificates_router)
app.include_router(config_router)
app.include_router(topology_router)
app.include_router(files_router)
app.include_router(api_keys_router)

# Ensure chat_ui_router is registered
from app.api.chat_ui import router as chat_ui_router_direct
app.include_router(chat_ui_router_direct)


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns application status and configuration info.
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug,
        "llm_configured": settings.llm_base_url is not None,
        "external_agent_configured": settings.external_agent_base_url is not None,
        "redis_configured": settings.get_redis_url() is not None,
        "postgres_configured": settings.get_postgres_dsn() is not None,
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Orchestrator Studio API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
        "chat": "/v1/chat"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
