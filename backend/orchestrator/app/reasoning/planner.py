"""
Planner - Task decomposition and planning logic.

Pure logic module - no HTTP or IO operations.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Task:
    """
    Individual task in a plan.
    
    Attributes:
        id: Unique task identifier
        description: Task description
        action: Action to perform (llm_call, tool_execution, etc.)
        parameters: Task parameters
        dependencies: List of task IDs this task depends on
        status: Current task status
        result: Task execution result
    """
    id: str
    description: str
    action: str
    parameters: Dict[str, Any]
    dependencies: List[str] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    
    def __post_init__(self):
        """Initialize dependencies if None."""
        if self.dependencies is None:
            self.dependencies = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "description": self.description,
            "action": self.action,
            "parameters": self.parameters,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "result": self.result
        }


@dataclass
class TaskPlan:
    """
    Complete task execution plan.
    
    Attributes:
        tasks: List of tasks to execute
        metadata: Plan metadata
    """
    tasks: List[Task]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize metadata if None."""
        if self.metadata is None:
            self.metadata = {}
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready to execute (dependencies met)."""
        ready = []
        for task in self.tasks:
            if task.status != TaskStatus.PENDING:
                continue
            
            # Check if all dependencies are completed
            deps_met = all(
                self.get_task(dep_id).status == TaskStatus.COMPLETED
                for dep_id in task.dependencies
            )
            
            if deps_met:
                ready.append(task)
        
        return ready
    
    def is_complete(self) -> bool:
        """Check if all tasks are completed or failed."""
        return all(
            task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED]
            for task in self.tasks
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tasks": [task.to_dict() for task in self.tasks],
            "metadata": self.metadata
        }


class Planner:
    """
    Task planner for decomposing complex requests.
    
    Analyzes requests and creates execution plans.
    """
    
    def __init__(self):
        """Initialize planner."""
        pass
    
    def create_plan(
        self,
        user_input: str,
        intent: str,
        context: Optional[Dict[str, Any]] = None
    ) -> TaskPlan:
        """
        Create execution plan for user request.
        
        Args:
            user_input: User's input text
            intent: Classified intent
            context: Optional context information
            
        Returns:
            TaskPlan with decomposed tasks
        """
        logger.info(f"[Planner] Creating plan for intent: {intent}")
        
        # Simple planning logic - can be enhanced with LLM-based planning
        if intent == "churn_analytics":
            return self._plan_churn_analytics(user_input, context)
        elif intent == "data_query":
            return self._plan_data_query(user_input, context)
        elif intent == "code_generation":
            return self._plan_code_generation(user_input, context)
        elif intent == "web_search":
            return self._plan_web_search(user_input, context)
        elif intent == "tool_execution":
            return self._plan_tool_execution(user_input, context)
        else:
            return self._plan_general_llm(user_input, context)
    
    def _plan_churn_analytics(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]]
    ) -> TaskPlan:
        """Create plan for churn analytics."""
        tasks = [
            Task(
                id="task_1",
                description="Retrieve customer data",
                action="data_query",
                parameters={"query": "SELECT * FROM customers"}
            ),
            Task(
                id="task_2",
                description="Analyze churn patterns",
                action="external_agent",
                parameters={"agent": "zain_agent", "task": "churn_analysis"},
                dependencies=["task_1"]
            ),
            Task(
                id="task_3",
                description="Generate insights report",
                action="llm_call",
                parameters={"prompt": "Summarize churn analysis results"},
                dependencies=["task_2"]
            )
        ]
        
        return TaskPlan(
            tasks=tasks,
            metadata={"intent": "churn_analytics", "complexity": "high"}
        )
    
    def _plan_data_query(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]]
    ) -> TaskPlan:
        """Create plan for data query."""
        tasks = [
            Task(
                id="task_1",
                description="Execute data query",
                action="data_query",
                parameters={"query": user_input}
            ),
            Task(
                id="task_2",
                description="Format results",
                action="llm_call",
                parameters={"prompt": "Format query results for user"},
                dependencies=["task_1"]
            )
        ]
        
        return TaskPlan(
            tasks=tasks,
            metadata={"intent": "data_query", "complexity": "medium"}
        )
    
    def _plan_code_generation(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]]
    ) -> TaskPlan:
        """Create plan for code generation."""
        tasks = [
            Task(
                id="task_1",
                description="Generate code",
                action="llm_call",
                parameters={"prompt": user_input, "mode": "code_generation"}
            ),
            Task(
                id="task_2",
                description="Execute code (if requested)",
                action="tool_execution",
                parameters={"tool": "code_executor"},
                dependencies=["task_1"]
            )
        ]
        
        return TaskPlan(
            tasks=tasks,
            metadata={"intent": "code_generation", "complexity": "medium"}
        )
    
    def _plan_web_search(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]]
    ) -> TaskPlan:
        """Create plan for web search."""
        tasks = [
            Task(
                id="task_1",
                description="Search the web",
                action="tool_execution",
                parameters={"tool": "web_search", "query": user_input}
            ),
            Task(
                id="task_2",
                description="Synthesize search results",
                action="llm_call",
                parameters={"prompt": "Summarize search results"},
                dependencies=["task_1"]
            )
        ]
        
        return TaskPlan(
            tasks=tasks,
            metadata={"intent": "web_search", "complexity": "low"}
        )
    
    def _plan_tool_execution(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]]
    ) -> TaskPlan:
        """Create plan for tool execution."""
        tasks = [
            Task(
                id="task_1",
                description="Execute tool",
                action="tool_execution",
                parameters={"input": user_input}
            )
        ]
        
        return TaskPlan(
            tasks=tasks,
            metadata={"intent": "tool_execution", "complexity": "low"}
        )
    
    def _plan_general_llm(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]]
    ) -> TaskPlan:
        """Create plan for general LLM interaction."""
        tasks = [
            Task(
                id="task_1",
                description="Process with LLM",
                action="llm_call",
                parameters={"prompt": user_input}
            )
        ]
        
        return TaskPlan(
            tasks=tasks,
            metadata={"intent": "general_llm", "complexity": "low"}
        )
