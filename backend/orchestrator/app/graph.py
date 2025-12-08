"""
Orchestration Graph - Main execution flow using state machine pattern.

Implements the orchestration flow:
Client → Intent Router → Planner → LLM/External Agent/Tools → Grounding → Memory → Response

Uses Settings and client abstractions - NO hard-coded endpoints.
"""

import logging
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from .config import Settings
from .clients import LLMClient, ExternalAgentClient, DataSourceClient
from .memory import ConversationMemory, CacheManager, StateStore
from .tools import ToolRegistry
from .reasoning import classify_intent, Planner, TaskPlan, TaskStatus

logger = logging.getLogger(__name__)


@dataclass
class GraphState:
    """
    State object passed through the graph.
    
    Contains all information needed for orchestration.
    """
    # Input
    user_input: str
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Execution tracking
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    current_node: str = "start"
    iteration: int = 0
    
    # Intent and planning
    intent: Optional[str] = None
    intent_confidence: float = 0.0
    plan: Optional[TaskPlan] = None
    
    # Results
    llm_response: Optional[str] = None
    tool_results: List[Dict[str, Any]] = field(default_factory=list)
    external_agent_result: Optional[Dict[str, Any]] = None
    grounding_data: Optional[Dict[str, Any]] = None
    
    # Final output
    answer: Optional[str] = None
    final_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Error handling
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            "user_input": self.user_input,
            "user_id": self.user_id,
            "metadata": self.metadata,
            "execution_id": self.execution_id,
            "current_node": self.current_node,
            "iteration": self.iteration,
            "intent": self.intent,
            "intent_confidence": self.intent_confidence,
            "plan": self.plan.to_dict() if self.plan else None,
            "answer": self.answer,
            "final_metadata": self.final_metadata,
            "error": self.error
        }


class OrchestrationGraph:
    """
    Main orchestration graph that coordinates the execution flow.
    
    Implements a state machine pattern for flexible orchestration.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize orchestration graph.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        
        # Initialize clients
        self.llm_client = LLMClient(settings)
        self.external_agent_client = ExternalAgentClient(settings)
        self.datasource_client = DataSourceClient(settings)
        
        # Initialize memory and cache
        self.conversation_memory = ConversationMemory(settings)
        self.cache_manager = CacheManager(settings)
        self.state_store = StateStore(settings)
        
        # Initialize tools
        self.tool_registry = ToolRegistry()
        
        # Initialize planner
        self.planner = Planner()
        
        # Node routing
        self.nodes = {
            "start": self.start_node,
            "intent_router": self.intent_router_node,
            "planner": self.planner_node,
            "llm_agent": self.llm_agent_node,
            "external_agent": self.external_agent_node,
            "tool_executor": self.tool_executor_node,
            "grounding": self.grounding_node,
            "memory_store": self.memory_store_node,
            "end": self.end_node
        }
    
    async def execute(self, state: GraphState) -> GraphState:
        """
        Execute the orchestration graph.
        
        Args:
            state: Initial graph state
            
        Returns:
            Final graph state with results
        """
        logger.info(f"[Graph] Starting execution {state.execution_id}")
        
        max_iterations = self.settings.orchestration_max_iterations
        
        try:
            while state.current_node != "end" and state.iteration < max_iterations:
                state.iteration += 1
                
                # Get current node function
                node_func = self.nodes.get(state.current_node)
                if not node_func:
                    state.error = f"Unknown node: {state.current_node}"
                    state.current_node = "end"
                    break
                
                # Execute node
                logger.info(f"[Graph] Executing node: {state.current_node} (iteration {state.iteration})")
                state = await node_func(state)
                
                # Save state
                await self.state_store.save_state(state.execution_id, state.to_dict())
                
                # Check for errors
                if state.error:
                    logger.error(f"[Graph] Error in node {state.current_node}: {state.error}")
                    state.current_node = "end"
                    break
            
            if state.iteration >= max_iterations:
                state.error = "Maximum iterations exceeded"
                logger.warning(f"[Graph] Max iterations exceeded for {state.execution_id}")
            
            logger.info(f"[Graph] Completed execution {state.execution_id}")
            return state
            
        except Exception as e:
            logger.error(f"[Graph] Execution error: {str(e)}")
            state.error = str(e)
            state.current_node = "end"
            return state
    
    async def start_node(self, state: GraphState) -> GraphState:
        """Start node - initializes execution."""
        logger.info("[Graph:Start] Initializing execution")
        state.current_node = "intent_router"
        return state
    
    async def intent_router_node(self, state: GraphState) -> GraphState:
        """Intent router node - classifies user intent."""
        logger.info("[Graph:IntentRouter] Classifying intent")
        
        try:
            # Classify intent
            classification = classify_intent(state.user_input, state.metadata)
            state.intent = classification["intent"]
            state.intent_confidence = classification["confidence"]
            
            logger.info(f"[Graph:IntentRouter] Intent: {state.intent} (confidence: {state.intent_confidence})")
            
            # Route to planner for complex intents
            if state.intent in ["churn_analytics", "data_query", "code_generation"]:
                state.current_node = "planner"
            else:
                # Simple intents go directly to execution
                state.current_node = self._route_by_intent(state.intent)
            
        except Exception as e:
            state.error = f"Intent classification error: {str(e)}"
        
        return state
    
    def _route_by_intent(self, intent: str) -> str:
        """Route to appropriate node based on intent."""
        routing = {
            "general_llm": "llm_agent",
            "web_search": "tool_executor",
            "tool_execution": "tool_executor",
            "external_agent": "external_agent",
            "unknown": "llm_agent"
        }
        return routing.get(intent, "llm_agent")
    
    async def planner_node(self, state: GraphState) -> GraphState:
        """Planner node - decomposes complex tasks."""
        logger.info("[Graph:Planner] Creating execution plan")
        
        try:
            # Create plan
            state.plan = self.planner.create_plan(
                state.user_input,
                state.intent,
                state.metadata
            )
            
            logger.info(f"[Graph:Planner] Created plan with {len(state.plan.tasks)} tasks")
            
            # Execute plan (simplified - execute first ready task)
            ready_tasks = state.plan.get_ready_tasks()
            if ready_tasks:
                first_task = ready_tasks[0]
                state.current_node = self._route_by_action(first_task.action)
            else:
                state.current_node = "end"
            
        except Exception as e:
            state.error = f"Planning error: {str(e)}"
        
        return state
    
    def _route_by_action(self, action: str) -> str:
        """Route to appropriate node based on action."""
        routing = {
            "llm_call": "llm_agent",
            "tool_execution": "tool_executor",
            "external_agent": "external_agent",
            "data_query": "grounding"
        }
        return routing.get(action, "llm_agent")
    
    async def llm_agent_node(self, state: GraphState) -> GraphState:
        """LLM agent node - calls configured LLM."""
        logger.info("[Graph:LLMAgent] Calling LLM")
        
        try:
            # Get conversation context
            context = await self.conversation_memory.get_context(
                state.user_id or "default"
            )
            
            # Add current message
            messages = context + [
                {"role": "user", "content": state.user_input}
            ]
            
            # Call LLM
            result = await self.llm_client.call(messages=messages)
            
            # Extract response
            response_data = result["response"]
            if "choices" in response_data and len(response_data["choices"]) > 0:
                state.llm_response = response_data["choices"][0]["message"]["content"]
            else:
                state.llm_response = str(response_data)
            
            logger.info("[Graph:LLMAgent] LLM call successful")
            
            # Route to memory store
            state.current_node = "memory_store"
            
        except Exception as e:
            state.error = f"LLM error: {str(e)}"
            logger.error(f"[Graph:LLMAgent] Error: {str(e)}")
        
        return state
    
    async def external_agent_node(self, state: GraphState) -> GraphState:
        """External agent node - calls external agent."""
        logger.info("[Graph:ExternalAgent] Calling external agent")
        
        try:
            # Call external agent
            result = await self.external_agent_client.call(
                endpoint="/execute",
                payload={
                    "task": state.user_input,
                    "context": state.metadata
                }
            )
            
            state.external_agent_result = result
            
            if result.get("success"):
                logger.info("[Graph:ExternalAgent] External agent call successful")
            else:
                logger.warning(f"[Graph:ExternalAgent] External agent returned error: {result.get('error')}")
            
            # Route to memory store
            state.current_node = "memory_store"
            
        except Exception as e:
            state.error = f"External agent error: {str(e)}"
            logger.error(f"[Graph:ExternalAgent] Error: {str(e)}")
        
        return state
    
    async def tool_executor_node(self, state: GraphState) -> GraphState:
        """Tool executor node - executes tools."""
        logger.info("[Graph:ToolExecutor] Executing tools")
        
        try:
            # Get available tools
            tools = self.tool_registry.get_all_tools()
            
            if not tools:
                state.error = "No tools registered"
                return state
            
            # Simple execution - execute first available tool
            # In production, this would be more sophisticated
            tool_name = list(tools.keys())[0]
            tool = tools[tool_name]
            
            result = await tool.execute(query=state.user_input)
            
            state.tool_results.append({
                "tool": tool_name,
                "result": result.to_dict()
            })
            
            logger.info(f"[Graph:ToolExecutor] Executed tool: {tool_name}")
            
            # Route to memory store
            state.current_node = "memory_store"
            
        except Exception as e:
            state.error = f"Tool execution error: {str(e)}"
            logger.error(f"[Graph:ToolExecutor] Error: {str(e)}")
        
        return state
    
    async def grounding_node(self, state: GraphState) -> GraphState:
        """Grounding node - retrieval and data fusion."""
        logger.info("[Graph:Grounding] Performing grounding")
        
        try:
            if self.settings.grounding_enabled:
                # Query data source
                result = await self.datasource_client.query(
                    query=state.user_input,
                    parameters={}
                )
                
                state.grounding_data = result
                logger.info("[Graph:Grounding] Grounding data retrieved")
            
            # Route to LLM for synthesis
            state.current_node = "llm_agent"
            
        except Exception as e:
            state.error = f"Grounding error: {str(e)}"
            logger.error(f"[Graph:Grounding] Error: {str(e)}")
        
        return state
    
    async def memory_store_node(self, state: GraphState) -> GraphState:
        """Memory store node - saves conversation and results."""
        logger.info("[Graph:MemoryStore] Storing results")
        
        try:
            # Save user message
            await self.conversation_memory.add_message(
                user_id=state.user_id or "default",
                role="user",
                content=state.user_input,
                metadata=state.metadata
            )
            
            # Determine final answer
            if state.llm_response:
                state.answer = state.llm_response
            elif state.external_agent_result:
                state.answer = str(state.external_agent_result.get("data", ""))
            elif state.tool_results:
                state.answer = str(state.tool_results[-1].get("result", {}).get("output", ""))
            else:
                state.answer = "No response generated"
            
            # Save assistant message
            await self.conversation_memory.add_message(
                user_id=state.user_id or "default",
                role="assistant",
                content=state.answer,
                metadata=state.final_metadata
            )
            
            logger.info("[Graph:MemoryStore] Results stored")
            
            # Route to end
            state.current_node = "end"
            
        except Exception as e:
            state.error = f"Memory store error: {str(e)}"
            logger.error(f"[Graph:MemoryStore] Error: {str(e)}")
        
        return state
    
    async def end_node(self, state: GraphState) -> GraphState:
        """End node - finalizes execution."""
        logger.info("[Graph:End] Finalizing execution")
        
        # Populate final metadata
        state.final_metadata.update({
            "execution_id": state.execution_id,
            "intent": state.intent,
            "intent_confidence": state.intent_confidence,
            "iterations": state.iteration,
            "has_error": state.error is not None
        })
        
        return state
    
    async def close(self):
        """Close all clients and connections."""
        await self.llm_client.close()
        await self.external_agent_client.close()
        await self.datasource_client.close()
        await self.conversation_memory.close()
        await self.cache_manager.close()
        await self.state_store.close()
