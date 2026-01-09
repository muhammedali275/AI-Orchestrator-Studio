"""
Database models for AIpanel.

Defines SQLAlchemy models for all required tables.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, 
    String, Text, JSON, Table, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# Association tables for many-to-many relationships
agent_tool_association = Table(
    "agent_tool_association",
    Base.metadata,
    Column("agent_id", String(36), ForeignKey("agents.id")),
    Column("tool_id", String(36), ForeignKey("tools.id"))
)


class LLMConnection(Base):
    """
    LLM connection configuration.
    
    Stores connection details for external LLM providers.
    """
    __tablename__ = "llm_connections"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True)
    provider = Column(String(50), nullable=False)  # openai, anthropic, ollama, etc.
    base_url = Column(String(255), nullable=True)
    api_key = Column(String(255), nullable=True)
    default_model = Column(String(100), nullable=True)
    
    # Additional configuration
    config = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    agents = relationship("Agent", back_populates="llm_connection")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "base_url": self.base_url,
            "default_model": self.default_model,
            "config": self.config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Tool(Base):
    """
    Tool configuration.
    
    Stores tool definitions and configurations.
    """
    __tablename__ = "tools"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True)
    type = Column(String(50), nullable=False)  # http, cubejs, web_search, etc.
    description = Column(Text, nullable=True)
    
    # Tool-specific configuration
    config = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    agents = relationship(
        "Agent",
        secondary=agent_tool_association,
        back_populates="tools"
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "config": self.config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Agent(Base):
    """
    Agent configuration.
    
    Stores agent definitions, system prompts, and configurations.
    """
    __tablename__ = "agents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=False)
    
    # LLM connection
    llm_connection_id = Column(String(36), ForeignKey("llm_connections.id"), nullable=True)
    
    # Agent-specific configuration
    router_config = Column(JSON, nullable=True)
    planner_config = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    llm_connection = relationship("LLMConnection", back_populates="agents")
    tools = relationship(
        "Tool",
        secondary=agent_tool_association,
        back_populates="agents"
    )
    chat_sessions = relationship("ChatSession", back_populates="agent")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "llm_connection_id": self.llm_connection_id,
            "router_config": self.router_config,
            "planner_config": self.planner_config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "tools": [tool.to_dict() for tool in self.tools] if self.tools else []
        }


class Credential(Base):
    """
    Credential storage.
    
    Securely stores authentication credentials for external services.
    """
    __tablename__ = "credentials"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True)
    type = Column(String(50), nullable=False)  # api_key, oauth, basic_auth, etc.
    
    # Credential data (encrypted in production)
    data = Column(JSON, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    datasources = relationship("DataSource", back_populates="credential")
    
    def to_dict(self, include_data: bool = False) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Args:
            include_data: Whether to include sensitive credential data
        """
        result = {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_data:
            result["data"] = self.data
        
        return result


class DataSource(Base):
    """
    Data source configuration.
    
    Stores connection details for external data sources.
    """
    __tablename__ = "datasources"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True)
    type = Column(String(50), nullable=False)  # cubejs, postgres, api, etc.
    url = Column(String(255), nullable=False)
    
    # Credential reference
    credential_id = Column(String(36), ForeignKey("credentials.id"), nullable=True)
    
    # Additional configuration
    config = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    credential = relationship("Credential", back_populates="datasources")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "url": self.url,
            "credential_id": self.credential_id,
            "config": self.config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class ChatSession(Base):
    """
    Chat session.
    
    Stores metadata for chat conversations.
    """
    __tablename__ = "chat_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=True)
    user_id = Column(String(255), nullable=True, index=True)
    
    # Agent reference
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=True)
    
    # Session metadata (renamed from 'metadata' to avoid SQLAlchemy reserved word)
    session_metadata = Column("metadata", JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    agent = relationship("Agent", back_populates="chat_sessions")
    messages = relationship("Message", back_populates="chat_session", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "metadata": self.session_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "message_count": len(self.messages) if self.messages else 0
        }


class Message(Base):
    """
    Chat message.
    
    Stores individual messages in chat sessions.
    """
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Chat session reference
    chat_session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False)
    
    # Message content
    role = Column(String(50), nullable=False)  # user, assistant, system, tool
    content = Column(Text, nullable=False)
    
    # Message metadata (renamed from 'metadata' to avoid SQLAlchemy reserved word)
    message_metadata = Column("metadata", JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    chat_session = relationship("ChatSession", back_populates="messages")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "chat_session_id": self.chat_session_id,
            "role": self.role,
            "content": self.content,
            "metadata": self.message_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ServiceCheck(Base):
    """
    Service health check.
    
    Stores results of service health checks.
    """
    __tablename__ = "service_checks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    service_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)  # healthy, degraded, unhealthy
    
    # Check details
    details = Column(JSON, nullable=True)
    
    # Timestamps
    checked_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "service_name": self.service_name,
            "status": self.status,
            "details": self.details,
            "checked_at": self.checked_at.isoformat() if self.checked_at else None
        }
