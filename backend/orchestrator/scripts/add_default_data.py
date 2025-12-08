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
