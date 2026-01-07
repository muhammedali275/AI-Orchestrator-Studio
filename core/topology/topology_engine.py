"""
Topology Engine - Central orchestration engine.

Uses LangChain or LangGraph behind the scenes.
Loads topology definition from config_service.
Executes nodes in a state-machine order.
"""

import logging
import time
import uuid
from typing import Dict, Any, Optional, List, Union, Callable

from ..config.config_service import ConfigService, TopologyConfig
from ..agent.agent_registry import AgentRegistry
from ..planner_router.planner_registry import PlannerRegistry
from ..planner_router.router_registry import RouterRegistry
from ..tools.tool_registry import ToolRegistry
from ..memory_cache.memory_service import MemoryService
from ..memory_cache.cache_service import CacheService

logger = logging.getLogger(__name__)


class TopologyEngine:
    """
    Central orchestration engine for AIPanel.
    
    Uses LangChain or LangGraph behind the scenes.
    Loads topology definition from config_service.
    Executes nodes in a state-machine order.
    """
    
    def __init__(
        self,
        config_service: ConfigService,
        agent_registry: AgentRegistry,
        planner_registry: PlannerRegistry,
        router_registry: RouterRegistry,
        tool_registry: ToolRegistry,
        memory_service: MemoryService,
        cache_service: CacheService
    ):
        """
        Initialize topology engine.
        
        Args:
            config_service: Configuration service
            agent_registry: Agent registry
            planner_registry: Planner registry
            router_registry: Router registry
            tool_registry: Tool registry
            memory_service: Memory service
            cache_service: Cache service
        """
        self.config_service = config_service
        self.agent_registry = agent_registry
        self.planner_registry = planner_registry
        self.router_registry = router_registry
        self.tool_registry = tool_registry
        self.memory_service = memory_service
        self.cache_service = cache_service
        
        # Initialize node registry
        self._node_registry = {}
        self._register_builtin_nodes()
        
        # Initialize topology registry
        self._topology_registry = {}
        self._initialize_topologies()
    
    def _register_builtin_nodes(self) -> None:
        """Register built-in nodes."""
        # Import nodes
        from .nodes.start_node import start_node
        from .nodes.intent_router_node import intent_router_node
        from .nodes.planner_node import planner_node
        from .nodes.llm_agent_node import llm_agent_node
        from .nodes.external_agent_node import external_agent_node
        from .nodes.tool_executor_node import tool_executor_node
        from .nodes.grounding_node import grounding_node
        from .nodes.memory_store_node import memory_store_node
        from .nodes.audit_node import audit_node
        from .nodes.end_node import end_node
        from .nodes.error_handler_node import error_handler_node
        
        # Register nodes
        self._register_node("start", start_node)
        self._register_node("intent_router", intent_router_node)
        self._register_node("planner", planner_node)
        self._register_node("llm_agent", llm_agent_node)
        self._register_node("external_agent", external_agent_node)
        self._register_node("tool_executor", tool_executor_node)
        self._register_node("grounding", grounding_node)
        self._register_node("memory_store", memory_store_node)
        self._register_node("audit", audit_node)
        self._register_node("end", end_node)
        self._register_node("error_handler", error_handler_node)
    
    def _register_node(self, node_type: str, node_factory: Callable) -> None:
        """
        Register node factory.
        
        Args:
            node_type: Node type
            node_factory: Node factory function
        """
        self._node_registry[node_type] = node_factory
    
    def _initialize_topologies(self) -> None:
        """Initialize topologies from configuration."""
        # Get topology configurations
        topology_configs = self.config_service.list_topologies()
        
        # Initialize topologies
        for config in topology_configs:
            if config.enabled:
                try:
                    self._initialize_topology(config)
                except Exception as e:
                    logger.error(f"Error initializing topology {config.name}: {str(e)}")
    
    def _initialize_topology(self, config: TopologyConfig) -> None:
        """
        Initialize topology from configuration.
        
        Args:
            config: Topology configuration
        """
        try:
            # Determine topology type
            topology_type = config.type.lower()
            
            if topology_type == "langgraph":
                self._initialize_langgraph_topology(config)
            elif topology_type == "langchain":
                self._initialize_langchain_topology(config)
            else:
                logger.error(f"Unsupported topology type: {topology_type}")
        except Exception as e:
            logger.error(f"Error initializing topology {config.name}: {str(e)}")
    
    def _initialize_langgraph_topology(self, config: TopologyConfig) -> None:
        """
        Initialize LangGraph topology.
        
        Args:
            config: Topology configuration
        """
        try:
            from langgraph.graph import StateGraph
            
            # Create state graph
            graph = StateGraph()
            
            # Add nodes
            for node_config in config.nodes:
                node_type = node_config.get("type")
                node_name = node_config.get("name", node_type)
                
                if node_type in self._node_registry:
                    # Create node
                    node_factory = self._node_registry[node_type]
                    node = node_factory(
                        config=node_config,
                        agent_registry=self.agent_registry,
                        planner_registry=self.planner_registry,
                        router_registry=self.router_registry,
                        tool_registry=self.tool_registry,
                        memory_service=self.memory_service,
                        cache_service=self.cache_service,
                        config_service=self.config_service
                    )
                    
                    # Add node to graph
                    graph.add_node(node_name, node)
                else:
                    logger.error(f"Unknown node type: {node_type}")
            
            # Add edges
            for edge in config.edges:
                source = edge.get("source")
                target = edge.get("target")
                condition = edge.get("condition")
                
                if condition:
                    # Conditional edge
                    graph.add_conditional_edges(
                        source,
                        lambda state, condition=condition: self._evaluate_condition(state, condition),
                        {
                            True: target,
                            False: edge.get("fallback", "error_handler")
                        }
                    )
                else:
                    # Direct edge
                    graph.add_edge(source, target)
            
            # Set entry point
            graph.set_entry_point(config.entry_point or "start")
            
            # Compile graph
            compiled_graph = graph.compile()
            
            # Store topology
            self._topology_registry[config.name] = {
                "type": "langgraph",
                "graph": compiled_graph,
                "config": config
            }
            
            logger.info(f"Initialized LangGraph topology: {config.name}")
            
        except ImportError:
            logger.error("LangGraph not installed. Install with 'pip install langgraph'")
        except Exception as e:
            logger.error(f"Error initializing LangGraph topology {config.name}: {str(e)}")
    
    def _initialize_langchain_topology(self, config: TopologyConfig) -> None:
        """
        Initialize LangChain topology.
        
        Args:
            config: Topology configuration
        """
        try:
            from langchain_core.runnables import RunnablePassthrough, RunnableSequence
            
            # Create nodes
            nodes = {}
            for node_config in config.nodes:
                node_type = node_config.get("type")
                node_name = node_config.get("name", node_type)
                
                if node_type in self._node_registry:
                    # Create node
                    node_factory = self._node_registry[node_type]
                    node = node_factory(
                        config=node_config,
                        agent_registry=self.agent_registry,
                        planner_registry=self.planner_registry,
                        router_registry=self.router_registry,
                        tool_registry=self.tool_registry,
                        memory_service=self.memory_service,
                        cache_service=self.cache_service,
                        config_service=self.config_service
                    )
                    
                    # Add node to nodes
                    nodes[node_name] = node
                else:
                    logger.error(f"Unknown node type: {node_type}")
            
            # Create sequence
            sequence = []
            current_node = config.entry_point or "start"
            
            while current_node:
                # Add node to sequence
                if current_node in nodes:
                    sequence.append(nodes[current_node])
                else:
                    logger.error(f"Node not found: {current_node}")
                    break
                
                # Find next node
                next_node = None
                for edge in config.edges:
                    if edge.get("source") == current_node:
                        next_node = edge.get("target")
                        break
                
                current_node = next_node
            
            # Create runnable sequence
            runnable = RunnableSequence(sequence)
            
            # Store topology
            self._topology_registry[config.name] = {
                "type": "langchain",
                "runnable": runnable,
                "config": config
            }
            
            logger.info(f"Initialized LangChain topology: {config.name}")
            
        except ImportError:
            logger.error("LangChain not installed. Install with 'pip install langchain'")
        except Exception as e:
            logger.error(f"Error initializing LangChain topology {config.name}: {str(e)}")
    
    def _evaluate_condition(self, state: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """
        Evaluate condition.
        
        Args:
            state: Current state
            condition: Condition to evaluate
            
        Returns:
            True if condition is met, False otherwise
        """
        try:
            condition_type = condition.get("type")
            
            if condition_type == "equals":
                # Check if field equals value
                field = condition.get("field")
                value = condition.get("value")
                
                if field in state:
                    return state[field] == value
                
                return False
            
            elif condition_type == "contains":
                # Check if field contains value
                field = condition.get("field")
                value = condition.get("value")
                
                if field in state and isinstance(state[field], (str, list, dict)):
                    return value in state[field]
                
                return False
            
            elif condition_type == "not_empty":
                # Check if field is not empty
                field = condition.get("field")
                
                if field in state:
                    return bool(state[field])
                
                return False
            
            elif condition_type == "has_error":
                # Check if state has error
                return "error" in state and state["error"]
            
            else:
                logger.error(f"Unknown condition type: {condition_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error evaluating condition: {str(e)}")
            return False
    
    async def execute(
        self,
        topology_name: str,
        input_text: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        client_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute topology.
        
        Args:
            topology_name: Topology name
            input_text: Input text
            user_id: User ID
            conversation_id: Conversation ID (generated if not provided)
            client_id: Client ID
            metadata: Additional metadata
            
        Returns:
            Execution result
        """
        # Check if topology exists
        if topology_name not in self._topology_registry:
            logger.error(f"Topology not found: {topology_name}")
            return {
                "error": f"Topology not found: {topology_name}",
                "output": f"Error: Topology not found: {topology_name}"
            }
        
        # Get topology
        topology = self._topology_registry[topology_name]
        
        # Generate conversation ID if not provided
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # Get or create conversation
        conversation = await self.memory_service.get_conversation(conversation_id)
        if not conversation:
            conversation = await self.memory_service.create_conversation(
                user_id=user_id,
                metadata={
                    "client_id": client_id,
                    "topology": topology_name,
                    **(metadata or {})
                }
            )
        
        # Add user message to conversation
        await self.memory_service.add_message(
            conversation_id=conversation_id,
            content=input_text,
            role="user",
            metadata=metadata
        )
        
        # Prepare initial state
        initial_state = {
            "input": input_text,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "client_id": client_id,
            "metadata": metadata or {},
            "timestamp": time.time(),
            "run_id": str(uuid.uuid4())
        }
        
        try:
            # Execute topology
            if topology["type"] == "langgraph":
                # Execute LangGraph topology
                result = await self._execute_langgraph_topology(topology, initial_state)
            else:
                # Execute LangChain topology
                result = await self._execute_langchain_topology(topology, initial_state)
            
            # Add assistant message to conversation
            output = result.get("output", "")
            await self.memory_service.add_message(
                conversation_id=conversation_id,
                content=output,
                role="assistant",
                metadata={
                    "run_id": initial_state["run_id"],
                    "topology": topology_name,
                    **(result.get("metadata", {}))
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing topology {topology_name}: {str(e)}")
            
            # Add error message to conversation
            error_message = f"Error: {str(e)}"
            await self.memory_service.add_message(
                conversation_id=conversation_id,
                content=error_message,
                role="assistant",
                metadata={
                    "run_id": initial_state["run_id"],
                    "topology": topology_name,
                    "error": str(e)
                }
            )
            
            return {
                "error": str(e),
                "output": error_message
            }
    
    async def _execute_langgraph_topology(
        self,
        topology: Dict[str, Any],
        initial_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute LangGraph topology.
        
        Args:
            topology: Topology
            initial_state: Initial state
            
        Returns:
            Execution result
        """
        # Get graph
        graph = topology["graph"]
        
        # Execute graph
        result = await graph.ainvoke(initial_state)
        
        return result
    
    async def _execute_langchain_topology(
        self,
        topology: Dict[str, Any],
        initial_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute LangChain topology.
        
        Args:
            topology: Topology
            initial_state: Initial state
            
        Returns:
            Execution result
        """
        # Get runnable
        runnable = topology["runnable"]
        
        # Execute runnable
        result = await runnable.ainvoke(initial_state)
        
        return result
    
    def refresh_topology(self, name: str) -> bool:
        """
        Refresh topology.
        
        Args:
            name: Topology name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get configuration
            config = self.config_service.get_topology_config(name)
            if not config:
                logger.error(f"Topology configuration not found: {name}")
                return False
            
            # Remove existing topology
            if name in self._topology_registry:
                del self._topology_registry[name]
            
            # Initialize topology
            if config.enabled:
                self._initialize_topology(config)
                return name in self._topology_registry
            
            return True
            
        except Exception as e:
            logger.error(f"Error refreshing topology {name}: {str(e)}")
            return False
    
    def refresh_all_topologies(self) -> None:
        """Refresh all topologies."""
        # Clear topology registry
        self._topology_registry.clear()
        
        # Initialize topologies
        self._initialize_topologies()
    
    def list_available_topologies(self) -> List[str]:
        """
        List names of all available topologies.
        
        Returns:
            List of topology names
        """
        return list(self._topology_registry.keys())
    
    def get_topology_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get topology information.
        
        Args:
            name: Topology name
            
        Returns:
            Topology information or None if not found
        """
        if name not in self._topology_registry:
            return None
        
        topology = self._topology_registry[name]
        config = topology["config"]
        
        return {
            "name": config.name,
            "type": config.type,
            "description": config.description,
            "entry_point": config.entry_point,
            "nodes": [
                {
                    "name": node.get("name", node.get("type")),
                    "type": node.get("type"),
                    "description": node.get("description", "")
                }
                for node in config.nodes
            ],
            "edges": [
                {
                    "source": edge.get("source"),
                    "target": edge.get("target"),
                    "condition": edge.get("condition"),
                    "fallback": edge.get("fallback")
                }
                for edge in config.edges
            ]
        }
