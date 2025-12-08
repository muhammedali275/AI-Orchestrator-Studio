"""
Prompt management for AIpanel.

Handles system prompts and prompt templates.
"""

import logging
from typing import Dict, Any, Optional, List, Union

from sqlalchemy.orm import Session
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

from ..config import get_settings
from ..db.models import Agent
from ..db.session import get_db

logger = logging.getLogger(__name__)
settings = get_settings()


# Standard tool usage instructions
TOOL_USAGE_INSTRUCTIONS = """
You have access to the following tools:

{tool_descriptions}

To use a tool, respond with:
```json
{
  "tool": "tool_name",
  "parameters": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

Only use tools when necessary. If you can answer directly, do so.
"""

# Standard safety and grounding instructions
SAFETY_GROUNDING_INSTRUCTIONS = """
Always prioritize accuracy and truthfulness in your responses.
If you don't know something, admit it rather than making up information.
When using data from tools, cite the source in your response.
Respect user privacy and confidentiality.
"""

# Default system prompt if none is found in the database
DEFAULT_SYSTEM_PROMPT = """
You are a helpful AI assistant that provides accurate and useful information.
Answer questions directly and concisely.
If you don't know something, admit it rather than making up information.
"""


async def get_agent_prompt(
    agent_name: str,
    db: Optional[Session] = None,
    tools_config: Optional[List[Dict[str, Any]]] = None
) -> ChatPromptTemplate:
    """
    Get agent prompt template.
    
    Args:
        agent_name: Agent name
        db: Database session
        tools_config: Tool configuration
        
    Returns:
        ChatPromptTemplate for the agent
    """
    system_prompt = await get_system_prompt(agent_name, db)
    
    # Add tool usage instructions if tools are provided
    if tools_config:
        tool_descriptions = "\n".join([
            f"- {tool['name']}: {tool.get('description', 'No description')}"
            for tool in tools_config
        ])
        
        system_prompt += "\n\n" + TOOL_USAGE_INSTRUCTIONS.format(
            tool_descriptions=tool_descriptions
        )
    
    # Add safety and grounding instructions
    system_prompt += "\n\n" + SAFETY_GROUNDING_INSTRUCTIONS
    
    # Create prompt template
    return ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_prompt),
        HumanMessagePromptTemplate.from_template("{input}")
    ])


async def get_system_prompt(
    agent_name: str,
    db: Optional[Session] = None
) -> str:
    """
    Get system prompt for an agent.
    
    Args:
        agent_name: Agent name
        db: Database session
        
    Returns:
        System prompt text
    """
    # Use provided session or create a new one
    if not db:
        async for db_session in get_db():
            db = db_session
            break
    
    try:
        # Query agent from database
        agent = db.query(Agent).filter(Agent.name == agent_name).first()
        
        if agent:
            logger.info(f"Found system prompt for agent: {agent_name}")
            return agent.system_prompt
        
        # If agent not found, use default agent
        if agent_name != settings.DEFAULT_AGENT_NAME:
            default_agent = db.query(Agent).filter(
                Agent.name == settings.DEFAULT_AGENT_NAME
            ).first()
            
            if default_agent:
                logger.info(
                    f"Agent {agent_name} not found, using default agent: "
                    f"{settings.DEFAULT_AGENT_NAME}"
                )
                return default_agent.system_prompt
        
        # If no agent found, use default prompt
        logger.warning(
            f"No agent found for {agent_name}, using default system prompt"
        )
        return DEFAULT_SYSTEM_PROMPT
        
    except Exception as e:
        logger.error(f"Error getting system prompt: {str(e)}")
        return DEFAULT_SYSTEM_PROMPT


def format_messages_for_llm(
    messages: List[Dict[str, Union[str, Dict[str, Any]]]]
) -> List[Dict[str, str]]:
    """
    Format messages for LLM API.
    
    Args:
        messages: List of messages
        
    Returns:
        Formatted messages
    """
    formatted_messages = []
    
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        
        # Handle function/tool calls and results
        if role == "function" or role == "tool":
            # Convert to assistant or user based on direction
            role = "assistant" if "function_call" in message else "user"
        
        # Add to formatted messages
        formatted_messages.append({
            "role": role,
            "content": content
        })
    
    return formatted_messages
