# Task 2: API Server Security Hardening - Implementation Plan

**Started**: October 14, 2025
**Estimated Duration**: 4-5 days
**Priority**: HIGH (production readiness)
**Dependencies**: None (Task 1 automated work complete)

---

## 🎯 Objectives

Transform the API servers from development-ready to production-hardened with enterprise-grade security controls:

1. **Rate Limiting**: Prevent abuse and DDoS attacks
2. **Authentication**: JWT tokens and API keys for access control
3. **Input Validation**: Sanitize all inputs to prevent injection attacks
4. **Security Headers**: HSTS, CSP, X-Frame-Options, etc.
5. **Audit Logging**: Comprehensive request/response tracking
6. **Error Handling**: Secure error messages (no information leakage)
7. **Testing**: OWASP ZAP scan, load testing, penetration testing

---

## 📋 Current State Analysis

### Existing API Servers

**1. `api_server_mock.py`** (Basic mock server)
- ✅ Has: Basic enrollment/verification endpoints
- ✅ Has: Deterministic DID generation (Phase 4.5)
- ✅ Has: Duplicate DID detection (Phase 4.5)
- ❌ Missing: ALL security controls

**2. `api_server.py`** (Production server)
- ✅ Has: Real biometric processing
- ✅ Has: Deterministic DID generation
- ✅ Has: Duplicate DID detection
- ❌ Missing: ALL security controls

**3. `api_server_secure.py`** (Secure server)
- ✅ Has: Basic rate limiting (simple counter)
- ✅ Has: Audit logging (basic)
- ✅ Has: Deterministic DID generation
- ✅ Has: Duplicate DID detection
- ⚠️ Needs: Enhanced rate limiting, authentication, headers, validation

### Security Gap Analysis

| Feature | Mock | Production | Secure | Target |
|---------|------|------------|--------|--------|
| Rate Limiting | ❌ | ❌ | ⚠️ Basic | ✅ Advanced |
| Authentication | ❌ | ❌ | ❌ | ✅ JWT + API Key |
| Input Validation | ❌ | ❌ | ❌ | ✅ Full |
| Security Headers | ❌ | ❌ | ❌ | ✅ Full |
| Audit Logging | ❌ | ❌ | ⚠️ Basic | ✅ Enhanced |
| Error Handling | ⚠️ | ⚠️ | ⚠️ | ✅ Secure |
| HTTPS Only | ❌ | ❌ | ❌ | ✅ Enforced |

---

## 🛡️ Security Requirements

### 1. Rate Limiting (CRITICAL)

**Goals**:
- Prevent brute-force attacks on verification endpoint
- Prevent DDoS attacks on enrollment endpoint
- Prevent API abuse and resource exhaustion

**Implementation**:
- **Library**: `slowapi` (MIT license, Flask/FastAPI compatible)
- **Strategies**:
  - Per-IP rate limiting (prevents single-source attacks)
  - Per-wallet rate limiting (prevents distributed attacks from single user)
  - Per-endpoint limits (different limits for different operations)
  - Sliding window algorithm (more accurate than fixed window)

**Rate Limits** (based on use case analysis):
```python
# Enrollment (expensive operation, creates blockchain data)
- Per IP: 5 enrollments per minute
- Per wallet: 3 enrollments per hour
- Global: 100 enrollments per minute (prevent system overload)

# Verification (cheaper operation, read-only)
- Per IP: 20 verifications per minute
- Per wallet: 100 verifications per hour
- Global: 500 verifications per minute

# Health check (free operation)
- Per IP: 60 requests per minute
- No per-wallet limit
```

**Response**:
- HTTP 429 (Too Many Requests)
- `Retry-After` header with seconds to wait
- Error message: "Rate limit exceeded. Try again in X seconds."

### 2. Authentication & Authorization (HIGH)

**Goals**:
- Prevent unauthorized access to API endpoints
- Track API usage per user/application
- Enable API key revocation
- Support multiple authentication methods

**Implementation**:
- **JWT Tokens** (for user sessions):
  - Library: `PyJWT` (MIT license)
  - Short-lived tokens (15 minutes)
  - Refresh token mechanism
  - HS256 signing algorithm
  - Claims: user_id, wallet_address, roles, exp, iat

- **API Keys** (for application access):
  - Library: Custom implementation (no external dependency)
  - Long-lived keys (30-90 days)
  - Stored hashed in database (bcrypt)
  - Format: `did_prod_<32-char-random>` or `did_test_<32-char-random>`
  - Per-key rate limits

**Endpoints**:
```python
POST /auth/register    # Create new API key
POST /auth/login       # Get JWT token (wallet signature auth)
POST /auth/refresh     # Refresh JWT token
DELETE /auth/revoke    # Revoke API key
```

**Authorization Levels**:
- **Public**: Health check (no auth required)
- **Authenticated**: Enrollment, verification (API key or JWT required)
- **Admin**: API key management (special admin JWT required)

### 3. Input Validation & Sanitization (CRITICAL)

**Goals**:
- Prevent injection attacks (SQL, NoSQL, command injection)
- Prevent XSS attacks
- Prevent buffer overflow attacks
- Ensure data integrity

**Implementation**:
- **Library**: `pydantic` v2 (MIT license, already in use)
- **Validation Rules**:
  ```python
  # Enrollment request
  - fingerprint_data: JSON object, max 100KB
  - wallet_address: Cardano address format (addr1... or addr_test1...)
  - metadata: Optional, max 10KB

  # Verification request
  - did: W3C DID format (did:cardano:...)
  - fingerprint_data: JSON object, max 100KB
  - helper_data: JSON object, max 20KB

  # Common rules
  - No null bytes
  - No control characters
  - UTF-8 encoding only
  - Max nesting depth: 10 levels
  - Max array length: 1000 items
  ```

**Sanitization**:
- Strip HTML tags from all string inputs
- Normalize Unicode characters
- Validate hex strings (helper data)
- Validate base58 strings (DIDs)

### 4. Security Headers (HIGH)

**Goals**:
- Prevent clickjacking attacks
- Prevent MIME-sniffing attacks
- Enforce HTTPS connections
- Restrict content sources (CSP)

**Implementation**:
- **Library**: `flask-talisman` (Apache 2.0 license) or custom middleware
- **Headers to Add**:
  ```python
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  X-XSS-Protection: 1; mode=block
  Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: geolocation=(), microphone=(), camera=()
  ```

**CORS Configuration**:
```python
Access-Control-Allow-Origin: https://wallet.example.com (production)
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Authorization, Content-Type
Access-Control-Max-Age: 86400
```

### 5. Enhanced Audit Logging (MEDIUM)

**Goals**:
- Track all API requests and responses
- Enable security incident investigation
- Compliance with regulations (GDPR, eIDAS)
- Performance monitoring

**Implementation**:
- **Library**: Python `logging` module + structured logging
- **Log Format**: JSON (machine-readable)
- **Log Fields**:
  ```json
  {
    "timestamp": "2025-10-14T10:30:00.123Z",
    "request_id": "req_abc123",
    "ip_address": "192.168.1.100",
    "wallet_address": "addr1...",
    "endpoint": "/enroll",
    "method": "POST",
    "status_code": 200,
    "duration_ms": 123,
    "user_agent": "Mozilla/5.0...",
    "api_key_id": "key_xyz789",
    "did": "did:cardano:mainnet:...",
    "error": null,
    "fingerprints_processed": 4
  }
  ```

**Sensitive Data Handling**:
- ❌ NEVER log: fingerprint data, helper data, private keys
- ✅ Log: DIDs, wallet addresses, request metadata
- ✅ Log: Error messages (sanitized, no stack traces to client)

**Log Retention**:
- Development: 7 days
- Production: 90 days (compliance requirement)
- Archive: 1 year (compressed, cold storage)

### 6. Secure Error Handling (MEDIUM)

**Goals**:
- Prevent information leakage through error messages
- Provide useful feedback to legitimate users
- Log detailed errors for debugging

**Implementation**:
```python
# Production error responses (client sees this)
{
  "error": "Invalid fingerprint data",
  "error_code": "INVALID_INPUT",
  "request_id": "req_abc123",
  "timestamp": "2025-10-14T10:30:00Z"
}

# Development error responses (client sees this)
{
  "error": "Invalid fingerprint data",
  "error_code": "INVALID_INPUT",
  "request_id": "req_abc123",
  "timestamp": "2025-10-14T10:30:00Z",
  "details": "Field 'minutiae' is required",
  "stack_trace": "..." # Only in dev mode
}

# Server-side logs (never sent to client)
{
  "error": "Invalid fingerprint data",
  "error_code": "INVALID_INPUT",
  "request_id": "req_abc123",
  "stack_trace": "Full stack trace...",
  "request_body": "{...}", # Sanitized
  "user_context": "..."
}
```

**Error Codes**:
- `INVALID_INPUT`: Client error (400)
- `UNAUTHORIZED`: No auth provided (401)
- `FORBIDDEN`: Auth provided but insufficient (403)
- `NOT_FOUND`: Resource not found (404)
- `RATE_LIMIT`: Too many requests (429)
- `INTERNAL_ERROR`: Server error (500)
- `SERVICE_UNAVAILABLE`: Temporary issue (503)

---

## 📦 Implementation Phases

### Phase 1: Rate Limiting (Day 1, 6-8 hours)

**Tasks**:
1. Install `slowapi` library (MIT license)
2. Implement rate limiter middleware
3. Add per-IP rate limiting to all endpoints
4. Add per-wallet rate limiting to enrollment/verification
5. Add global rate limiting
6. Implement `Retry-After` header
7. Add rate limit bypass for testing (admin API key)
8. Write unit tests for rate limiter
9. Write integration tests for rate limit enforcement

**Files to Modify**:
- `api_server.py` (add rate limiting)
- `api_server_secure.py` (enhance existing rate limiting)
- `requirements.txt` (add slowapi)
- Create `src/decentralized_did/api/rate_limiter.py`

**Tests**:
- `tests/test_api_rate_limiting.py` (new file, 20+ tests)

### Phase 2: Authentication & Authorization (Day 2, 8-10 hours)

**Tasks**:
1. Install `PyJWT` library (MIT license)
2. Implement JWT token generation and validation
3. Implement API key generation and hashing
4. Create authentication middleware
5. Add `/auth/*` endpoints (register, login, refresh, revoke)
6. Implement wallet signature verification (for JWT issuance)
7. Add authentication to enrollment/verification endpoints
8. Implement API key database (SQLite for simplicity)
9. Write unit tests for auth logic
10. Write integration tests for auth flows

**Files to Create**:
- `src/decentralized_did/api/auth.py` (JWT and API key logic)
- `src/decentralized_did/api/middleware.py` (auth middleware)
- `src/decentralized_did/api/models.py` (API key database models)

**Files to Modify**:
- `api_server.py` (add auth endpoints and middleware)
- `api_server_secure.py` (add auth endpoints and middleware)
- `requirements.txt` (add PyJWT, bcrypt)

**Tests**:
- `tests/test_api_auth.py` (new file, 30+ tests)

### Phase 3: Input Validation & Sanitization (Day 3, 6-8 hours)

**Tasks**:
1. Enhance existing Pydantic models with strict validation
2. Add custom validators for Cardano addresses
3. Add custom validators for DIDs
4. Add custom validators for hex strings (helper data)
5. Implement input sanitization (strip HTML, normalize Unicode)
6. Add max size limits to all inputs
7. Add depth limits for nested JSON
8. Write unit tests for validators
9. Write integration tests for malicious inputs

**Files to Modify**:
- `src/decentralized_did/validator.py` (enhance existing validators)
- `api_server.py` (apply validators to endpoints)
- `api_server_secure.py` (apply validators to endpoints)

**Files to Create**:
- `src/decentralized_did/api/sanitizers.py` (input sanitization functions)

**Tests**:
- `tests/test_api_validation.py` (new file, 25+ tests)
- `tests/test_api_sanitization.py` (new file, 15+ tests)

### Phase 4: Security Headers & HTTPS (Day 4, 4-6 hours)

**Tasks**:
1. Install `flask-talisman` (Apache 2.0) or implement custom middleware
2. Add all security headers to responses
3. Configure CORS properly
4. Enforce HTTPS in production mode
5. Add HTTP → HTTPS redirect
6. Test headers with online security scanners
7. Write unit tests for header middleware
8. Write integration tests for HTTPS enforcement

**Files to Create**:
- `src/decentralized_did/api/security_headers.py` (middleware)

**Files to Modify**:
- `api_server.py` (add header middleware)
- `api_server_secure.py` (add header middleware)
- `requirements.txt` (add flask-talisman if used)

**Tests**:
- `tests/test_api_security_headers.py` (new file, 15+ tests)

### Phase 5: Enhanced Audit Logging (Day 4-5, 4-6 hours)

**Tasks**:
1. Implement structured JSON logging
2. Add request/response logging middleware
3. Add performance timing to logs
4. Implement log sanitization (remove sensitive data)
5. Add log rotation and retention policies
6. Test log format and content
7. Write unit tests for logging logic
8. Write integration tests for log capture

**Files to Create**:
- `src/decentralized_did/api/audit_logger.py` (enhanced logging)

**Files to Modify**:
- `api_server.py` (add audit logging)
- `api_server_secure.py` (enhance existing audit logging)

**Tests**:
- `tests/test_api_audit_logging.py` (new file, 20+ tests)

### Phase 6: Secure Error Handling (Day 5, 3-4 hours)

**Tasks**:
1. Implement error response formatter
2. Add production vs development error modes
3. Sanitize all error messages (no info leakage)
4. Add request ID to all error responses
5. Implement error code taxonomy
6. Write unit tests for error formatter
7. Write integration tests for error scenarios

**Files to Create**:
- `src/decentralized_did/api/error_handler.py` (error formatting)

**Files to Modify**:
- `api_server.py` (add error handling middleware)
- `api_server_secure.py` (enhance existing error handling)

**Tests**:
- `tests/test_api_error_handling.py` (new file, 20+ tests)

### Phase 7: Security Testing (Day 5, 4-6 hours)

**Tasks**:
1. Install OWASP ZAP (open-source security scanner)
2. Run automated security scan against API servers
3. Fix any vulnerabilities found
4. Run load testing with `locust` (MIT license)
5. Test rate limiting under load
6. Test authentication bypass attempts
7. Test injection attacks (SQL, NoSQL, command, XSS)
8. Document all findings and mitigations
9. Create security test report

**Files to Create**:
- `tests/security/owasp_zap_test.py` (ZAP integration)
- `tests/security/load_test.py` (locust load tests)
- `docs/security-test-report.md` (findings and mitigations)

**Tools**:
- OWASP ZAP (open-source, no cost)
- locust (MIT license, load testing)

---

## 🧪 Testing Strategy

### Unit Tests (~150 tests total)
- Rate limiting logic (20 tests)
- Authentication (JWT, API keys) (30 tests)
- Input validation (25 tests)
- Input sanitization (15 tests)
- Security headers (15 tests)
- Audit logging (20 tests)
- Error handling (20 tests)

### Integration Tests (~50 tests total)
- End-to-end auth flows (10 tests)
- Rate limit enforcement (10 tests)
- Malicious input handling (15 tests)
- HTTPS enforcement (5 tests)
- Error response formats (10 tests)

### Security Tests (~20 tests total)
- OWASP ZAP scan (automated)
- Load testing (100, 500, 1000 concurrent users)
- Brute-force attack simulation
- Injection attack attempts
- Authentication bypass attempts

**Total Test Coverage**: ~220 tests

---

## 📊 Success Criteria

### Security Metrics
- ✅ OWASP ZAP scan: 0 high/critical vulnerabilities
- ✅ Rate limiting: <1% false positives under normal load
- ✅ Authentication: 100% of unauthorized requests blocked
- ✅ Input validation: 100% of malicious inputs rejected
- ✅ Audit logging: 100% of requests logged

### Performance Metrics
- ✅ Enrollment: <150ms with security overhead (was <100ms)
- ✅ Verification: <75ms with security overhead (was <50ms)
- ✅ Rate limiter overhead: <5ms per request
- ✅ Auth overhead: <10ms per request
- ✅ Logging overhead: <2ms per request

### Load Testing
- ✅ 100 concurrent users: <200ms p95 latency
- ✅ 500 concurrent users: <500ms p95 latency
- ✅ 1000 concurrent users: <1s p95 latency, no crashes

---

## 📝 Documentation Deliverables

1. **API Security Documentation** (`docs/api-security.md`)
   - Authentication guide (JWT and API keys)
   - Rate limiting policies
   - Security headers explanation
   - Error codes and handling

2. **Security Test Report** (`docs/security-test-report.md`)
   - OWASP ZAP findings
   - Load testing results
   - Penetration testing summary
   - Mitigations implemented

3. **API Key Management Guide** (`docs/api-key-management.md`)
   - How to generate API keys
   - How to revoke API keys
   - Best practices for key rotation
   - Security considerations

4. **Deployment Security Checklist** (`docs/deployment-security-checklist.md`)
   - Environment configuration
   - HTTPS setup
   - Firewall rules
   - Monitoring and alerting

---

## 🔧 Dependencies & Tools

### Python Libraries (All Open-Source)
- `slowapi` (MIT) - Rate limiting
- `PyJWT` (MIT) - JWT tokens
- `bcrypt` (Apache 2.0) - Password/API key hashing
- `flask-talisman` (Apache 2.0) - Security headers
- `pydantic` v2 (MIT) - Input validation (already installed)
- `locust` (MIT) - Load testing

### Security Tools (All Open-Source)
- OWASP ZAP (Apache 2.0) - Security scanning
- SQLite (Public domain) - API key storage

### Total New Dependencies: 5 libraries
### Total Cost: $0 (all open-source)

---

## 🚀 Next Steps

1. **Review this plan** - Ensure alignment with project goals
2. **Start Phase 1** - Implement rate limiting (Day 1)
3. **Progressive implementation** - Complete phases 1-7 sequentially
4. **Continuous testing** - Run tests after each phase
5. **Security review** - Final OWASP ZAP scan and penetration testing
6. **Documentation** - Complete all security docs

**Estimated Total Time**: 4-5 days (35-45 hours)
**Estimated Completion**: October 18-19, 2025

---

## 📋 Checklist

- [ ] Phase 1: Rate Limiting (6-8 hours)
- [ ] Phase 2: Authentication & Authorization (8-10 hours)
- [ ] Phase 3: Input Validation & Sanitization (6-8 hours)
- [ ] Phase 4: Security Headers & HTTPS (4-6 hours)
- [ ] Phase 5: Enhanced Audit Logging (4-6 hours)
- [ ] Phase 6: Secure Error Handling (3-4 hours)
- [ ] Phase 7: Security Testing (4-6 hours)
- [ ] All unit tests passing (150 tests)
- [ ] All integration tests passing (50 tests)
- [ ] OWASP ZAP scan clean (0 high/critical)
- [ ] Load testing successful (1000 concurrent users)
- [ ] Documentation complete (4 documents)
- [ ] Code review and approval
- [ ] Deployment to testnet

**Ready to begin Phase 1: Rate Limiting**
