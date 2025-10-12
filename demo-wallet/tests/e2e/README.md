# End-to-End Testing Documentation

## Overview

This directory contains E2E (end-to-end) tests for the biometric DID system using Playwright. The tests cover the complete user journey from biometric enrollment through DID generation and verification.

## Test Structure

```
tests/e2e/
├── fixtures/
│   └── biometric-fixtures.ts    # Test fixtures with WebAuthn mocking
├── mocks/
│   └── webauthn-mock.ts         # WebAuthn API mock for testing
├── utils/
│   └── api-client.ts            # API client utilities
├── biometric-enrollment.spec.ts # Enrollment flow tests
└── biometric-verification.spec.ts # Verification flow tests
```

## Prerequisites

### Backend API
The E2E tests require the backend API to be running:

```bash
# From project root
python3 api_server_secure.py
```

The API should be accessible at `http://localhost:8000`.

### Frontend (Optional)
For full integration tests, the demo wallet frontend can be running:

```bash
# From demo-wallet directory
npm run dev
```

## Running Tests

### Run all E2E tests
```bash
cd demo-wallet
npx playwright test
```

### Run specific test file
```bash
npx playwright test biometric-enrollment.spec.ts
```

### Run in headed mode (see browser)
```bash
npx playwright test --headed
```

### Run with UI mode (interactive debugging)
```bash
npx playwright test --ui
```

### Run specific test by name
```bash
npx playwright test -g "should enroll 3 fingers"
```

## Test Scenarios

### Biometric Enrollment (`biometric-enrollment.spec.ts`)

**Happy Path Tests**:
- ✅ Enroll 3 fingers and generate DID
- ✅ Enroll 5 fingers successfully
- ✅ Support inline helper storage mode
- ✅ Support external helper storage mode
- ✅ Generate unique DIDs for different enrollments
- ✅ Include all required helper data fields
- ✅ Generate consistent DID format

**Error Handling Tests**:
- ✅ Reject enrollment with insufficient fingers (< 3)

**Performance Tests**:
- ✅ Complete enrollment within 5 seconds
- ✅ Handle concurrent enrollments

### Biometric Verification (`biometric-verification.spec.ts`)

**Happy Path Tests**:
- ✅ Verify with 2 matching fingers
- ✅ Verify with all 3 enrolled fingers
- ✅ Verify successfully with minimal noise
- ✅ Return unmatched fingers list

**Error Handling Tests**:
- ✅ Fail verification with only 1 finger
- ✅ Fail verification with wrong helper data
- ✅ Handle high biometric noise gracefully
- ✅ Handle missing helper data gracefully
- ✅ Handle corrupted helper data

**Performance Tests**:
- ✅ Complete verification within 3 seconds
- ✅ Handle concurrent verifications

## Mocking Strategy

### WebAuthn Mock (`mocks/webauthn-mock.ts`)

The WebAuthn mock simulates biometric authentication without requiring real hardware:

```typescript
const mock = new WebAuthnMock();
await mock.install(page);

// Enroll biometric
const biometric = await mock.enrollBiometric(page, 'finger_1', 85);

// Clear enrollments
await mock.clearEnrollments(page);
```

**Features**:
- Simulates fingerprint enrollment and verification
- Adds realistic noise to minutiae data
- Supports quality scores
- Compatible with Playwright page context

### API Client (`utils/api-client.ts`)

The API client provides helper functions for backend interactions:

```typescript
const client = new BiometricApiClient({ baseUrl: 'http://localhost:8000' });

// Check health
await client.checkHealth();

// Enroll
const response = await client.generate({
  wallet_address: 'addr_test1...',
  fingers: [finger1, finger2, finger3],
  helper_storage: 'inline',
});

// Verify
const result = await client.verify({
  fingers: [finger1, finger2],
  helpers: response.helpers,
});
```

## Configuration

### Environment Variables

Tests can be configured via environment variables:

```bash
export API_URL=http://localhost:8000
export TEST_TIMEOUT=30000  # 30 seconds
```

### Playwright Configuration

See `playwright.config.ts` for:
- Browser configuration (Chromium, Firefox, WebKit)
- Timeouts and retries
- Test directories
- Reporter configuration

## Performance Benchmarks

### Expected Performance

| Operation | Target | Acceptable |
|-----------|--------|------------|
| Enrollment (3 fingers) | < 2s | < 5s |
| Verification (2 fingers) | < 1s | < 3s |
| Concurrent enrollments (5) | < 10s | < 20s |
| Concurrent verifications (5) | < 5s | < 15s |

### Measuring Performance

Tests automatically measure and report timing:

```typescript
const startTime = Date.now();
const response = await apiClient.generate(request);
const endTime = Date.now();
const duration = endTime - startTime;

console.log(`Enrollment completed in ${duration}ms`);
expect(duration).toBeLessThan(5000);
```

## CI/CD Integration

### GitHub Actions

E2E tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Manual workflow dispatch

See `.github/workflows/e2e-tests.yml` for configuration.

### Artifacts

The CI pipeline uploads:
- **Playwright Report**: HTML test results
- **API Logs**: Backend server logs
- **Screenshots**: On test failures (when implemented)

## Debugging Tests

### View Test Results

```bash
# Open HTML report
npx playwright show-report
```

### Debug Specific Test

```bash
# Run in debug mode
npx playwright test --debug biometric-enrollment.spec.ts
```

### Trace Viewer

```bash
# Enable tracing in playwright.config.ts
npx playwright test --trace on

# View trace
npx playwright show-trace trace.zip
```

### Check API Logs

```bash
# View backend logs
tail -f logs/api_server.log
```

## Writing New Tests

### Test Template

```typescript
import { test, expect, biometricAssertions } from '../fixtures/biometric-fixtures';
import { createMockFingerData } from '../utils/api-client';

test.describe('My Test Suite', () => {
  test.beforeEach(async ({ apiClient }) => {
    // Setup before each test
    await apiClient.checkHealth();
  });

  test('should do something', async ({ apiClient, webauthnMock }) => {
    // Arrange
    const finger = createMockFingerData('finger_1');

    // Act
    const response = await apiClient.generate({
      wallet_address: 'addr_test1...',
      fingers: [finger],
    });

    // Assert
    biometricAssertions.assertValidDid(response.did);
    expect(response).toHaveProperty('wallet_bundle');
  });
});
```

### Best Practices

1. **Use fixtures**: Leverage `webauthnMock` and `apiClient` fixtures
2. **Use custom assertions**: Use `biometricAssertions` for DID validation
3. **Clean up**: Tests should be independent and clean up after themselves
4. **Performance**: Add timing measurements for performance-critical operations
5. **Error cases**: Test both happy path and error scenarios
6. **Realistic data**: Use `addMinutiaeNoise()` to simulate real-world variation

## Troubleshooting

### API Not Starting

```bash
# Check if API is running
curl http://localhost:8000/health

# Check logs
cat logs/api_server.log

# Restart API
pkill -f api_server_secure.py
python3 api_server_secure.py &
```

### Tests Timing Out

- Increase timeout in `playwright.config.ts`
- Check if backend API is responsive
- Verify network connectivity

### Flaky Tests

- Add explicit waits: `await page.waitForTimeout(1000)`
- Use `test.describe.serial` for dependent tests
- Increase retry count in config

### Browser Not Launching

```bash
# Reinstall browsers
npx playwright install --with-deps
```

## Future Enhancements

- [ ] Add visual regression testing
- [ ] Add accessibility (a11y) tests
- [ ] Add load testing scenarios
- [ ] Add screenshot comparison
- [ ] Add video recording on failures
- [ ] Add performance profiling
- [ ] Add cross-browser testing matrix

## References

- [Playwright Documentation](https://playwright.dev)
- [Project Roadmap](../../docs/roadmap.md)
- [Wallet Integration Guide](../../docs/wallet-integration.md)
- [API Documentation](../../docs/api-specification.md)
