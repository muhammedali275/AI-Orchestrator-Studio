"""
Database initialization script for AIpanel.

This script initializes the database with default data.
"""

import logging
import os
import sys
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy.orm import Session

from app.db.models import Base, LLMConnection, Tool, Agent, Credential, DataSource, ChatSession
from app.db.session import engine, SessionLocal
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def init_db() -> None:
    """
    Initialize database.
    
    Creates tables and adds default data.
    """
    logger.info("Initializing database...")
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Add default data
    add_default_data()
    
    logger.info("Database initialized successfully")


def add_default_data() -> None:
    """Add default data to database."""
    db = SessionLocal()
    
    try:
        # Add default LLM connection
        add_default_llm_connections(db)
        
        # Add default tools
        add_default_tools(db)
        
        # Add default agents
        add_default_agents(db)
        
        # Add default credentials
        add_default_credentials(db)
        
        # Add default data sources
        add_default_datasources(db)
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Error adding default data: {str(e)}")
        db.rollback()
        raise
    
    finally:
        db.close()


def add_default_llm_connections(db: Session) -> None:
    """
    Add default LLM connections.
    
    Args:
        db: Database session
    """
    # Check if connections already exist
    if db.query(LLMConnection).count() > 0:
        logger.info("LLM connections already exist, skipping...")
        return
    
    # Add default connections
    connections = [
        LLMConnection(
            name="OpenAI",
            provider="openai",
            base_url="https://api.openai.com/v1",
            api_key=settings.LLM_API_KEY,
            default_model="gpt-4",
            config={
                "timeout": 60,
                "max_retries": 3
            }
        ),
        LLMConnection(
            name="Ollama",
            provider="ollama",
            base_url="http://localhost:11434",
            default_model="llama2",
            config={
                "timeout": 120,
                "max_retries": 2
            }
        ),
        LLMConnection(
            name="Local LLM",
            provider="local",
            base_url="http://localhost:8080",
            default_model="mistral",
            config={
                "timeout": 300,
                "max_retries": 1
            }
        )
    ]
    
    for connection in connections:
        db.add(connection)
    
    logger.info(f"Added {len(connections)} default LLM connections")


def add_default_tools(db: Session) -> None:
    """
    Add default tools.
    
    Args:
        db: Database session
    """
    # Check if tools already exist
    if db.query(Tool).count() > 0:
        logger.info("Tools already exist, skipping...")
        return
    
    # Add default tools
    tools = [
        Tool(
            name="cubejs_tool",
            type="data_query",
            description="Query Cube.js for analytics data",
            config={
                "timeout": 30,
                "max_retries": 3
            }
        ),
        Tool(
            name="http_tool",
            type="web",
            description="Make HTTP requests to external APIs",
            config={
                "timeout": 30,
                "max_retries": 3
            }
        ),
        Tool(
            name="churn_query_tool",
            type="specialized",
            description="Query for top contracts by churn rate",
            config={
                "timeout": 30,
                "max_retries": 3
            }
        )
    ]
    
    for tool in tools:
        db.add(tool)
    
    logger.info(f"Added {len(tools)} default tools")


def add_default_agents(db: Session) -> None:
    """
    Add default agents.
    
    Args:
        db: Database session
    """
    # Check if agents already exist
    if db.query(Agent).count() > 0:
        logger.info("Agents already exist, skipping...")
        return
    
    # Get default LLM connection
    llm_connection = db.query(LLMConnection).filter(
        LLMConnection.name == "OpenAI"
    ).first()
    
    # Get tools
    tools = db.query(Tool).all()
    
    # Add default agents
    agents = [
        Agent(
            name="zain_agent",
            description="Default agent for general queries",
            system_prompt=(
                "You are a helpful AI assistant that provides accurate and useful information. "
                "Answer questions directly and concisely. "
                "If you don't know something, admit it rather than making up information."
            ),
            llm_connection_id=llm_connection.id if llm_connection else None,
            router_config={
                "default_route": "llm_agent",
                "routes": {
                    "data_query": "tool_executor",
                    "churn_analytics": "tool_executor"
                }
            },
            planner_config={
                "enabled": True,
                "max_iterations": 5
            },
            tools=tools
        ),
        Agent(
            name="data_agent",
            description="Specialized agent for data queries",
            system_prompt=(
                "You are a data analysis assistant that helps users understand their data. "
                "Focus on providing clear insights and visualizations. "
                "Always cite the source of your data."
            ),
            llm_connection_id=llm_connection.id if llm_connection else None,
            router_config={
                "default_route": "tool_executor",
                "routes": {
                    "general_query": "llm_agent"
                }
            },
            planner_config={
                "enabled": True,
                "max_iterations": 10
            },
            tools=tools
        )
    ]
    
    for agent in agents:
        db.add(agent)
    
    logger.info(f"Added {len(agents)} default agents")


def add_default_credentials(db: Session) -> None:
    """
    Add default credentials.
    
    Args:
        db: Database session
    """
    # Check if credentials already exist
    if db.query(Credential).count() > 0:
        logger.info("Credentials already exist, skipping...")
        return
    
    # Add default credentials
    credentials = [
        Credential(
            name="cubejs_api_key",
            type="api_key",
            secret=str({
                "header_name": "Authorization",
                "key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiZXhhbXBsZSJ9.example"
            })
        ),
        Credential(
            name="http_basic_auth",
            type="basic_auth",
            secret=str({
                "username": "example_user",
                "password": "example_password"
            })
        )
    ]
    
    for credential in credentials:
        db.add(credential)
    
    logger.info(f"Added {len(credentials)} default credentials")


def add_default_datasources(db: Session) -> None:
    """
    Add default data sources.
    
    Args:
        db: Database session
    """
    # Check if data sources already exist
    if db.query(DataSource).count() > 0:
        logger.info("Data sources already exist, skipping...")
        return
    
    # Get credentials
    cubejs_credential = db.query(Credential).filter(
        Credential.name == "cubejs_api_key"
    ).first()
    
    # Add default data sources
    datasources = [
        DataSource(
            name="cubejs_main",
            type="cubejs",
            url="http://localhost:4000",
            credential_id=cubejs_credential.id if cubejs_credential else None,
            config={
                "timeout": 30,
                "max_retries": 3
            }
        )
    ]
    
    for datasource in datasources:
        db.add(datasource)
    
    logger.info(f"Added {len(datasources)} default data sources")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Initialize database
    init_db()
