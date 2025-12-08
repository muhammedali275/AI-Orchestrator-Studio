# GUI Implementation Plan

## Overview
This document outlines the implementation plan for the AI Orchestrator Studio GUI according to the specified requirements.

## Current Status

### ✅ Completed Components
1. **Sidebar.tsx** - Updated with new menu structure
2. **Dashboard.tsx** - Existing dashboard with system metrics
3. **LLMConfig.tsx** - LLM configuration page (needs minor updates)
4. **ToolsConfig.tsx** - Tools configuration page (needs to include datasources)
5. **Topology.tsx** - Orchestration flow visualization
6. **ChatStudio.tsx** - Internal chat test interface
7. **Monitoring.tsx** - Server monitoring (needs updates)

### 🔄 Pages to Create/Update

#### 1. Agents & System Prompts Page (NEW)
**File:** `frontend/src/pages/AgentsConfig.tsx`
**Route:** `/agents`
**API Endpoints:**
- GET `/api/agents`
- POST `/api/agents`
- PUT `/api/agents/{id}`
- DELETE `/api/agents/{id}`
- POST `/api/agents/{id}/test`

**Features:**
- CRUD operations for agents
- System prompt editor (multi-line textarea)
- LLM connection dropdown
- Tools multi-select
- LangGraph profile selector
- System prompt helper template
- Test agent connectivity

#### 2. Credentials & Security Page (NEW)
**File:** `frontend/src/pages/CredentialsSecurity.tsx`
**Route:** `/credentials`
**API Endpoints:**
- GET `/api/credentials`
- POST `/api/credentials`
- PUT `/api/credentials/{id}`
- DELETE `/api/credentials/{id}`
- POST `/api/credentials/{id}/test`

**Features:**
- CRUD operations for credentials
- Credential types: SSH, HTTP Basic, Bearer Token, DB DSN, API Key, Custom
- Masked secret display
- Credential testing
- Security warnings

#### 3. Certificates (HTTPS) Page (NEW)
**File:** `frontend/src/pages/Certificates.tsx`
**Route:** `/certificates`
**API Endpoints:**
- GET `/api/certs`
- POST `/api/certs/upload`
- POST `/api/certs/enable`
- POST `/api/certs/disable`

**Features:**
- File upload for certificate.pem and private_key.pem
- Current TLS status display
- Enable/Disable TLS
- Certificate validation
- Security best practices guide

#### 4. Tools & Data Sources Page (UPDATE)
**File:** `frontend/src/pages/ToolsConfig.tsx`
**Current:** Only manages tools
**Update:** Add datasources management

**Additional API Endpoints:**
- GET `/api/datasources`
- POST `/api/datasources`
- PUT `/api/datasources/{id}`
- DELETE `/api/datasources/{id}`
- POST `/api/datasources/{id}/test`

**New Features:**
- Cube.js datasource configuration
- Test query functionality
- Datasource type selection (Cube.js, HTTP, Database)

#### 5. LLM Connections Page (UPDATE)
**File:** `frontend/src/pages/LLMConfig.tsx`
**Current:** Basic LLM configuration
**Update:** Match exact requirements

**Updates Needed:**
- Rename to "LLM Connections"
- Support multiple LLM connections (table view)
- Each connection has: Name, Base URL, API Key, Model, Timeout, max_tokens, temperature
- Test connection per LLM

#### 6. Monitoring & Services Page (UPDATE)
**File:** `frontend/src/pages/Monitoring.tsx`
**Current:** Basic server monitoring
**Update:** Add service management and location display

**New Features:**
- Map widget showing region/zone
- Service status cards (UP, DOWN, DEGRADED)
- Restart service buttons
- Health check endpoints integration

#### 7. Orchestration Flow Page (UPDATE)
**File:** `frontend/src/pages/Topology.tsx`
**Current:** Basic topology visualization
**Update:** Add visual editor with config panels

**New Features:**
- Visual editor for 8-node flow
- Right-side config panel for each node
- Node configuration editing
- Save flow configuration
- Flow validation

#### 8. Internal Chat Test Page (UPDATE)
**File:** `frontend/src/pages/ChatStudio.tsx`
**Current:** Basic chat interface
**Update:** Add tool/step visualization

**New Features:**
- Display which tools were used
- Show execution steps
- Streaming response visualization
- Debug mode toggle

### 📝 App.tsx Updates
**File:** `frontend/src/App.tsx`

**New Routes to Add:**
```typescript
<Route path="/agents" element={<AgentsConfig />} />
<Route path="/credentials" element={<CredentialsSecurity />} />
<Route path="/certificates" element={<Certificates />} />
```

### 🎨 Design Considerations

#### Theme
- Dark theme by default (already implemented)
- Enterprise-suitable color scheme
- Consistent with existing Material-UI theme

#### Layout
- Left sidebar navigation (already implemented)
- Top header with theme toggle (already implemented)
- Main content area with proper spacing
- Responsive design for different screen sizes

#### Components
- Reuse existing Material-UI components
- Consistent card styling
- Gradient buttons and accents
- Smooth animations and transitions

### 🔧 Implementation Order

1. **Phase 1: Create New Pages**
   - [ ] AgentsConfig.tsx
   - [ ] CredentialsSecurity.tsx
   - [ ] Certificates.tsx

2. **Phase 2: Update Existing Pages**
   - [ ] Update ToolsConfig.tsx (add datasources)
   - [ ] Update LLMConfig.tsx (multiple connections)
   - [ ] Update Monitoring.tsx (add services & map)
   - [ ] Update Topology.tsx (add visual editor)
   - [ ] Update ChatStudio.tsx (add tool visualization)

3. **Phase 3: Update App.tsx**
   - [ ] Add new routes
   - [ ] Import new components

4. **Phase 4: Update Dashboard.tsx**
   - [ ] Add quick links to new pages
   - [ ] Update metrics to reflect new components
   - [ ] Add system health overview

5. **Phase 5: Testing & Polish**
   - [ ] Test all CRUD operations
   - [ ] Test API integrations
   - [ ] Verify responsive design
   - [ ] Check accessibility
   - [ ] Performance optimization

### 📚 API Endpoints Summary

#### Existing Endpoints
- `/api/llm/*` - LLM configuration
- `/api/agents/*` - Agent management
- `/api/tools/*` - Tools management
- `/api/datasources/*` - Datasources management
- `/api/credentials/*` - Credentials management
- `/api/certs/*` - Certificate management
- `/api/monitoring/*` - System monitoring
- `/api/topology/*` - Topology management
- `/api/chat/*` - Chat interface

#### Backend Status
✅ All required API endpoints are already implemented in the backend

### 🚀 Next Steps

1. Start with creating the three new pages (Agents, Credentials, Certificates)
2. Update existing pages to match requirements
3. Update App.tsx with new routes
4. Enhance Dashboard with new features
5. Test end-to-end functionality
6. Document usage and configuration

### 📋 Notes

- The backend API is already fully implemented
- Focus on creating intuitive, user-friendly interfaces
- Ensure proper error handling and validation
- Add loading states and feedback messages
- Follow existing code patterns and styling
- Maintain consistency with the current design system

## Timeline Estimate

- **Phase 1:** 2-3 hours (New pages)
- **Phase 2:** 2-3 hours (Update existing pages)
- **Phase 3:** 30 minutes (App.tsx updates)
- **Phase 4:** 1 hour (Dashboard updates)
- **Phase 5:** 1-2 hours (Testing & polish)

**Total:** 6-9 hours of development time

## Success Criteria

✅ All 9 pages are functional and accessible
✅ All CRUD operations work correctly
✅ API integrations are successful
✅ UI is consistent and professional
✅ Responsive design works on different screen sizes
✅ No console errors or warnings
✅ Smooth user experience with proper feedback
✅ Documentation is complete and accurate
