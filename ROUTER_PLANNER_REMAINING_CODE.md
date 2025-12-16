# Router & Planner Implementation - Remaining Code

## Status: 40% Complete

### What's Been Completed ✅
1. RouterConfig and PlannerConfig models added to config.py
2. Routers and planners dictionaries added to Settings
3. get_router() and get_planner() methods added
4. add_router() and add_planner() methods added
5. remove_router() and remove_planner() methods added

### What Remains (60% of work)

---

## 1. Complete config.py - Add Load and Persist Methods

Add these methods after `load_datasources_from_file()`:

```python
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
```

Add these methods after `_persist_agents()`:

```python
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

Update `get_settings()` function - add after datasources loading:

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

---

## 2. Fix tools.py - Add Cache Clearing

In `backend/orchestrator/app/api/tools.py`:

Update import at top:
```python
from ..config import get_settings, Settings, ToolConfig, clear_settings_cache
```

In `create_tool()` after `settings.add_tool(tool_config)`:
```python
clear_settings_cache()
```

In `update_tool()` after `settings.add_tool(tool_config)`:
```python
clear_settings_cache()
```

In `delete_tool()` after `settings.remove_tool(name)`:
```python
clear_settings_cache()
```

---

## 3. Fix datasources.py - Add Cache Clearing

In `backend/orchestrator/app/api/datasources.py`:

Update import at top:
```python
from ..config import get_settings, Settings, DataSourceConfig, clear_settings_cache
```

In `create_datasource()` after `settings.add_datasource(ds_config)`:
```python
clear_settings_cache()
```

In `update_datasource()` after `settings.add_datasource(ds_config)`:
```python
clear_settings_cache()
```

In `delete_datasource()` after `settings.remove_datasource(name)`:
```python
clear_settings_cache()
```

---

## 4. Create routers.py API

Create file: `backend/orchestrator/app/api/routers.py`

See ROUTER_PLANNER_COMPLETE_IMPLEMENTATION.md for the full routers.py code (similar structure to tools.py)

---

## 5. Create planners.py API

Create file: `backend/orchestrator/app/api/planners.py`

See ROUTER_PLANNER_COMPLETE_IMPLEMENTATION.md for the full planners.py code (similar structure to tools.py)

---

## 6. Update main.py

In `backend/orchestrator/app/main.py`:

Add imports:
```python
from .api.routers import router as routers_router
from .api.planners import router as planners_router
```

Register routers (after existing router registrations):
```python
app.include_router(routers_router)
app.include_router(planners_router)
```

---

## 7. Create Frontend GUI

Create file: `frontend/src/pages/RoutersPlannersConfig.tsx`

This should be similar to ToolsDataSources.tsx with tabs for Routers and Planners.

---

## 8. Update App.tsx

Add route in `frontend/src/App.tsx`:
```typescript
import RoutersPlannersConfig from './pages/RoutersPlannersConfig';

// In routes:
<Route path="/routers-planners" element={<RoutersPlannersConfig />} />
```

---

## 9. Create Example Config Files

Create `backend/orchestrator/config/routers.example.json`:
```json
{
  "routers": [
    {
      "name": "default_router",
      "type": "rule_based",
      "enabled": true,
      "priority": 0,
      "rules": {
        "keywords": {
          "churn": "churn_analytics",
          "query": "data_query",
          "search": "web_search"
        }
      },
      "description": "Default keyword-based intent router"
    }
  ]
}
```

Create `backend/orchestrator/config/planners.example.json`:
```json
{
  "planners": [
    {
      "name": "default_planner",
      "type": "sequential",
      "enabled": true,
      "strategy": "sequential",
      "templates": {
        "churn_analytics": {
          "steps": ["data_retrieval", "analysis", "report"]
        },
        "data_query": {
          "steps": ["query_execution", "formatting"]
        }
      },
      "description": "Default sequential task planner"
    }
  ]
}
```

---

## Implementation Priority

1. ✅ Complete config.py (load/persist methods) - 10%
2. ✅ Fix tools.py cache clearing - 2%
3. ✅ Fix datasources.py cache clearing - 2%
4. ⏳ Create routers.py API - 15%
5. ⏳ Create planners.py API - 15%
6. ⏳ Update main.py - 1%
7. ⏳ Create Frontend GUI - 20%
8. ⏳ Update App.tsx - 1%
9. ⏳ Create example configs - 2%
10. ⏳ Testing - 32%

## Next Steps

Continue with items 1-3 first (config.py completion and cache fixes), then move to API creation.
