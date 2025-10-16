# API Server Test Configuration Guide

**Task 4 Phase 1.2-1.5**: Secure API JWT + Mock Server + Test Environment
**Date**: October 16, 2025
**Status**: Secure/mock servers documented; standardized `.env.test` + fixtures published

---

## Overview

This guide provides test credentials, environment configuration, and authentication examples for the three API servers (basic, secure, mock) in the biometric DID system.

---

## 1. API Server Overview

### Basic API Server (`api_server.py`)
- **Port**: 8000
- **Authentication**: None (open access)
- **Rate Limiting**: No
- **Use Case**: Development and quick testing
- **Status**: ✅ OPERATIONAL

### Secure API Server (`api_server_secure.py`)
- **Port**: 8001 (recommended; pass `--port 8001` to uvicorn to avoid basic-server conflict)
- **Authentication**: JWT tokens via API key
- **Rate Limiting**: Configurable (SlowAPI; disabled when `RATE_LIMIT_ENABLED=false`)
- **Security Headers**: Yes
- **Audit Logging**: Yes
- **Use Case**: Production-ready, integration testing
- **Status**: ✅ OPERATIONAL (deterministic helper hashing, mock parity)

### Mock API Server (`api_server_mock.py`)
- **Port**: 8002 (default, override with `MOCK_API_PORT`)
- **Authentication**: None
- **Deterministic**: Yes (helper salts/auth hashes derived from finger_id)
- **Hash Verification**: `expected_id_hash` must match helper-derived hash
- **Use Case**: Fast unit testing, CI/CD
- **Status**: ✅ TESTED (Phase 1.3)

---

## 2. Test Credentials

### For Secure API Server

#### Test API Keys

The secure server uses API keys for authentication. Here are test keys for development:

```bash
# Test API Key 1 (admin user)
TEST_API_KEY_1="test_api_key_admin_32_chars_long_abcdef123456"

# Test API Key 2 (standard user)
TEST_API_KEY_2="test_api_key_user_32_chars_long_xyz789abc"

# Test API Key 3 (integration tests)
TEST_API_KEY_3="test_api_key_integration_32_chars_long_xyz"
```

#### Server Secret Keys

These should be set as environment variables:

```bash
# API Secret Key (for validating incoming API keys)
export API_SECRET_KEY="test_api_key_admin_32_chars_long_abcdef123456"

# JWT Secret Key (for signing tokens)
export JWT_SECRET_KEY="jwt_secret_for_signing_tokens_32_chars_long"
```

---

## 3. Environment Configuration

### 3.1 Quickstart

1. Review `.env.test` (tracked in git) for canonical integration-test defaults.
2. Export the variables before running servers or scripts:
  ```bash
  set -a
  source .env.test
  set +a
  ```
3. Launch the desired API server(s) (`python api_server.py`, `uvicorn api_server_secure:app --port 8001`, etc.).

`ENVIRONMENT` controls security enforcement: `integration` (default for tests) logs warnings for relaxed settings, while `staging`/`production` reject insecure values at startup.

`test_api_auth.sh` automatically loads `${ENV_FILE:-.env.test}` at runtime, so no extra sourcing is required for the harness.

### 3.2 Integration Test Environment (`.env.test`)

```bash
# Environment classification
ENVIRONMENT=integration

# API Server URLs
BASIC_API_URL=http://localhost:8000
SECURE_API_URL=http://localhost:8001
MOCK_API_URL=http://localhost:8002

# Authentication / JWT
API_SECRET_KEY=test_api_key_admin_32_chars_long_abcdef123456
JWT_SECRET_KEY=jwt_secret_for_signing_tokens_32_chars_long
JWT_EXPIRATION_HOURS=1

# Feature Flags (keep tests fast)
RATE_LIMIT_ENABLED=false
AUDIT_LOG_ENABLED=false
HTTPS_ONLY=false

# CORS Origins for local tooling
CORS_ORIGINS=http://localhost:3000,http://localhost:3003,http://localhost:5173

# Mock server tuning
MOCK_API_HOST=0.0.0.0
MOCK_API_PORT=8002
MOCK_API_RELOAD=false

# Demo wallet integration tests
BIOMETRIC_API_URL=http://localhost:8002
RUN_API_TESTS=false

# Blockfrost (set when validating duplicate detection logic)
# Leave blank during deterministic local runs to skip remote lookups.
BLOCKFROST_API_KEY=
CARDANO_NETWORK=testnet

# Test harness defaults
API_KEY=test_api_key_admin_32_chars_long_abcdef123456
```

> **Tip**: Override any value ad-hoc via `ENV_FILE=path/to/custom.env ./test_api_auth.sh secure`. Leaving `BLOCKFROST_API_KEY` empty disables duplicate detection, keeping the mock/secure servers fully offline for deterministic tests. Flip `RUN_API_TESTS=true` only when the mock/secure servers are running.

### 3.3 Development/Production `.env`

For longer-lived environments, start from `.env.example` and tailor the values (e.g., enable rate limiting, audit logging, and HTTPS). The secure server reads identical variable names, so promoting a configuration from `.env.test` → `.env` is a file copy followed by key rotation.

---

## 4. Authentication Flow

> Need full endpoint schemas? See `docs/API-ENDPOINTS.md`.

### Step 1: Get JWT Token

**Request**:
```bash
curl -X POST http://localhost:8001/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "test_api_key_admin_32_chars_long_abcdef123456"
  }'
```

**Response**:
```json
{
  "access_token": "eyJ1c2VyX2lkIjogIjEyMzQ1Njc4OTBhYmNkZWYiLCAiZXhwIjogMTY5NzQwMzYwMC4wLCAiaWF0IjogMTY5NzMxNzIwMC4wfQ==.a1b2c3d4e5f6...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### Step 2: Use Token for API Requests

**Request (Generate DID)**:
```bash
TOKEN="eyJ1c2VyX2lkIjogIjEyMzQ1Njc4OTBhYmNkZWYi..."  # From Step 1

curl -X POST http://localhost:8001/api/biometric/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "wallet_address": "addr_test1_demo_wallet",
    "storage": "inline",
    "fingers": [
      {
        "finger_id": "left_thumb",
        "minutiae": [[100.5, 200.3, 45.0], [150.2, 180.9, 90.5]]
      },
      {
        "finger_id": "left_index",
        "minutiae": [[110.2, 210.5, 50.0], [160.5, 190.2, 95.5]]
      }
    ]
  }'
```

**Response**:
```json
{
  "did": "did:cardano:mainnet:zQmXyZ...",
  "id_hash": "zQmXyZ...",
  "wallet_address": "addr_test1_demo_wallet",
  "helpers": { ... },
  "metadata_cip30_inline": { ... }
}
```

### Step 3: Verify DID with Stored Helper Data

Use the helper entries and `id_hash` returned in Step 2 to check whether a biometric probe matches the enrolled identity.

```bash
curl -X POST http://localhost:8001/api/biometric/verify \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "fingers": [
      {
        "finger_id": "left_thumb",
        "minutiae": [[100.5, 200.3, 45.0], [150.2, 180.9, 90.5]]
      },
      {
        "finger_id": "left_index",
        "minutiae": [[110.2, 210.5, 50.0], [160.5, 190.2, 95.5]]
      }
    ],
    "helpers": { ... },
    "expected_id_hash": "zQmXyZ..."
  }'
```

The `expected_id_hash` must match the value previously issued by the `/api/biometric/generate` endpoint; otherwise the server intentionally returns `success: false`.

---

## 5. Mock Server Fixtures

Deterministic payloads for reproducible CI runs live under `tests/fixtures/api/`:

- `mock_generate_request.json`
- `mock_verify_request.json`
- `README.md` (usage notes and Schematron checks)

These fixtures encode helper data generated by the same Blake2b pipeline used in `api_server_mock.py`, so enrollment and verification requests round-trip without manual edits.

### 5.1 Quickstart

Use the mock server for deterministic, dependency-free tests.

```bash
# Start mock server on port 8002
MOCK_API_PORT=8002 python api_server_mock.py

# Alternatively, with uvicorn (no auto-reload)
uvicorn api_server_mock:app --host 0.0.0.0 --port 8002

# Run the mock test suite
MOCK_API_URL=http://localhost:8002 ./test_api_auth.sh mock
```

- `generate` responses are deterministic for a given wallet + minutiae set.
- Helper data contains deterministic `salt_b64` / `auth_b64` values.
- `verify` recomputes the helper hash and requires `expected_id_hash` to match.
- CIP-30 metadata (`metadata_cip30_inline`) mirrors the deterministic `id_hash`.

---

## 6. Production Hardening & Compliance

Government-scale deployments must satisfy stringent regulatory, privacy, and operational controls. The secure API server ships with the hooks required to meet frameworks such as NIST SP 800-63, ISO/IEC 24745, GDPR, BIPA, and eIDAS—enable them via environment configuration and infrastructure policy.

### 6.1 Security Baseline

- **Environment Guardrails**: Set `ENVIRONMENT=production` or `staging` to enforce mandatory settings (TLS, rate limiting, audit logging, non-default secrets, Blockfrost keys). In these modes the server refuses to start if requirements are not met.
- **Secrets**: Rotate `API_SECRET_KEY` and `JWT_SECRET_KEY` to 256-bit values generated from a FIPS 140-3 validated source (HSM or OS RNG). Store in a secrets manager (HashiCorp Vault, AWS Secrets Manager, etc.) and inject at process start.
- **Transport**: Set `HTTPS_ONLY=true` and terminate TLS 1.3 (FIPS ciphersuites) at an ingress proxy. Enforce HSTS, CSP, and OCSP stapling; inspect `Strict-Transport-Security` header emitted by FastAPI middleware.
- **Authentication**: Persist API keys in an auditable registry with rotation periods ≤90 days. Require signed on-chain attestations or hardware secure elements for issuer enrollment APIs.
- **Rate Limiting**: Keep `RATE_LIMIT_ENABLED=true` in production. Calibrate SlowAPI quotas (`3/min` generate, `5/min` verify by default) per relying-party SLA. Back the limiter with Redis for horizontal scale.
- **Audit Logging**: Keep `AUDIT_LOG_ENABLED=true`. Ship `audit.log` to a WORM-compliant log store (e.g., s3 object lock, immutable syslog). Correlate with SIEM baselines (Splunk, ELK) and retain ≥7 years for national ID programs.
- **Data Minimization**: Inline helper storage is deterministic and can be pruned after on-chain registration. For external helper data, store encrypted at rest (AES-256-GCM) with envelope keys in an HSM per ISO/IEC 24745 guidance.

### 6.2 Regulatory Alignment Checklist

- **ISO/IEC 24745**: Document helper data lifecycle; verify `compute_helper_hash` enforces unlinkability; configure retention schedule for `metadata_cip30_inline` exports.
- **NIST SP 800-63-B**: Classify enrollment as AAL3. Require multifactor attestation during `/api/biometric/generate` by layering wallet signature validation within the calling client.
- **GDPR/BIPA**: Record explicit consent including revocation timestamps via metadata `revoked` + `revokedAt`. Provide data-subject export by replaying deterministic enrollment with stored minutiae commitments.
- **eIDAS 2.0**: Map DID issuance events to Qualified Electronic Attestation Services (QEAS) logs. Ensure DID metadata contains controller wallet addresses for cross-border verification.
- **Auditability**: Maintain tamper-evident ledger of `/auth/token` requests. Consider pairing with a consortium blockchain notarization for legal admissibility.

### 6.3 Operational Safeguards

- **Network Segmentation**: Deploy API servers inside a restricted enclave with zero-trust ingress policies. Permit outbound egress only to Blockfrost endpoints or national ledger infrastructure.
- **Key Custody**: Use FIPS 140-3 Level 3 HSMs or secure enclaves for JWT signing. Update `JWT_SIGNING_BACKEND` (planned Phase 5) to route through PKCS#11 or KMIP.
- **Disaster Recovery**: Replicate `.env` secrets with Shamir Secret Sharing among custodians. Test restore drills quarterly; ensure helper data backups respect erasure policies.
- **Monitoring**: Instrument Prometheus/Grafana dashboards for latency targets (<75 ms verification P95). Alert on anomaly detection (duplicate DID spikes, rate-limit breaches).
- **Change Management**: Enforce Infrastructure-as-Code (Terraform/Kubernetes) with policy-as-code (OPA/Rego) to guarantee configuration parity across regions.

---

## 7. Incident Response & Continuity

- **Breach Handling**: Trigger DID revocation (`revoked=true`) and broadcast via governing ledger if helper data leakage is suspected. Rotate salts via new deterministic seeds (`_deterministic_bytes`) without re-capturing raw biometrics when possible.
- **Forensic Logging**: Preserve `audit.log` chain-of-custody with signed digests (BLAKE2b + timestamp). Correlate with reverse-proxy access logs for attribution.
- **Business Continuity**: Maintain cold-standby regions. Validate failover by running `test_api_auth.sh secure` against disaster-recovery endpoints monthly.
- **Legal Coordination**: Map incident severities to statutory reporting windows (GDPR 72h, BIPA immediate). Provide deterministic DID reconstruction evidence to regulators and courts as required.

---

## 8. Code Examples

### Python Example

```python
import requests
import json

# Configuration
API_URL = "http://localhost:8001"
API_KEY = "test_api_key_admin_32_chars_long_abcdef123456"

# Step 1: Authenticate and get token
auth_response = requests.post(
    f"{API_URL}/auth/token",
    json={"api_key": API_KEY}
)
auth_response.raise_for_status()
token = auth_response.json()["access_token"]

print(f"✅ Got token: {token[:50]}...")

# Step 2: Generate biometric DID
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

generate_request = {
    "wallet_address": "addr_test1_demo",
    "storage": "inline",
    "fingers": [
        {
            "finger_id": "left_thumb",
            "minutiae": [[100.5, 200.3, 45.0], [150.2, 180.9, 90.5]]
        },
        {
            "finger_id": "left_index",
            "minutiae": [[110.2, 210.5, 50.0], [160.5, 190.2, 95.5]]
        }
    ]
}

generate_response = requests.post(
    f"{API_URL}/api/biometric/generate",
    headers=headers,
    json=generate_request
)
generate_response.raise_for_status()
result = generate_response.json()

print(f"✅ Generated DID: {result['did']}")
print(f"   ID Hash: {result['id_hash']}")
print(f"   Wallet: {result['wallet_address']}")
```

### JavaScript/TypeScript Example (for demo-wallet)

```typescript
// src/core/biometric/apiClient.ts

interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

interface GenerateRequest {
  wallet_address: string;
  storage: string;
  fingers: Array<{
    finger_id: string;
    minutiae: number[][];
  }>;
}

class BiometricAPIClient {
  private baseURL: string;
  private apiKey: string;
  private token: string | null = null;
  private tokenExpiry: number | null = null;

  constructor(baseURL: string, apiKey: string) {
    this.baseURL = baseURL;
    this.apiKey = apiKey;
  }

  async authenticate(): Promise<string> {
    const response = await fetch(`${this.baseURL}/auth/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: this.apiKey })
    });

    if (!response.ok) {
      throw new Error(`Authentication failed: ${response.statusText}`);
    }

    const data: AuthResponse = await response.json();
    this.token = data.access_token;
    this.tokenExpiry = Date.now() + (data.expires_in * 1000);

    return this.token;
  }

  async getToken(): Promise<string> {
    // Return cached token if still valid
    if (this.token && this.tokenExpiry && Date.now() < this.tokenExpiry) {
      return this.token;
    }

    // Otherwise, re-authenticate
    return await this.authenticate();
  }

  async generateDID(request: GenerateRequest): Promise<any> {
    const token = await this.getToken();

    const response = await fetch(`${this.baseURL}/api/biometric/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      throw new Error(`DID generation failed: ${response.statusText}`);
    }

    return await response.json();
  }
}

// Usage
const apiClient = new BiometricAPIClient(
  'http://localhost:8001',
  'test_api_key_integration_32_chars_long_xyz'
);

const result = await apiClient.generateDID({
  wallet_address: 'addr_test1_demo',
  storage: 'inline',
  fingers: [
    {
      finger_id: 'left_thumb',
      minutiae: [[100.5, 200.3, 45.0], [150.2, 180.9, 90.5]]
    },
    {
      finger_id: 'left_index',
      minutiae: [[110.2, 210.5, 50.0], [160.5, 190.2, 95.5]]
    }
  ]
});

console.log('Generated DID:', result.did);
```

### cURL Examples

```bash
#!/bin/bash
# test_api_auth.sh - Test secure API server authentication
# Optional overrides:
#   export BASIC_API_URL="http://localhost:8000"
#   export SECURE_API_URL="http://localhost:8001"
#   export API_KEY="test_api_key_admin_32_chars_long_abcdef123456"

API_URL="http://localhost:8001"
API_KEY="test_api_key_admin_32_chars_long_abcdef123456"

echo "=== Testing Secure API Server Authentication ==="
echo

# Step 1: Get token
echo "1. Getting JWT token..."
TOKEN_RESPONSE=$(curl -s -X POST "$API_URL/auth/token" \
  -H "Content-Type: application/json" \
  -d "{\"api_key\": \"$API_KEY\"}")

TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')
echo "✅ Token: ${TOKEN:0:50}..."
echo

# Step 2: Test health endpoint (no auth required)
echo "2. Testing /health endpoint..."
curl -s "$API_URL/health" | jq '.'
echo

# Step 3: Test generate endpoint (requires auth)
echo "3. Testing /api/biometric/generate (with auth)..."
curl -s -X POST "$API_URL/api/biometric/generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "wallet_address": "addr_test1_demo",
    "storage": "inline",
    "fingers": [
      {"finger_id": "left_thumb", "minutiae": [[100, 200, 45]]},
      {"finger_id": "left_index", "minutiae": [[110, 210, 50]]}
    ]
  }' | jq '.'
echo

# Step 4: Test without auth (should fail)
echo "4. Testing /api/biometric/generate (without auth - should fail)..."
curl -s -X POST "$API_URL/api/biometric/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_address": "addr_test1_demo",
    "storage": "inline",
    "fingers": [
      {"finger_id": "left_thumb", "minutiae": [[100, 200, 45]]},
      {"finger_id": "left_index", "minutiae": [[110, 210, 50]]}
    ]
  }' | jq '.'
```

---

## 6. Integration Test Configuration

### Update Demo Wallet Test Configuration

**File**: `demo-wallet/.env.test`

```bash
# API configuration for biometric integration tests
BIOMETRIC_API_URL=http://localhost:8001
BIOMETRIC_API_KEY=test_api_key_integration_32_chars_long_xyz

# Toggle API-backed suites (set to true once servers are running)
RUN_API_TESTS=false

# Deterministic sample wallet address used in fixtures
TEST_WALLET_ADDRESS=addr_test1_demo_integration_testing
```

### Update Jest Configuration

**File**: `demo-wallet/jest.config.js`

```javascript
module.exports = {
  // ...existing config...

  setupFiles: [
    '<rootDir>/tests/setupEnv.ts',
    '<rootDir>/src/ui/__mocks__/swiper.tsx'
  ],
  setupFilesAfterEnv: [
    '<rootDir>/src/setupTests.ts',
    'jest-canvas-mock'
  ],

  // ...rest of config...
};
```

Ensure `setupFiles` includes the new environment loader before other utilities so Jest loads the shared `.env.test` values prior to bootstrapping the wallet test harness.

### Create Environment Loader

**File**: `demo-wallet/tests/setupEnv.ts`

```typescript
import path from 'path';
import { config as loadEnv } from 'dotenv';

const envPath = path.resolve(__dirname, '..', '.env.test');
const result = loadEnv({ path: envPath });

if (result.error) {
  // eslint-disable-next-line no-console
  console.warn(`[biometric-tests] Missing ${envPath}, falling back to ambient process.env values.`);
} else {
  // eslint-disable-next-line no-console
  console.info(`[biometric-tests] Loaded environment from ${envPath}`);
}

process.env.RUN_API_TESTS = process.env.RUN_API_TESTS ?? 'false';
process.env.BIOMETRIC_API_URL = process.env.BIOMETRIC_API_URL ?? 'http://localhost:8001';
process.env.BIOMETRIC_API_KEY = process.env.BIOMETRIC_API_KEY ?? '';
process.env.TEST_WALLET_ADDRESS = process.env.TEST_WALLET_ADDRESS ?? 'addr_test1_demo_integration_testing';
```

With this loader in place, the integration tests can rely on deterministic defaults while still allowing CI or local workflows to opt into hitting live API servers by exporting `RUN_API_TESTS=true` before running Jest.
```

---

## 7. Rate Limiting

The secure API server has the following rate limits:

| Endpoint | Rate Limit | Note |
|----------|-----------|------|
| `/health` | 30/minute | Per IP |
| `/auth/token` | 5/minute | Per IP |
| `/api/biometric/generate` | 3/minute | Per IP |
| `/api/biometric/verify` | 5/minute | Per IP |

### Handling Rate Limit Errors

**Response (429 Too Many Requests)**:
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60
}
```

**Python Example with Retry**:
```python
import time

def api_request_with_retry(url, headers, data, max_retries=3):
    for attempt in range(max_retries):
        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            print(f"⏳ Rate limited, retrying after {retry_after}s...")
            time.sleep(retry_after)
            continue

        response.raise_for_status()
        return response.json()

    raise Exception(f"Max retries ({max_retries}) exceeded")
```

---

## 8. Testing Checklist

### Phase 1.2 Test Tasks

- [ ] **Server Startup**
  ```bash
  cd /workspaces/decentralized-did
  export API_SECRET_KEY="test_api_key_admin_32_chars_long_abcdef123456"
  export JWT_SECRET_KEY="jwt_secret_for_signing_tokens_32_chars_long"
  python api_server_secure.py
  ```

- [ ] **Health Check** (no auth)
  ```bash
  curl http://localhost:8001/health | jq '.'
  ```

- [ ] **Authentication** (get token)
  ```bash
  curl -X POST http://localhost:8001/auth/token \
    -H "Content-Type: application/json" \
    -d '{"api_key": "test_api_key_admin_32_chars_long_abcdef123456"}' | jq '.'
  ```

- [ ] **Generate DID** (with token)
  ```bash
  TOKEN="..." # From previous step
  curl -X POST http://localhost:8001/api/biometric/generate \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{ ... }' | jq '.'
  ```

- [ ] **Unauthorized Access** (without token - should fail)
  ```bash
  curl -X POST http://localhost:8001/api/biometric/generate \
    -H "Content-Type: application/json" \
    -d '{ ... }' | jq '.'
  # Expected: 401 Unauthorized
  ```

- [ ] **Invalid API Key** (should fail)
  ```bash
  curl -X POST http://localhost:8001/auth/token \
    -H "Content-Type: application/json" \
    -d '{"api_key": "invalid_key"}' | jq '.'
  # Expected: 401 Unauthorized
  ```

- [ ] **Token Expiration** (wait for expiry or test with short TTL)

- [ ] **Rate Limiting** (exceed 3 requests/minute)
  ```bash
  for i in {1..5}; do
    curl -X POST http://localhost:8001/api/biometric/generate \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{ ... }'
  done
  # Expected: 429 on 4th request
  ```

---

## 9. Troubleshooting

### Issue: "Invalid token format"
- **Cause**: Token not in correct format
- **Solution**: Ensure token is Base64-encoded JSON + signature

### Issue: "Token expired"
- **Cause**: Token TTL exceeded (default 24 hours)
- **Solution**: Re-authenticate to get new token

### Issue: "Invalid API key"
- **Cause**: API key doesn't match `API_SECRET_KEY`
- **Solution**: Check environment variable matches test key

### Issue: "Rate limit exceeded"
- **Cause**: Too many requests in time window
- **Solution**: Wait for rate limit window to reset (check `Retry-After` header)

### Issue: "CORS error in browser"
- **Cause**: Origin not in `CORS_ORIGINS` list
- **Solution**: Add origin to environment variable: `CORS_ORIGINS=http://localhost:3003,http://localhost:5173`

---

## 10. Security Best Practices

### Development
- ✅ Use test API keys (never production keys)
- ✅ Keep `.env` file in `.gitignore`
- ✅ Use different keys for different environments
- ✅ Disable rate limiting in tests (optional)

### Production
- ⚠️ Use strong, randomly generated keys (32+ characters)
- ⚠️ Store keys in secure secret management (AWS Secrets Manager, HashiCorp Vault)
- ⚠️ Enable HTTPS only (`HTTPS_ONLY=true`)
- ⚠️ Use short token expiration (1-4 hours)
- ⚠️ Implement token refresh mechanism
- ⚠️ Enable audit logging (`AUDIT_LOG_ENABLED=true`)
- ⚠️ Monitor rate limit violations
- ⚠️ Rotate API keys regularly
- ⚠️ Use role-based access control (RBAC)

---

## Next Steps

After completing Phase 1.2 configuration:

1. ✅ Test secure API server with credentials
2. ✅ Update demo wallet API client with auth
3. ✅ Enable `RUN_API_TESTS=true` in demo wallet
4. ✅ Run 9 deferred integration tests
5. ✅ Document any issues or limitations

**Proceed to**: Phase 1.3 - Set up mock API server (1 hour)

---

**Status**: Configuration guide complete ✅
**Ready for**: Testing and integration ✅
