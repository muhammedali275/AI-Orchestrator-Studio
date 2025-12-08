"""
Memory management for AIpanel.

Implements conversation memory and caching using LangChain.
"""

import logging
import json
import hashlib
from typing import Dict, Any, Optional, List, Tuple, Union

from langchain.memory import ConversationBufferMemory, ChatMessageHistory
from langchain.schema import BaseChatMessageHistory
from langchain.schema.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db.models import ChatSession, Message
from ..db.session import get_db

logger = logging.getLogger(__name__)
settings = get_settings()


class DatabaseChatMessageHistory(BaseChatMessageHistory):
    """
    Chat message history backed by database.
    
    Stores messages in the database for persistence.
    """
    
    def __init__(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ):
        """
        Initialize database chat message history.
        
        Args:
            session_id: Chat session ID
            user_id: User ID
            db: Database session
        """
        self.session_id = session_id
        self.user_id = user_id
        self.db = db
        self._chat_session = None
    
    async def _ensure_db(self) -> None:
        """Ensure database session is available."""
        if not self.db:
            async for db_session in get_db():
                self.db = db_session
                break
    
    async def _ensure_chat_session(self) -> None:
        """Ensure chat session exists in database."""
        await self._ensure_db()
        
        if not self._chat_session:
            # Try to find existing session
            self._chat_session = self.db.query(ChatSession).filter(
                ChatSession.id == self.session_id
            ).first()
            
            # Create new session if not found
            if not self._chat_session:
                self._chat_session = ChatSession(
                    id=self.session_id,
                    user_id=self.user_id,
                    title="New Conversation"
                )
                self.db.add(self._chat_session)
                self.db.commit()
    
    async def add_message(self, message: BaseMessage) -> None:
        """
        Add a message to the history.
        
        Args:
            message: Message to add
        """
        await self._ensure_chat_session()
        
        # Map LangChain message type to database role
        if isinstance(message, HumanMessage):
            role = "user"
        elif isinstance(message, AIMessage):
            role = "assistant"
        elif isinstance(message, SystemMessage):
            role = "system"
        else:
            role = "unknown"
        
        # Create message in database
        db_message = Message(
            chat_session_id=self.session_id,
            role=role,
            content=message.content,
            metadata=message.additional_kwargs
        )
        
        self.db.add(db_message)
        self.db.commit()
    
    async def clear(self) -> None:
        """Clear message history."""
        await self._ensure_db()
        
        # Delete all messages for this session
        self.db.query(Message).filter(
            Message.chat_session_id == self.session_id
        ).delete()
        
        self.db.commit()
    
    @property
    def messages(self) -> List[BaseMessage]:
        """
        Get all messages in history.
        
        Returns:
            List of messages
        """
        # This is a synchronous method required by LangChain
        # We'll use a simple approach to get messages
        
        if not self.db:
            # Create a new session if not provided
            from sqlalchemy.orm import sessionmaker
            from ..db.session import engine
            
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            self.db = SessionLocal()
        
        # Get messages from database
        db_messages = self.db.query(Message).filter(
            Message.chat_session_id == self.session_id
        ).order_by(Message.created_at).all()
        
        # Convert to LangChain messages
        messages = []
        for db_message in db_messages:
            if db_message.role == "user":
                messages.append(HumanMessage(
                    content=db_message.content,
                    additional_kwargs=db_message.metadata or {}
                ))
            elif db_message.role == "assistant":
                messages.append(AIMessage(
                    content=db_message.content,
                    additional_kwargs=db_message.metadata or {}
                ))
            elif db_message.role == "system":
                messages.append(SystemMessage(
                    content=db_message.content,
                    additional_kwargs=db_message.metadata or {}
                ))
        
        return messages


class DatabaseMemory(ConversationBufferMemory):
    """
    Conversation memory backed by database.
    
    Extends LangChain's ConversationBufferMemory to use database storage.
    """
    
    def __init__(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
        memory_key: str = "history",
        return_messages: bool = False,
        output_key: Optional[str] = None,
        input_key: Optional[str] = None,
        human_prefix: str = "Human",
        ai_prefix: str = "AI"
    ):
        """
        Initialize database memory.
        
        Args:
            session_id: Chat session ID
            user_id: User ID
            db: Database session
            memory_key: Memory key in prompt variables
            return_messages: Whether to return messages or string
            output_key: Key for outputs in prompt variables
            input_key: Key for inputs in prompt variables
            human_prefix: Prefix for human messages
            ai_prefix: Prefix for AI messages
        """
        chat_memory = DatabaseChatMessageHistory(
            session_id=session_id,
            user_id=user_id,
            db=db
        )
        
        super().__init__(
            chat_memory=chat_memory,
            memory_key=memory_key,
            return_messages=return_messages,
            output_key=output_key,
            input_key=input_key,
            human_prefix=human_prefix,
            ai_prefix=ai_prefix
        )


class GlobalCache:
    """
    Global cache for answers and embeddings.
    
    Provides caching to avoid redundant computation.
    """
    
    def __init__(self, db: Optional[Session] = None):
        """
        Initialize global cache.
        
        Args:
            db: Database session
        """
        self.db = db
        self._in_memory_cache = {}
    
    def _generate_key(self, data: Any) -> str:
        """
        Generate cache key from data.
        
        Args:
            data: Data to hash
            
        Returns:
            Cache key
        """
        # Convert data to JSON string and hash it
        if isinstance(data, dict):
            # Sort keys for consistent hashing
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        # For now, use in-memory cache
        # In a production implementation, this would use Redis or a database
        return self._in_memory_cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        # For now, use in-memory cache
        # In a production implementation, this would use Redis or a database
        self._in_memory_cache[key] = value
    
    async def get_or_set(
        self,
        key: str,
        getter_func: callable,
        ttl: Optional[int] = None
    ) -> Any:
        """
        Get value from cache or set it if not found.
        
        Args:
            key: Cache key
            getter_func: Function to get value if not in cache
            ttl: Time to live in seconds
            
        Returns:
            Cached or computed value
        """
        # Check cache first
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value
        
        # Compute value
        value = await getter_func()
        
        # Cache value
        await self.set(key, value, ttl)
        
        return value
    
    async def delete(self, key: str) -> None:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
        """
        if key in self._in_memory_cache:
            del self._in_memory_cache[key]
    
    async def clear(self) -> None:
        """Clear cache."""
        self._in_memory_cache.clear()


async def get_memory_for_session(
    session_id: str,
    user_id: Optional[str] = None,
    db: Optional[Session] = None
) -> DatabaseMemory:
    """
    Get memory for a chat session.
    
    Args:
        session_id: Chat session ID
        user_id: User ID
        db: Database session
        
    Returns:
        DatabaseMemory instance
    """
    return DatabaseMemory(
        session_id=session_id,
        user_id=user_id,
        db=db
    )


async def get_global_cache(db: Optional[Session] = None) -> GlobalCache:
    """
    Get global cache.
    
    Args:
        db: Database session
        
    Returns:
        GlobalCache instance
    """
    return GlobalCache(db=db)
