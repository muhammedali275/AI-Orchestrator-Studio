"""
Planner Registry - Factory for planners.

Builds planners using config from config_service.
Supports LLM-based, rules-based, and semantic-layer planners.
"""

import logging
from typing import Dict, Any, Optional, List, Callable, Union

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

from ..config.config_service import ConfigService, PlannerConfig
from ..llm.llm_registry import LLMRegistry

logger = logging.getLogger(__name__)


class TaskPlan:
    """Represents a plan with tasks to execute."""
    
    def __init__(self, tasks: List[Dict[str, Any]], metadata: Dict[str, Any] = None):
        """
        Initialize task plan.
        
        Args:
            tasks: List of tasks to execute
            metadata: Additional metadata
        """
        self.tasks = tasks
        self.metadata = metadata or {}
    
    def get_ready_tasks(self) -> List[Dict[str, Any]]:
        """
        Get tasks that are ready to execute.
        
        Returns:
            List of ready tasks
        """
        return [task for task in self.tasks if task.get("status") == "ready"]
    
    def get_completed_tasks(self) -> List[Dict[str, Any]]:
        """
        Get completed tasks.
        
        Returns:
            List of completed tasks
        """
        return [task for task in self.tasks if task.get("status") == "completed"]
    
    def get_failed_tasks(self) -> List[Dict[str, Any]]:
        """
        Get failed tasks.
        
        Returns:
            List of failed tasks
        """
        return [task for task in self.tasks if task.get("status") == "failed"]
    
    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """
        Get pending tasks.
        
        Returns:
            List of pending tasks
        """
        return [task for task in self.tasks if task.get("status") == "pending"]
    
    def update_task_status(self, task_id: str, status: str, result: Any = None) -> bool:
        """
        Update task status.
        
        Args:
            task_id: Task ID
            status: New status
            result: Task result
            
        Returns:
            True if task was found and updated, False otherwise
        """
        for task in self.tasks:
            if task.get("id") == task_id:
                task["status"] = status
                if result is not None:
                    task["result"] = result
                return True
        return False
    
    def is_complete(self) -> bool:
        """
        Check if plan is complete.
        
        Returns:
            True if all tasks are completed or failed, False otherwise
        """
        return all(task.get("status") in ["completed", "failed"] for task in self.tasks)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert plan to dictionary.
        
        Returns:
            Dictionary representation of plan
        """
        return {
            "tasks": self.tasks,
            "metadata": self.metadata,
            "is_complete": self.is_complete(),
            "total_tasks": len(self.tasks),
            "completed_tasks": len(self.get_completed_tasks()),
            "failed_tasks": len(self.get_failed_tasks()),
            "pending_tasks": len(self.get_pending_tasks()),
            "ready_tasks": len(self.get_ready_tasks())
        }


class PlannerRegistry:
    """
    Factory for planners.
    
    Builds planners using config from config_service.
    """
    
    def __init__(
        self, 
        config_service: ConfigService,
        llm_registry: LLMRegistry
    ):
        """
        Initialize planner registry.
        
        Args:
            config_service: Configuration service
            llm_registry: LLM registry
        """
        self.config_service = config_service
        self.llm_registry = llm_registry
        self._planner_instances: Dict[str, Callable] = {}
    
    def get_planner(self, name: str) -> Optional[Callable]:
        """
        Get planner instance by name.
        
        Args:
            name: Planner name/identifier
            
        Returns:
            Planner function or None if not found/configured
        """
        # Return cached instance if available
        if name in self._planner_instances:
            return self._planner_instances[name]
        
        # Get configuration
        config = self.config_service.get_planner_config(name)
        if not config:
            logger.error(f"Planner configuration not found: {name}")
            return None
        
        if not config.enabled:
            logger.warning(f"Planner is disabled: {name}")
            return None
        
        # Create planner instance
        try:
            planner = self._create_planner_instance(config)
            if planner:
                self._planner_instances[name] = planner
                return planner
            else:
                logger.error(f"Failed to create planner instance: {name}")
                return None
        except Exception as e:
            logger.error(f"Error creating planner instance {name}: {str(e)}")
            return None
    
    def _create_planner_instance(self, config: PlannerConfig) -> Optional[Callable]:
        """
        Create planner instance based on configuration.
        
        Args:
            config: Planner configuration
            
        Returns:
            Planner function or None if creation fails
        """
        planner_type = config.type.lower()
        
        if planner_type == "llm":
            return self._create_llm_planner(config)
        elif planner_type == "rules":
            return self._create_rules_planner(config)
        elif planner_type == "semantic":
            return self._create_semantic_planner(config)
        else:
            logger.error(f"Unsupported planner type: {planner_type}")
            return None
    
    def _create_llm_planner(self, config: PlannerConfig) -> Optional[Callable]:
        """
        Create LLM-based planner.
        
        Args:
            config: Planner configuration
            
        Returns:
            Planner function or None if creation fails
        """
        try:
            # Get LLM
            llm = self.llm_registry.get_llm(config.llm_name)
            if not llm:
                logger.error(f"LLM not found for planner {config.name}: {config.llm_name}")
                return None
            
            # Get system prompt
            system_prompt = config.parameters.get("system_prompt", """
            You are a task planner. Your job is to break down a complex task into smaller, manageable steps.
            For each step, provide:
            1. A clear description of what needs to be done
            2. The type of action required (tool_execution, llm_call, data_query, etc.)
            3. Any specific parameters or inputs needed
            
            Format your response as a JSON array of tasks, where each task has:
            - id: A unique identifier for the task
            - description: What needs to be done
            - action: The type of action required
            - parameters: Any specific parameters or inputs
            - dependencies: IDs of tasks that must be completed before this one
            - status: "ready" if it has no dependencies, otherwise "pending"
            """)
            
            # Create prompt template
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=system_prompt),
                HumanMessage(content="{input}")
            ])
            
            # Create chain
            chain = prompt | llm
            
            # Create planner function
            def llm_planner(input_text: str, intent: str = None, metadata: Dict[str, Any] = None) -> TaskPlan:
                """
                LLM-based planner function.
                
                Args:
                    input_text: User input
                    intent: Detected intent
                    metadata: Additional metadata
                    
                Returns:
                    Task plan
                """
                try:
                    # Add intent to input if provided
                    if intent:
                        input_text = f"Intent: {intent}\nInput: {input_text}"
                    
                    # Add metadata to input if provided
                    if metadata:
                        metadata_str = "\n".join([f"{k}: {v}" for k, v in metadata.items()])
                        input_text = f"{input_text}\nContext:\n{metadata_str}"
                    
                    # Invoke chain
                    result = chain.invoke({"input": input_text})
                    
                    # Parse result
                    import json
                    
                    # Extract JSON from result
                    if isinstance(result, str):
                        # Try to find JSON array in the string
                        import re
                        json_match = re.search(r'\[\s*{.*}\s*\]', result, re.DOTALL)
                        if json_match:
                            tasks = json.loads(json_match.group(0))
                        else:
                            # Try to parse the whole string as JSON
                            tasks = json.loads(result)
                    else:
                        # If result is already a structured object
                        tasks = result
                    
                    # Ensure tasks is a list
                    if not isinstance(tasks, list):
                        tasks = [tasks]
                    
                    # Create plan
                    plan_metadata = {
                        "planner": config.name,
                        "intent": intent,
                        "input": input_text
                    }
                    if metadata:
                        plan_metadata.update(metadata)
                    
                    return TaskPlan(
                        tasks=tasks,
                        metadata=plan_metadata
                    )
                    
                except Exception as e:
                    logger.error(f"Error in LLM planner: {str(e)}")
                    # Return a simple plan with an error task
                    error_task = {
                        "id": "error",
                        "description": f"Error in planner: {str(e)}",
                        "action": "llm_call",
                        "parameters": {"input": input_text},
                        "dependencies": [],
                        "status": "ready"
                    }
                    
                    error_metadata = {
                        "planner": config.name,
                        "intent": intent,
                        "input": input_text,
                        "error": str(e)
                    }
                    if metadata:
                        error_metadata.update(metadata)
                    
                    return TaskPlan(
                        tasks=[error_task],
                        metadata=error_metadata
                    )
            
            return llm_planner
            
        except Exception as e:
            logger.error(f"Error creating LLM planner: {str(e)}")
            return None
    
    def _create_rules_planner(self, config: PlannerConfig) -> Optional[Callable]:
        """
        Create rules-based planner.
        
        Args:
            config: Planner configuration
            
        Returns:
            Planner function or None if creation fails
        """
        try:
            # Get rules from configuration
            rules = config.parameters.get("rules", [])
            
            # Create planner function
            def rules_planner(input_text: str, intent: str = None, metadata: Dict[str, Any] = None) -> TaskPlan:
                """
                Rules-based planner function.
                
                Args:
                    input_text: User input
                    intent: Detected intent
                    metadata: Additional metadata
                    
                Returns:
                    Task plan
                """
                try:
                    # Default to a simple plan with a single task
                    tasks = [{
                        "id": "default",
                        "description": "Process user request",
                        "action": "llm_call",
                        "parameters": {"input": input_text},
                        "dependencies": [],
                        "status": "ready"
                    }]
                    
                    # Apply rules based on intent
                    if intent:
                        for rule in rules:
                            if rule.get("intent") == intent:
                                tasks = rule.get("tasks", tasks)
                                break
                    
                    # Create plan
                    plan_metadata = {
                        "planner": config.name,
                        "intent": intent,
                        "input": input_text
                    }
                    if metadata:
                        plan_metadata.update(metadata)
                    
                    return TaskPlan(
                        tasks=tasks,
                        metadata=plan_metadata
                    )
                    
                except Exception as e:
                    logger.error(f"Error in rules planner: {str(e)}")
                    # Return a simple plan with an error task
                    error_task = {
                        "id": "error",
                        "description": f"Error in planner: {str(e)}",
                        "action": "llm_call",
                        "parameters": {"input": input_text},
                        "dependencies": [],
                        "status": "ready"
                    }
                    
                    error_metadata = {
                        "planner": config.name,
                        "intent": intent,
                        "input": input_text,
                        "error": str(e)
                    }
                    if metadata:
                        error_metadata.update(metadata)
                    
                    return TaskPlan(
                        tasks=[error_task],
                        metadata=error_metadata
                    )
            
            return rules_planner
            
        except Exception as e:
            logger.error(f"Error creating rules planner: {str(e)}")
            return None
    
    def _create_semantic_planner(self, config: PlannerConfig) -> Optional[Callable]:
        """
        Create semantic-layer planner.
        
        Args:
            config: Planner configuration
            
        Returns:
            Planner function or None if creation fails
        """
        try:
            # Get API endpoint from configuration
            api_endpoint = config.parameters.get("api_endpoint")
            if not api_endpoint:
                logger.error(f"API endpoint not configured for semantic planner: {config.name}")
                return None
            
            # Create planner function
            def semantic_planner(input_text: str, intent: str = None, metadata: Dict[str, Any] = None) -> TaskPlan:
                """
                Semantic-layer planner function.
                
                Args:
                    input_text: User input
                    intent: Detected intent
                    metadata: Additional metadata
                    
                Returns:
                    Task plan
                """
                try:
                    import httpx
                    
                    # Prepare request payload
                    payload = {
                        "input": input_text,
                        "intent": intent,
                        "metadata": metadata
                    }
                    
                    # Make request to semantic API
                    response = httpx.post(
                        api_endpoint,
                        json=payload,
                        timeout=30
                    )
                    
                    # Parse response
                    result = response.json()
                    
                    # Extract tasks from response
                    tasks = result.get("tasks", [])
                    
                    # Create plan
                    plan_metadata = {
                        "planner": config.name,
                        "intent": intent,
                        "input": input_text
                    }
                    if metadata:
                        plan_metadata.update(metadata)
                    
                    return TaskPlan(
                        tasks=tasks,
                        metadata=plan_metadata
                    )
                    
                except Exception as e:
                    logger.error(f"Error in semantic planner: {str(e)}")
                    # Return a simple plan with an error task
                    error_task = {
                        "id": "error",
                        "description": f"Error in planner: {str(e)}",
                        "action": "llm_call",
                        "parameters": {"input": input_text},
                        "dependencies": [],
                        "status": "ready"
                    }
                    
                    error_metadata = {
                        "planner": config.name,
                        "intent": intent,
                        "input": input_text,
                        "error": str(e)
                    }
                    if metadata:
                        error_metadata.update(metadata)
                    
                    return TaskPlan(
                        tasks=[error_task],
                        metadata=error_metadata
                    )
            
            return semantic_planner
            
        except Exception as e:
            logger.error(f"Error creating semantic planner: {str(e)}")
            return None
    
    def list_available_planners(self) -> List[str]:
        """
        List names of all available planners.
        
        Returns:
            List of planner names
        """
        configs = self.config_service.list_planners()
        return [config.name for config in configs if config.enabled]
    
    def refresh_planner(self, name: str) -> bool:
        """
        Refresh planner instance by name.
        
        Args:
            name: Planner name/identifier
            
        Returns:
            True if successful, False otherwise
        """
        if name in self._planner_instances:
            del self._planner_instances[name]
        
        return self.get_planner(name) is not None
    
    def refresh_all_planners(self) -> None:
        """Refresh all planner instances."""
        self._planner_instances.clear()
