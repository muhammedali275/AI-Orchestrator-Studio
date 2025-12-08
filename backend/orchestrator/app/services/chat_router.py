"""
Chat Router Service - Handles routing logic for Chat Studio.

Routes chat requests to appropriate backends based on routing profile.
"""

import logging
import time
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime

from ..config import Settings
from ..clients.llm_client import LLMClient
from ..clients.external_agent_client import ExternalAgentClient
from ..graph import OrchestrationGraph, GraphState
from ..memory.conversation_memory import ConversationMemory
from ..db.models import ChatMetric
from ..db.database import get_db

logger = logging.getLogger(__name__)


class ChatRouter:
    """
    Routes chat requests based on routing profile.
    
    Supports three routing profiles:
    - direct_llm: Direct call to LLM server
    - zain_agent: Route through external agent
    - tools_data: Use orchestration graph with tools and data sources
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize chat router.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.llm_client = LLMClient(settings)
        self.conversation_memory = ConversationMemory(settings)
    
    async def route_message(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        model_id: Optional[str] = None,
        routing_profile: str = "direct_llm",
        use_memory: bool = True,
        use_tools: bool = False,
        user_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Route a chat message based on routing profile.
        
        Args:
            message: User message
            conversation_id: Conversation ID for context
            model_id: Model to use
            routing_profile: Routing profile (direct_llm, zain_agent, tools_data)
            use_memory: Whether to use conversation memory
            use_tools: Whether to enable tools
            user_id: User identifier
            system_prompt: Optional system prompt
            metadata: Additional metadata
            
        Returns:
            Response dictionary with answer and metadata
        """
        start_time = time.time()
        metric_data = {
            "conversation_id": conversation_id,
            "model_id": model_id,
            "routing_profile": routing_profile,
            "request_timestamp": datetime.utcnow()
        }
        
        try:
            # Build messages list
            messages = await self._build_messages(
                message=message,
                user_id=user_id or "default",
                use_memory=use_memory,
                system_prompt=system_prompt
            )
            
            # Route based on profile
            if routing_profile == "direct_llm":
                result = await self._route_direct_llm(messages, model_id, metadata)
            elif routing_profile == "zain_agent":
                result = await self._route_zain_agent(message, metadata)
            elif routing_profile == "tools_data":
                result = await self._route_tools_data(message, user_id, use_tools, metadata)
            else:
                raise ValueError(f"Unknown routing profile: {routing_profile}")
            
            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            metric_data.update({
                "latency_ms": latency_ms,
                "success": True,
                "tokens_in": result.get("tokens_in"),
                "tokens_out": result.get("tokens_out")
            })
            
            # Store metric
            await self._store_metric(metric_data)
            
            # Store in memory if enabled
            if use_memory and user_id:
                await self.conversation_memory.add_message(
                    user_id=user_id,
                    role="user",
                    content=message
                )
                await self.conversation_memory.add_message(
                    user_id=user_id,
                    role="assistant",
                    content=result.get("answer", ""),
                    metadata=result.get("metadata", {})
                )
            
            return result
            
        except Exception as e:
            logger.error(f"[ChatRouter] Error routing message: {str(e)}")
            
            # Store error metric
            latency_ms = (time.time() - start_time) * 1000
            metric_data.update({
                "latency_ms": latency_ms,
                "success": False,
                "error_code": type(e).__name__,
                "error_message": str(e)
            })
            await self._store_metric(metric_data)
            
            raise
    
    async def stream_message(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        model_id: Optional[str] = None,
        routing_profile: str = "direct_llm",
        use_memory: bool = True,
        user_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream a chat message response.
        
        Args:
            message: User message
            conversation_id: Conversation ID
            model_id: Model to use
            routing_profile: Routing profile
            use_memory: Whether to use memory
            user_id: User identifier
            system_prompt: Optional system prompt
            metadata: Additional metadata
            
        Yields:
            Response chunks
        """
        start_time = time.time()
        
        try:
            # Build messages list
            messages = await self._build_messages(
                message=message,
                user_id=user_id or "default",
                use_memory=use_memory,
                system_prompt=system_prompt
            )
            
            # Only direct_llm supports streaming currently
            if routing_profile == "direct_llm":
                full_response = ""
                async for chunk in self.llm_client.stream(messages=messages, model=model_id):
                    full_response += chunk
                    yield chunk
                
                # Store in memory after streaming completes
                if use_memory and user_id:
                    await self.conversation_memory.add_message(
                        user_id=user_id,
                        role="user",
                        content=message
                    )
                    await self.conversation_memory.add_message(
                        user_id=user_id,
                        role="assistant",
                        content=full_response
                    )
                
                # Store metric
                latency_ms = (time.time() - start_time) * 1000
                await self._store_metric({
                    "conversation_id": conversation_id,
                    "model_id": model_id,
                    "routing_profile": routing_profile,
                    "request_timestamp": datetime.utcnow(),
                    "latency_ms": latency_ms,
                    "success": True
                })
            else:
                # For non-streaming profiles, get full response and yield it
                result = await self.route_message(
                    message=message,
                    conversation_id=conversation_id,
                    model_id=model_id,
                    routing_profile=routing_profile,
                    use_memory=use_memory,
                    user_id=user_id,
                    system_prompt=system_prompt,
                    metadata=metadata
                )
                yield result.get("answer", "")
                
        except Exception as e:
            logger.error(f"[ChatRouter] Error streaming message: {str(e)}")
            yield f"Error: {str(e)}"
    
    async def _build_messages(
        self,
        message: str,
        user_id: str,
        use_memory: bool,
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Build messages list with optional memory and system prompt."""
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history if memory is enabled
        if use_memory:
            context = await self.conversation_memory.get_context(user_id)
            messages.extend(context)
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        return messages
    
    async def _route_direct_llm(
        self,
        messages: List[Dict[str, str]],
        model_id: Optional[str],
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Route directly to LLM."""
        logger.info("[ChatRouter] Routing to direct LLM")
        
        result = await self.llm_client.call(messages=messages, model=model_id)
        
        # Extract response - handle both Ollama and OpenAI formats
        response_data = result.get("response", {})
        
        # Ollama format: {"response": "text"}
        if "response" in response_data and isinstance(response_data["response"], str):
            answer = response_data["response"]
            tokens_in = response_data.get("prompt_eval_count")
            tokens_out = response_data.get("eval_count")
        # OpenAI format: {"choices": [{"message": {"content": "text"}}]}
        elif "choices" in response_data and len(response_data["choices"]) > 0:
            answer = response_data["choices"][0]["message"]["content"]
            usage = response_data.get("usage", {})
            tokens_in = usage.get("prompt_tokens")
            tokens_out = usage.get("completion_tokens")
        else:
            answer = "No response generated"
            tokens_in = None
            tokens_out = None
        
        return {
            "answer": answer,
            "metadata": {
                "routing_profile": "direct_llm",
                "model_used": result.get("model_used"),
                "attempts": result.get("attempts", 1)
            },
            "tokens_in": tokens_in,
            "tokens_out": tokens_out
        }
    
    async def _route_zain_agent(
        self,
        message: str,
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Route to external Zain agent."""
        logger.info("[ChatRouter] Routing to Zain agent")
        
        # Get default agent configuration
        agent_config = self.settings.get_agent("default")
        if not agent_config:
            raise ValueError("No default agent configured")
        
        # Create agent client and call
        agent_client = ExternalAgentClient(self.settings)
        try:
            result = await agent_client.call(
                agent_name="default",
                prompt=message,
                metadata=metadata or {}
            )
            
            return {
                "answer": result.get("response", "No response from agent"),
                "metadata": {
                    "routing_profile": "zain_agent",
                    "agent_name": "default",
                    **result.get("metadata", {})
                }
            }
        finally:
            await agent_client.close()
    
    async def _route_tools_data(
        self,
        message: str,
        user_id: Optional[str],
        use_tools: bool,
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Route through orchestration graph with tools and data sources."""
        logger.info("[ChatRouter] Routing to tools+data orchestration")
        
        # Create initial state
        state = GraphState(
            user_input=message,
            user_id=user_id,
            metadata=metadata or {}
        )
        
        # Execute orchestration graph
        graph = OrchestrationGraph(self.settings)
        try:
            final_state = await graph.execute(state)
            
            return {
                "answer": final_state.answer or "No response generated",
                "metadata": {
                    "routing_profile": "tools_data",
                    "execution_id": final_state.execution_id,
                    "tools_used": final_state.final_metadata.get("tools_used", []),
                    **final_state.final_metadata
                },
                "error": final_state.error
            }
        finally:
            await graph.close()
    
    async def _store_metric(self, metric_data: Dict[str, Any]) -> None:
        """Store chat metric in database."""
        try:
            db = next(get_db())
            # Rename 'metadata' to 'metric_metadata' for SQLAlchemy compatibility
            if 'metadata' in metric_data:
                metric_data['metric_metadata'] = metric_data.pop('metadata')
            metric = ChatMetric(**metric_data)
            db.add(metric)
            db.commit()
            logger.debug(f"[ChatRouter] Stored metric: {metric.id}")
        except Exception as e:
            logger.error(f"[ChatRouter] Error storing metric: {str(e)}")
    
    async def close(self):
        """Close all clients."""
        await self.llm_client.close()
        await self.conversation_memory.close()
