# Chat Studio Model Loading Fix - TODO

## Objective
Fix the "Failed to load models" error in Chat Studio by improving error handling and providing better user feedback when LLM is not configured.

## Current Issues
1. Chat Studio shows generic error "Failed to load models. Please check that at least one LLM is configured."
2. No clear guidance on how to configure LLM
3. Error handling doesn't distinguish between different failure scenarios
4. No retry mechanism or refresh button for models

## Implementation Plan

### Phase 1: Backend Improvements ✓
- [x] Improve `/api/chat/ui/models` endpoint error handling
- [x] Add better logging for debugging
- [x] Return more specific error messages
- [x] Ensure fallback models are always available

### Phase 2: Frontend Improvements
- [ ] Update ChatStudio.tsx to show more helpful error messages
- [ ] Add link to LLM Config page when no LLM is configured
- [ ] Improve model dropdown UI with better empty state
- [ ] Add manual refresh button for models
- [ ] Show loading state while fetching models

### Phase 3: Testing
- [ ] Test with no LLM configured
- [ ] Test with Ollama configured
- [ ] Test with OpenAI-compatible endpoint
- [ ] Test error recovery after configuring LLM

## Files to Edit
1. `backend/orchestrator/app/api/chat_ui.py` - Improve models endpoint
2. `frontend/src/pages/ChatStudio.tsx` - Better error handling and UI
3. `frontend/src/pages/LLMConfig.tsx` - Add helper text about Chat Studio

## Success Criteria
- Clear error messages when LLM not configured
- Easy path to configure LLM from Chat Studio
- Models load successfully when LLM is configured
- Graceful fallback when LLM server is unreachable
