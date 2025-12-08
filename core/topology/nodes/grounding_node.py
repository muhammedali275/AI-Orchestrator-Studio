"""
Grounding Node - Ensures responses are grounded in facts and data.

Performs retrieval and data fusion to ground responses.
"""

import logging
import re
from typing import Dict, Any, Callable, List, Optional

from ...agent.agent_registry import AgentRegistry
from ...planner_router.planner_registry import PlannerRegistry
from ...planner_router.router_registry import RouterRegistry
from ...tools.tool_registry import ToolRegistry
from ...memory_cache.memory_service import MemoryService
from ...memory_cache.cache_service import CacheService
from ...config.config_service import ConfigService
from ...llm.llm_registry import LLMRegistry

logger = logging.getLogger(__name__)


def grounding_node(
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
    Create grounding node.
    
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
    # Get LLM name from config
    llm_name = config.get("llm_name", "default")
    
    # Get retrieval configuration
    retrieval_enabled = config.get("retrieval_enabled", False)
    retrieval_tool_name = config.get("retrieval_tool", "vector_search")
    
    # Get citation configuration
    add_citations = config.get("add_citations", False)
    citation_format = config.get("citation_format", "inline")
    
    # Get fact-checking configuration
    fact_checking_enabled = config.get("fact_checking_enabled", False)
    fact_checking_threshold = config.get("fact_checking_threshold", 0.7)
    
    async def node_fn(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Grounding node function.
        
        Args:
            state: Current state
            
        Returns:
            Updated state
        """
        try:
            logger.info(f"Grounding response: {state.get('run_id')}")
            
            # Get input and output
            input_text = state.get("input", "")
            output_text = state.get("output", "")
            
            # Skip if no output
            if not output_text:
                logger.info("No output to ground")
                return state
            
            # Initialize sources
            if "sources" not in state:
                state["sources"] = []
            
            # Perform retrieval if enabled
            if retrieval_enabled:
                await _perform_retrieval(state, input_text, output_text)
            
            # Perform fact checking if enabled
            if fact_checking_enabled:
                await _perform_fact_checking(state, output_text)
            
            # Ground the response
            grounded_output = await _ground_response(state, output_text)
            
            # Update output
            state["output"] = grounded_output
            
            # Add to history
            state["history"].append({
                "node": "grounding",
                "sources": state.get("sources", []),
                "output": state["output"]
            })
            
            logger.info(f"Grounding complete")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in grounding node: {str(e)}")
            state["error"] = str(e)
            return state
    
    async def _perform_retrieval(state: Dict[str, Any], input_text: str, output_text: str) -> None:
        """
        Perform retrieval to find relevant sources.
        
        Args:
            state: Current state
            input_text: Input text
            output_text: Output text
        """
        try:
            # Get retrieval tool
            retrieval_tool = tool_registry.get_tool(retrieval_tool_name)
            if not retrieval_tool:
                logger.warning(f"Retrieval tool not found: {retrieval_tool_name}")
                return
            
            # Extract key terms from input and output
            key_terms = _extract_key_terms(input_text, output_text)
            
            # Perform retrieval for each key term
            for term in key_terms:
                try:
                    # Call retrieval tool
                    result = await retrieval_tool.ainvoke({
                        "query": term,
                        "top_k": 3
                    })
                    
                    # Add sources to state
                    if "documents" in result:
                        for doc in result["documents"]:
                            # Check if source already exists
                            source_exists = False
                            for source in state["sources"]:
                                if source.get("id") == doc.get("id"):
                                    source_exists = True
                                    break
                            
                            if not source_exists:
                                state["sources"].append({
                                    "id": doc.get("id"),
                                    "title": doc.get("title", ""),
                                    "content": doc.get("content", ""),
                                    "url": doc.get("url", ""),
                                    "relevance": doc.get("relevance", 0.0)
                                })
                
                except Exception as e:
                    logger.warning(f"Error retrieving sources for term '{term}': {str(e)}")
            
        except Exception as e:
            logger.warning(f"Error performing retrieval: {str(e)}")
    
    async def _perform_fact_checking(state: Dict[str, Any], output_text: str) -> None:
        """
        Perform fact checking on the output.
        
        Args:
            state: Current state
            output_text: Output text
        """
        try:
            # Get LLM
            llm_registry = LLMRegistry(config_service)
            llm = llm_registry.get_llm(llm_name)
            if not llm:
                logger.warning(f"LLM not found for fact checking: {llm_name}")
                return
            
            # Extract statements to fact check
            statements = _extract_statements(output_text)
            
            # Initialize fact checking results
            if "fact_checking" not in state:
                state["fact_checking"] = []
            
            # Check each statement against sources
            for statement in statements:
                # Skip short statements
                if len(statement) < 10:
                    continue
                
                # Check statement against sources
                statement_verified = False
                supporting_sources = []
                
                for source in state.get("sources", []):
                    source_content = source.get("content", "")
                    
                    # Skip empty sources
                    if not source_content:
                        continue
                    
                    # Check if statement is supported by source
                    prompt = f"""
                    Statement: "{statement}"
                    
                    Source: "{source_content}"
                    
                    Is the statement supported by the source? Respond with a number between 0 and 1, where:
                    - 0 means the statement is completely unsupported or contradicted by the source
                    - 1 means the statement is fully supported by the source
                    
                    Only respond with a number between 0 and 1.
                    """
                    
                    try:
                        response = await llm.ainvoke(prompt)
                        
                        # Extract score
                        score_match = re.search(r'(\d+\.\d+|\d+)', response)
                        if score_match:
                            score = float(score_match.group(1))
                            
                            # Check if score exceeds threshold
                            if score >= fact_checking_threshold:
                                statement_verified = True
                                supporting_sources.append({
                                    "id": source.get("id"),
                                    "score": score
                                })
                    
                    except Exception as e:
                        logger.warning(f"Error fact checking statement against source: {str(e)}")
                
                # Add fact checking result
                state["fact_checking"].append({
                    "statement": statement,
                    "verified": statement_verified,
                    "supporting_sources": supporting_sources
                })
            
        except Exception as e:
            logger.warning(f"Error performing fact checking: {str(e)}")
    
    async def _ground_response(state: Dict[str, Any], output_text: str) -> str:
        """
        Ground the response with sources and fact checking.
        
        Args:
            state: Current state
            output_text: Output text
            
        Returns:
            Grounded output text
        """
        try:
            # Get LLM
            llm_registry = LLMRegistry(config_service)
            llm = llm_registry.get_llm(llm_name)
            if not llm:
                logger.warning(f"LLM not found for grounding: {llm_name}")
                return output_text
            
            # Check if we have sources or fact checking results
            sources = state.get("sources", [])
            fact_checking = state.get("fact_checking", [])
            
            if not sources and not fact_checking:
                logger.info("No sources or fact checking results for grounding")
                return output_text
            
            # Prepare sources text
            sources_text = ""
            for i, source in enumerate(sources):
                sources_text += f"Source {i+1}: {source.get('content', '')}\n\n"
            
            # Prepare fact checking text
            fact_checking_text = ""
            for result in fact_checking:
                if result.get("verified"):
                    fact_checking_text += f"Verified statement: {result.get('statement')}\n"
                else:
                    fact_checking_text += f"Unverified statement: {result.get('statement')}\n"
            
            # Create grounding prompt
            prompt = f"""
            Original response:
            {output_text}
            
            Sources:
            {sources_text}
            
            Fact checking results:
            {fact_checking_text}
            
            Task: Rewrite the original response to ensure it is fully grounded in the provided sources. 
            
            Guidelines:
            1. Ensure all factual claims are supported by the sources
            2. Remove or qualify any statements that are not supported by the sources
            3. Maintain the same tone and style as the original response
            4. Do not add new information that is not in the original response or sources
            5. Keep the response concise and clear
            """
            
            if add_citations:
                prompt += f"\n6. Add citations to the sources using {citation_format} format"
            
            prompt += "\n\nGrounded response:"
            
            # Generate grounded response
            grounded_output = await llm.ainvoke(prompt)
            
            # Clean up the response
            grounded_output = grounded_output.strip()
            
            # Add sources section if configured
            if config.get("include_sources_section", False) and sources:
                grounded_output += "\n\nSources:\n"
                for i, source in enumerate(sources):
                    title = source.get("title", "")
                    url = source.get("url", "")
                    
                    if title and url:
                        grounded_output += f"{i+1}. {title} - {url}\n"
                    elif title:
                        grounded_output += f"{i+1}. {title}\n"
                    elif url:
                        grounded_output += f"{i+1}. {url}\n"
            
            return grounded_output
            
        except Exception as e:
            logger.warning(f"Error grounding response: {str(e)}")
            return output_text
    
    def _extract_key_terms(input_text: str, output_text: str) -> List[str]:
        """
        Extract key terms from input and output for retrieval.
        
        Args:
            input_text: Input text
            output_text: Output text
            
        Returns:
            List of key terms
        """
        # Simple implementation - extract noun phrases
        import re
        
        # Combine input and output
        combined_text = f"{input_text} {output_text}"
        
        # Remove special characters
        cleaned_text = re.sub(r'[^\w\s]', ' ', combined_text)
        
        # Split into words
        words = cleaned_text.split()
        
        # Get unique words with length > 3
        unique_words = set(word for word in words if len(word) > 3)
        
        # Get top 5 words by length
        top_words = sorted(unique_words, key=len, reverse=True)[:5]
        
        # Create key terms by combining input with top words
        key_terms = [input_text]  # Always include the full input
        
        # Add combinations of input with top words
        for word in top_words:
            key_terms.append(f"{word} {input_text}")
        
        return key_terms
    
    def _extract_statements(text: str) -> List[str]:
        """
        Extract statements from text for fact checking.
        
        Args:
            text: Text to extract statements from
            
        Returns:
            List of statements
        """
        # Simple implementation - split by periods
        statements = []
        
        # Split by periods
        for sentence in re.split(r'(?<=[.!?])\s+', text):
            # Clean up sentence
            sentence = sentence.strip()
            
            # Skip empty sentences
            if not sentence:
                continue
            
            # Add sentence
            statements.append(sentence)
        
        return statements
    
    return node_fn
