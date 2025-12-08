"""
Monitoring Service - Checks health of orchestrator host, external LLM VM, tools, DBs.

Provides health checks and metrics for the AIPanel system.
"""

import logging
import time
import asyncio
import socket
import platform
import os
import psutil
from typing import Dict, Any, List, Optional, Tuple

from ..core.config.config_service import ConfigService

logger = logging.getLogger(__name__)


class MonitoringService:
    """
    Monitoring service for AIPanel.
    
    Checks health of orchestrator host, external LLM VM, tools, DBs.
    """
    
    def __init__(self, config_service: ConfigService):
        """
        Initialize monitoring service.
        
        Args:
            config_service: Configuration service
        """
        self.config_service = config_service
        self._last_check = {}
        self._cache_ttl = 60  # Cache results for 60 seconds
    
    async def check_system_health(self) -> Dict[str, Any]:
        """
        Check system health.
        
        Returns:
            System health information
        """
        # Check if cached result is available
        cache_key = "system_health"
        if cache_key in self._last_check:
            last_time, result = self._last_check[cache_key]
            if time.time() - last_time < self._cache_ttl:
                return result
        
        try:
            # Get system information
            system_info = {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "hostname": socket.gethostname(),
                "cpu_count": os.cpu_count(),
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "percent": psutil.virtual_memory().percent
                },
                "disk": {
                    "total": psutil.disk_usage("/").total,
                    "free": psutil.disk_usage("/").free,
                    "percent": psutil.disk_usage("/").percent
                },
                "network": {
                    "connections": len(psutil.net_connections())
                },
                "processes": {
                    "count": len(psutil.pids())
                },
                "timestamp": time.time()
            }
            
            # Determine status
            status = "healthy"
            if system_info["cpu_percent"] > 90:
                status = "warning"
            if system_info["memory"]["percent"] > 90:
                status = "warning"
            if system_info["disk"]["percent"] > 90:
                status = "warning"
            
            # Create result
            result = {
                "status": status,
                "info": system_info
            }
            
            # Cache result
            self._last_check[cache_key] = (time.time(), result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking system health: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def check_llm_health(self, llm_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Check LLM health.
        
        Args:
            llm_id: LLM ID (if None, check all LLMs)
            
        Returns:
            LLM health information
        """
        # Check if cached result is available
        cache_key = f"llm_health:{llm_id or 'all'}"
        if cache_key in self._last_check:
            last_time, result = self._last_check[cache_key]
            if time.time() - last_time < self._cache_ttl:
                return result
        
        try:
            # Get LLM configurations
            if llm_id:
                llm_configs = [self.config_service.get_llm_config(llm_id)]
                if not llm_configs[0]:
                    return {
                        "status": "error",
                        "error": f"LLM not found: {llm_id}"
                    }
            else:
                llm_configs = self.config_service.list_llm_configs()
            
            # Check each LLM
            llm_statuses = {}
            overall_status = "healthy"
            
            for config in llm_configs:
                if not config:
                    continue
                
                llm_id = config.id
                
                # Check LLM health
                if config.type.lower() == "openai":
                    # Check OpenAI API
                    status = await self._check_openai_health(config)
                elif config.type.lower() == "azure":
                    # Check Azure OpenAI API
                    status = await self._check_azure_openai_health(config)
                elif config.type.lower() == "ollama":
                    # Check Ollama API
                    status = await self._check_ollama_health(config)
                elif config.type.lower() == "vllm":
                    # Check vLLM API
                    status = await self._check_vllm_health(config)
                else:
                    # Unknown LLM type
                    status = {
                        "status": "unknown",
                        "message": f"Unknown LLM type: {config.type}"
                    }
                
                llm_statuses[llm_id] = status
                
                # Update overall status
                if status["status"] == "error":
                    overall_status = "error"
                elif status["status"] == "warning" and overall_status != "error":
                    overall_status = "warning"
            
            # Create result
            result = {
                "status": overall_status,
                "llms": llm_statuses
            }
            
            # Cache result
            self._last_check[cache_key] = (time.time(), result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking LLM health: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _check_openai_health(self, config: Any) -> Dict[str, Any]:
        """
        Check OpenAI API health.
        
        Args:
            config: LLM configuration
            
        Returns:
            Health status
        """
        try:
            import openai
            
            # Set API key
            openai.api_key = config.api_key
            
            # Check API
            start_time = time.time()
            response = await openai.Completion.acreate(
                model="text-davinci-003",
                prompt="Hello",
                max_tokens=5
            )
            end_time = time.time()
            
            # Calculate latency
            latency = (end_time - start_time) * 1000  # ms
            
            # Determine status
            status = "healthy"
            if latency > 1000:
                status = "warning"
            
            return {
                "status": status,
                "latency_ms": latency,
                "message": "OpenAI API is operational"
            }
            
        except ImportError:
            return {
                "status": "error",
                "error": "OpenAI package not installed"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _check_azure_openai_health(self, config: Any) -> Dict[str, Any]:
        """
        Check Azure OpenAI API health.
        
        Args:
            config: LLM configuration
            
        Returns:
            Health status
        """
        try:
            import openai
            
            # Set API key and endpoint
            openai.api_key = config.api_key
            openai.api_base = config.endpoint
            openai.api_type = "azure"
            openai.api_version = config.api_version
            
            # Check API
            start_time = time.time()
            response = await openai.Completion.acreate(
                engine=config.deployment_name,
                prompt="Hello",
                max_tokens=5
            )
            end_time = time.time()
            
            # Calculate latency
            latency = (end_time - start_time) * 1000  # ms
            
            # Determine status
            status = "healthy"
            if latency > 1000:
                status = "warning"
            
            return {
                "status": status,
                "latency_ms": latency,
                "message": "Azure OpenAI API is operational"
            }
            
        except ImportError:
            return {
                "status": "error",
                "error": "OpenAI package not installed"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _check_ollama_health(self, config: Any) -> Dict[str, Any]:
        """
        Check Ollama API health.
        
        Args:
            config: LLM configuration
            
        Returns:
            Health status
        """
        try:
            import httpx
            
            # Get Ollama endpoint
            endpoint = config.endpoint or "http://localhost:11434"
            
            # Check API
            start_time = time.time()
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{endpoint}/api/tags")
            end_time = time.time()
            
            # Calculate latency
            latency = (end_time - start_time) * 1000  # ms
            
            # Check if model is available
            model_available = False
            if response.status_code == 200:
                models = response.json().get("models", [])
                for model in models:
                    if model.get("name") == config.model:
                        model_available = True
                        break
            
            # Determine status
            status = "healthy"
            if not model_available:
                status = "warning"
            if latency > 1000:
                status = "warning"
            
            return {
                "status": status,
                "latency_ms": latency,
                "model_available": model_available,
                "message": "Ollama API is operational"
            }
            
        except ImportError:
            return {
                "status": "error",
                "error": "httpx package not installed"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _check_vllm_health(self, config: Any) -> Dict[str, Any]:
        """
        Check vLLM API health.
        
        Args:
            config: LLM configuration
            
        Returns:
            Health status
        """
        try:
            import httpx
            
            # Get vLLM endpoint
            endpoint = config.endpoint or "http://localhost:8000"
            
            # Check API
            start_time = time.time()
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{endpoint}/v1/completions",
                    json={
                        "prompt": "Hello",
                        "max_tokens": 5
                    }
                )
            end_time = time.time()
            
            # Calculate latency
            latency = (end_time - start_time) * 1000  # ms
            
            # Determine status
            status = "healthy"
            if response.status_code != 200:
                status = "error"
            if latency > 1000:
                status = "warning"
            
            return {
                "status": status,
                "latency_ms": latency,
                "message": "vLLM API is operational"
            }
            
        except ImportError:
            return {
                "status": "error",
                "error": "httpx package not installed"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def check_database_health(self, db_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Check database health.
        
        Args:
            db_id: Database ID (if None, check all databases)
            
        Returns:
            Database health information
        """
        # Check if cached result is available
        cache_key = f"db_health:{db_id or 'all'}"
        if cache_key in self._last_check:
            last_time, result = self._last_check[cache_key]
            if time.time() - last_time < self._cache_ttl:
                return result
        
        try:
            # Get database configurations
            if db_id:
                db_configs = [self.config_service.get_db_config(db_id)]
                if not db_configs[0]:
                    return {
                        "status": "error",
                        "error": f"Database not found: {db_id}"
                    }
            else:
                db_configs = self.config_service.list_db_configs()
            
            # Check each database
            db_statuses = {}
            overall_status = "healthy"
            
            for config in db_configs:
                if not config:
                    continue
                
                db_id = config.id
                
                # Check database health
                if config.type.lower() == "postgres":
                    # Check PostgreSQL
                    status = await self._check_postgres_health(config)
                elif config.type.lower() == "mysql":
                    # Check MySQL
                    status = await self._check_mysql_health(config)
                elif config.type.lower() == "mongodb":
                    # Check MongoDB
                    status = await self._check_mongodb_health(config)
                elif config.type.lower() == "redis":
                    # Check Redis
                    status = await self._check_redis_health(config)
                else:
                    # Unknown database type
                    status = {
                        "status": "unknown",
                        "message": f"Unknown database type: {config.type}"
                    }
                
                db_statuses[db_id] = status
                
                # Update overall status
                if status["status"] == "error":
                    overall_status = "error"
                elif status["status"] == "warning" and overall_status != "error":
                    overall_status = "warning"
            
            # Create result
            result = {
                "status": overall_status,
                "databases": db_statuses
            }
            
            # Cache result
            self._last_check[cache_key] = (time.time(), result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking database health: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _check_postgres_health(self, config: Any) -> Dict[str, Any]:
        """
        Check PostgreSQL health.
        
        Args:
            config: Database configuration
            
        Returns:
            Health status
        """
        try:
            import psycopg2
            
            # Connect to PostgreSQL
            start_time = time.time()
            conn = psycopg2.connect(
                host=config.host,
                port=config.port,
                user=config.username,
                password=config.password,
                dbname=config.database
            )
            
            # Execute query
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
            
            # Close connection
            conn.close()
            end_time = time.time()
            
            # Calculate latency
            latency = (end_time - start_time) * 1000  # ms
            
            # Determine status
            status = "healthy"
            if latency > 1000:
                status = "warning"
            
            return {
                "status": status,
                "latency_ms": latency,
                "message": "PostgreSQL is operational"
            }
            
        except ImportError:
            return {
                "status": "error",
                "error": "psycopg2 package not installed"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _check_mysql_health(self, config: Any) -> Dict[str, Any]:
        """
        Check MySQL health.
        
        Args:
            config: Database configuration
            
        Returns:
            Health status
        """
        try:
            import mysql.connector
            
            # Connect to MySQL
            start_time = time.time()
            conn = mysql.connector.connect(
                host=config.host,
                port=config.port,
                user=config.username,
                password=config.password,
                database=config.database
            )
            
            # Execute query
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            
            # Close connection
            cursor.close()
            conn.close()
            end_time = time.time()
            
            # Calculate latency
            latency = (end_time - start_time) * 1000  # ms
            
            # Determine status
            status = "healthy"
            if latency > 1000:
                status = "warning"
            
            return {
                "status": status,
                "latency_ms": latency,
                "message": "MySQL is operational"
            }
            
        except ImportError:
            return {
                "status": "error",
                "error": "mysql-connector-python package not installed"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _check_mongodb_health(self, config: Any) -> Dict[str, Any]:
        """
        Check MongoDB health.
        
        Args:
            config: Database configuration
            
        Returns:
            Health status
        """
        try:
            import pymongo
            
            # Connect to MongoDB
            start_time = time.time()
            client = pymongo.MongoClient(
                host=config.host,
                port=config.port,
                username=config.username,
                password=config.password
            )
            
            # Execute command
            client.admin.command("ping")
            
            # Close connection
            client.close()
            end_time = time.time()
            
            # Calculate latency
            latency = (end_time - start_time) * 1000  # ms
            
            # Determine status
            status = "healthy"
            if latency > 1000:
                status = "warning"
            
            return {
                "status": status,
                "latency_ms": latency,
                "message": "MongoDB is operational"
            }
            
        except ImportError:
            return {
                "status": "error",
                "error": "pymongo package not installed"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _check_redis_health(self, config: Any) -> Dict[str, Any]:
        """
        Check Redis health.
        
        Args:
            config: Database configuration
            
        Returns:
            Health status
        """
        try:
            import redis
            
            # Connect to Redis
            start_time = time.time()
            client = redis.Redis(
                host=config.host,
                port=config.port,
                password=config.password,
                db=config.database
            )
            
            # Execute command
            client.ping()
            
            # Close connection
            client.close()
            end_time = time.time()
            
            # Calculate latency
            latency = (end_time - start_time) * 1000  # ms
            
            # Determine status
            status = "healthy"
            if latency > 1000:
                status = "warning"
            
            return {
                "status": status,
                "latency_ms": latency,
                "message": "Redis is operational"
            }
            
        except ImportError:
            return {
                "status": "error",
                "error": "redis package not installed"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def check_tool_health(self, tool_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Check tool health.
        
        Args:
            tool_id: Tool ID (if None, check all tools)
            
        Returns:
            Tool health information
        """
        # Check if cached result is available
        cache_key = f"tool_health:{tool_id or 'all'}"
        if cache_key in self._last_check:
            last_time, result = self._last_check[cache_key]
            if time.time() - last_time < self._cache_ttl:
                return result
        
        try:
            # Get tool configurations
            if tool_id:
                tool_configs = [self.config_service.get_tool_config(tool_id)]
                if not tool_configs[0]:
                    return {
                        "status": "error",
                        "error": f"Tool not found: {tool_id}"
                    }
            else:
                tool_configs = self.config_service.list_tool_configs()
            
            # Check each tool
            tool_statuses = {}
            overall_status = "healthy"
            
            for config in tool_configs:
                if not config:
                    continue
                
                tool_id = config.id
                
                # Check tool health
                if config.type.lower() == "http":
                    # Check HTTP tool
                    status = await self._check_http_tool_health(config)
                elif config.type.lower() == "database":
                    # Check database tool
                    status = await self._check_database_tool_health(config)
                elif config.type.lower() == "vector":
                    # Check vector tool
                    status = await self._check_vector_tool_health(config)
                else:
                    # Unknown tool type
                    status = {
                        "status": "unknown",
                        "message": f"Unknown tool type: {config.type}"
                    }
                
                tool_statuses[tool_id] = status
                
                # Update overall status
                if status["status"] == "error":
                    overall_status = "error"
                elif status["status"] == "warning" and overall_status != "error":
                    overall_status = "warning"
            
            # Create result
            result = {
                "status": overall_status,
                "tools": tool_statuses
            }
            
            # Cache result
            self._last_check[cache_key] = (time.time(), result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking tool health: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _check_http_tool_health(self, config: Any) -> Dict[str, Any]:
        """
        Check HTTP tool health.
        
        Args:
            config: Tool configuration
            
        Returns:
            Health status
        """
        try:
            import httpx
            
            # Get endpoint
            endpoint = config.endpoint
            
            # Check endpoint
            start_time = time.time()
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint)
            end_time = time.time()
            
            # Calculate latency
            latency = (end_time - start_time) * 1000  # ms
            
            # Determine status
            status = "healthy"
            if response.status_code >= 400:
                status = "error"
            elif response.status_code >= 300:
                status = "warning"
            if latency > 1000:
                status = "warning"
            
            return {
                "status": status,
                "latency_ms": latency,
                "status_code": response.status_code,
                "message": f"HTTP endpoint is {status}"
            }
            
        except ImportError:
            return {
                "status": "error",
                "error": "httpx package not installed"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _check_database_tool_health(self, config: Any) -> Dict[str, Any]:
        """
        Check database tool health.
        
        Args:
            config: Tool configuration
            
        Returns:
            Health status
        """
        try:
            # Get database ID
            db_id = config.database_id
            
            # Check database health
            return await self.check_database_health(db_id)
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _check_vector_tool_health(self, config: Any) -> Dict[str, Any]:
        """
        Check vector tool health.
        
        Args:
            config: Tool configuration
            
        Returns:
            Health status
        """
        try:
            # Get vector database type
            vector_db_type = config.vector_db_type.lower()
            
            if vector_db_type == "chroma":
                # Check Chroma
                return await self._check_chroma_health(config)
            elif vector_db_type == "pinecone":
                # Check Pinecone
                return await self._check_pinecone_health(config)
            else:
                # Unknown vector database type
                return {
                    "status": "unknown",
                    "message": f"Unknown vector database type: {vector_db_type}"
                }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _check_chroma_health(self, config: Any) -> Dict[str, Any]:
        """
        Check Chroma health.
        
        Args:
            config: Tool configuration
            
        Returns:
            Health status
        """
        try:
            from langchain_community.vectorstores import Chroma
            
            # Get Chroma settings
            persist_directory = config.persist_directory
            
            # Check Chroma
            start_time = time.time()
            db = Chroma(persist_directory=persist_directory)
            db.get()
            end_time = time.time()
            
            # Calculate latency
            latency = (end_time - start_time) * 1000  # ms
            
            # Determine status
            status = "healthy"
            if latency > 1000:
                status = "warning"
            
            return {
                "status": status,
                "latency_ms": latency,
                "message": "Chroma is operational"
            }
            
        except ImportError:
            return {
                "status": "error",
                "error": "langchain-community package not installed"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _check_pinecone_health(self, config: Any) -> Dict[str, Any]:
        """
        Check Pinecone health.
        
        Args:
            config: Tool configuration
            
        Returns:
            Health status
        """
        try:
            import pinecone
            
            # Get Pinecone settings
            api_key = config.api_key
            environment = config.environment
            
            # Initialize Pinecone
            pinecone.init(api_key=api_key, environment=environment)
            
            # Check Pinecone
            start_time = time.time()
            indexes = pinecone.list_indexes()
            end_time = time.time()
            
            # Calculate latency
            latency = (end_time - start_time) * 1000  # ms
            
            # Determine status
            status = "healthy"
            if latency > 1000:
                status = "warning"
            
            return {
                "status": status,
                "latency_ms": latency,
                "indexes": indexes,
                "message": "Pinecone is operational"
            }
            
        except ImportError:
            return {
                "status": "error",
                "error": "pinecone-client package not installed"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_monitoring_summary(self) -> Dict[str, Any]:
        """
        Get monitoring summary.
        
        Returns:
            Monitoring summary
        """
        try:
            # Check system health
            system_health = await self.check_system_health()
            
            # Check LLM health
            llm_health = await self.check_llm_health()
            
            # Check database health
            db_health = await self.check_database_health()
            
            # Check tool health
            tool_health = await self.check_tool_health()
            
            # Determine overall status
            status = "healthy"
            if system_health["status"] == "error" or llm_health["status"] == "error" or db_health["status"] == "error" or tool_health["status"] == "error":
                status = "error"
            elif system_health["status"] == "warning" or llm_health["status"] == "warning" or db_health["status"] == "warning" or tool_health["status"] == "warning":
                status = "warning"
            
            # Create summary
            summary = {
                "status": status,
                "components": {
                    "system": system_health,
                    "llm": llm_health,
                    "database": db_health,
                    "tool": tool_health
                },
                "timestamp": time.time()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting monitoring summary: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
