"""
Routers API - Endpoints for intent router configuration and management.

Provides CRUD operations for router settings and testing.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from ..config import get_settings, Settings, RouterConfig, clear_settings_cache
from ..reasoning.router_prompt import classify_intent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/routers", tags=["routers"])


class RouterConfigModel(BaseModel):
    """Router configuration model."""
    name: str = Field(..., description="Router name/identifier")
    type: str = Field(..., description="Router type (rule_based, llm_based, hybrid, keyword)")
    enabled: bool = Field(default=True, description="Whether router is enabled")
    priority: int = Field(default=0, description="Router priority (higher = evaluated first)")
    rules: Dict[str, Any] = Field(default_factory=dict, description="Router-specific rules/patterns")
    description: Optional[str] = Field(None, description="Router description")


class RouterTestRequest(BaseModel):
    """Router test request model."""
    input_text: str = Field(..., description="Test input text for intent classification")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional context")


@router.get("", response_model=List[RouterConfigModel])
async def list_routers(settings: Settings = Depends(get_settings)) -> List[RouterConfigModel]:
    """
    List all configured routers.
    
    Returns:
        List of router configurations
    """
    routers = []
    for name, config in settings.routers.items():
        routers.append(RouterConfigModel(
            name=config.name,
            type=config.type,
            enabled=config.enabled,
            priority=config.priority,
            rules=config.rules,
            description=config.description
        ))
    
    # Sort by priority (higher first)
    routers.sort(key=lambda r: r.priority, reverse=True)
    
    return routers


@router.get("/{name}", response_model=RouterConfigModel)
async def get_router(
    name: str,
    settings: Settings = Depends(get_settings)
) -> RouterConfigModel:
    """
    Get a specific router configuration.
    
    Args:
        name: Router name
        
    Returns:
        Router configuration
    """
    router_config = settings.get_router(name)
    
    if not router_config:
        raise HTTPException(
            status_code=404,
            detail=f"Router '{name}' not found"
        )
    
    return RouterConfigModel(
        name=router_config.name,
        type=router_config.type,
        enabled=router_config.enabled,
        priority=router_config.priority,
        rules=router_config.rules,
        description=router_config.description
    )


@router.post("", status_code=201)
async def create_router(
    router_data: RouterConfigModel,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Register a new router.
    
    Args:
        router_data: Router configuration
        
    Returns:
        Success message and created router
    """
    # Check if router already exists
    if settings.get_router(router_data.name):
        raise HTTPException(
            status_code=409,
            detail=f"Router '{router_data.name}' already exists"
        )
    
    try:
        # Create router config
        router_config = RouterConfig(
            name=router_data.name,
            type=router_data.type,
            enabled=router_data.enabled,
            priority=router_data.priority,
            rules=router_data.rules,
            description=router_data.description
        )
        
        # Add to settings
        settings.add_router(router_config)
        
        # Clear cache to reload settings
        clear_settings_cache()
        
        logger.info(f"[Routers API] Created router: {router_data.name}")
        
        return {
            "success": True,
            "message": f"Router '{router_data.name}' created successfully",
            "router": router_data.dict()
        }
        
    except Exception as e:
        logger.error(f"[Routers API] Error creating router: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create router: {str(e)}"
        )


@router.put("/{name}")
async def update_router(
    name: str,
    router_data: RouterConfigModel,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Update an existing router configuration.
    
    Args:
        name: Router name
        router_data: Updated router configuration
        
    Returns:
        Success message and updated router
    """
    # Check if router exists
    if not settings.get_router(name):
        raise HTTPException(
            status_code=404,
            detail=f"Router '{name}' not found"
        )
    
    try:
        # Create updated router config
        router_config = RouterConfig(
            name=router_data.name,
            type=router_data.type,
            enabled=router_data.enabled,
            priority=router_data.priority,
            rules=router_data.rules,
            description=router_data.description
        )
        
        # Update in settings
        settings.add_router(router_config)
        
        # Clear cache to reload settings
        clear_settings_cache()
        
        logger.info(f"[Routers API] Updated router: {name}")
        
        return {
            "success": True,
            "message": f"Router '{name}' updated successfully",
            "router": router_data.dict()
        }
        
    except Exception as e:
        logger.error(f"[Routers API] Error updating router: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update router: {str(e)}"
        )


@router.delete("/{name}")
async def delete_router(
    name: str,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Remove a router configuration.
    
    Args:
        name: Router name
        
    Returns:
        Success message
    """
    if not settings.remove_router(name):
        raise HTTPException(
            status_code=404,
            detail=f"Router '{name}' not found"
        )
    
    # Clear cache to reload settings
    clear_settings_cache()
    
    logger.info(f"[Routers API] Deleted router: {name}")
    
    return {
        "success": True,
        "message": f"Router '{name}' deleted successfully"
    }


@router.post("/{name}/test")
async def test_router(
    name: str,
    test_request: RouterTestRequest,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Test a specific router with sample input.
    
    Args:
        name: Router name
        test_request: Test request with input text and optional context
        
    Returns:
        Test result with intent classification
    """
    router_config = settings.get_router(name)
    
    if not router_config:
        raise HTTPException(
            status_code=404,
            detail=f"Router '{name}' not found"
        )
    
    # Configuration validation result
    result = {
        "router": name,
        "type": router_config.type,
        "config_valid": True,
        "enabled": router_config.enabled,
        "priority": router_config.priority
    }
    
    if not router_config.enabled:
        result.update({
            "success": False,
            "message": "Router is disabled. Enable it to test.",
            "warning": "Router configuration is saved but router is disabled"
        })
        return result
    
    try:
        # Test the router with the provided input
        classification_result = classify_intent(
            test_request.input_text,
            test_request.context
        )
        
        result.update({
            "success": True,
            "message": "Router test completed successfully",
            "test_input": test_request.input_text,
            "classification": classification_result
        })
        
        return result
        
    except Exception as e:
        logger.error(f"[Routers API] Test failed for {name}: {str(e)}")
        result.update({
            "success": False,
            "error": type(e).__name__,
            "error_detail": str(e),
            "message": f"Router test failed: {str(e)}"
        })
        return result


@router.get("/types/available")
async def get_available_router_types() -> Dict[str, Any]:
    """
    Get list of available router types.
    
    Returns:
        List of supported router types
    """
    return {
        "router_types": [
            {
                "type": "rule_based",
                "description": "Rule-based intent classification using keywords and patterns",
                "required_config": ["rules"],
                "optional_config": ["priority", "fallback_intent"]
            },
            {
                "type": "llm_based",
                "description": "LLM-powered intent classification",
                "required_config": [],
                "optional_config": ["model", "temperature", "prompt_template"]
            },
            {
                "type": "hybrid",
                "description": "Combination of rule-based and LLM-based routing",
                "required_config": ["rules"],
                "optional_config": ["llm_fallback", "confidence_threshold"]
            },
            {
                "type": "keyword",
                "description": "Simple keyword matching for intent classification",
                "required_config": ["keywords"],
                "optional_config": ["case_sensitive"]
            }
        ]
    }


@router.get("/intents/available")
async def get_available_intents() -> Dict[str, Any]:
    """
    Get list of available intent labels.
    
    Returns:
        List of supported intent labels
    """
    from ..reasoning.router_prompt import INTENT_LABELS
    
    return {
        "intents": [
            {"label": label, "description": desc}
            for label, desc in INTENT_LABELS.items()
        ]
    }
