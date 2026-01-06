"""
Intent Router - Classifies user requests into intent categories.

Pure logic module - no HTTP or IO operations.
"""

from typing import Dict, Any, Optional
from enum import Enum


class IntentLabel(Enum):
    """Intent classification labels."""
    GENERAL_LLM = "general_llm"
    CHURN_ANALYTICS = "churn_analytics"
    DATA_QUERY = "data_query"
    TOOL_EXECUTION = "tool_execution"
    CODE_GENERATION = "code_generation"
    WEB_SEARCH = "web_search"
    EXTERNAL_AGENT = "external_agent"
    UNKNOWN = "unknown"


# Intent labels for easy access
INTENT_LABELS = {
    "general_llm": "General conversation or question answering",
    "churn_analytics": "Customer churn analysis and prediction",
    "data_query": "Database or data source queries",
    "tool_execution": "Execute specific tools or APIs",
    "code_generation": "Generate or execute code",
    "web_search": "Search the web for information",
    "external_agent": "Delegate to external specialized agent",
    "unknown": "Unable to classify intent"
}


ROUTER_SYSTEM_PROMPT = """You are an intent classification system for the exampleOne Orchestrator.

Your task is to analyze user requests and classify them into one of the following intents:

1. **general_llm**: General conversation, questions, explanations, or tasks that can be handled by a language model directly.
   Examples: "What is machine learning?", "Explain quantum computing", "Write a poem"

2. **churn_analytics**: Customer churn analysis, prediction, or related analytics tasks.
   Examples: "Analyze customer churn", "Predict which customers will leave", "Show churn trends"

3. **data_query**: Queries that require accessing databases or data sources.
   Examples: "Get sales data for Q4", "Show customer records", "Query the database"

4. **tool_execution**: Tasks that require executing specific tools or APIs.
   Examples: "Make an HTTP request to...", "Execute this API call", "Run this tool"

5. **code_generation**: Generate, analyze, or execute code.
   Examples: "Write Python code to...", "Execute this script", "Generate a function"

6. **web_search**: Search the internet for current information.
   Examples: "Search for latest news on...", "Find information about...", "What's the weather"

7. **external_agent**: Complex tasks that should be delegated to specialized external agents.
   Examples: "Perform deep analysis on...", "Use the specialized agent for..."

8. **unknown**: Unable to determine intent or ambiguous request.

Respond with ONLY the intent label (e.g., "general_llm", "churn_analytics", etc.) and a brief confidence score (0.0-1.0).

Format your response as JSON:
{
    "intent": "intent_label",
    "confidence": 0.95,
    "reasoning": "Brief explanation of why this intent was chosen"
}
"""


def classify_intent(user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Classify user intent (placeholder for LLM-based classification).
    
    This function would typically call an LLM with the router prompt.
    For now, it provides a simple rule-based classification.
    
    Args:
        user_input: User's input text
        context: Optional context information
        
    Returns:
        Classification result with intent, confidence, and reasoning
    """
    user_input_lower = user_input.lower()
    
    # Simple rule-based classification
    if any(word in user_input_lower for word in ["churn", "customer retention", "attrition"]):
        return {
            "intent": IntentLabel.CHURN_ANALYTICS.value,
            "confidence": 0.9,
            "reasoning": "Request contains churn-related keywords"
        }
    
    elif any(word in user_input_lower for word in ["query", "database", "select", "data from"]):
        return {
            "intent": IntentLabel.DATA_QUERY.value,
            "confidence": 0.85,
            "reasoning": "Request contains database query keywords"
        }
    
    elif any(word in user_input_lower for word in ["search", "find", "look up", "google"]):
        return {
            "intent": IntentLabel.WEB_SEARCH.value,
            "confidence": 0.85,
            "reasoning": "Request contains search keywords"
        }
    
    elif any(word in user_input_lower for word in ["code", "script", "program", "function", "execute"]):
        return {
            "intent": IntentLabel.CODE_GENERATION.value,
            "confidence": 0.8,
            "reasoning": "Request contains code-related keywords"
        }
    
    elif any(word in user_input_lower for word in ["api", "http", "request", "call", "tool"]):
        return {
            "intent": IntentLabel.TOOL_EXECUTION.value,
            "confidence": 0.8,
            "reasoning": "Request contains tool/API keywords"
        }
    
    else:
        return {
            "intent": IntentLabel.GENERAL_LLM.value,
            "confidence": 0.7,
            "reasoning": "Default to general LLM for conversation"
        }


def get_intent_description(intent: str) -> str:
    """
    Get description for an intent label.
    
    Args:
        intent: Intent label
        
    Returns:
        Intent description
    """
    return INTENT_LABELS.get(intent, "Unknown intent")
