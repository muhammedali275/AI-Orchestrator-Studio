"""
LangGraph orchestrator for AIpanel.

Defines a state machine with nodes for orchestration flow.
"""

import logging
import uuid
from typing import Dict, Any, Optional, List, Tuple, Union, TypedDict, Annotated
from datetime import datetime

from langchain.schema.runnable import RunnableConfig
from langchain.schema.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.schema.output_parser import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db.models import Agent
from ..db.session import get_db
from ..llm.client import LLMClient
from ..llm.prompts import get_agent_prompt, format_messages_for_llm
from .langchain_tools import get_tools_for_query
from .memory import get_memory_for_session, get_global_cache

logger = logging.getLogger(__name__)
settings = get_settings()


class GraphState(TypedDict):
    """State passed between nodes in the graph."""
    # Input
    user_input: str
    user_id: Optional[str]
    session_id: str
    agent_name: str
    
    # Execution tracking
    execution_id: str
    current_node: str
    start_time: float
    
    # Intent and routing
    intent: Optional[str]
    intent_confidence: Optional[float]
    route: Optional[str]
    
    # Messages and context
    messages: List[Dict[str, Any]]
    context: Dict[str, Any]
    
    # Tool execution
    tools: List[Dict[str, Any]]
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    
    # Results
    answer: Optional[str]
    sources: List[Dict[str, Any]]
    
    # Error handling
    error: Optional[str]


def create_empty_state() -> GraphState:
    """
    Create empty graph state.
    
    Returns:
        Empty graph state
    """
    return GraphState(
        # Input
        user_input="",
        user_id=None,
        session_id=str(uuid.uuid4()),
        agent_name=settings.DEFAULT_AGENT_NAME,
        
        # Execution tracking
        execution_id=str(uuid.uuid4()),
        current_node="start",
        start_time=datetime.now().timestamp(),
        
        # Intent and routing
        intent=None,
        intent_confidence=None,
        route=None,
        
        # Messages and context
        messages=[],
        context={},
        
        # Tool execution
        tools=[],
        tool_calls=[],
        tool_results=[],
        
        # Results
        answer=None,
        sources=[],
        
        # Error handling
        error=None
    )


async def start_node(state: GraphState, db: Optional[Session] = None) -> GraphState:
    """
    Start node - initializes execution.
    
    Args:
        state: Current state
        db: Database session
        
    Returns:
        Updated state
    """
    logger.info(f"[Graph:Start] Starting execution {state['execution_id']}")
    
    # Update current node
    state["current_node"] = "start"
    
    # Add user message to messages
    state["messages"].append({
        "role": "user",
        "content": state["user_input"]
    })
    
    return state


async def intent_router_node(state: GraphState, db: Optional[Session] = None) -> str:
    """
    Intent router node - determines processing route.
    
    Args:
        state: Current state
        db: Database session
        
    Returns:
        Next node name
    """
    logger.info(f"[Graph:IntentRouter] Routing request: {state['user_input'][:50]}...")
    
    # Update current node
    state["current_node"] = "intent_router"
    
    # Simple pattern matching for now
    # In a production implementation, this would use an LLM or classifier
    user_input = state["user_input"].lower()
    
    if any(term in user_input for term in ["churn", "customer retention", "attrition"]):
        state["intent"] = "churn_analytics"
        state["intent_confidence"] = 0.9
        state["route"] = "planner"
        return "planner_node"
    
    elif any(term in user_input for term in ["search", "find", "look up"]):
        state["intent"] = "web_search"
        state["intent_confidence"] = 0.8
        state["route"] = "tool_executor"
        return "tool_executor_node"
    
    elif any(term in user_input for term in ["query", "database", "data"]):
        state["intent"] = "data_query"
        state["intent_confidence"] = 0.85
        state["route"] = "planner"
        return "planner_node"
    
    else:
        # Default to LLM for general queries
        state["intent"] = "general_llm"
        state["intent_confidence"] = 0.7
        state["route"] = "llm_agent"
        return "llm_agent_node"


async def planner_node(state: GraphState, db: Optional[Session] = None) -> str:
    """
    Planner node - creates execution plan.
    
    Args:
        state: Current state
        db: Database session
        
    Returns:
        Next node name
    """
    logger.info(f"[Graph:Planner] Planning for intent: {state['intent']}")
    
    # Update current node
    state["current_node"] = "planner"
    
    # Get tools based on intent
    tools = await get_tools_for_query(state["user_input"], db)
    
    # Convert tools to tool descriptions
    state["tools"] = [
        {
            "name": tool.name,
            "description": tool.description,
            "args_schema": tool.args_schema.schema() if hasattr(tool, "args_schema") else {}
        }
        for tool in tools
    ]
    
    # Determine next node based on intent
    if state["intent"] == "churn_analytics":
        return "tool_executor_node"
    elif state["intent"] == "data_query":
        return "tool_executor_node"
    else:
        return "llm_agent_node"


async def llm_agent_node(state: GraphState, db: Optional[Session] = None) -> Union[str, Dict[str, str]]:
    """
    LLM agent node - processes request with LLM.
    
    Args:
        state: Current state
        db: Database session
        
    Returns:
        Next node name or END
    """
    logger.info(f"[Graph:LLMAgent] Processing with LLM")
    
    # Update current node
    state["current_node"] = "llm_agent"
    
    try:
        # Get agent configuration
        agent_name = state["agent_name"]
        
        # Create LLM client
        llm_client = LLMClient(db=db)
        
        # Get agent prompt
        prompt_template = await get_agent_prompt(
            agent_name=agent_name,
            db=db,
            tools_config=state["tools"]
        )
        
        # Format prompt with user input
        prompt = prompt_template.format(input=state["user_input"])
        
        # Get conversation history
        memory = await get_memory_for_session(
            session_id=state["session_id"],
            user_id=state["user_id"],
            db=db
        )
        
        # Format messages for LLM
        messages = []
        
        # Add system message
        messages.append({
            "role": "system",
            "content": prompt
        })
        
        # Add conversation history
        if memory:
            history = memory.chat_memory.messages
            for msg in history:
                if isinstance(msg, HumanMessage):
                    messages.append({
                        "role": "user",
                        "content": msg.content
                    })
                elif isinstance(msg, AIMessage):
                    messages.append({
                        "role": "assistant",
                        "content": msg.content
                    })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": state["user_input"]
        })
        
        # Call LLM
        response = await llm_client.chat(messages=messages)
        
        # Extract answer
        if "response" in response and "choices" in response["response"]:
            choices = response["response"]["choices"]
            if choices and "message" in choices[0]:
                answer = choices[0]["message"]["content"]
                state["answer"] = answer
                
                # Add assistant message to messages
                state["messages"].append({
                    "role": "assistant",
                    "content": answer
                })
        
        # Check for tool calls
        if state["tools"] and "tool_calls" in state:
            return "tool_executor_node"
        
        # Go to memory store
        return "memory_store_node"
        
    except Exception as e:
        logger.error(f"[Graph:LLMAgent] Error: {str(e)}")
        state["error"] = f"LLM processing error: {str(e)}"
        return "end_node"


async def tool_executor_node(state: GraphState, db: Optional[Session] = None) -> str:
    """
    Tool executor node - executes tools.
    
    Args:
        state: Current state
        db: Database session
        
    Returns:
        Next node name
    """
    logger.info(f"[Graph:ToolExecutor] Executing tools")
    
    # Update current node
    state["current_node"] = "tool_executor"
    
    try:
        # Get tools based on intent
        tools = await get_tools_for_query(state["user_input"], db)
        
        # Execute appropriate tool based on intent
        if state["intent"] == "churn_analytics":
            # Find churn query tool
            churn_tool = next((tool for tool in tools if tool.name == "churn_query_tool"), None)
            if churn_tool:
                result = await churn_tool._arun(limit=50, order="desc")
                state["tool_results"].append({
                    "tool": "churn_query_tool",
                    "result": result
                })
                
                # Add source
                state["sources"].append({
                    "type": "cubejs",
                    "name": "Churn Analytics",
                    "data": result
                })
        
        elif state["intent"] == "web_search":
            # Find web search tool
            search_tool = next((tool for tool in tools if "search" in tool.name), None)
            if search_tool:
                result = await search_tool._arun(query=state["user_input"])
                state["tool_results"].append({
                    "tool": search_tool.name,
                    "result": result
                })
                
                # Add source
                state["sources"].append({
                    "type": "web_search",
                    "name": "Web Search",
                    "data": result
                })
        
        # Go to grounding node to process results
        return "grounding_node"
        
    except Exception as e:
        logger.error(f"[Graph:ToolExecutor] Error: {str(e)}")
        state["error"] = f"Tool execution error: {str(e)}"
        
        # If tool execution fails, try with LLM
        if not state["answer"]:
            return "llm_agent_node"
        else:
            return "memory_store_node"


async def grounding_node(state: GraphState, db: Optional[Session] = None) -> str:
    """
    Grounding node - grounds responses in data.
    
    Args:
        state: Current state
        db: Database session
        
    Returns:
        Next node name
    """
    logger.info(f"[Graph:Grounding] Grounding response in data")
    
    # Update current node
    state["current_node"] = "grounding"
    
    try:
        # If we have tool results, use LLM to generate answer
        if state["tool_results"]:
            # Create LLM client
            llm_client = LLMClient(db=db)
            
            # Create prompt for grounding
            grounding_prompt = """
            Based on the following data, provide a clear and concise answer to the user's question.
            Include relevant information from the data but avoid technical details unless necessary.
            
            User question: {question}
            
            Data:
            {data}
            
            Your answer should be informative, accurate, and easy to understand.
            """
            
            # Format data from tool results
            data_str = "\n\n".join([
                f"Tool: {result['tool']}\nResult: {result['result']}"
                for result in state["tool_results"]
            ])
            
            # Format prompt
            formatted_prompt = grounding_prompt.format(
                question=state["user_input"],
                data=data_str
            )
            
            # Call LLM
            response = await llm_client.chat(messages=[
                {"role": "system", "content": "You are a helpful assistant that provides accurate information based on data."},
                {"role": "user", "content": formatted_prompt}
            ])
            
            # Extract answer
            if "response" in response and "choices" in response["response"]:
                choices = response["response"]["choices"]
                if choices and "message" in choices[0]:
                    answer = choices[0]["message"]["content"]
                    state["answer"] = answer
                    
                    # Add assistant message to messages
                    state["messages"].append({
                        "role": "assistant",
                        "content": answer
                    })
        
        # Go to memory store
        return "memory_store_node"
        
    except Exception as e:
        logger.error(f"[Graph:Grounding] Error: {str(e)}")
        state["error"] = f"Grounding error: {str(e)}"
        
        # If grounding fails but we have tool results, use them directly
        if state["tool_results"] and not state["answer"]:
            # Create simple answer from tool results
            result_str = state["tool_results"][0]["result"]
            state["answer"] = f"Here are the results: {result_str}"
        
        return "memory_store_node"


async def memory_store_node(state: GraphState, db: Optional[Session] = None) -> str:
    """
    Memory store node - stores conversation in memory.
    
    Args:
        state: Current state
        db: Database session
        
    Returns:
        Next node name
    """
    logger.info(f"[Graph:MemoryStore] Storing conversation")
    
    # Update current node
    state["current_node"] = "memory_store"
    
    try:
        # Get memory for session
        memory = await get_memory_for_session(
            session_id=state["session_id"],
            user_id=state["user_id"],
            db=db
        )
        
        # Save user message
        await memory.chat_memory.add_message(HumanMessage(
            content=state["user_input"]
        ))
        
        # Save assistant message if available
        if state["answer"]:
            await memory.chat_memory.add_message(AIMessage(
                content=state["answer"]
            ))
        
        # Go to end node
        return "end_node"
        
    except Exception as e:
        logger.error(f"[Graph:MemoryStore] Error: {str(e)}")
        state["error"] = f"Memory storage error: {str(e)}"
        return "end_node"


async def end_node(state: GraphState, db: Optional[Session] = None) -> GraphState:
    """
    End node - finalizes execution.
    
    Args:
        state: Current state
        db: Database session
        
    Returns:
        Final state
    """
    logger.info(f"[Graph:End] Ending execution {state['execution_id']}")
    
    # Update current node
    state["current_node"] = "end"
    
    # Calculate execution time
    end_time = datetime.now().timestamp()
    execution_time = end_time - state["start_time"]
    
    # Add execution metadata to context
    state["context"]["execution_time"] = execution_time
    state["context"]["execution_id"] = state["execution_id"]
    
    # Ensure we have an answer
    if not state["answer"] and not state["error"]:
        state["answer"] = "I'm sorry, I couldn't process your request."
    
    return state


def create_orchestration_graph(db: Optional[Session] = None) -> StateGraph:
    """
    Create orchestration graph.
    
    Args:
        db: Database session
        
    Returns:
        StateGraph instance
    """
    # Create graph
    graph = StateGraph(GraphState)
    
    # Add nodes
    graph.add_node("start_node", lambda state: start_node(state, db))
    graph.add_node("intent_router_node", lambda state: intent_router_node(state, db))
    graph.add_node("planner_node", lambda state: planner_node(state, db))
    graph.add_node("llm_agent_node", lambda state: llm_agent_node(state, db))
    graph.add_node("tool_executor_node", lambda state: tool_executor_node(state, db))
    graph.add_node("grounding_node", lambda state: grounding_node(state, db))
    graph.add_node("memory_store_node", lambda state: memory_store_node(state, db))
    graph.add_node("end_node", lambda state: end_node(state, db))
    
    # Add edges
    graph.add_edge("start_node", "intent_router_node")
    graph.add_conditional_edges(
        "intent_router_node",
        lambda state: state["route"] or "llm_agent_node",
        {
            "planner_node": lambda state: state["route"] == "planner",
            "llm_agent_node": lambda state: state["route"] == "llm_agent",
            "tool_executor_node": lambda state: state["route"] == "tool_executor"
        }
    )
    graph.add_conditional_edges(
        "planner_node",
        lambda state: "llm_agent_node",
        {
            "llm_agent_node": lambda state: True,
            "tool_executor_node": lambda state: len(state["tools"]) > 0
        }
    )
    graph.add_conditional_edges(
        "llm_agent_node",
        lambda state: "memory_store_node",
        {
            "tool_executor_node": lambda state: len(state["tool_calls"]) > 0,
            "memory_store_node": lambda state: True,
            END: lambda state: state["error"] is not None
        }
    )
    graph.add_edge("tool_executor_node", "grounding_node")
    graph.add_edge("grounding_node", "memory_store_node")
    graph.add_edge("memory_store_node", "end_node")
    graph.add_edge("end_node", END)
    
    # Set entry point
    graph.set_entry_point("start_node")
    
    return graph


async def run_graph(
    user_input: str,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Run orchestration graph.
    
    Args:
        user_input: User input
        session_id: Chat session ID
        user_id: User ID
        agent_name: Agent name
        db: Database session
        
    Returns:
        Execution result
    """
    # Create initial state
    state = create_empty_state()
    state["user_input"] = user_input
    state["session_id"] = session_id or str(uuid.uuid4())
    state["user_id"] = user_id
    state["agent_name"] = agent_name or settings.DEFAULT_AGENT_NAME
    
    # Create graph
    graph = create_orchestration_graph(db)
    
    # Run graph
    result = await graph.ainvoke(state)
    
    # Return result
    return {
        "answer": result["answer"],
        "sources": result["sources"],
        "execution_id": result["execution_id"],
        "error": result["error"]
    }
