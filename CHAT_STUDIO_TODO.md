# Chat Studio Implementation TODO

## Phase 1: Database Models & Schema ✅
- [ ] Extend `backend/orchestrator/app/db/models.py` with:
  - [ ] Conversation model
  - [ ] Message model
  - [ ] PromptProfile model
  - [ ] ChatMetric model

## Phase 2: Backend API - Chat UI Controller
- [ ] Create `backend/orchestrator/app/api/chat_ui.py` with endpoints:
  - [ ] POST /api/chat/ui/send (with streaming)
  - [ ] GET /api/chat/ui/conversations
  - [ ] GET /api/chat/ui/conversations/{id}
  - [ ] POST /api/chat/ui/conversations
  - [ ] DELETE /api/chat/ui/conversations/{id}
  - [ ] GET /api/chat/ui/models
  - [ ] GET /api/chat/ui/profiles
  - [ ] GET /api/chat/ui/prompt-profiles
  - [ ] POST /api/chat/ui/prompt-profiles
  - [ ] GET /api/chat/ui/metrics

- [ ] Create `backend/orchestrator/app/services/chat_router.py`:
  - [ ] Direct LLM routing
  - [ ] Zain Agent routing
  - [ ] Tools+Data routing
  - [ ] Memory integration
  - [ ] Metrics logging

## Phase 3: Frontend - Chat Studio Page
- [ ] Create `frontend/src/pages/ChatStudio.tsx`
- [ ] Create `frontend/src/components/chat/ConversationList.tsx`
- [ ] Create `frontend/src/components/chat/ChatMessage.tsx`
- [ ] Create `frontend/src/components/chat/ChatInput.tsx`
- [ ] Create `frontend/src/components/chat/ToolCallDisplay.tsx`
- [ ] Create `frontend/src/components/chat/ModelSelector.tsx`
- [ ] Create `frontend/src/components/chat/RoutingProfileSelector.tsx`

## Phase 4: Integration & Wiring
- [ ] Update `frontend/src/App.tsx` - add /chat route
- [ ] Update `frontend/src/components/Sidebar.tsx` - add Chat Studio menu
- [ ] Update `backend/orchestrator/app/main.py` - register chat_ui router
- [ ] Update `backend/orchestrator/app/config.py` - add chat settings

## Phase 5: Auto-detect Model Feature
- [ ] Implement model auto-detection in LLM API
- [ ] Update Chat Studio to use detected models
- [ ] Add "Detect Models" button in LLM Config

## Testing
- [ ] Test all API endpoints
- [ ] Test streaming functionality
- [ ] Test model auto-detection
- [ ] Verify no hardcoded values
- [ ] Test dark/light mode
- [ ] Performance testing

## Current Status: Starting Phase 1
