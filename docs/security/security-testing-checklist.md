# Security Testing Checklist

This comprehensive checklist ensures the Decentralized DID API servers meet security requirements and follow best practices.

## Overview

Use this checklist to validate security controls, identify vulnerabilities, and ensure compliance with security standards. The checklist covers:

- OWASP API Security Top 10 validation
- Authentication and authorization testing
- Input validation and sanitization
- Rate limiting and DDoS protection
- Encryption and data protection
- Audit logging and monitoring
- Security headers and configuration
- Manual penetration testing scenarios

## Quick Reference

| Category | Tests | Priority | Status |
|----------|-------|----------|--------|
| Authentication | 8 | Critical | ⏳ |
| Authorization | 6 | Critical | ⏳ |
| Input Validation | 7 | High | ⏳ |
| Rate Limiting | 5 | High | ⏳ |
| Data Protection | 6 | High | ⏳ |
| Error Handling | 5 | Medium | ⏳ |
| Security Headers | 7 | Medium | ⏳ |
| Audit Logging | 6 | Medium | ⏳ |
| Configuration | 5 | Low | ⏳ |

**Legend**: ✅ Pass | ❌ Fail | ⏳ Not Tested | ⚠️ Warning

## OWASP API Security Top 10 (2023)

### API1:2023 - Broken Object Level Authorization (BOLA)

- [ ] **Test 1.1**: Attempt to access other users' DIDs by changing wallet address
  ```bash
  # Enroll as user A
  curl -X POST http://localhost:8000/api/v1/did/enroll \
    -H "Content-Type: application/json" \
    -d '{"wallet_address":"addr_user_a","biometric_hash":"hash_a"}'

  # Try to access user A's DID as user B
  curl -X GET http://localhost:8000/api/v1/did/addr_user_a \
    -H "X-API-Key: user_b_key"

  # Expected: 403 Forbidden or proper authorization check
  ```

- [ ] **Test 1.2**: Verify object ownership before modification
  ```bash
  # Try to update another user's DID
  curl -X PUT http://localhost:8000/api/v1/did/addr_user_a \
    -H "X-API-Key: user_b_key" \
    -H "Content-Type: application/json" \
    -d '{"revoked":true}'

  # Expected: 403 Forbidden
  ```

- [ ] **Test 1.3**: Test enumeration attacks
  ```bash
  # Try to enumerate DIDs
  for i in {1..100}; do
    curl http://localhost:8000/api/v1/did/addr_test$i
  done

  # Expected: Rate limiting or authentication required
  ```

### API2:2023 - Broken Authentication

- [ ] **Test 2.1**: Attempt requests without authentication
  ```bash
  # Protected endpoint without API key
  curl -X POST http://localhost:8000/api/v1/did/enroll \
    -H "Content-Type: application/json" \
    -d '{"wallet_address":"addr","biometric_hash":"hash"}'

  # Expected: 401 Unauthorized
  ```

- [ ] **Test 2.2**: Test invalid API key
  ```bash
  curl -X POST http://localhost:8000/api/v1/did/enroll \
    -H "X-API-Key: invalid_key_12345" \
    -H "Content-Type: application/json" \
    -d '{"wallet_address":"addr","biometric_hash":"hash"}'

  # Expected: 401 Unauthorized
  ```

- [ ] **Test 2.3**: Test expired JWT tokens (if using JWT)
  ```bash
  # Generate expired token
  EXPIRED_TOKEN="eyJ...expired"

  curl -X POST http://localhost:8000/api/v1/did/enroll \
    -H "Authorization: Bearer $EXPIRED_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"wallet_address":"addr","biometric_hash":"hash"}'

  # Expected: 401 Unauthorized with error code AUTH_TOKEN_EXPIRED
  ```

- [ ] **Test 2.4**: Test weak API keys
  ```bash
  # Try common weak keys
  for key in "password" "123456" "api_key" "test"; do
    curl -H "X-API-Key: $key" http://localhost:8000/api/v1/did/enroll
  done

  # Expected: All should fail
  ```

- [ ] **Test 2.5**: Test authentication bypass
  ```bash
  # Try SQL injection in auth header
  curl -H "X-API-Key: ' OR '1'='1" http://localhost:8000/api/v1/did/enroll

  # Try command injection
  curl -H "X-API-Key: \$(whoami)" http://localhost:8000/api/v1/did/enroll

  # Expected: 401 Unauthorized, no code execution
  ```

### API3:2023 - Broken Object Property Level Authorization

- [ ] **Test 3.1**: Attempt to modify read-only fields
  ```bash
  # Try to change creation timestamp
  curl -X PUT http://localhost:8000/api/v1/did/update \
    -H "Content-Type: application/json" \
    -d '{"wallet_address":"addr","created_at":"2020-01-01"}'

  # Expected: 400 Bad Request or field ignored
  ```

- [ ] **Test 3.2**: Test excessive data exposure
  ```bash
  # Check response doesn't include sensitive fields
  curl http://localhost:8000/api/v1/did/addr_test

  # Expected: No internal IDs, no system paths, no sensitive metadata
  ```

### API4:2023 - Unrestricted Resource Consumption

- [ ] **Test 4.1**: Test rate limiting on enrollment
  ```bash
  # Rapid enrollment attempts (should hit 5/minute limit)
  for i in {1..10}; do
    curl -X POST http://localhost:8000/api/v1/did/enroll \
      -H "Content-Type: application/json" \
      -d "{\"wallet_address\":\"addr$i\",\"biometric_hash\":\"hash$i\"}"
    sleep 0.1
  done

  # Expected: 429 Too Many Requests after 5 requests
  ```

- [ ] **Test 4.2**: Test rate limiting on verification
  ```bash
  # Rapid verification attempts (should hit 20/minute limit)
  for i in {1..25}; do
    curl -X POST http://localhost:8000/api/v1/did/verify \
      -H "Content-Type: application/json" \
      -d '{"wallet_address":"addr","biometric_hash":"hash","timestamp":'$(date +%s)'}'
    sleep 0.1
  done

  # Expected: 429 Too Many Requests after 20 requests
  ```

- [ ] **Test 4.3**: Test payload size limits
  ```bash
  # Send large payload (> 10MB)
  dd if=/dev/zero bs=1M count=15 | curl -X POST http://localhost:8000/api/v1/did/enroll \
    -H "Content-Type: application/json" \
    --data-binary @-

  # Expected: 413 Payload Too Large
  ```

- [ ] **Test 4.4**: Test pagination limits
  ```bash
  # Request excessive number of results
  curl "http://localhost:8000/api/v1/did/list?limit=10000"

  # Expected: Limit capped at reasonable maximum (e.g., 100)
  ```

### API5:2023 - Broken Function Level Authorization

- [ ] **Test 5.1**: Test admin endpoints with regular user
  ```bash
  # Try to access admin endpoint with regular user token
  curl -X POST http://localhost:8000/api/v1/admin/revoke-all \
    -H "X-API-Key: regular_user_key"

  # Expected: 403 Forbidden
  ```

- [ ] **Test 5.2**: Test privilege escalation
  ```bash
  # Try to modify user roles
  curl -X PUT http://localhost:8000/api/v1/user/update \
    -H "Content-Type: application/json" \
    -d '{"role":"admin"}'

  # Expected: 403 Forbidden or role field ignored
  ```

### API6:2023 - Unrestricted Access to Sensitive Business Flows

- [ ] **Test 6.1**: Test enrollment flow manipulation
  ```bash
  # Try to skip verification step
  curl -X POST http://localhost:8000/api/v1/did/enroll \
    -H "Content-Type: application/json" \
    -d '{"wallet_address":"addr","biometric_hash":"hash","verified":true}'

  # Expected: Verification status ignored or 400 Bad Request
  ```

- [ ] **Test 6.2**: Test duplicate enrollment prevention
  ```bash
  # Enroll once
  curl -X POST http://localhost:8000/api/v1/did/enroll \
    -H "Content-Type: application/json" \
    -d '{"wallet_address":"addr_dup","biometric_hash":"hash_dup"}'

  # Try to enroll again with same data
  curl -X POST http://localhost:8000/api/v1/did/enroll \
    -H "Content-Type: application/json" \
    -d '{"wallet_address":"addr_dup","biometric_hash":"hash_dup"}'

  # Expected: 409 Conflict with error code DID_DUPLICATE
  ```

### API7:2023 - Server Side Request Forgery (SSRF)

- [ ] **Test 7.1**: Test SSRF in URL parameters
  ```bash
  # Try to access internal services
  curl -X POST http://localhost:8000/api/v1/did/import \
    -H "Content-Type: application/json" \
    -d '{"url":"http://localhost:22"}'

  # Expected: URL validation or 400 Bad Request
  ```

- [ ] **Test 7.2**: Test SSRF in metadata fields
  ```bash
  # Try SSRF via metadata
  curl -X POST http://localhost:8000/api/v1/did/enroll \
    -H "Content-Type: application/json" \
    -d '{"wallet_address":"addr","biometric_hash":"hash","metadata":{"avatar_url":"http://169.254.169.254/latest/meta-data/"}}'

  # Expected: URL not fetched or validated
  ```

### API8:2023 - Security Misconfiguration

- [ ] **Test 8.1**: Check security headers
  ```bash
  curl -I http://localhost:8000/health

  # Expected headers:
  # Strict-Transport-Security: max-age=31536000; includeSubDomains
  # X-Content-Type-Options: nosniff
  # X-Frame-Options: DENY
  # X-XSS-Protection: 1; mode=block
  # Content-Security-Policy: default-src 'self'
  ```

- [ ] **Test 8.2**: Check for debug information
  ```bash
  curl http://localhost:8000/api/v1/does-not-exist

  # Expected: Generic error, no stack traces in production
  ```

- [ ] **Test 8.3**: Check CORS configuration
  ```bash
  curl -H "Origin: https://evil.com" http://localhost:8000/api/v1/did/enroll

  # Expected: No Access-Control-Allow-Origin: * in production
  ```

- [ ] **Test 8.4**: Check HTTP methods
  ```bash
  # Test if only allowed methods work
  curl -X TRACE http://localhost:8000/api/v1/did/enroll
  curl -X OPTIONS http://localhost:8000/api/v1/did/enroll

  # Expected: 405 Method Not Allowed for TRACE
  ```

### API9:2023 - Improper Inventory Management

- [ ] **Test 9.1**: Check API versioning
  ```bash
  # Old version should be deprecated
  curl http://localhost:8000/api/v0/did/enroll

  # Expected: 404 Not Found or 410 Gone
  ```

- [ ] **Test 9.2**: Check API documentation exposure
  ```bash
  curl http://localhost:8000/docs
  curl http://localhost:8000/openapi.json

  # Expected: Disabled in production or requires authentication
  ```

### API10:2023 - Unsafe Consumption of APIs

- [ ] **Test 10.1**: Check external API timeout handling
  ```bash
  # If consuming external APIs, verify timeout handling
  # (Not applicable if not consuming external APIs)
  ```

- [ ] **Test 10.2**: Check external API error handling
  ```bash
  # Verify graceful degradation when external services fail
  # (Not applicable if not consuming external APIs)
  ```

## Authentication & Authorization Testing

### Authentication

- [ ] **Auth 1**: API key validation works correctly
- [ ] **Auth 2**: JWT token validation works correctly (if applicable)
- [ ] **Auth 3**: Expired credentials are rejected
- [ ] **Auth 4**: Invalid credentials return 401 Unauthorized
- [ ] **Auth 5**: Authentication is required for protected endpoints
- [ ] **Auth 6**: Rate limiting applies to authentication attempts
- [ ] **Auth 7**: Credential storage is secure (hashed, not plain text)
- [ ] **Auth 8**: Session management is secure (if applicable)

### Authorization

- [ ] **Authz 1**: Users can only access their own resources
- [ ] **Authz 2**: Admin functions require admin role
- [ ] **Authz 3**: Role-based access control is enforced
- [ ] **Authz 4**: Privilege escalation is prevented
- [ ] **Authz 5**: Direct object reference is validated
- [ ] **Authz 6**: Authorization checks cannot be bypassed

## Input Validation Testing

- [ ] **Input 1**: SQL injection is prevented (N/A - no SQL database)
- [ ] **Input 2**: NoSQL injection is prevented (if using NoSQL)
- [ ] **Input 3**: Command injection is prevented
- [ ] **Input 4**: XSS is prevented (N/A - API returns JSON)
- [ ] **Input 5**: Path traversal is prevented
- [ ] **Input 6**: Invalid data types are rejected (400 Bad Request)
- [ ] **Input 7**: Required fields are enforced

**Test Script**:
```bash
#!/bin/bash
# input-validation-tests.sh

echo "Testing input validation..."

# Test 1: Invalid wallet address format
curl -X POST http://localhost:8000/api/v1/did/enroll \
  -H "Content-Type: application/json" \
  -d '{"wallet_address":"invalid","biometric_hash":"hash"}' \
  | jq '.code' | grep -q "VAL_INVALID_INPUT" && echo "✅ Test 1 Pass" || echo "❌ Test 1 Fail"

# Test 2: Missing required field
curl -X POST http://localhost:8000/api/v1/did/enroll \
  -H "Content-Type: application/json" \
  -d '{"wallet_address":"addr"}' \
  | jq '.code' | grep -q "VAL_MISSING_FIELD" && echo "✅ Test 2 Pass" || echo "❌ Test 2 Fail"

# Test 3: Invalid data type
curl -X POST http://localhost:8000/api/v1/did/enroll \
  -H "Content-Type: application/json" \
  -d '{"wallet_address":12345,"biometric_hash":"hash"}' \
  | jq '.code' | grep -q "VAL_INVALID_TYPE" && echo "✅ Test 3 Pass" || echo "❌ Test 3 Fail"

# Test 4: Command injection attempt
curl -X POST http://localhost:8000/api/v1/did/enroll \
  -H "Content-Type: application/json" \
  -d '{"wallet_address":"addr; rm -rf /","biometric_hash":"hash"}' \
  | jq '.code' | grep -q "VAL_INVALID_INPUT" && echo "✅ Test 4 Pass" || echo "❌ Test 4 Fail"

# Test 5: Path traversal attempt
curl -X GET "http://localhost:8000/api/v1/did/../../../etc/passwd" \
  | grep -q "404\|400" && echo "✅ Test 5 Pass" || echo "❌ Test 5 Fail"

echo "Input validation tests complete"
```

## Rate Limiting Testing

- [ ] **Rate 1**: Enrollment rate limit (5/minute) is enforced
- [ ] **Rate 2**: Verification rate limit (20/minute) is enforced
- [ ] **Rate 3**: Rate limit headers are present (X-RateLimit-*)
- [ ] **Rate 4**: 429 status code returned when rate limited
- [ ] **Rate 5**: Rate limits reset after time window

**Test Script**:
```bash
#!/bin/bash
# rate-limiting-tests.sh

echo "Testing rate limiting..."

# Test enrollment rate limit (5/minute)
echo "Testing enrollment rate limit..."
SUCCESS=0
for i in {1..10}; do
  RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/did/enroll \
    -H "Content-Type: application/json" \
    -d "{\"wallet_address\":\"addr$i\",\"biometric_hash\":\"hash$i\"}")

  STATUS=$(echo $RESPONSE | jq -r '.status_code // 201')

  if [ "$STATUS" = "429" ]; then
    echo "✅ Rate limit enforced after $i requests"
    SUCCESS=1
    break
  fi
done

if [ "$SUCCESS" = "0" ]; then
  echo "❌ Rate limit not enforced"
fi

# Check rate limit headers
HEADERS=$(curl -s -I http://localhost:8000/api/v1/did/enroll)
if echo "$HEADERS" | grep -q "X-RateLimit-Limit"; then
  echo "✅ Rate limit headers present"
else
  echo "❌ Rate limit headers missing"
fi

echo "Rate limiting tests complete"
```

## Data Protection Testing

- [ ] **Data 1**: PII is masked in logs
- [ ] **Data 2**: Biometric data is hashed (not stored in plain text)
- [ ] **Data 3**: API keys are not logged
- [ ] **Data 4**: Sensitive data is encrypted at rest (if applicable)
- [ ] **Data 5**: Sensitive data is encrypted in transit (HTTPS)
- [ ] **Data 6**: Data retention policies are enforced

**Test Script**:
```bash
#!/bin/bash
# data-protection-tests.sh

echo "Testing data protection..."

# Test 1: Check logs don't contain PII
LOG_FILE="/var/log/did-api/audit.log"
if [ -f "$LOG_FILE" ]; then
  # Check for email patterns
  if grep -E "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}" "$LOG_FILE" | grep -v "@example.com"; then
    echo "❌ Found unmasked emails in logs"
  else
    echo "✅ No unmasked emails in logs"
  fi

  # Check for API keys
  if grep -E "api[_-]?key.*[a-zA-Z0-9]{32,}" "$LOG_FILE"; then
    echo "❌ Found API keys in logs"
  else
    echo "✅ No API keys in logs"
  fi
else
  echo "⚠️ Log file not found"
fi

# Test 2: Verify HTTPS is enforced
if curl -s http://localhost:8000/health | grep -q "301\|302"; then
  echo "✅ HTTP redirects to HTTPS"
else
  echo "⚠️ HTTP not redirecting to HTTPS (OK in dev)"
fi

echo "Data protection tests complete"
```

## Error Handling Testing

- [ ] **Error 1**: Production mode returns generic error messages
- [ ] **Error 2**: Stack traces are disabled in production
- [ ] **Error 3**: Error codes are consistent and documented
- [ ] **Error 4**: Errors include correlation IDs for debugging
- [ ] **Error 5**: Sensitive information is not exposed in errors

**Test Script**:
```bash
#!/bin/bash
# error-handling-tests.sh

echo "Testing error handling..."

# Test 1: Generic error messages in production
export ENVIRONMENT=production
ERROR_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/invalid-endpoint)

if echo "$ERROR_RESPONSE" | jq -e '.stack_trace' > /dev/null; then
  echo "❌ Stack trace exposed in production"
else
  echo "✅ No stack trace in production errors"
fi

# Test 2: Error code present
if echo "$ERROR_RESPONSE" | jq -e '.code' > /dev/null; then
  echo "✅ Error code present"
else
  echo "❌ Error code missing"
fi

# Test 3: Request ID present
if echo "$ERROR_RESPONSE" | jq -e '.request_id' > /dev/null; then
  echo "✅ Request ID present"
else
  echo "❌ Request ID missing"
fi

echo "Error handling tests complete"
```

## Security Headers Testing

- [ ] **Header 1**: Strict-Transport-Security is set
- [ ] **Header 2**: X-Content-Type-Options: nosniff is set
- [ ] **Header 3**: X-Frame-Options: DENY is set
- [ ] **Header 4**: X-XSS-Protection is set
- [ ] **Header 5**: Content-Security-Policy is set
- [ ] **Header 6**: Permissions-Policy is set
- [ ] **Header 7**: Referrer-Policy is set

**Test Script**:
```bash
#!/bin/bash
# security-headers-tests.sh

echo "Testing security headers..."

HEADERS=$(curl -s -I http://localhost:8000/health)

check_header() {
  HEADER=$1
  if echo "$HEADERS" | grep -qi "$HEADER"; then
    echo "✅ $HEADER present"
  else
    echo "❌ $HEADER missing"
  fi
}

check_header "Strict-Transport-Security"
check_header "X-Content-Type-Options"
check_header "X-Frame-Options"
check_header "X-XSS-Protection"
check_header "Content-Security-Policy"
check_header "Permissions-Policy"
check_header "Referrer-Policy"

echo "Security headers tests complete"
```

## Audit Logging Testing

- [ ] **Audit 1**: All API requests are logged
- [ ] **Audit 2**: Logs include timestamp, method, path, status
- [ ] **Audit 3**: Logs include correlation IDs
- [ ] **Audit 4**: Logs don't contain sensitive data (PII masked)
- [ ] **Audit 5**: Logs are stored securely with proper permissions
- [ ] **Audit 6**: Log rotation is configured

**Test Script**:
```bash
#!/bin/bash
# audit-logging-tests.sh

echo "Testing audit logging..."

# Make test request
curl -s http://localhost:8000/health > /dev/null

# Check log file
LOG_FILE="/var/log/did-api/audit.log"
if [ -f "$LOG_FILE" ]; then
  LAST_LOG=$(tail -1 "$LOG_FILE")

  # Check required fields
  echo "$LAST_LOG" | jq -e '.timestamp' > /dev/null && echo "✅ Timestamp present" || echo "❌ Timestamp missing"
  echo "$LAST_LOG" | jq -e '.method' > /dev/null && echo "✅ Method present" || echo "❌ Method missing"
  echo "$LAST_LOG" | jq -e '.path' > /dev/null && echo "✅ Path present" || echo "❌ Path missing"
  echo "$LAST_LOG" | jq -e '.status_code' > /dev/null && echo "✅ Status code present" || echo "❌ Status code missing"
  echo "$LAST_LOG" | jq -e '.request_id' > /dev/null && echo "✅ Request ID present" || echo "❌ Request ID missing"

  # Check permissions
  PERMS=$(stat -c %a "$LOG_FILE")
  if [ "$PERMS" = "640" ] || [ "$PERMS" = "600" ]; then
    echo "✅ Log file permissions secure"
  else
    echo "⚠️ Log file permissions: $PERMS (should be 640 or 600)"
  fi
else
  echo "❌ Log file not found"
fi

echo "Audit logging tests complete"
```

## Manual Penetration Testing Scenarios

### Scenario 1: Brute Force Attack

```bash
# Try to brute force API keys
for i in {1..100}; do
  curl -H "X-API-Key: test_key_$i" http://localhost:8000/api/v1/did/enroll
done

# Expected: Rate limited after threshold
```

### Scenario 2: Replay Attack

```bash
# Capture a valid request
REQUEST='{"wallet_address":"addr","biometric_hash":"hash","timestamp":1697500000}'

# Replay the same request multiple times
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/v1/did/verify \
    -H "Content-Type: application/json" \
    -d "$REQUEST"
done

# Expected: Timestamp validation or nonce checking prevents replay
```

### Scenario 3: Race Condition

```bash
# Try to enroll same DID from multiple threads simultaneously
for i in {1..10}; do
  (curl -X POST http://localhost:8000/api/v1/did/enroll \
    -H "Content-Type: application/json" \
    -d '{"wallet_address":"addr_race","biometric_hash":"hash_race"}' &)
done
wait

# Expected: Only one enrollment succeeds, others get 409 Conflict
```

## Automated Testing Integration

Create `.github/workflows/security-tests.yml`:

```yaml
name: Security Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * 1'  # Weekly

jobs:
  security-tests:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -e ".[api]"

    - name: Start API server
      run: |
        uvicorn src.decentralized_did.api.server:app --host 0.0.0.0 --port 8000 &
        sleep 5

    - name: Run security checklist tests
      run: |
        bash scripts/security/input-validation-tests.sh
        bash scripts/security/rate-limiting-tests.sh
        bash scripts/security/security-headers-tests.sh
        bash scripts/security/error-handling-tests.sh

    - name: Run OWASP ZAP scan
      uses: zaproxy/action-baseline@v0.11.0
      with:
        target: 'http://localhost:8000'
```

## Success Criteria

✅ **Pass Criteria**:
- [ ] All OWASP API Top 10 tests pass
- [ ] Authentication and authorization tests pass
- [ ] Input validation tests pass
- [ ] Rate limiting tests pass
- [ ] Security headers tests pass
- [ ] Audit logging tests pass
- [ ] No high or critical vulnerabilities found
- [ ] Performance targets met (<150ms P95 enrollment, <75ms P95 verification)

❌ **Fail Criteria**:
- Any critical security vulnerability found
- Authentication can be bypassed
- Rate limiting not enforced
- PII exposed in logs
- Stack traces in production errors

## Post-Testing Actions

After completing security testing:

1. **Document Findings**: Create security test report
2. **Prioritize Issues**: Rank by severity (Critical > High > Medium > Low)
3. **Remediate**: Fix high and critical issues immediately
4. **Re-test**: Verify fixes with security tests
5. **Update Documentation**: Document security controls
6. **Schedule Regular Tests**: Set up automated security testing

## References

- [OWASP API Security Top 10 2023](https://owasp.org/www-project-api-security/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CIS Controls](https://www.cisecurity.org/controls)

---

**Last Updated**: October 15, 2025
**Review Schedule**: Quarterly
**Next Review**: January 15, 2026
