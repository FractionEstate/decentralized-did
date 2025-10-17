# Task 4: Integration Testing - Implementation Plan

**Date**: October 15, 2025
**Status**: IN PROGRESS - Phase 2: Demo Wallet Integration Tests (API suites passing; docs & perf pending)
**Duration**: 5-6 days (estimated)
**Priority**: HIGH

---

## Overview

Comprehensive end-to-end integration testing to validate the complete biometric DID system: demo wallet → API servers → blockchain. This task includes completing the 9 deferred integration tests from Task 1 and full-stack testing of all system components.

---

## Objectives

### Primary Goals
1. ✅ Fix and configure all 3 API servers (basic, secure, mock)
2. ✅ Complete 9 deferred demo wallet integration tests
3. ✅ Test end-to-end flows (enrollment, verification, blockchain)
4. ✅ Validate security controls (rate limiting, auth, headers)
5. ✅ Performance benchmarks (<150ms enrollment, <75ms verification)
6. ✅ Load testing (100+ concurrent users)

### Success Criteria
- [x] All 3 API servers operational and tested
- [x] 9 deferred integration tests passing (total: 14/14)
- [ ] End-to-end blockchain integration validated
- [ ] Performance targets met (P95 <150ms enrollment, <75ms verification)
- [ ] Load testing successful (100+ concurrent users, <1% error rate)
- [ ] Security controls validated (OWASP Top 10 compliance)
- [ ] Comprehensive test documentation

---

## Phase 1: API Server Setup & Configuration (1 day / 8 hours)

### Objectives
- Fix basic API server (import errors)
- Configure secure API server JWT authentication
- Set up mock API server for testing
- Create test credentials and configuration
- Document API endpoints and authentication flows

### 1.1 Fix Basic API Server (2 hours)

**Current Issue**: Import error in `api_server.py` (line 13)
```python
from src.biometrics.fuzzy_extractor_v2 import (
    FuzzyExtractor,  # ❌ Does not exist
    extract_key,     # ❌ Does not exist
    reproduce_key,   # ❌ Does not exist
)
```

**Available Functions** (from module inspection):
- `fuzzy_extract_gen()` - Generate key and helper data
- `fuzzy_extract_rep()` - Reproduce key from noisy biometric
- `BCHCodec` - Error correction codec
- `HelperData` - Helper data structure
- `derive_key_from_biometric()` - Key derivation

**Tasks** (Completed October 15, 2025):
- [x] Update imports to use correct function names
- [x] Fix `did.generator_v2` imports (check current structure)
- [x] Update endpoint implementations to use new APIs
- [x] Test basic server startup (no errors)
- [x] Test `/health` endpoint
- [x] Document API changes

**Files to Modify**:
- `api_server.py` - Fix imports and update logic

### 1.2 Configure Secure API Server JWT Authentication (3 hours)

**Current Status**: Secure server running at localhost:8000 but requires JWT auth

**Tasks** (Completed October 15, 2025):
- [x] Review JWT authentication implementation (`src/decentralized_did/security/authentication.py`)
- [x] Create test user credentials
- [x] Document JWT token generation process
- [x] Create authentication helper for tests
- [x] Test token generation and validation
- [x] Update API client in demo wallet (if needed)
- [x] Document authentication flow

**Files to Review/Modify**:
- `api_server_secure.py` - Current implementation
- `src/decentralized_did/security/authentication.py` - JWT manager
- `demo-wallet/tests/utils/api-client.ts` - Client-side auth

**Test Credentials Setup**:
```python
# Create test user with API key
test_user = {
    "username": "test_user",
    "api_key": "test_api_key_for_integration_testing",
    "roles": ["user", "admin"],
    "permissions": ["biometric:generate", "biometric:verify"]
}
```

### 1.3 Set Up Mock API Server (1 hour)

**Purpose**: Fast testing without full backend (in-memory, deterministic)

**Tasks** (Completed October 15, 2025):
- [x] Review `api_server_mock.py` implementation
- [x] Test mock server startup (port 8002)
- [x] Verify mock endpoints work
- [x] Document mock server behavior
- [x] Create mock data fixtures

**Files to Review**:
- `api_server_mock.py` - Mock implementation

### 1.4 API Endpoint Documentation (1 hour)

**Tasks** (Completed October 16, 2025):
- [x] Document all endpoints (basic, secure, mock servers)
- [x] Document request/response schemas
- [x] Document authentication requirements
- [x] Create Postman/curl examples
- [x] Update OpenAPI/Swagger docs

**Endpoints to Document**:

#### Basic API Server (Port 8000)
- `POST /api/biometric/generate` - Generate biometric DID
- `POST /api/biometric/verify` - Verify fingerprints
- `GET /health` - Health check

#### Secure API Server (Port 8001)
- `POST /auth/token` - Get JWT access token
- `POST /api/biometric/generate` - Generate biometric DID (requires JWT)
- `POST /api/biometric/verify` - Verify fingerprints (requires JWT)
- `GET /health` - Health check

#### Mock API Server (Port 8002)
- `POST /api/biometric/generate` - Mock DID generation
- `POST /api/biometric/verify` - Mock verification
- `GET /health` - Health check

### 1.5 Test Configuration & Credentials (1 hour)

**Tasks** (Completed October 16, 2025):
- [x] Create `.env.test` configuration file
- [x] Set up test API keys and JWT secrets
- [x] Configure Blockfrost test API key
- [x] Document environment variables
- [x] Create test data fixtures

**Environment Variables**:
```bash
# API Configuration
API_HOST=localhost
API_PORT_BASIC=8000
API_PORT_SECURE=8001
API_PORT_MOCK=8002

# Authentication
JWT_SECRET=test_jwt_secret_for_integration_testing
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# Blockfrost (Cardano Testnet)
BLOCKFROST_API_KEY=testnet_api_key_here
CARDANO_NETWORK=testnet

# Test Credentials
TEST_USER_USERNAME=test_user
TEST_USER_API_KEY=test_api_key_for_integration_testing
```

---

## Phase 2: Demo Wallet Integration Tests (1-1.5 days / 10-12 hours)

### Objectives
- Complete 9 deferred API integration tests
- Test enrollment flow (wallet → API → backend)
- Test verification flow (wallet → API → backend)
- Test error handling and edge cases
- Performance benchmarks (end-to-end)

### 2.1 Complete Deferred Integration Tests (6 hours)

**9 Deferred Tests** (from Task 1):
1. should generate deterministic DID with mock API server
2. should generate consistent DIDs for same biometric (via API)
3. should generate different DIDs for different biometrics (via API)
4. should store and retrieve helper data correctly (via API)
5. should verify with same biometric (exact match via API)
6. should verify with noisy recapture (fuzzy matching via API)
7. should fail verification with wrong biometric (via API)
8. should complete enrollment in <100ms (end-to-end with API)
9. should complete verification in <50ms (end-to-end with API)

**Tasks**:
- [x] Set up API authentication for tests
    - [x] Implemented JWT token retrieval/caching in `BiometricDidService` (Oct 16)
    - [x] Validate secure server flow end-to-end via integration suite (Oct 17)
- [x] Enable API tests (`RUN_API_TESTS=true`)
- [x] Run tests against mock API server (fast)
- [x] Run tests against basic API server (harness wallet address updated Oct 17)
- [x] Run tests against secure API server (with JWT)
- [x] Fix any failing tests
- [x] Document test results (docs/API-ENDPOINTS.md, docs/API-TEST-CONFIGURATION.md updated Oct 17)

**Files to Modify**:
- `demo-wallet/src/core/biometric/__tests__/biometricDidService.integration.test.ts`
- `demo-wallet/tests/utils/api-client.ts` (add auth support)

### 2.2 Enrollment Flow Testing (2 hours)

**Scenarios**:
- [x] Successful enrollment (happy path)
- [ ] Duplicate DID detection (Sybil resistance)
- [x] Invalid biometric data rejection (client-side guard; server-side negative test queued)
- [x] Helper data storage (inline save/load verified; external helper URI pending Phase 3)
- [x] Metadata v1.1 validation
- [ ] Error handling (network errors, timeouts)

### 2.3 Verification Flow Testing (2 hours)

**Scenarios**:
- [x] Exact match verification (same biometric)
- [x] Fuzzy matching verification (noisy recapture)
- [x] Failed verification (wrong biometric)
- [x] Missing helper data error (client storage guard; API-level failure scenario queued)
- [x] Invalid DID format error (client guard)
- [ ] Threshold tuning (false accept/reject rates)

### 2.4 Performance Benchmarks (2 hours)

**Metrics**:
- [ ] Enrollment end-to-end latency (P50, P95, P99)
- [ ] Verification end-to-end latency (P50, P95, P99)
- [ ] API response times (per endpoint)
- [ ] Network overhead measurement
- [ ] Database query times (if applicable)

**Targets**:
- Enrollment P95: <150ms (end-to-end)
- Verification P95: <75ms (end-to-end)
- API overhead: <20ms

### 2.5 Test Run Summary (October 17, 2025)

| Server | Auth Mode | Tests (pass/fail) | Enrollment time (ms) | Verification time (ms) | Notes |
| --- | --- | --- | --- | --- | --- |
| Mock (`api_server_mock.py`) | None | 14/14 | 1.42 | 1.22 | `npm test` exits with code 1 because global coverage thresholds remain at legacy values; assertions all pass. |
| Basic (`api_server.py`) | None (cleared API_KEY/API_SECRET_KEY) | 14/14 | 1.34 | 1.17 | Requires blanking shared auth env vars (`API_KEY= API_SECRET_KEY=`) so the client skips JWT handshake. |
| Secure (`api_server_secure.py`) | JWT bearer | 14/14 | 2.24 | 1.90 | Token exchange exercised; security warnings expected in integration mode (rate limits/audit logging disabled). |

> Coverage gating follow-up: Jest global thresholds still reflect pre-Phase 4 deterministic baselines. Resolving or updating thresholds is tracked separately; failing exit code does not indicate assertion failures in the integration suite.

---

## Phase 3: API Server Testing (1.5 days / 12 hours)

### Objectives
- Test all 3 servers comprehensively
- Validate security controls
- Load testing (concurrent users)
- Error handling and resilience
- Documentation validation

### 3.1 Basic API Server Testing (3 hours)

**Tests**:
- [ ] Endpoint functionality (generate, verify, health)
- [ ] Request/response schema validation
- [ ] Error handling (400, 404, 500 errors)
- [ ] CORS configuration
- [ ] Logging and audit trails
- [ ] Performance benchmarks

### 3.2 Secure API Server Testing (4 hours)

**Security Tests**:
- [ ] JWT authentication (token generation, validation)
- [ ] API key authentication
- [ ] Rate limiting (per-IP, per-user, global)
- [ ] Security headers (HSTS, CSP, X-Frame-Options)
- [ ] Input validation and sanitization
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] CSRF protection (if applicable)

**OWASP API Security Top 10 Validation**:
- [ ] API1: Broken Object Level Authorization
- [ ] API2: Broken Authentication
- [ ] API3: Broken Object Property Level Authorization
- [ ] API4: Unrestricted Resource Consumption
- [ ] API5: Broken Function Level Authorization
- [ ] API6: Unrestricted Access to Sensitive Business Flows
- [ ] API7: Server Side Request Forgery
- [ ] API8: Security Misconfiguration
- [ ] API9: Improper Inventory Management
- [ ] API10: Unsafe Consumption of APIs

### 3.3 Mock API Server Testing (2 hours)

**Tests**:
- [ ] Mock behavior (deterministic responses)
- [ ] Fast response times (<10ms)
- [ ] No external dependencies
- [ ] Test data fixtures
- [ ] Edge case simulation

### 3.4 Load Testing (3 hours)

**Scenarios**:
- [ ] 10 concurrent users (baseline)
- [ ] 50 concurrent users (normal load)
- [ ] 100 concurrent users (high load)
- [ ] 500 concurrent users (stress test)
- [ ] 1000 concurrent users (breaking point)

**Metrics**:
- [ ] Throughput (requests/second)
- [ ] Response time distribution (P50, P95, P99)
- [ ] Error rate (<1% target)
- [ ] Resource utilization (CPU, memory, network)
- [ ] Database connections (if applicable)

**Tools**:
- Locust (Python-based load testing)
- k6 (Go-based JavaScript load testing)
- Apache Bench (ab) for quick tests

---

## Phase 4: End-to-End Blockchain Integration (1-1.5 days / 10-12 hours)

### Objectives
- Cardano blockchain integration tests
- DID registration on-chain
- Metadata storage and retrieval
- Transaction building and submission
- Blockchain query validation

### 4.1 Blockfrost Integration Testing (4 hours)

**Tests**:
- [ ] API key validation
- [ ] Network selection (testnet vs mainnet)
- [ ] Transaction submission
- [ ] Query transactions by wallet address
- [ ] Query metadata by transaction hash
- [ ] Error handling (rate limits, network errors)
- [ ] Retry logic and resilience

### 4.2 DID Registration On-Chain (4 hours)

**Tests**:
- [ ] Build transaction with metadata
- [ ] Sign transaction (wallet integration)
- [ ] Submit transaction to blockchain
- [ ] Wait for confirmation (block inclusion)
- [ ] Query DID metadata from blockchain
- [ ] Verify metadata integrity
- [ ] Test duplicate DID detection

### 4.3 Metadata Storage & Retrieval (2 hours)

**Tests**:
- [ ] Inline helper data (small datasets)
- [ ] External helper data (large datasets, IPFS)
- [ ] Metadata v1.1 format validation
- [ ] Multi-controller support
- [ ] Revocation flag updates
- [ ] Timestamp validation

### 4.4 Transaction Building (2 hours)

**Tests**:
- [ ] CIP-30 wallet integration
- [ ] Transaction fee calculation
- [ ] UTxO selection
- [ ] Change address handling
- [ ] Metadata encoding (CBOR)
- [ ] Transaction serialization

---

## Phase 5: Performance & Load Testing (1 day / 8 hours)

### Objectives
- Comprehensive load testing
- Performance profiling
- Memory leak detection
- Stress testing (degradation analysis)
- Benchmark documentation

### 5.1 Load Testing (4 hours)

**Test Scenarios**:
- [ ] Enrollment load test (100 users, 10 req/s each)
- [ ] Verification load test (100 users, 20 req/s each)
- [ ] Mixed workload (50% enrollment, 50% verification)
- [ ] Spike test (sudden traffic increase)
- [ ] Soak test (sustained load for 1 hour)

**Metrics to Collect**:
- Throughput (requests/second)
- Response time (P50, P95, P99, P99.9)
- Error rate (%)
- Resource utilization (CPU, memory, disk, network)
- Database performance (query times, connection pool)

### 5.2 Performance Profiling (2 hours)

**Tools**:
- cProfile (Python CPU profiling)
- py-spy (Python sampling profiler)
- memory_profiler (Python memory profiling)
- Chrome DevTools (JavaScript profiling)

**Analysis**:
- [ ] Identify bottlenecks (CPU, I/O, network)
- [ ] Optimize slow functions
- [ ] Reduce memory allocations
- [ ] Optimize database queries
- [ ] Cache frequently accessed data

### 5.3 Memory Leak Detection (1 hour)

**Tests**:
- [ ] Run 10,000 enrollments (monitor memory growth)
- [ ] Run 10,000 verifications (monitor memory growth)
- [ ] Check for unreleased resources (connections, file handles)
- [ ] Verify garbage collection effectiveness

### 5.4 Stress Testing (1 hour)

**Scenarios**:
- [ ] Gradual load increase (find breaking point)
- [ ] Sustained overload (degradation analysis)
- [ ] Recovery testing (system resilience)
- [ ] Cascading failure prevention

---

## Deliverables

### Documentation
- [ ] API Server Setup Guide
- [ ] Integration Testing Guide
- [ ] Performance Benchmark Report
- [ ] Load Testing Report
- [ ] Security Validation Report
- [ ] Known Issues and Limitations
- [ ] Troubleshooting Guide

### Test Artifacts
- [ ] 14/14 integration tests passing (9 new + 5 existing)
- [ ] Load test scripts (Locust, k6)
- [ ] Performance profiles (cProfile, py-spy)
- [ ] Security scan reports (OWASP ZAP)
- [ ] Test data fixtures
- [ ] CI/CD pipeline configuration

### Code
- [ ] Fixed basic API server (api_server.py)
- [ ] Configured secure API server (api_server_secure.py)
- [ ] Updated demo wallet API client (with auth)
- [ ] Integration test suite updates
- [ ] Load testing scripts

---

## Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Phase 1: API Server Setup | 1 day (8h) | 🚧 IN PROGRESS |
| Phase 2: Demo Wallet Tests | 1-1.5 days (10-12h) | ⏳ PENDING |
| Phase 3: API Server Testing | 1.5 days (12h) | ⏳ PENDING |
| Phase 4: Blockchain Integration | 1-1.5 days (10-12h) | ⏳ PENDING |
| Phase 5: Performance & Load | 1 day (8h) | ⏳ PENDING |
| **Total** | **5-6 days** | **IN PROGRESS** |

**Start Date**: October 15, 2025
**Target Completion**: October 20-21, 2025

---

## Dependencies

### External Services
- Blockfrost API (Cardano testnet) - API key required
- Cardano testnet node (optional, for local testing)
- Redis (optional, for distributed rate limiting)

### Tools & Libraries
- Python 3.10+
- Node.js 18+
- Locust (load testing)
- k6 (load testing)
- OWASP ZAP (security scanning)
- pytest (Python testing)
- Jest (JavaScript testing)

---

## Risk Assessment

### High Risk
- ⚠️ Blockfrost API rate limits (testnet: 50 req/10s)
- ⚠️ API server import errors (breaking changes in module structure)
- ⚠️ JWT authentication complexity (secure server)

### Medium Risk
- ⚠️ Performance targets may require optimization
- ⚠️ Load testing may reveal scaling issues
- ⚠️ Blockchain transaction delays (testnet)

### Low Risk
- ⚠️ Mock server implementation (simple, no external dependencies)
- ⚠️ Documentation updates (time-consuming but straightforward)

---

## Mitigation Strategies

### For API Server Import Errors
- Review current module structure (`src/biometrics/`, `src/did/`)
- Update imports to match current API
- Create adapter layer if needed (backwards compatibility)

### For Blockfrost Rate Limits
- Implement request throttling (respect 50 req/10s limit)
- Use mock server for bulk testing
- Cache blockchain queries (reduce API calls)

### For Performance Issues
- Profile code early (identify bottlenecks)
- Optimize hot paths (caching, parallelization)
- Use async/await (non-blocking I/O)
- Consider connection pooling (database, HTTP)

---

## Success Criteria Checklist

### Must Have (Critical)
- [ ] All 3 API servers operational
- [ ] 14/14 integration tests passing
- [ ] JWT authentication working
- [ ] Enrollment P95 <150ms
- [ ] Verification P95 <75ms
- [ ] Load test: 100 users, <1% error rate
- [ ] Security: OWASP Top 10 validated
- [ ] Documentation complete

### Should Have (Important)
- [ ] 500+ concurrent users supported
- [ ] Memory leaks fixed
- [ ] Performance profiling done
- [ ] Stress testing complete
- [ ] Blockchain integration validated

### Nice to Have (Optional)
- [ ] 1000+ concurrent users supported
- [ ] Redis rate limiting (distributed)
- [ ] Advanced caching (Redis, Memcached)
- [ ] CI/CD pipeline fully automated

---

## Notes

- Task 1 (Demo Wallet) at 95% - manual testing can be completed alongside this task
- 9 deferred integration tests are the highest priority in Phase 2
- Focus on quality over speed - comprehensive testing is critical for production readiness
- Document all issues and limitations discovered during testing

---

**Next Step**: Start Phase 1.1 - Fix basic API server import errors
