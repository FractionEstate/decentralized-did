# API Endpoint Reference

**Task 4 Phase 1.4** — API endpoint documentation for the biometric DID servers

_Last updated: October 17, 2025_

---

## Overview

Three FastAPI services are available during integration testing:

| Server | Module | Default Port | Authentication | Primary Use |
| --- | --- | --- | --- | --- |
| Basic API | `api_server.py` | `8000` | None | Local development, deterministic smoke tests |
| Secure API | `api_server_secure.py` | `8001` (recommended) | JWT bearer token (API key exchange) | Production-hardening, auth/rate-limit validation |
| Mock API | `api_server_mock.py` | `8002` | None | Deterministic CI runs, fast demo-wallet tests |

All servers expose the same biometric endpoints (`/api/biometric/generate`, `/api/biometric/verify`) but differ in authentication, rate limiting, and helper-data expectations.

> Quickstart: `set -a; source .env.test; set +a` exports the canonical integration-test configuration used by `test_api_auth.sh` and the demo wallet.

For environment and credential setup, see `docs/API-TEST-CONFIGURATION.md`. Automated test coverage is available through `./test_api_auth.sh` (`basic`, `secure`, or `mock` modes).

---

## Shared Schemas

Unless otherwise noted, all JSON payloads use `application/json` with UTF-8 encoding.

### FingerData
```json
{
  "finger_id": "left_thumb",
  "minutiae": [
    [100.5, 200.3, 45.0],
    [150.2, 180.9, 90.5]
  ]
}
```
- `finger_id` — string identifier (`left_thumb`, `left_index`, ...)
- `minutiae` — array of `[x, y, angle]` float triples

### GenerateRequest
```json
{
  "wallet_address": "addr_test1...",
  "storage": "inline",
  "format": "json",
  "fingers": [ FingerData, ... ]
}
```
- `storage` — `"inline"` or `"external"` (inline embeds helper data in response)
- `format` — reserved for future formats (default `json`)
- Requires 1–10 fingers (`min_items=1` in secure server)

### HelperDataEntry (inline storage)
```json
{
  "finger_id": "left_thumb",
  "salt_b64": "U0lSrmTJCctVw61u8uZSPA",
  "auth_b64": "kpi2...",
  "grid_size": 0.05,
  "angle_bins": 32
}
```
- `salt_b64` / `auth_b64` — base64url encoded helper artifacts
- `grid_size`, `angle_bins` — metadata for downstream quantization

### GenerateResponse
```json
{
  "did": "did:cardano:mainnet:...",
  "id_hash": "...",
  "wallet_address": "addr_test1...",
  "helpers": { "left_thumb": HelperDataEntry, ... },
  "metadata_cip30_inline": {
    "version": "1.1",
    "walletAddress": "addr_test1...",
    "controllers": ["addr_test1..."],
    "enrollmentTimestamp": "2025-10-16T01:23:45.123456+00:00",
    "biometric": {
      "idHash": "...",
      "helperStorage": "inline",
      "helperData": { "left_thumb": HelperDataEntry, ... }
    },
    "revoked": false,
    "revokedAt": null
  }
}
```
- `id_hash` — deterministic identifier derived from the commitment
- `metadata_cip30_inline` — Wallet/CIP-30 compatible payload (version `1.1`)

### VerifyRequest
```json
{
  "fingers": [ FingerData, ... ],
  "helpers": { "left_thumb": HelperDataEntry, ... },
  "expected_id_hash": "..."
}
```
- All deployments require `expected_id_hash` to match the stored helper-data digest
- Success additionally requires the submitted helper map to reference the enrolled fingers (minimum two by default)

### VerifyResponse
```json
{
  "success": true,
  "matched_fingers": ["left_thumb", "left_index"],
  "unmatched_fingers": [],
  "error": null
}
```
- `success=false` accompanied by `error` message (`"Helper data hash mismatch"`, `"Insufficient matching fingerprints"`, ...)

---

## Basic API Server (`api_server.py`)

| Method | Path | Auth | Notes |
| --- | --- | --- | --- |
| `GET` | `/health` | None | Returns status/version JSON |
| `POST` | `/api/biometric/generate` | None | Deterministic commitment (wallet + minutiae); duplicate detection via Koios when configured |
| `POST` | `/api/biometric/verify` | None | Recomputes helper hash; requires matching helper set and expected hash |

### `/health`
**200 OK**
```json
{
  "status": "healthy",
  "service": "biometric-did-api-basic",
  "version": "1.1.0"
}
```

### `/api/biometric/generate`
- **200 OK** — returns `GenerateResponse`
- **409 Conflict** — duplicate DID detected when Koios client finds an existing enrollment
- **500 Internal Server Error** — unhandled exceptions (stack trace logged to console)

Example:
```bash
curl -X POST http://localhost:8000/api/biometric/generate \
  -H "Content-Type: application/json" \
  -d '{
        "wallet_address": "addr_test1qz2...",
        "storage": "inline",
        "fingers": [
          {"finger_id": "left_thumb", "minutiae": [[100,200,45]]},
          {"finger_id": "left_index", "minutiae": [[110,210,50]]}
        ]
      }'
```

### `/api/biometric/verify`
- **200 OK** — returns `VerifyResponse`
- **500 Internal Server Error** — verification failure (mock helper schema mismatch)

> **Note**: Helper data is derived deterministically from each `finger_id`. Verification succeeds when at least two enrolled fingers are supplied and the `expected_id_hash` matches the enrolled helper digest.

---

## Secure API Server (`api_server_secure.py`)

| Method | Path | Auth | Rate Limit* |
| --- | --- | --- | --- |
| `GET` | `/health` | None | `30/minute` |
| `POST` | `/auth/token` | API key (in body) | `5/minute`
| `POST` | `/api/biometric/generate` | Bearer token | `3/minute`
| `POST` | `/api/biometric/verify` | Bearer token | `5/minute`

\* Disabled automatically when `RATE_LIMIT_ENABLED=false` (default in `.env.test` for deterministic runs).

### Security Hardening Checklist

- **Secrets**: Provision `API_SECRET_KEY` and `JWT_SECRET_KEY` from an HSM or FIPS 140-3 validated RNG. Rotate on a ≤90 day schedule and feed the values via secrets manager.
- **Transport**: Launch with `HTTPS_ONLY=true` and place behind a TLS 1.3 ingress proxy that enforces HSTS, OCSP stapling, and modern cipher suites.
- **Rate Limiting**: Keep `RATE_LIMIT_ENABLED=true` in production. Back SlowAPI with Redis or another shared store to avoid bypass across replicas; tune quotas by relying-party classification (citizen services, agency portals, etc.).
- **Audit Logging**: Forward `audit.log` to immutable storage (SIEM, WORM bucket) and maintain ≥7 year retention for national identity regulations.
- **Key Custody**: Plan migration to hardware signing for JWTs (`JWT_SIGNING_BACKEND` roadmap) so bearer tokens remain defensible in court-administered audits.
- **Compliance Mapping**: Cross-check endpoints against `docs/API-TEST-CONFIGURATION.md#6-production-hardening--compliance` to satisfy NIST SP 800-63, ISO/IEC 24745, GDPR, and eIDAS requirements.
- **Environment Gate**: `ENVIRONMENT` values `production`/`staging` enforce TLS, rate limiting, audit logging, non-default secrets, and Koios connectivity at startup—startup aborts if any requirement is unmet.

### Authentication Flow
1. Exchange an API key for a JWT access token:
   ```bash
   curl -X POST http://localhost:8001/auth/token \
     -H "Content-Type: application/json" \
     -d '{"api_key": "test_api_key_admin_32_chars_long_abcdef123456"}'
   ```
   Response contains `access_token`, `token_type`, and `expires_in`.
2. Use the token in the `Authorization: Bearer <token>` header for protected endpoints.

### `/api/biometric/generate`
- Request body matches `GenerateRequest`
- **200 OK** — deterministic DID + helper data
- **401/403** — missing or invalid bearer token
- **409 Conflict** — duplicate DID from Koios lookup
- **429 Too Many Requests** — rate limit exceeded
- **500 Internal Server Error** — unexpected failure (logged + audit entry)

Example:
```bash
TOKEN=$(curl -s -X POST http://localhost:8001/auth/token \
  -H "Content-Type: application/json" \
  -d '{"api_key": "test_api_key_admin_32_chars_long_abcdef123456"}' \
  | jq -r '.access_token')

curl -X POST http://localhost:8001/api/biometric/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
        "wallet_address": "addr_test1...",
        "storage": "inline",
        "fingers": [ ... ]
      }'
```

### `/api/biometric/verify`
- Requires helpers returned during enrollment and the matching `expected_id_hash`
- **200 OK** — `success` true when hash matches and ≥2 fingers reproduced
- **200 OK + success=false** — helper hash mismatch or insufficient matches (`error` field populated)
- **401/403** — missing/invalid token
- **429 Too Many Requests** — rate limit exceeded
- **500 Internal Server Error** — server-side failure (audit logged)

Sample payload:
```json
{
  "fingers": [ FingerData, ... ],
  "helpers": { "left_thumb": HelperDataEntry, ... },
  "expected_id_hash": "EqvPVfD4MXgPHNyFG8cRVXAbRWFUWA3p2yYAnV7KyUcn"
}
```

### Audit & Logging
- Audit log entries (`audit.log`) capture auth attempts, generate/verify lifecycle events, and verification outcomes (success/failure).
- Security headers (CSP, HSTS, etc.) included on every response.

---

## Mock API Server (`api_server_mock.py`)

| Method | Path | Auth | Notes |
| --- | --- | --- | --- |
| `GET` | `/health` | None | Identifies mock build & version |
| `POST` | `/api/biometric/generate` | None | Deterministic helper salts/auth derived from `finger_id` |
| `POST` | `/api/biometric/verify` | None | Validates helper hash + requires ≥2 matching fingers |

### Deterministic Behaviour
- Helper data generated by `_deterministic_bytes(label, finger_id)` using Blake2b.
- `compute_helper_hash` hashes helper entries (and optional wallet) to produce `id_hash`.
- Two requests with identical payloads yield identical `did`/`id_hash` outcomes.

### Example Test Run
```bash
uvicorn api_server_mock:app --host 0.0.0.0 --port 8002 --log-level info &
MOCK_API_URL=http://localhost:8002 ./test_api_auth.sh mock
```
Expected results:
- Health check succeeds (`status: healthy`)
- `/generate` called twice returns identical `did` and `id_hash`
- `/verify` returns `{ "success": true }` when using the captured helpers and `expected_id_hash`

### Usage Notes
- Default configuration: `MOCK_API_HOST=0.0.0.0`, `MOCK_API_PORT=8002`, `MOCK_API_RELOAD=false`
- CIP-30 metadata mirrors the deterministic `idHash`
- Deterministic fixtures documented in `docs/API-TEST-CONFIGURATION.md#5-mock-server-fixtures`
- Ideal for demo-wallet integration tests without external dependencies

---

## Error Codes & Responses

| Status | Context | Description |
| --- | --- | --- |
| `200 OK` | Success | Payload returned (may require checking `success` flag) |
| `401 Unauthorized` | Secure API | Missing or invalid bearer token; also returned for malformed JWT signature |
| `403 Forbidden` | Secure API | No credentials provided (FastAPI dependency rejection) |
| `409 Conflict` | Basic/Secure | Duplicate DID detected via Koios client |
| `429 Too Many Requests` | Secure API | Rate limit exceeded (SlowAPI) |
| `500 Internal Server Error` | All | Unhandled exception; inspect logs/audit trail |

---

## Testing Utilities

| Command | Purpose |
| --- | --- |
| `./test_api_auth.sh basic` | Smoke-test basic server (`/health`, `/generate`) |
| `./test_api_auth.sh secure` | JWT token issuance + protected endpoints + auth failure cases |
| `./test_api_auth.sh mock` | Deterministic helper validation for mock server |

Environment overrides:
```bash
export BASIC_API_URL=http://localhost:8000
export SECURE_API_URL=http://localhost:8001
export MOCK_API_URL=http://localhost:8002
export API_KEY=test_api_key_admin_32_chars_long_abcdef123456
```

---

## References
- `api_server.py`, `api_server_secure.py`, `api_server_mock.py`
- `docs/API-TEST-CONFIGURATION.md` — environment & credential setup
- `docs/TASK-4-PHASE-1.2-PROGRESS.md` — secure server JWT progress
- `docs/TASK-4-PHASE-1.3-PROGRESS.md` — mock server deterministic behaviour
- `./test_api_auth.sh` — automated verification of authentication and mock flows
