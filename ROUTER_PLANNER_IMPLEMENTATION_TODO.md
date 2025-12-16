# Router & Planner GUI Implementation + Tools/Datasources Fix

## Implementation Checklist

### Phase 1: Backend - Configuration Models & Persistence
- [ ] Update `backend/orchestrator/app/config.py`
  - [ ] Add RouterConfig model
  - [ ] Add PlannerConfig model
  - [ ] Add router/planner dictionaries to Settings
  - [ ] Add CRUD methods for routers
  - [ ] Add CRUD methods for planners
  - [ ] Add persistence methods
  - [ ] Update get_settings() to load configs

### Phase 2: Backend - API Endpoints
- [ ] Create `backend/orchestrator/app/api/routers.py`
  - [ ] List routers endpoint
  - [ ] Get router endpoint
  - [ ] Create router endpoint
  - [ ] Update router endpoint
  - [ ] Delete router endpoint
  - [ ] Test router endpoint
  - [ ] Get available types endpoint

- [ ] Create `backend/orchestrator/app/api/planners.py`
  - [ ] List planners endpoint
  - [ ] Get planner endpoint
  - [ ] Create planner endpoint
  - [ ] Update planner endpoint
  - [ ] Delete planner endpoint
  - [ ] Test planner endpoint
  - [ ] Get available types endpoint

- [ ] Update `backend/orchestrator/app/main.py`
  - [ ] Import routers API
  - [ ] Import planners API
  - [ ] Register routers

### Phase 3: Backend - Fix Tools & Datasources
- [ ] Fix `backend/orchestrator/app/api/tools.py`
  - [ ] Add cache clearing after create
  - [ ] Add cache clearing after update
  - [ ] Add cache clearing after delete

- [ ] Fix `backend/orchestrator/app/api/datasources.py`
  - [ ] Add cache clearing after create
  - [ ] Add cache clearing after update
  - [ ] Add cache clearing after delete

### Phase 4: Frontend - Router & Planner GUI
- [ ] Create `frontend/src/pages/RoutersPlannersConfig.tsx`
  - [ ] Tab interface (Routers | Planners)
  - [ ] List routers with accordion
  - [ ] List planners with accordion
  - [ ] Add/Edit router dialog
  - [ ] Add/Edit planner dialog
  - [ ] Test functionality
  - [ ] Enable/disable toggle
  - [ ] Delete confirmation

- [ ] Update `frontend/src/App.tsx`
  - [ ] Add route for routers/planners page

### Phase 5: Configuration Files
- [ ] Create `backend/orchestrator/config/routers.example.json`
- [ ] Create `backend/orchestrator/config/planners.example.json`

### Phase 6: Testing
- [ ] Test router CRUD via API
- [ ] Test planner CRUD via API
- [ ] Test GUI functionality
- [ ] Test persistence across restarts
- [ ] Test tools/datasources fixes

## Status: Starting Implementation
