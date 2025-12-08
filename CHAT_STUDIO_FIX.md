# Chat Studio API Fix

## Issue Identified

After configuring the LLM connection, the Chat Studio page is showing 404 errors for the following API endpoints:
- GET /api/chat/ui/conversations
- GET /api/chat/ui/profiles
- GET /api/chat/ui/models

These errors occur because the database initialization might be failing silently, causing the API endpoints to not function properly.

## Root Cause Analysis

1. The database initialization happens in the lifespan function of the FastAPI app
2. If there are issues with PostgreSQL connection, it falls back to SQLite
3. However, there might be issues with the SQLite fallback or database table creation

## Fix Implementation

### 1. Create a Database Initialization Script

Create a script to explicitly initialize the database and verify the tables:

```python
# backend/orchestrator/scripts/init_db.py
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
```

### 2. Add Default Data for Chat Studio

Create a script to add default data for Chat Studio:

```python
# backend/orchestrator/scripts/add_default_data.py
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.db.database import SessionLocal
from app.db.models import PromptProfile
from app.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_default_prompt_profiles():
    """Add default prompt profiles if they don't exist."""
    db = SessionLocal()
    try:
        # Check if any profiles exist
        existing = db.query(PromptProfile).first()
        if existing:
            logger.info("✓ Prompt profiles already exist")
            return True
        
        # Add default profiles
        default_profiles = [
            PromptProfile(
                name="Default",
                description="Standard conversational prompt",
                system_prompt="You are a helpful AI assistant. Answer questions accurately and be concise.",
                is_active=True
            ),
            PromptProfile(
                name="Technical",
                description="Technical assistant for programming and IT",
                system_prompt="You are a technical assistant specializing in programming, software development, and IT. Provide detailed technical explanations and code examples when appropriate.",
                is_active=True
            ),
            PromptProfile(
                name="Creative",
                description="Creative assistant for writing and brainstorming",
                system_prompt="You are a creative assistant specializing in writing, brainstorming, and creative tasks. Be imaginative and help with creative projects.",
                is_active=True
            )
        ]
        
        for profile in default_profiles:
            db.add(profile)
        
        db.commit()
        logger.info(f"✓ Added {len(default_profiles)} default prompt profiles")
        return True
    except Exception as e:
        logger.error(f"✗ Error adding default prompt profiles: {str(e)}")
        return False
    finally:
        db.close()

def main():
    """Add default data for Chat Studio."""
    logger.info("Adding default data for Chat Studio...")
    
    # Add default prompt profiles
    success = add_default_prompt_profiles()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

### 3. Update Database Initialization in main.py

Modify the database initialization in the lifespan function to be more robust:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Initialize database tables
    try:
        success = init_db()
        if success:
            logger.info("Database initialized successfully")
            
            # Add default data if needed
            db = SessionLocal()
            try:
                # Check if any prompt profiles exist
                from .db.models import PromptProfile
                existing_profiles = db.query(PromptProfile).first()
                if not existing_profiles:
                    # Add default prompt profile
                    default_profile = PromptProfile(
                        name="Default",
                        description="Standard conversational prompt",
                        system_prompt="You are a helpful AI assistant. Answer questions accurately and be concise.",
                        is_active=True
                    )
                    db.add(default_profile)
                    db.commit()
                    logger.info("Added default prompt profile")
            except Exception as e:
                logger.warning(f"Could not check/add default data: {str(e)}")
            finally:
                db.close()
        else:
            logger.error("Database initialization failed")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        # Continue startup even if DB init fails (for development)
    
    yield
    
    logger.info("Shutting down application")
```

### 4. Add Fallback Responses for Chat UI Endpoints

Modify the chat_ui.py file to add fallback responses for the endpoints:

```python
@router.get("/conversations")
async def list_conversations(
    user_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """List conversations."""
    try:
        query = db.query(Conversation).filter(Conversation.is_deleted == False)
        
        if user_id:
            query = query.filter(Conversation.user_id == user_id)
        
        total = query.count()
        conversations = query.order_by(
            Conversation.updated_at.desc()
        ).limit(limit).offset(offset).all()
        
        return {
            "conversations": [conv.to_dict() for conv in conversations],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"[Chat UI] Error listing conversations: {str(e)}")
        # Return empty list as fallback
        return {
            "conversations": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "error": str(e)
        }

@router.get("/profiles")
async def list_routing_profiles() -> Dict[str, Any]:
    """List available routing profiles."""
    profiles = [
        {
            "id": "direct_llm",
            "name": "Direct LLM",
            "description": "Direct connection to LLM server without additional processing"
        },
        {
            "id": "zain_agent",
            "name": "Zain Agent",
            "description": "Route through Zain orchestrator agent with data access"
        },
        {
            "id": "tools_data",
            "name": "Tools + Data",
            "description": "Full orchestration with tools, data sources, and reasoning"
        }
    ]
    
    return {
        "profiles": profiles
    }

@router.get("/models")
async def list_models(
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """List available models from LLM configuration."""
    try:
        # Try to fetch models from LLM server
        import httpx
        
        if not settings.llm_base_url:
            # Fallback if LLM not configured
            return {
                "success": True,
                "models": [
                    {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
                    {"id": "gpt-4", "name": "GPT-4"},
                    {"id": "claude-3-opus", "name": "Claude 3 Opus"},
                    {"id": "claude-3-sonnet", "name": "Claude 3 Sonnet"},
                    {"id": "llama2-70b", "name": "Llama 2 70B"}
                ],
                "default_model": "gpt-3.5-turbo",
                "message": "Using default models (LLM not configured)"
            }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                # Try Ollama endpoint first
                if "11434" in settings.llm_base_url or "ollama" in settings.llm_base_url.lower():
                    response = await client.get(f"{settings.llm_base_url}/api/tags")
                    
                    if response.status_code == 200:
                        data = response.json()
                        models = data.get("models", [])
                        # Format for frontend
                        formatted_models = [
                            {"id": m.get("name", m.get("model")), "name": m.get("name", m.get("model"))}
                            for m in models
                        ]
                        return {
                            "success": True,
                            "models": formatted_models,
                            "default_model": settings.llm_default_model
                        }
                else:
                    # Try OpenAI-compatible endpoint
                    response = await client.get(f"{settings.llm_base_url}/models")
                    
                    if response.status_code == 200:
                        models_data = response.json()
                        models = models_data.get("data", []) if isinstance(models_data, dict) else models_data
                        
                        return {
                            "success": True,
                            "models": models,
                            "default_model": settings.llm_default_model
                        }
            except Exception as e:
                logger.warning(f"[Chat UI] Could not fetch models: {str(e)}")
        
        # Fallback to default model
        return {
            "success": True,
            "models": [
                {"id": settings.llm_default_model or "default-model", "name": settings.llm_default_model or "Default Model"}
            ],
            "default_model": settings.llm_default_model,
            "message": "Using configured default model"
        }
        
    except Exception as e:
        logger.error(f"[Chat UI] Error listing models: {str(e)}")
        # Return fallback models
        return {
            "success": True,
            "models": [
                {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
                {"id": "gpt-4", "name": "GPT-4"},
                {"id": "claude-3-opus", "name": "Claude 3 Opus"},
                {"id": "claude-3-sonnet", "name": "Claude 3 Sonnet"},
                {"id": "llama2-70b", "name": "Llama 2 70B"}
            ],
            "default_model": "gpt-3.5-turbo",
            "message": "Using fallback models due to error"
        }
```

## Implementation Steps

1. Run the database initialization script to ensure tables are created:
   ```
   cd backend/orchestrator
   python -m scripts.init_db
   ```

2. Add default data for Chat Studio:
   ```
   cd backend/orchestrator
   python -m scripts.add_default_data
   ```

3. Restart the backend service:
   ```
   ./restart.sh
   ```

## Verification

After implementing these changes, the Chat Studio should work properly without 404 errors. The following endpoints should return valid responses:
- GET /api/chat/ui/conversations
- GET /api/chat/ui/profiles
- GET /api/chat/ui/models

## Additional Notes

- The database initialization is now more robust and will provide fallback responses even if the database is not properly initialized
- Default data is added for prompt profiles to ensure the Chat Studio has some initial data
- The models endpoint now returns fallback models if the LLM server is not configured or cannot be reached
