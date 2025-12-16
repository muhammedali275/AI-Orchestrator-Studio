# Router & Planner GUI Implementation - Complete Guide

## Summary
This document provides the complete implementation for adding Router and Planner management via GUI, plus fixing Tools/Datasources persistence issues.

## What Has Been Completed

### 1. Configuration Models (backend/orchestrator/app/config.py)
✅ Added `RouterConfig` and `PlannerConfig` models
✅ Added `routers` and `planners` dictionaries to Settings
✅ Added `get_router()` and `get_planner()` methods

### 2. What Remains

#### A. Complete config.py (Add these methods after `add_datasource`):

```python
def add_router(self, router: RouterConfig) -> None:
    """Add or update a router configuration."""
    self.routers[router.name] = router
    self._persist_routers()

def add_planner(self, planner: PlannerConfig) -> None:
    """Add or update a planner configuration."""
    self.planners[planner.name] = planner
    self._persist_planners()

def remove_router(self, name: str) -> bool:
    """Remove a router configuration. Returns True if removed."""
    if name in self.routers:
        del self.routers[name]
        self._persist_routers()
        return True
    return False

def remove_planner(self, name: str) -> bool:
    """Remove a planner configuration. Returns True if removed."""
    if name in self.planners:
        del self.planners[name]
        self._persist_planners()
        return True
    return False

def load_routers_from_file(self, filepath: str) -> None:
    """Load router configurations from JSON file."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            routers_data = data.get('routers', [])
            
            for router_data in routers_data:
                router_config = RouterConfig(**router_data)
                self.routers[router_config.name] = router_config
            
            logger.info(f"Loaded {len(routers_data)} router configurations from {filepath}")
    except FileNotFoundError:
        logger.warning(f"Router config file not found: {filepath}")
    except Exception as e:
        logger.error(f"Error loading router configs from {filepath}: {str(e)}")

def load_planners_from_file(self, filepath: str) -> None:
    """Load planner configurations from JSON file."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            planners_data = data.get('planners', [])
            
            for planner_data in planners_data:
                planner_config = PlannerConfig(**planner_data)
                self.planners[planner_config.name] = planner_config
            
            logger.info(f"Loaded {len(planners_data)} planner configurations from {filepath}")
    except FileNotFoundError:
        logger.warning(f"Planner config file not found: {filepath}")
    except Exception as e:
        logger.error(f"Error loading planner configs from {filepath}: {str(e)}")

def _persist_routers(self) -> None:
    """Persist routers configuration to file."""
    try:
        from pathlib import Path
        config_dir = Path("config")
        config_dir.mkdir(parents=True, exist_ok=True)
        
        routers_file = config_dir / "routers.json"
        routers_list = [router.dict() for router in self.routers.values()]
        
        with open(routers_file, 'w') as f:
            json.dump({"routers": routers_list}, f, indent=2)
        
        logger.info(f"Persisted {len(routers_list)} routers to {routers_file.absolute()}")
    except Exception as e:
        logger.error(f"Error persisting routers: {str(e)}")

def _persist_planners(self) -> None:
    """Persist planners configuration to file."""
    try:
        from pathlib import Path
        config_dir = Path("config")
        config_dir.mkdir(parents=True, exist_ok=True)
        
        planners_file = config_dir / "planners.json"
        planners_list = [planner.dict() for planner in self.planners.values()]
        
        with open(planners_file, 'w') as f:
            json.dump({"planners": planners_list}, f, indent=2)
        
        logger.info(f"Persisted {len(planners_list)} planners to {planners_file.absolute()}")
    except Exception as e:
        logger.error(f"Error persisting planners: {str(e)}")
```

#### B. Update get_settings() function (add after datasources loading):

```python
# Load routers
if settings.routers_config_path:
    settings.load_routers_from_file(settings.routers_config_path)
else:
    from pathlib import Path
    default_routers_file = Path("config/routers.json")
    if default_routers_file.exists():
        settings.load_routers_from_file(str(default_routers_file))

# Load planners
if settings.planners_config_path:
    settings.load_planners_from_file(settings.planners_config_path)
else:
    from pathlib import Path
    default_planners_file = Path("config/planners.json")
    if default_planners_file.exists():
        settings.load_planners_from_file(str(default_planners_file))
```

#### C. Fix Tools API (backend/orchestrator/app/api/tools.py)

Add `clear_settings_cache()` import at top:
```python
from ..config import get_settings, Settings, ToolConfig, clear_settings_cache
```

In `create_tool`, after `settings.add_tool(tool_config)`:
```python
clear_settings_cache()
```

In `update_tool`, after `settings.add_tool(tool_config)`:
```python
clear_settings_cache()
```

In `delete_tool`, after `settings.remove_tool(name)`:
```python
clear_settings_cache()
```

#### D. Fix Datasources API (backend/orchestrator/app/api/datasources.py)

Same as tools - add import and call `clear_settings_cache()` after create/update/delete operations.

## Next Steps for Full Implementation

1. **Complete config.py** - Add remaining methods listed above
2. **Fix tools.py and datasources.py** - Add cache clearing
3. **Create routers.py API** - Similar to tools.py
4. **Create planners.py API** - Similar to tools.py  
5. **Update main.py** - Register new routers
6. **Create Frontend GUI** - RoutersPlannersConfig.tsx
7. **Update App.tsx** - Add route
8. **Create example configs** - routers.example.json, planners.example.json

## Testing Checklist

- [ ] Test router CRUD via API
- [ ] Test planner CRUD via API
- [ ] Test tools persistence fix
- [ ] Test datasources persistence fix
- [ ] Test GUI functionality
- [ ] Test persistence across server restarts

## Key Files to Create/Modify

### To Modify:
1. backend/orchestrator/app/config.py
2. backend/orchestrator/app/api/tools.py
3. backend/orchestrator/app/api/datasources.py
4. backend/orchestrator/app/main.py
5. frontend/src/App.tsx

### To Create:
1. backend/orchestrator/app/api/routers.py
2. backend/orchestrator/app/api/planners.py
3. frontend/src/pages/RoutersPlannersConfig.tsx
4. backend/orchestrator/config/routers.example.json
5. backend/orchestrator/config/planners.example.json

## Implementation is 30% Complete

The foundation (models and basic methods) is in place. The remaining work involves:
- Completing CRUD methods (20%)
- Creating API endpoints (25%)
- Creating GUI (20%)
- Testing and fixes (5%)
