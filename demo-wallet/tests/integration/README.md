# Integration Tests

This directory contains integration tests that validate end-to-end functionality of the demo wallet with external services (API servers, blockchain, etc.).

## Test Structure

- **biometricDidService.integration.test.ts** - Tests biometric DID enrollment and verification with Python API servers

## Running Tests

### Quick Test (No Setup Required)

Run tests that don't require external services:

```bash
npm test -- src/core/biometric/__tests__/biometricDidService.integration.test.ts
```

This will run:

- ✅ Error handling tests (5 tests)
- ✅ Storage operations tests
- ⏭️ API-dependent tests (skipped)

**Expected output**: 5 passed, 9 skipped

### Full Integration Test (Requires API Server)

To run all integration tests including API-dependent tests:

1. **Start the Python API server** (in a separate terminal):

   ```bash
   cd /workspaces/decentralized-did
   python api_server_mock.py
   ```

   The server should start on `http://localhost:8000`

2. **Run all tests**:

   ```bash
   RUN_API_TESTS=1 npm test -- src/core/biometric/__tests__/biometricDidService.integration.test.ts
   ```

**Expected output**: 14 passed, 0 skipped

## Test Coverage

### Enrollment Flow (4 tests)

- ✅ Generate deterministic DID with API server
- ✅ Sybil resistance (same biometric → same DID)
- ✅ Uniqueness (different biometrics → different DIDs)
- ✅ Helper data storage and retrieval

### Verification Flow (3 tests)

- ✅ Verification with exact biometric match
- ✅ Verification with noisy recapture (fuzzy matching)
- ✅ Rejection of wrong biometric

### Performance Benchmarks (2 tests)

- ✅ Enrollment completes in <5 seconds
- ✅ Verification completes in <5 seconds

### Error Handling (3 tests)

- ✅ Missing helper data
- ✅ Invalid DID format
- ✅ Empty minutiae data

### Storage Operations (2 tests)

- ✅ Helper data existence check
- ✅ Current DID management

## Troubleshooting

### "Backend API unavailable" errors

**Problem**: Tests that require the API server are failing.

**Solution**:

1. Check if the API server is running:
   ```bash
   curl http://localhost:8000/health
   ```
2. If not running, start it:
   ```bash
   python api_server_mock.py
   ```
3. Run tests with the API flag:
   ```bash
   RUN_API_TESTS=1 npm test -- src/core/biometric/__tests__/biometricDidService.integration.test.ts
   ```

### Coverage threshold warnings

**Problem**: Jest reports coverage below 80%

**Solution**: This is expected for integration tests. Integration tests focus on end-to-end flows rather than line coverage. Unit tests (see `biometricDidService.deterministic.test.ts`) provide detailed coverage.

### Tests timeout after 30 seconds

**Problem**: API calls are taking too long.

**Solution**:

1. Check network connectivity
2. Verify API server is responsive:
   ```bash
   time curl -X POST http://localhost:8000/generate -H "Content-Type: application/json" -d '{"wallet":"test"}'
   ```
3. Check API server logs for errors

## API Server Options

You can test against different API servers:

### Mock API Server (Recommended for Testing)

```bash
python api_server_mock.py
# Runs on http://localhost:8000
# No blockchain, fast responses, predictable data
```

### Basic API Server

```bash
python -m decentralized_did.api_server
# Runs on http://localhost:8000
# Full DID generation, no authentication
```

### Secure API Server

```bash
python -m decentralized_did.api_server_secure
# Runs on http://localhost:8001
# JWT authentication, audit logging
```

## CI/CD Integration

For continuous integration:

```yaml
# .github/workflows/test.yml
- name: Start API server
  run: python api_server_mock.py &

- name: Wait for API server
  run: npx wait-on http://localhost:8000/health

- name: Run integration tests
  run: RUN_API_TESTS=1 npm test -- src/core/biometric/__tests__/biometricDidService.integration.test.ts
```

## Next Steps

- [ ] Add E2E tests for full user flows (Playwright/WebDriverIO)
- [ ] Add integration tests for blockchain transactions
- [ ] Add integration tests for wallet storage backends
- [ ] Performance profiling and optimization
