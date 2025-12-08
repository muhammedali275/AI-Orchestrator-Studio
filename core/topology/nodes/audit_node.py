"""
Audit Node - Logs execution for auditing purposes.

Records execution details for compliance and debugging.
"""

import logging
import time
import json
import os
from typing import Dict, Any, Callable, List, Optional
from datetime import datetime

from ...agent.agent_registry import AgentRegistry
from ...planner_router.planner_registry import PlannerRegistry
from ...planner_router.router_registry import RouterRegistry
from ...tools.tool_registry import ToolRegistry
from ...memory_cache.memory_service import MemoryService
from ...memory_cache.cache_service import CacheService
from ...config.config_service import ConfigService

logger = logging.getLogger(__name__)


def audit_node(
    config: Dict[str, Any],
    agent_registry: AgentRegistry,
    planner_registry: PlannerRegistry,
    router_registry: RouterRegistry,
    tool_registry: ToolRegistry,
    memory_service: MemoryService,
    cache_service: CacheService,
    config_service: ConfigService
) -> Callable:
    """
    Create audit node.
    
    Args:
        config: Node configuration
        agent_registry: Agent registry
        planner_registry: Planner registry
        router_registry: Router registry
        tool_registry: Tool registry
        memory_service: Memory service
        cache_service: Cache service
        config_service: Configuration service
        
    Returns:
        Node function
    """
    # Get audit configuration
    audit_enabled = config.get("audit_enabled", True)
    audit_log_file = config.get("audit_log_file", "")
    audit_db_enabled = config.get("audit_db_enabled", False)
    
    # Get privacy configuration
    redact_sensitive_data = config.get("redact_sensitive_data", True)
    sensitive_fields = config.get("sensitive_fields", ["api_key", "password", "token", "secret"])
    
    # Get retention configuration
    retention_days = config.get("retention_days", 90)
    
    async def node_fn(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Audit node function.
        
        Args:
            state: Current state
            
        Returns:
            Updated state
        """
        try:
            logger.info(f"Auditing execution: {state.get('run_id')}")
            
            # Skip if auditing is disabled
            if not audit_enabled:
                logger.info("Auditing is disabled")
                return state
            
            # Create audit record
            audit_record = _create_audit_record(state)
            
            # Store audit record
            if audit_log_file:
                _write_to_audit_log(audit_record, audit_log_file)
            
            if audit_db_enabled:
                await _write_to_audit_db(audit_record)
            
            # Add to history
            state["history"].append({
                "node": "audit",
                "timestamp": time.time()
            })
            
            logger.info(f"Auditing complete")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in audit node: {str(e)}")
            # Don't set error in state, as this is a non-critical node
            return state
    
    def _create_audit_record(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create audit record from state.
        
        Args:
            state: Current state
            
        Returns:
            Audit record
        """
        # Get basic information
        run_id = state.get("run_id", "")
        user_id = state.get("user_id", "")
        client_id = state.get("client_id", "")
        conversation_id = state.get("conversation_id", "")
        
        # Get timestamps
        start_time = state.get("timestamp", 0)
        end_time = time.time()
        execution_time = state.get("execution_time", end_time - start_time)
        
        # Get input and output
        input_text = state.get("input", "")
        output_text = state.get("output", "")
        
        # Create audit record
        audit_record = {
            "run_id": run_id,
            "user_id": user_id,
            "client_id": client_id,
            "conversation_id": conversation_id,
            "timestamp": start_time,
            "end_time": end_time,
            "execution_time": execution_time,
            "input": input_text,
            "output": output_text,
            "status": "error" if "error" in state else "success"
        }
        
        # Add error if present
        if "error" in state:
            audit_record["error"] = state["error"]
        
        # Add history
        if "history" in state:
            audit_record["history"] = state["history"]
        
        # Add sources if present
        if "sources" in state:
            audit_record["sources"] = state["sources"]
        
        # Add tool results if present
        if "tool_results" in state:
            audit_record["tool_results"] = state["tool_results"]
        
        # Redact sensitive data if enabled
        if redact_sensitive_data:
            audit_record = _redact_sensitive_data(audit_record)
        
        return audit_record
    
    def _redact_sensitive_data(data: Any) -> Any:
        """
        Redact sensitive data from audit record.
        
        Args:
            data: Data to redact
            
        Returns:
            Redacted data
        """
        if isinstance(data, dict):
            redacted_data = {}
            for key, value in data.items():
                # Check if key is sensitive
                if any(sensitive in key.lower() for sensitive in sensitive_fields):
                    redacted_data[key] = "***REDACTED***"
                else:
                    redacted_data[key] = _redact_sensitive_data(value)
            return redacted_data
        elif isinstance(data, list):
            return [_redact_sensitive_data(item) for item in data]
        else:
            return data
    
    def _write_to_audit_log(audit_record: Dict[str, Any], log_file: str) -> None:
        """
        Write audit record to log file.
        
        Args:
            audit_record: Audit record
            log_file: Log file path
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            # Format timestamp
            timestamp = datetime.fromtimestamp(audit_record["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            
            # Format log entry
            log_entry = f"[{timestamp}] {json.dumps(audit_record)}\n"
            
            # Write to log file
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
                
        except Exception as e:
            logger.error(f"Error writing to audit log: {str(e)}")
    
    async def _write_to_audit_db(audit_record: Dict[str, Any]) -> None:
        """
        Write audit record to database.
        
        Args:
            audit_record: Audit record
        """
        try:
            # Get database configuration
            db_config = config_service.get_audit_db_config()
            if not db_config:
                logger.warning("Audit database not configured")
                return
            
            # Determine database type
            db_type = db_config.get("type", "").lower()
            
            if db_type == "postgres":
                await _write_to_postgres(audit_record, db_config)
            elif db_type == "mongodb":
                await _write_to_mongodb(audit_record, db_config)
            else:
                logger.warning(f"Unsupported audit database type: {db_type}")
                
        except Exception as e:
            logger.error(f"Error writing to audit database: {str(e)}")
    
    async def _write_to_postgres(audit_record: Dict[str, Any], db_config: Dict[str, Any]) -> None:
        """
        Write audit record to PostgreSQL.
        
        Args:
            audit_record: Audit record
            db_config: Database configuration
        """
        try:
            import psycopg2
            import psycopg2.extras
            
            # Get connection parameters
            host = db_config.get("host", "localhost")
            port = db_config.get("port", 5432)
            user = db_config.get("username", "postgres")
            password = db_config.get("password", "")
            database = db_config.get("database", "aipanel")
            table = db_config.get("table", "audit_logs")
            
            # Connect to PostgreSQL
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                dbname=database
            )
            
            # Create table if it doesn't exist
            with conn.cursor() as cur:
                cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {table} (
                    id SERIAL PRIMARY KEY,
                    run_id TEXT,
                    user_id TEXT,
                    client_id TEXT,
                    conversation_id TEXT,
                    timestamp TIMESTAMP WITH TIME ZONE,
                    end_time TIMESTAMP WITH TIME ZONE,
                    execution_time FLOAT,
                    input TEXT,
                    output TEXT,
                    status TEXT,
                    error TEXT,
                    data JSONB
                )
                """)
                conn.commit()
            
            # Insert audit record
            with conn.cursor() as cur:
                cur.execute(f"""
                INSERT INTO {table} (
                    run_id, user_id, client_id, conversation_id,
                    timestamp, end_time, execution_time,
                    input, output, status, error, data
                ) VALUES (
                    %s, %s, %s, %s, 
                    to_timestamp(%s), to_timestamp(%s), %s,
                    %s, %s, %s, %s, %s
                )
                """, (
                    audit_record.get("run_id"),
                    audit_record.get("user_id"),
                    audit_record.get("client_id"),
                    audit_record.get("conversation_id"),
                    audit_record.get("timestamp"),
                    audit_record.get("end_time"),
                    audit_record.get("execution_time"),
                    audit_record.get("input"),
                    audit_record.get("output"),
                    audit_record.get("status"),
                    audit_record.get("error"),
                    json.dumps({
                        k: v for k, v in audit_record.items()
                        if k not in ["run_id", "user_id", "client_id", "conversation_id",
                                    "timestamp", "end_time", "execution_time",
                                    "input", "output", "status", "error"]
                    })
                ))
                conn.commit()
            
            # Close connection
            conn.close()
            
        except Exception as e:
            logger.error(f"Error writing to PostgreSQL: {str(e)}")
    
    async def _write_to_mongodb(audit_record: Dict[str, Any], db_config: Dict[str, Any]) -> None:
        """
        Write audit record to MongoDB.
        
        Args:
            audit_record: Audit record
            db_config: Database configuration
        """
        try:
            import pymongo
            from datetime import datetime
            
            # Get connection parameters
            host = db_config.get("host", "localhost")
            port = db_config.get("port", 27017)
            user = db_config.get("username", "")
            password = db_config.get("password", "")
            database = db_config.get("database", "aipanel")
            collection = db_config.get("collection", "audit_logs")
            
            # Create MongoDB client
            client = pymongo.MongoClient(
                host=host,
                port=port,
                username=user,
                password=password
            )
            
            # Get database and collection
            db = client[database]
            coll = db[collection]
            
            # Convert timestamps to datetime
            if "timestamp" in audit_record:
                audit_record["timestamp"] = datetime.fromtimestamp(audit_record["timestamp"])
            
            if "end_time" in audit_record:
                audit_record["end_time"] = datetime.fromtimestamp(audit_record["end_time"])
            
            # Insert audit record
            coll.insert_one(audit_record)
            
            # Close connection
            client.close()
            
        except Exception as e:
            logger.error(f"Error writing to MongoDB: {str(e)}")
    
    return node_fn
