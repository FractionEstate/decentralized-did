# API Test Fixtures

Integration test payloads for Task 4 mock and secure API validation.

- `mock_generate_request.json` – Example enrollment payload used by the mock server. Two fingers with deterministic minutiae so the helper data and DID output remain stable across runs.
- `mock_verify_request.json` – Matching verification payload that reuses the helper data returned during enrollment. The `expected_id_hash` equals the Blake2b digest derived from the helper bundle.

Usage tips:

1. Source `.env.test` to export the same secrets used by the fixtures (`API_SECRET_KEY`, `API_KEY`, etc.).
2. Start the mock API: `uvicorn api_server_mock:app --port 8002`.
3. Exercise the fixture via cURL:
   ```bash
   curl -X POST http://localhost:8002/api/biometric/generate \
     -H "Content-Type: application/json" \
     --data @tests/fixtures/api/mock_generate_request.json

   curl -X POST http://localhost:8002/api/biometric/verify \
     -H "Content-Type: application/json" \
     --data @tests/fixtures/api/mock_verify_request.json
   ```
4. Both requests return deterministic results; verification should succeed with `success: true`.
