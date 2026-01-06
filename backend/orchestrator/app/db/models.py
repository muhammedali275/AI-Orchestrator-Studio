"""
Database models for exampleOne Orchestrator Studio.

Defines SQLAlchemy models for credential storage, conversations, messages, and chat metrics.
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Credential(Base):
    """
    Credential model for secure storage of authentication credentials.
    
    Supports multiple credential types:
    - ssh: SSH credentials (username + password or key)
    - http_basic: HTTP Basic Auth (username + password)
    - bearer_token: Bearer token authentication
    - db_dsn: Database connection string
    - api_key: API key authentication
    - custom: Custom credential type
    
    Security:
    - The 'secret' field MUST always be encrypted before storage
    - The 'secret' field MUST NEVER be returned in API responses
    - The 'extra' field MUST NOT contain sensitive data
    """
    __tablename__ = "credentials"
    
    # Primary key - use string UUID for SQLite compatibility
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Human-readable name/label
    name = Column(String(255), nullable=False, unique=True, index=True)
    
    # Credential type
    type = Column(String(50), nullable=False, index=True)
    # Valid types: ssh, http_basic, bearer_token, db_dsn, api_key, custom
    
    # Username (optional, depends on type)
    username = Column(String(255), nullable=True)
    
    # Encrypted secret (MUST be encrypted before storage)
    secret = Column(Text, nullable=False)
    
    # Additional metadata (JSON) - MUST NOT contain secrets
    # Examples: {"port": 22, "auth_method": "key", "host": "example.com"}
    extra = Column(JSON, nullable=True, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Active status
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    def __repr__(self) -> str:
        """String representation (NEVER include secret)."""
        return f"<Credential(id={self.id}, name={self.name}, type={self.type}, active={self.is_active})>"
    
    def to_dict(self, include_secret: bool = False) -> dict:
        """
        Convert to dictionary.
        
        Args:
            include_secret: If True, include encrypted secret (for internal use only)
            
        Returns:
            Dictionary representation
            
        Security:
            - By default, secret is NOT included
            - Even when included, it's the ENCRYPTED value, not plain text
            - NEVER use include_secret=True for API responses
        """
        data = {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "username": self.username,
            "extra": self.extra or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active
        }
        
        if include_secret:
            # Only include encrypted secret for internal use
            data["secret"] = self.secret
        
        return data
    
    def to_safe_dict(self) -> dict:
        """
        Convert to safe dictionary for API responses.
        
        Returns:
            Dictionary without any secret information
            
        Security:
            - NEVER includes secret field
            - Safe to return in API responses
        """
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "username": self.username,
            "extra": self.extra or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active
        }


class Conversation(Base):
    """
    Conversation model for Chat Studio.
    
    Stores conversation metadata and settings.
    """
    __tablename__ = "conversations"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Conversation metadata
    title = Column(String(255), nullable=False, default="New Conversation")
    user_id = Column(String(255), nullable=True, index=True)
    
    # Model and routing configuration
    model_id = Column(String(255), nullable=True)
    routing_profile = Column(String(50), nullable=False, default="direct_llm")
    # Valid routing profiles: direct_llm, example_agent, tools_data
    
    # Optional summary for quick display
    summary = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Soft delete
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    
    # Relationship to messages
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title={self.title}, routing_profile={self.routing_profile})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "user_id": self.user_id,
            "model_id": self.model_id,
            "routing_profile": self.routing_profile,
            "summary": self.summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_deleted": self.is_deleted,
            "message_count": len(self.messages) if self.messages else 0
        }


class Message(Base):
    """
    Message model for Chat Studio.
    
    Stores individual messages within conversations.
    """
    __tablename__ = "messages"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign key to conversation
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False, index=True)
    
    # Message content
    role = Column(String(50), nullable=False)
    # Valid roles: user, assistant, system, tool
    content = Column(Text, nullable=False)
    
    # Message metadata (JSON) - stores tool calls, tokens, latency, etc.
    # Note: Using 'message_metadata' instead of 'metadata' as 'metadata' is reserved in SQLAlchemy
    message_metadata = Column(JSON, nullable=True, default=dict)
    
    # Timestamp
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Relationship to conversation
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self) -> str:
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, role={self.role})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "metadata": self.message_metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class PromptProfile(Base):
    """
    Prompt Profile model for Chat Studio.
    
    Stores system prompts and profiles for different use cases.
    """
    __tablename__ = "prompt_profiles"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Profile metadata
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # System prompt
    system_prompt = Column(Text, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Active status
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    def __repr__(self) -> str:
        return f"<PromptProfile(id={self.id}, name={self.name}, active={self.is_active})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active
        }


class ChatMetric(Base):
    """
    Chat Metric model for monitoring and analytics.
    
    Stores metrics for each chat request.
    """
    __tablename__ = "chat_metrics"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign key to conversation (optional)
    conversation_id = Column(String(36), nullable=True, index=True)
    
    # Request metadata
    request_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    model_id = Column(String(255), nullable=True, index=True)
    routing_profile = Column(String(50), nullable=True, index=True)
    
    # Performance metrics
    latency_ms = Column(Float, nullable=True)
    tokens_in = Column(Integer, nullable=True)
    tokens_out = Column(Integer, nullable=True)
    
    # Status
    success = Column(Boolean, nullable=False, default=True, index=True)
    error_code = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Additional metric metadata
    # Note: Using 'metric_metadata' instead of 'metadata' as 'metadata' is reserved in SQLAlchemy
    metric_metadata = Column(JSON, nullable=True, default=dict)
    
    def __repr__(self) -> str:
        return f"<ChatMetric(id={self.id}, conversation_id={self.conversation_id}, success={self.success})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "request_timestamp": self.request_timestamp.isoformat() if self.request_timestamp else None,
            "model_id": self.model_id,
            "routing_profile": self.routing_profile,
            "latency_ms": self.latency_ms,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "success": self.success,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "metadata": self.metric_metadata or {}
        }
