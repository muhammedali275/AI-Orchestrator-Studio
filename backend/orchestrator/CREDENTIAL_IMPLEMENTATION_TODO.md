# Credential Management Implementation TODO

## Phase 1: Foundation (Database & Encryption)
- [ ] Create database models directory and Credential model
- [ ] Create encryption utilities
- [ ] Update requirements.txt

## Phase 2: Service Layer
- [ ] Create credential service with CRUD operations

## Phase 3: API Layer
- [ ] Create credential API endpoints
- [ ] Register credential router in main.py

## Phase 4: Configuration Integration
- [ ] Update config models to reference credentials
- [ ] Add credential_id fields to existing configs

## Phase 5: Client Integration
- [ ] Update LLM client to use credentials
- [ ] Update external agent client to use credentials
- [ ] Update datasource client to use credentials
- [ ] Update monitoring to use credentials

## Phase 6: Configuration & Documentation
- [ ] Update example.env with ORCH_CRED_KEY
- [ ] Create migration guide

## Security Checklist
- [ ] NO credentials in plain text storage
- [ ] NO credentials in API responses
- [ ] NO credentials in logs
- [ ] Master key from environment only
- [ ] Support multiple credential types (ssh, http_basic, bearer_token, db_dsn)
