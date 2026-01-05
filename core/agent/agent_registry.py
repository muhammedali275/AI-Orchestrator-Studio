"""
Agent Registry - Factory for LangChain Agents.

Builds LangChain-compatible agents using config from config_service.
Defines agents by name for external integrations.
"""

import logging
from typing import Dict, Any, Optional, List, Union

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage
from langchain.schema.runnable import RunnablePassthrough
from langchain.memory import ConversationBufferMemory

from ..config.config_service import ConfigService, AgentConfig
from ..llm.llm_registry import LLMRegistry
from ..tools.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Factory for LangChain Agents.
    
    Builds LangChain-compatible agents using config from config_service.
    """
    
    def __init__(
        self, 
        config_service: ConfigService,
        llm_registry: LLMRegistry,
        tool_registry: ToolRegistry
    ):
        """
        Initialize agent registry.
        
        Args:
            config_service: Configuration service
            llm_registry: LLM registry
            tool_registry: Tool registry
        """
        self.config_service = config_service
        self.llm_registry = llm_registry
        self.tool_registry = tool_registry
        self._agent_instances: Dict[str, AgentExecutor] = {}
    
    def get_agent(self, name: str) -> Optional[AgentExecutor]:
        """
        Get agent instance by name.
        
        Args:
            name: Agent name/identifier
            
        Returns:
            LangChain agent instance or None if not found/configured
        """
        # Return cached instance if available
        if name in self._agent_instances:
            return self._agent_instances[name]
        
        # Get configuration
        config = self.config_service.get_agent_config(name)
        if not config:
            logger.error(f"Agent configuration not found: {name}")
            return None
        
        if not config.enabled:
            logger.warning(f"Agent is disabled: {name}")
            return None
        
        # Create agent instance
        try:
            agent = self._create_agent_instance(config)
            if agent:
                self._agent_instances[name] = agent
                return agent
            else:
                logger.error(f"Failed to create agent instance: {name}")
                return None
        except Exception as e:
            logger.error(f"Error creating agent instance {name}: {str(e)}")
            return None
    
    def _create_agent_instance(self, config: AgentConfig) -> Optional[AgentExecutor]:
        """
        Create agent instance based on configuration.
        
        Args:
            config: Agent configuration
            
        Returns:
            LangChain agent instance or None if creation fails
        """
        try:
            # Get LLM
            llm = self.llm_registry.get_llm(config.llm_name)
            if not llm:
                logger.error(f"LLM not found for agent {config.name}: {config.llm_name}")
                return None
            
            # Get tools
            tools = []
            for tool_name in config.tools:
                tool = self.tool_registry.get_tool(tool_name)
                if tool:
                    tools.append(tool)
                else:
                    logger.warning(f"Tool not found for agent {config.name}: {tool_name}")
            
            if not tools:
                logger.warning(f"No tools available for agent {config.name}")
            
            # Create system message
            system_message = SystemMessage(content=config.system_prompt)
            
            # Create prompt
            prompt = ChatPromptTemplate.from_messages(
                [
                    system_message,
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("user", "{input}"),
                    MessagesPlaceholder(variable_name="agent_scratchpad"),
                ]
            )
            
            # Create memory
            memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
            
            # Create agent
            agent = create_openai_functions_agent(llm, tools, prompt)
            
            # Create agent executor
            agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                memory=memory,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=config.metadata.get("max_iterations", 10),
                early_stopping_method=config.metadata.get("early_stopping_method", "force"),
                return_intermediate_steps=True
            )
            
            return agent_executor
            
        except Exception as e:
            logger.error(f"Error creating agent instance: {str(e)}")
            return None
    
    def list_available_agents(self) -> List[str]:
        """
        List names of all available agents.
        
        Returns:
            List of agent names
        """
        configs = self.config_service.list_agents()
        return [config.name for config in configs if config.enabled]
    
    def refresh_agent(self, name: str) -> bool:
        """
        Refresh agent instance by name.
        
        Args:
            name: Agent name/identifier
            
        Returns:
            True if successful, False otherwise
        """
        if name in self._agent_instances:
            del self._agent_instances[name]
        
        return self.get_agent(name) is not None
    
    def refresh_all_agents(self) -> None:
        """Refresh all agent instances."""
        self._agent_instances.clear()
    
    def create_langgraph_node(self, name: str) -> Optional[Any]:
        """
        Create a LangGraph node for the agent.
        
        Args:
            name: Agent name/identifier
            
        Returns:
            LangGraph node or None if creation fails
        """
        try:
            from langgraph.graph import StateGraph
            
            # Get agent
            agent = self.get_agent(name)
            if not agent:
                return None
            
            # Create a simple wrapper function for the agent
            def agent_node(state):
                """Agent node function for LangGraph."""
                # Extract input from state
                input_value = state.get("input")
                if not input_value:
                    return {"output": "No input provided", "error": "Missing input"}
                
                # Run agent
                try:
                    result = agent.invoke({"input": input_value})
                    return {"output": result.get("output", ""), "intermediate_steps": result.get("intermediate_steps", [])}
                except Exception as e:
                    return {"output": f"Error: {str(e)}", "error": str(e)}
            
            return agent_node
            
        except ImportError:
            logger.error("LangGraph not installed. Install with 'pip install langgraph'")
            return None
        except Exception as e:
            logger.error(f"Error creating LangGraph node: {str(e)}")
            return None
