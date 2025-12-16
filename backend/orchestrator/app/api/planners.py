"""
Planners API - Endpoints for task planner configuration and management.

Provides CRUD operations for planner settings and testing.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from ..config import get_settings, Settings, PlannerConfig, clear_settings_cache
from ..reasoning.planner import Planner

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/planners", tags=["planners"])


class PlannerConfigModel(BaseModel):
    """Planner configuration model."""
    name: str = Field(..., description="Planner name/identifier")
    type: str = Field(..., description="Planner type (sequential, parallel, conditional, llm_based)")
    enabled: bool = Field(default=True, description="Whether planner is enabled")
    strategy: str = Field(default="sequential", description="Planning strategy")
    templates: Dict[str, Any] = Field(default_factory=dict, description="Plan templates for different intents")
    description: Optional[str] = Field(None, description="Planner description")


class PlannerTestRequest(BaseModel):
    """Planner test request model."""
    user_input: str = Field(..., description="Test user input")
    intent: str = Field(..., description="Intent for planning")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional context")


@router.get("", response_model=List[PlannerConfigModel])
async def list_planners(settings: Settings = Depends(get_settings)) -> List[PlannerConfigModel]:
    """
    List all configured planners.
    
    Returns:
        List of planner configurations
    """
    planners = []
    for name, config in settings.planners.items():
        planners.append(PlannerConfigModel(
            name=config.name,
            type=config.type,
            enabled=config.enabled,
            strategy=config.strategy,
            templates=config.templates,
            description=config.description
        ))
    
    return planners


@router.get("/{name}", response_model=PlannerConfigModel)
async def get_planner(
    name: str,
    settings: Settings = Depends(get_settings)
) -> PlannerConfigModel:
    """
    Get a specific planner configuration.
    
    Args:
        name: Planner name
        
    Returns:
        Planner configuration
    """
    planner_config = settings.get_planner(name)
    
    if not planner_config:
        raise HTTPException(
            status_code=404,
            detail=f"Planner '{name}' not found"
        )
    
    return PlannerConfigModel(
        name=planner_config.name,
        type=planner_config.type,
        enabled=planner_config.enabled,
        strategy=planner_config.strategy,
        templates=planner_config.templates,
        description=planner_config.description
    )


@router.post("", status_code=201)
async def create_planner(
    planner_data: PlannerConfigModel,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Register a new planner.
    
    Args:
        planner_data: Planner configuration
        
    Returns:
        Success message and created planner
    """
    # Check if planner already exists
    if settings.get_planner(planner_data.name):
        raise HTTPException(
            status_code=409,
            detail=f"Planner '{planner_data.name}' already exists"
        )
    
    try:
        # Create planner config
        planner_config = PlannerConfig(
            name=planner_data.name,
            type=planner_data.type,
            enabled=planner_data.enabled,
            strategy=planner_data.strategy,
            templates=planner_data.templates,
            description=planner_data.description
        )
        
        # Add to settings
        settings.add_planner(planner_config)
        
        # Clear cache to reload settings
        clear_settings_cache()
        
        logger.info(f"[Planners API] Created planner: {planner_data.name}")
        
        return {
            "success": True,
            "message": f"Planner '{planner_data.name}' created successfully",
            "planner": planner_data.dict()
        }
        
    except Exception as e:
        logger.error(f"[Planners API] Error creating planner: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create planner: {str(e)}"
        )


@router.put("/{name}")
async def update_planner(
    name: str,
    planner_data: PlannerConfigModel,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Update an existing planner configuration.
    
    Args:
        name: Planner name
        planner_data: Updated planner configuration
        
    Returns:
        Success message and updated planner
    """
    # Check if planner exists
    if not settings.get_planner(name):
        raise HTTPException(
            status_code=404,
            detail=f"Planner '{name}' not found"
        )
    
    try:
        # Create updated planner config
        planner_config = PlannerConfig(
            name=planner_data.name,
            type=planner_data.type,
            enabled=planner_data.enabled,
            strategy=planner_data.strategy,
            templates=planner_data.templates,
            description=planner_data.description
        )
        
        # Update in settings
        settings.add_planner(planner_config)
        
        # Clear cache to reload settings
        clear_settings_cache()
        
        logger.info(f"[Planners API] Updated planner: {name}")
        
        return {
            "success": True,
            "message": f"Planner '{name}' updated successfully",
            "planner": planner_data.dict()
        }
        
    except Exception as e:
        logger.error(f"[Planners API] Error updating planner: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update planner: {str(e)}"
        )


@router.delete("/{name}")
async def delete_planner(
    name: str,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Remove a planner configuration.
    
    Args:
        name: Planner name
        
    Returns:
        Success message
    """
    if not settings.remove_planner(name):
        raise HTTPException(
            status_code=404,
            detail=f"Planner '{name}' not found"
        )
    
    # Clear cache to reload settings
    clear_settings_cache()
    
    logger.info(f"[Planners API] Deleted planner: {name}")
    
    return {
        "success": True,
        "message": f"Planner '{name}' deleted successfully"
    }


@router.post("/{name}/test")
async def test_planner(
    name: str,
    test_request: PlannerTestRequest,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Test a specific planner with sample input.
    
    Args:
        name: Planner name
        test_request: Test request with user input, intent, and optional context
        
    Returns:
        Test result with generated plan
    """
    planner_config = settings.get_planner(name)
    
    if not planner_config:
        raise HTTPException(
            status_code=404,
            detail=f"Planner '{name}' not found"
        )
    
    # Configuration validation result
    result = {
        "planner": name,
        "type": planner_config.type,
        "config_valid": True,
        "enabled": planner_config.enabled,
        "strategy": planner_config.strategy
    }
    
    if not planner_config.enabled:
        result.update({
            "success": False,
            "message": "Planner is disabled. Enable it to test.",
            "warning": "Planner configuration is saved but planner is disabled"
        })
        return result
    
    try:
        # Test the planner with the provided input
        planner = Planner()
        plan = planner.create_plan(
            test_request.user_input,
            test_request.intent,
            test_request.context
        )
        
        result.update({
            "success": True,
            "message": "Planner test completed successfully",
            "test_input": test_request.user_input,
            "intent": test_request.intent,
            "plan": plan.to_dict()
        })
        
        return result
        
    except Exception as e:
        logger.error(f"[Planners API] Test failed for {name}: {str(e)}")
        result.update({
            "success": False,
            "error": type(e).__name__,
            "error_detail": str(e),
            "message": f"Planner test failed: {str(e)}"
        })
        return result


@router.get("/types/available")
async def get_available_planner_types() -> Dict[str, Any]:
    """
    Get list of available planner types.
    
    Returns:
        List of supported planner types
    """
    return {
        "planner_types": [
            {
                "type": "sequential",
                "description": "Execute tasks one after another in sequence",
                "required_config": [],
                "optional_config": ["max_tasks", "timeout_per_task"]
            },
            {
                "type": "parallel",
                "description": "Execute independent tasks in parallel",
                "required_config": [],
                "optional_config": ["max_concurrent", "timeout"]
            },
            {
                "type": "conditional",
                "description": "Execute tasks based on conditions and branching logic",
                "required_config": ["conditions"],
                "optional_config": ["default_branch"]
            },
            {
                "type": "llm_based",
                "description": "LLM-powered dynamic task planning",
                "required_config": [],
                "optional_config": ["model", "temperature", "max_tasks"]
            }
        ]
    }


@router.get("/strategies/available")
async def get_available_strategies() -> Dict[str, Any]:
    """
    Get list of available planning strategies.
    
    Returns:
        List of supported planning strategies
    """
    return {
        "strategies": [
            {
                "name": "sequential",
                "description": "Tasks executed one after another"
            },
            {
                "name": "parallel",
                "description": "Independent tasks executed concurrently"
            },
            {
                "name": "adaptive",
                "description": "Dynamically adjust plan based on results"
            },
            {
                "name": "hierarchical",
                "description": "Break down into sub-tasks recursively"
            }
        ]
    }
