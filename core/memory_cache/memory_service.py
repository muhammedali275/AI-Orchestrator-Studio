"""
Memory Service - Stores per-user chat history.

Manages conversation memory in external DB or vectorDB.
"""

import logging
import json
import time
import uuid
from typing import Dict, Any, Optional, List, Union

from ..config.config_service import ConfigService
from .cache_service import CacheService

logger = logging.getLogger(__name__)


class Message:
    """Represents a message in a conversation."""
    
    def __init__(
        self,
        content: str,
        role: str,
        message_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None
    ):
        """
        Initialize message.
        
        Args:
            content: Message content
            role: Message role (user, assistant, system)
            message_id: Message ID (generated if not provided)
            metadata: Additional metadata
            timestamp: Message timestamp (current time if not provided)
        """
        self.content = content
        self.role = role
        self.message_id = message_id or str(uuid.uuid4())
        self.metadata = metadata or {}
        self.timestamp = timestamp or time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert message to dictionary.
        
        Returns:
            Dictionary representation of message
        """
        return {
            "content": self.content,
            "role": self.role,
            "message_id": self.message_id,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """
        Create message from dictionary.
        
        Args:
            data: Dictionary representation of message
            
        Returns:
            Message instance
        """
        return cls(
            content=data["content"],
            role=data["role"],
            message_id=data.get("message_id"),
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp")
        )
    
    def to_langchain_message(self) -> Dict[str, str]:
        """
        Convert to LangChain message format.
        
        Returns:
            LangChain message dictionary
        """
        return {
            "content": self.content,
            "role": self.role
        }


class Conversation:
    """Represents a conversation with multiple messages."""
    
    def __init__(
        self,
        conversation_id: str,
        user_id: str,
        messages: Optional[List[Message]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[float] = None,
        updated_at: Optional[float] = None
    ):
        """
        Initialize conversation.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID
            messages: List of messages
            metadata: Additional metadata
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.messages = messages or []
        self.metadata = metadata or {}
        self.created_at = created_at or time.time()
        self.updated_at = updated_at or time.time()
    
    def add_message(self, message: Message) -> None:
        """
        Add message to conversation.
        
        Args:
            message: Message to add
        """
        self.messages.append(message)
        self.updated_at = time.time()
    
    def get_messages(self, max_messages: Optional[int] = None) -> List[Message]:
        """
        Get messages from conversation.
        
        Args:
            max_messages: Maximum number of messages to return
            
        Returns:
            List of messages
        """
        if max_messages is None:
            return self.messages
        
        return self.messages[-max_messages:]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert conversation to dictionary.
        
        Returns:
            Dictionary representation of conversation
        """
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "messages": [message.to_dict() for message in self.messages],
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conversation":
        """
        Create conversation from dictionary.
        
        Args:
            data: Dictionary representation of conversation
            
        Returns:
            Conversation instance
        """
        return cls(
            conversation_id=data["conversation_id"],
            user_id=data["user_id"],
            messages=[Message.from_dict(message) for message in data.get("messages", [])],
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
    
    def to_langchain_messages(self, max_messages: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Convert to LangChain messages format.
        
        Args:
            max_messages: Maximum number of messages to return
            
        Returns:
            List of LangChain message dictionaries
        """
        messages = self.get_messages(max_messages)
        return [message.to_langchain_message() for message in messages]


class MemoryService:
    """
    Memory service for AIPanel.
    
    Stores per-user chat history in external DB or vectorDB.
    """
    
    def __init__(self, config_service: ConfigService, cache_service: CacheService):
        """
        Initialize memory service.
        
        Args:
            config_service: Configuration service
            cache_service: Cache service
        """
        self.config_service = config_service
        self.cache_service = cache_service
        self._memory_client = None
        self._memory_type = None
        self._initialize_memory()
    
    def _initialize_memory(self) -> None:
        """Initialize memory client based on configuration."""
        # Get memory configuration
        memory_enabled = self.config_service.memory_enabled
        if not memory_enabled:
            logger.info("Memory is disabled in configuration")
            return
        
        # Determine memory type
        if self.config_service.get_postgres_dsn():
            self._initialize_postgres_memory()
            self._memory_type = "postgres"
        elif self.config_service.vector_db_url:
            self._initialize_vector_memory()
            self._memory_type = "vector"
        else:
            self._initialize_memory_memory()
            self._memory_type = "memory"
    
    def _initialize_postgres_memory(self) -> None:
        """Initialize PostgreSQL memory client."""
        try:
            import psycopg2
            import psycopg2.extras
            
            postgres_dsn = self.config_service.get_postgres_dsn()
            if not postgres_dsn:
                logger.warning("PostgreSQL DSN not configured, falling back to in-memory memory")
                self._initialize_memory_memory()
                return
            
            # Connect to PostgreSQL
            conn = psycopg2.connect(postgres_dsn)
            
            # Create memory tables if they don't exist
            with conn.cursor() as cur:
                # Create conversations table
                cur.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE,
                    updated_at TIMESTAMP WITH TIME ZONE
                )
                """)
                
                # Create messages table
                cur.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata JSONB,
                    timestamp TIMESTAMP WITH TIME ZONE,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (conversation_id)
                )
                """)
                
                # Create index on conversation_id
                cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
                ON messages (conversation_id)
                """)
                
                conn.commit()
            
            self._memory_client = conn
            logger.info("Initialized PostgreSQL memory client")
            
        except ImportError:
            logger.warning("psycopg2 package not installed, falling back to in-memory memory")
            self._initialize_memory_memory()
        except Exception as e:
            logger.error(f"Error initializing PostgreSQL memory: {str(e)}")
            self._initialize_memory_memory()
    
    def _initialize_vector_memory(self) -> None:
        """Initialize vector database memory client."""
        try:
            # Determine vector DB type
            vector_db_type = self.config_service.vector_db_type.lower()
            
            if vector_db_type == "chroma":
                self._initialize_chroma_memory()
            elif vector_db_type == "pinecone":
                self._initialize_pinecone_memory()
            else:
                logger.warning(f"Unsupported vector DB type: {vector_db_type}, falling back to in-memory memory")
                self._initialize_memory_memory()
                
        except Exception as e:
            logger.error(f"Error initializing vector memory: {str(e)}")
            self._initialize_memory_memory()
    
    def _initialize_chroma_memory(self) -> None:
        """Initialize Chroma memory client."""
        try:
            from langchain_community.vectorstores import Chroma
            from langchain_openai import OpenAIEmbeddings
            
            # Get Chroma settings
            collection_name = self.config_service.vector_db_collection
            
            # Create embedding function
            embedding_function = OpenAIEmbeddings(
                api_key=self.config_service.vector_db_api_key
            )
            
            # Create Chroma client
            db = Chroma(
                collection_name=collection_name,
                embedding_function=embedding_function,
                persist_directory=self.config_service.vector_db_url
            )
            
            self._memory_client = db
            self._memory_type = "chroma"
            logger.info("Initialized Chroma memory client")
            
        except ImportError:
            logger.warning("Chroma not installed, falling back to in-memory memory")
            self._initialize_memory_memory()
        except Exception as e:
            logger.error(f"Error initializing Chroma memory: {str(e)}")
            self._initialize_memory_memory()
    
    def _initialize_pinecone_memory(self) -> None:
        """Initialize Pinecone memory client."""
        try:
            from langchain_community.vectorstores import Pinecone
            from langchain_openai import OpenAIEmbeddings
            import pinecone
            
            # Initialize Pinecone
            pinecone.init(
                api_key=self.config_service.vector_db_api_key,
                environment=self.config_service.vector_db_url
            )
            
            # Get index name
            index_name = self.config_service.vector_db_collection
            
            # Create embedding function
            embedding_function = OpenAIEmbeddings()
            
            # Create Pinecone client
            db = Pinecone.from_existing_index(
                index_name=index_name,
                embedding=embedding_function
            )
            
            self._memory_client = db
            self._memory_type = "pinecone"
            logger.info("Initialized Pinecone memory client")
            
        except ImportError:
            logger.warning("Pinecone not installed, falling back to in-memory memory")
            self._initialize_memory_memory()
        except Exception as e:
            logger.error(f"Error initializing Pinecone memory: {str(e)}")
            self._initialize_memory_memory()
    
    def _initialize_memory_memory(self) -> None:
        """Initialize in-memory memory."""
        self._memory_client = {}
        self._memory_type = "memory"
        logger.info("Initialized in-memory memory")
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Get conversation by ID.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation or None if not found
        """
        if not self._memory_client:
            return None
        
        try:
            if self._memory_type == "postgres":
                return await self._get_conversation_from_postgres(conversation_id)
            elif self._memory_type in ["chroma", "pinecone"]:
                return await self._get_conversation_from_vector(conversation_id)
            else:
                return self._get_conversation_from_memory(conversation_id)
        except Exception as e:
            logger.error(f"Error getting conversation: {str(e)}")
            return None
    
    async def get_conversations(self, user_id: str) -> List[Conversation]:
        """
        Get all conversations for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of conversations
        """
        if not self._memory_client:
            return []
        
        try:
            if self._memory_type == "postgres":
                return await self._get_conversations_from_postgres(user_id)
            elif self._memory_type in ["chroma", "pinecone"]:
                return await self._get_conversations_from_vector(user_id)
            else:
                return self._get_conversations_from_memory(user_id)
        except Exception as e:
            logger.error(f"Error getting conversations: {str(e)}")
            return []
    
    async def create_conversation(self, user_id: str, metadata: Optional[Dict[str, Any]] = None) -> Conversation:
        """
        Create a new conversation.
        
        Args:
            user_id: User ID
            metadata: Additional metadata
            
        Returns:
            Created conversation
        """
        conversation_id = str(uuid.uuid4())
        conversation = Conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            metadata=metadata or {}
        )
        
        if not self._memory_client:
            return conversation
        
        try:
            if self._memory_type == "postgres":
                await self._save_conversation_to_postgres(conversation)
            elif self._memory_type in ["chroma", "pinecone"]:
                await self._save_conversation_to_vector(conversation)
            else:
                self._save_conversation_to_memory(conversation)
            
            return conversation
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            return conversation
    
    async def add_message(
        self,
        conversation_id: str,
        content: str,
        role: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Message]:
        """
        Add message to conversation.
        
        Args:
            conversation_id: Conversation ID
            content: Message content
            role: Message role (user, assistant, system)
            metadata: Additional metadata
            
        Returns:
            Added message or None if failed
        """
        # Create message
        message = Message(
            content=content,
            role=role,
            metadata=metadata or {}
        )
        
        if not self._memory_client:
            return message
        
        try:
            # Get conversation
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                logger.warning(f"Conversation not found: {conversation_id}")
                return None
            
            # Add message to conversation
            conversation.add_message(message)
            
            # Save conversation
            if self._memory_type == "postgres":
                await self._save_message_to_postgres(conversation_id, message)
                await self._update_conversation_timestamp_postgres(conversation_id)
            elif self._memory_type in ["chroma", "pinecone"]:
                await self._save_message_to_vector(conversation_id, message)
            else:
                self._save_conversation_to_memory(conversation)
            
            return message
        except Exception as e:
            logger.error(f"Error adding message: {str(e)}")
            return None
    
    async def get_messages(
        self,
        conversation_id: str,
        max_messages: Optional[int] = None
    ) -> List[Message]:
        """
        Get messages from conversation.
        
        Args:
            conversation_id: Conversation ID
            max_messages: Maximum number of messages to return
            
        Returns:
            List of messages
        """
        if not self._memory_client:
            return []
        
        try:
            # Get conversation
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                logger.warning(f"Conversation not found: {conversation_id}")
                return []
            
            # Get messages
            return conversation.get_messages(max_messages)
        except Exception as e:
            logger.error(f"Error getting messages: {str(e)}")
            return []
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete conversation.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            True if successful, False otherwise
        """
        if not self._memory_client:
            return False
        
        try:
            if self._memory_type == "postgres":
                return await self._delete_conversation_from_postgres(conversation_id)
            elif self._memory_type in ["chroma", "pinecone"]:
                return await self._delete_conversation_from_vector(conversation_id)
            else:
                return self._delete_conversation_from_memory(conversation_id)
        except Exception as e:
            logger.error(f"Error deleting conversation: {str(e)}")
            return False
    
    async def clear_conversations(self, user_id: str) -> bool:
        """
        Clear all conversations for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        if not self._memory_client:
            return False
        
        try:
            if self._memory_type == "postgres":
                return await self._clear_conversations_from_postgres(user_id)
            elif self._memory_type in ["chroma", "pinecone"]:
                return await self._clear_conversations_from_vector(user_id)
            else:
                return self._clear_conversations_from_memory(user_id)
        except Exception as e:
            logger.error(f"Error clearing conversations: {str(e)}")
            return False
    
    async def close(self) -> None:
        """Close memory client."""
        if not self._memory_client:
            return
        
        try:
            if self._memory_type == "postgres":
                await self._close_postgres()
            elif self._memory_type == "chroma":
                await self._close_chroma()
            elif self._memory_type == "pinecone":
                await self._close_pinecone()
        except Exception as e:
            logger.error(f"Error closing memory client: {str(e)}")
    
    # PostgreSQL implementation
    
    async def _get_conversation_from_postgres(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation from PostgreSQL."""
        try:
            # Get connection
            conn = self._memory_client
            
            # Get conversation
            with conn.cursor() as cur:
                cur.execute("""
                SELECT conversation_id, user_id, metadata, created_at, updated_at
                FROM conversations
                WHERE conversation_id = %s
                """, (conversation_id,))
                
                conversation_row = cur.fetchone()
                
                if not conversation_row:
                    return None
                
                conversation_id, user_id, metadata, created_at, updated_at = conversation_row
                
                # Get messages
                cur.execute("""
                SELECT message_id, role, content, metadata, timestamp
                FROM messages
                WHERE conversation_id = %s
                ORDER BY timestamp
                """, (conversation_id,))
                
                message_rows = cur.fetchall()
                
                # Create messages
                messages = []
                for message_row in message_rows:
                    message_id, role, content, msg_metadata, timestamp = message_row
                    messages.append(Message(
                        message_id=message_id,
                        role=role,
                        content=content,
                        metadata=msg_metadata or {},
                        timestamp=timestamp.timestamp() if timestamp else None
                    ))
                
                # Create conversation
                return Conversation(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    messages=messages,
                    metadata=metadata or {},
                    created_at=created_at.timestamp() if created_at else None,
                    updated_at=updated_at.timestamp() if updated_at else None
                )
        except Exception as e:
            logger.error(f"Error getting conversation from PostgreSQL: {str(e)}")
            return None
    
    async def _get_conversations_from_postgres(self, user_id: str) -> List[Conversation]:
        """Get conversations from PostgreSQL."""
        try:
            # Get connection
            conn = self._memory_client
            
            # Get conversations
            with conn.cursor() as cur:
                cur.execute("""
                SELECT conversation_id, user_id, metadata, created_at, updated_at
                FROM conversations
                WHERE user_id = %s
                ORDER BY updated_at DESC
                """, (user_id,))
                
                conversation_rows = cur.fetchall()
                
                # Create conversations
                conversations = []
                for conversation_row in conversation_rows:
                    conversation_id, user_id, metadata, created_at, updated_at = conversation_row
                    
                    # Get messages
                    cur.execute("""
                    SELECT message_id, role, content, metadata, timestamp
                    FROM messages
                    WHERE conversation_id = %s
                    ORDER BY timestamp
                    """, (conversation_id,))
                    
                    message_rows = cur.fetchall()
                    
                    # Create messages
                    messages = []
                    for message_row in message_rows:
                        message_id, role, content, msg_metadata, timestamp = message_row
                        messages.append(Message(
                            message_id=message_id,
                            role=role,
                            content=content,
                            metadata=msg_metadata or {},
                            timestamp=timestamp.timestamp() if timestamp else None
                        ))
                    
                    # Create conversation
                    conversations.append(Conversation(
                        conversation_id=conversation_id,
                        user_id=user_id,
                        messages=messages,
                        metadata=metadata or {},
                        created_at=created_at.timestamp() if created_at else None,
                        updated_at=updated_at.timestamp() if updated_at else None
                    ))
                
                return conversations
        except Exception as e:
            logger.error(f"Error getting conversations from PostgreSQL: {str(e)}")
            return []
    
    async def _save_conversation_to_postgres(self, conversation: Conversation) -> bool:
        """Save conversation to PostgreSQL."""
        try:
            # Get connection
            conn = self._memory_client
            
            # Save conversation
            with conn.cursor() as cur:
                cur.execute("""
                INSERT INTO conversations (conversation_id, user_id, metadata, created_at, updated_at)
                VALUES (%s, %s, %s, to_timestamp(%s), to_timestamp(%s))
                ON CONFLICT (conversation_id) DO UPDATE
                SET metadata = EXCLUDED.metadata, updated_at = EXCLUDED.updated_at
                """, (
                    conversation.conversation_id,
                    conversation.user_id,
                    json.dumps(conversation.metadata),
                    conversation.created_at,
                    conversation.updated_at
                ))
                
                # Save messages
                for message in conversation.messages:
                    cur.execute("""
                    INSERT INTO messages (message_id, conversation_id, role, content, metadata, timestamp)
                    VALUES (%s, %s, %s, %s, %s, to_timestamp(%s))
                    ON CONFLICT (message_id) DO NOTHING
                    """, (
                        message.message_id,
                        conversation.conversation_id,
                        message.role,
                        message.content,
                        json.dumps(message.metadata),
                        message.timestamp
                    ))
                
                conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error saving conversation to PostgreSQL: {str(e)}")
            return False
    
    async def _save_message_to_postgres(self, conversation_id: str, message: Message) -> bool:
        """Save message to PostgreSQL."""
        try:
            # Get connection
            conn = self._memory_client
            
            # Save message
            with conn.cursor() as cur:
                cur.execute("""
                INSERT INTO messages (message_id, conversation_id, role, content, metadata, timestamp)
                VALUES (%s, %s, %s, %s, %s, to_timestamp(%s))
                ON CONFLICT (message_id) DO NOTHING
                """, (
                    message.message_id,
                    conversation_id,
                    message.role,
                    message.content,
                    json.dumps(message.metadata),
                    message.timestamp
                ))
                
                conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error saving message to PostgreSQL: {str(e)}")
            return False
    
    async def _update_conversation_timestamp_postgres(self, conversation_id: str) -> bool:
        """Update conversation timestamp in PostgreSQL."""
        try:
            # Get connection
            conn = self._memory_client
            
            # Update timestamp
            with conn.cursor() as cur:
                cur.execute("""
                UPDATE conversations
                SET updated_at = NOW()
                WHERE conversation_id = %s
                """, (conversation_id,))
                
                conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error updating conversation timestamp in PostgreSQL: {str(e)}")
            return False
    
    async def _delete_conversation_from_postgres(self, conversation_id: str) -> bool:
        """Delete conversation from PostgreSQL."""
        try:
            # Get connection
            conn = self._memory_client
            
            # Delete conversation and messages
            with conn.cursor() as cur:
                # Delete messages first (due to foreign key constraint)
                cur.execute("""
                DELETE FROM messages
                WHERE conversation_id = %s
                """, (conversation_id,))
                
                # Delete conversation
                cur.execute("""
                DELETE FROM conversations
                WHERE conversation_id = %s
                """, (conversation_id,))
                
                conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting conversation from PostgreSQL: {str(e)}")
            return False
    
    async def _clear_conversations_from_postgres(self, user_id: str) -> bool:
        """Clear conversations from PostgreSQL."""
        try:
            # Get connection
            conn = self._memory_client
            
            # Get conversation IDs
            conversation_ids = []
            with conn.cursor() as cur:
                cur.execute("""
                SELECT conversation_id
                FROM conversations
                WHERE user_id = %s
                """, (user_id,))
                
                for row in cur.fetchall():
                    conversation_ids.append(row[0])
            
            # Delete conversations and messages
            with conn.cursor() as cur:
                # Delete messages first (due to foreign key constraint)
                if conversation_ids:
                    cur.execute(f"""
                    DELETE FROM messages
                    WHERE conversation_id IN %s
                    """, (tuple(conversation_ids),))
                
                # Delete conversations
                cur.execute("""
                DELETE FROM conversations
                WHERE user_id = %s
                """, (user_id,))
                
                conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error clearing conversations from PostgreSQL: {str(e)}")
            return False
    
    async def _close_postgres(self) -> None:
        """Close PostgreSQL client."""
        try:
            if self._memory_client:
                self._memory_client.close()
        except Exception as e:
            logger.error(f"Error closing PostgreSQL client: {str(e)}")
    
    # Vector database implementation
    
    async def _get_conversation_from_vector(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation from vector database."""
        try:
            # Use cache for conversation metadata
            conversation_key = f"conversation:{conversation_id}"
            conversation_data = await self.cache_service.get(conversation_key)
            
            if not conversation_data:
                return None
            
            # Create conversation
            conversation = Conversation.from_dict(conversation_data)
            
            # Get messages
            if self._memory_type == "chroma":
                messages = await self._get_messages_from_chroma(conversation_id)
            elif self._memory_type == "pinecone":
                messages = await self._get_messages_from_pinecone(conversation_id)
            else:
                messages = []
            
            # Add messages to conversation
            conversation.messages = messages
            
            return conversation
        except Exception as e:
            logger.error(f"Error getting conversation from vector database: {str(e)}")
            return None
    
    async def _get_conversations_from_vector(self, user_id: str) -> List[Conversation]:
        """Get conversations from vector database."""
        try:
            # Use cache for conversation list
            conversations_key = f"conversations:{user_id}"
            conversation_ids = await self.cache_service.get(conversations_key) or []
            
            # Get conversations
            conversations = []
            for conversation_id in conversation_ids:
                conversation = await self._get_conversation_from_vector(conversation_id)
                if conversation:
                    conversations.append(conversation)
            
            return conversations
        except Exception as e:
            logger.error(f"Error getting conversations from vector database: {str(e)}")
            return []
    
    async def _save_conversation_to_vector(self, conversation: Conversation) -> bool:
        """Save conversation to vector database."""
        try:
            # Use cache for conversation metadata
            conversation_key = f"conversation:{conversation.conversation_id}"
            await self.cache_service.set(conversation_key, conversation.to_dict())
            
            # Update conversation list
            conversations_key = f"conversations:{conversation.user_id}"
            conversation_ids = await self.cache_service.get(conversations_key) or []
            
            if conversation.conversation_id not in conversation_ids:
                conversation_ids.append(conversation.conversation_id)
                await self.cache_service.set(conversations_key, conversation_ids)
            
            # Save messages
            for message in conversation.messages:
                await self._save_message_to_vector(conversation.conversation_id, message)
            
            return True
        except Exception as e:
            logger.error(f"Error saving conversation to vector database: {str(e)}")
            return False
    
    async def _save_message_to_vector(self, conversation_id: str, message: Message) -> bool:
        """Save message to vector database."""
        try:
            if self._memory_type == "chroma":
                return await self._save_message_to_chroma(conversation_id, message)
            elif self._memory_type == "pinecone":
                return await self._save_message_to_pinecone(conversation_id, message)
            else:
                return False
        except Exception as e:
            logger.error(f"Error saving message to vector database: {str(e)}")
            return False
    
    async def _get_messages_from_chroma(self, conversation_id: str) -> List[Message]:
        """Get messages from Chroma."""
        try:
            # Query Chroma
            db = self._memory_client
            
            # Query for documents with conversation_id metadata
            results = db.similarity_search_with_score(
                query="",
                k=1000,  # Get all messages
                filter={"conversation_id": conversation_id}
            )
            
            # Convert to messages
            messages = []
            for doc, _ in results:
                # Extract message data from metadata
                metadata = doc.metadata
                
                # Create message
                message = Message(
                    message_id=metadata.get("message_id"),
                    role=metadata.get("role"),
                    content=doc.page_content,
                    metadata=metadata.get("metadata", {}),
                    timestamp=metadata.get("timestamp")
                )
                
                messages.append(message)
            
            # Sort by timestamp
            messages.sort(key=lambda m: m.timestamp)
            
            return messages
        except Exception as e:
            logger.error(f"Error getting messages from Chroma: {str(e)}")
            return []
    
    async def _get_messages_from_pinecone(self, conversation_id: str) -> List[Message]:
        """Get messages from Pinecone."""
        try:
            # Query Pinecone
            db = self._memory_client
            
            # Query for documents with conversation_id metadata
            results = db.similarity_search_with_score(
                query="",
                k=1000,  # Get all messages
                filter={"conversation_id": {"$eq": conversation_id}}
            )
            
            # Convert to messages
            messages = []
            for doc, _ in results:
                # Extract message data from metadata
                metadata = doc.metadata
                
                # Create message
                message = Message(
                    message_id=metadata.get("message_id"),
                    role=metadata.get("role"),
                    content=doc.page_content,
                    metadata=metadata.get("metadata", {}),
                    timestamp=metadata.get("timestamp")
                )
                
                messages.append(message)
            
            # Sort by timestamp
            messages.sort(key=lambda m: m.timestamp)
            
            return messages
        except Exception as e:
            logger.error(f"Error getting messages from Pinecone: {str(e)}")
            return []
    
    async def _save_message_to_chroma(self, conversation_id: str, message: Message) -> bool:
        """Save message to Chroma."""
        try:
            from langchain_core.documents import Document
            
            # Create document
            doc = Document(
                page_content=message.content,
                metadata={
                    "message_id": message.message_id,
                    "conversation_id": conversation_id,
                    "role": message.role,
                    "metadata": message.metadata,
                    "timestamp": message.timestamp
                }
            )
            
            # Add to Chroma
            db = self._memory_client
            db.add_documents([doc])
            
            return True
        except Exception as e:
            logger.error(f"Error saving message to Chroma: {str(e)}")
            return False
    
    async def _save_message_to_pinecone(self, conversation_id: str, message: Message) -> bool:
        """Save message to Pinecone."""
        try:
            from langchain_core.documents import Document
            
            # Create document
            doc = Document(
                page_content=message.content,
                metadata={
                    "message_id": message.message_id,
                    "conversation_id": conversation_id,
                    "role": message.role,
                    "metadata": message.metadata,
                    "timestamp": message.timestamp
                }
            )
            
            # Add to Pinecone
            db = self._memory_client
            db.add_documents([doc])
            
            return True
        except Exception as e:
            logger.error(f"Error saving message to Pinecone: {str(e)}")
            return False
    
    async def _delete_conversation_from_vector(self, conversation_id: str) -> bool:
        """Delete conversation from vector database."""
        try:
            # Delete from cache
            conversation_key = f"conversation:{conversation_id}"
            await self.cache_service.delete(conversation_key)
            
            # Get user ID from conversation
            conversation = await self._get_conversation_from_vector(conversation_id)
            if conversation:
                # Update conversation list
                conversations_key = f"conversations:{conversation.user_id}"
                conversation_ids = await self.cache_service.get(conversations_key) or []
                
                if conversation_id in conversation_ids:
                    conversation_ids.remove(conversation_id)
                    await self.cache_service.set(conversations_key, conversation_ids)
            
            # Delete messages
            if self._memory_type == "chroma":
                return await self._delete_messages_from_chroma(conversation_id)
            elif self._memory_type == "pinecone":
                return await self._delete_messages_from_pinecone(conversation_id)
            else:
                return False
        except Exception as e:
            logger.error(f"Error deleting conversation from vector database: {str(e)}")
            return False
    
    async def _clear_conversations_from_vector(self, user_id: str) -> bool:
        """Clear conversations from vector database."""
        try:
            # Get conversation IDs
            conversations_key = f"conversations:{user_id}"
            conversation_ids = await self.cache_service.get(conversations_key) or []
            
            # Delete each conversation
            for conversation_id in conversation_ids:
                await self._delete_conversation_from_vector(conversation_id)
            
            # Clear conversation list
            await self.cache_service.delete(conversations_key)
            
            return True
        except Exception as e:
            logger.error(f"Error clearing conversations from vector database: {str(e)}")
            return False
    
    async def _delete_messages_from_chroma(self, conversation_id: str) -> bool:
        """Delete messages from Chroma."""
        try:
            # Delete from Chroma
            db = self._memory_client
            
            # Get message IDs
            results = db.similarity_search_with_score(
                query="",
                k=1000,  # Get all messages
                filter={"conversation_id": conversation_id}
            )
            
            # Delete messages
            message_ids = [doc.metadata.get("message_id") for doc, _ in results]
            if message_ids:
                db.delete(message_ids)
            
            return True
        except Exception as e:
            logger.error(f"Error deleting messages from Chroma: {str(e)}")
            return False
    
    async def _delete_messages_from_pinecone(self, conversation_id: str) -> bool:
        """Delete messages from Pinecone."""
        try:
            # Delete from Pinecone
            db = self._memory_client
            
            # Get message IDs
            results = db.similarity_search_with_score(
                query="",
                k=1000,  # Get all messages
                filter={"conversation_id": {"$eq": conversation_id}}
            )
            
            # Delete messages
            message_ids = [doc.metadata.get("message_id") for doc, _ in results]
            if message_ids:
                db.delete(message_ids)
            
            return True
        except Exception as e:
            logger.error(f"Error deleting messages from Pinecone: {str(e)}")
            return False
    
    async def _close_chroma(self) -> None:
        """Close Chroma client."""
        try:
            if self._memory_client:
                self._memory_client.persist()
        except Exception as e:
            logger.error(f"Error closing Chroma client: {str(e)}")
    
    async def _close_pinecone(self) -> None:
        """Close Pinecone client."""
        try:
            # Pinecone doesn't need explicit closing
            pass
        except Exception as e:
            logger.error(f"Error closing Pinecone client: {str(e)}")
    
    # In-memory implementation
    
    def _get_conversation_from_memory(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation from in-memory storage."""
        try:
            return self._memory_client.get(conversation_id)
        except Exception as e:
            logger.error(f"Error getting conversation from memory: {str(e)}")
            return None
    
    def _get_conversations_from_memory(self, user_id: str) -> List[Conversation]:
        """Get conversations from in-memory storage."""
        try:
            return [
                conversation for conversation in self._memory_client.values()
                if conversation.user_id == user_id
            ]
        except Exception as e:
            logger.error(f"Error getting conversations from memory: {str(e)}")
            return []
    
    def _save_conversation_to_memory(self, conversation: Conversation) -> bool:
        """Save conversation to in-memory storage."""
        try:
            self._memory_client[conversation.conversation_id] = conversation
            return True
        except Exception as e:
            logger.error(f"Error saving conversation to memory: {str(e)}")
            return False
    
    def _delete_conversation_from_memory(self, conversation_id: str) -> bool:
        """Delete conversation from in-memory storage."""
        try:
            if conversation_id in self._memory_client:
                del self._memory_client[conversation_id]
            return True
        except Exception as e:
            logger.error(f"Error deleting conversation from memory: {str(e)}")
            return False
    
    def _clear_conversations_from_memory(self, user_id: str) -> bool:
        """Clear conversations from in-memory storage."""
        try:
            conversation_ids = [
                conversation_id for conversation_id, conversation in self._memory_client.items()
                if conversation.user_id == user_id
            ]
            
            for conversation_id in conversation_ids:
                del self._memory_client[conversation_id]
            
            return True
        except Exception as e:
            logger.error(f"Error clearing conversations from memory: {str(e)}")
            return False
