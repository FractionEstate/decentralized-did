# Troubleshooting Guide

This guide covers common issues and their resolutions for the Decentralized DID system.

## Table of Contents

- [API Server Issues](#api-server-issues)
- [Demo Wallet Issues](#demo-wallet-issues)
- [Deployment Issues](#deployment-issues)
- [Python SDK Issues](#python-sdk-issues)
- [Database and Blockchain Issues](#database-and-blockchain-issues)
- [Performance Issues](#performance-issues)

---

## API Server Issues

### Server Won't Start - ModuleNotFoundError

**Symptom**: Server fails with `ModuleNotFoundError: No module named 'src'` or `'decentralized_did'`

**Cause**: Import paths not configured correctly or SDK not installed

**Solution**:
```bash
# Option 1: Install SDK in development mode
cd sdk/
pip install -e .

# Option 2: Set PYTHONPATH
export PYTHONPATH="/workspaces/decentralized-did/sdk/src:$PYTHONPATH"

# Verify SDK is importable
python -c "from decentralized_did.did.generator import generate_deterministic_did; print('✅ SDK imports work')"
```

**Fixed Files**:
- `/workspaces/decentralized-did/core/api/api_server.py`
- `/workspaces/decentralized-did/core/api/api_server_secure.py`
- `/workspaces/decentralized-did/core/api/api_server_mock.py`

All now use `sdk_path = Path(__file__).parent.parent.parent / "sdk" / "src"` to resolve imports.

### Server Crashes Under Load

**Symptom**: Server responds to first few requests then stops responding

**Cause**: Resource exhaustion, blocking I/O, or unhandled exceptions

**Solutions**:

1. **Increase worker timeout**:
```bash
uvicorn core.api.api_server:app --timeout-keep-alive 300
```

2. **Use multiple workers** (production):
```bash
gunicorn core.api.api_server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

3. **Check server logs**:
```bash
# Tail logs in real-time
tail -f /tmp/api_server_basic.log

# Search for errors
grep -i error /tmp/api_server_basic.log
```

4. **Monitor resource usage**:
```bash
# CPU and memory
htop

# Network connections
netstat -tuln | grep :8000
```

### JWT Authentication Failures (Secure Server)

**Symptom**: `401 Unauthorized` or `Invalid token` errors

**Cause**: Missing or expired JWT token

**Solutions**:

1. **Generate a test token**:
```bash
cd sdk/
python -c "
from decentralized_did.security.authentication import JWTManager
jwt_mgr = JWTManager(secret_key='test-secret-key-min-32-characters-long!')
token = jwt_mgr.create_access_token({'username': 'test_user', 'roles': ['user']})
print(f'Token: {token}')
"
```

2. **Use token in requests**:
```bash
TOKEN="<your_jwt_token_here>"
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8001/api/biometric/generate \
  -X POST -H "Content-Type: application/json" \
  -d '{"fingers": [...]}'
```

3. **Check token expiration**:
- Default access token TTL: 15 minutes
- Use refresh token endpoint if expired: `POST /auth/refresh`

### Rate Limiting Errors

**Symptom**: `429 Too Many Requests` responses

**Cause**: Rate limit exceeded (default: 10 requests/minute per IP for enrollment)

**Solutions**:

1. **Wait and retry**:
```bash
# Exponential backoff
for i in 1 2 4 8 16; do
  curl http://localhost:8000/api/biometric/generate ... && break || sleep $i
done
```

2. **Adjust rate limits** (development only):
```python
# In api_server_secure.py
RATE_LIMITS = {
    "/api/biometric/generate": "50/minute",  # Increase from 10
    # ...
}
```

3. **Use different IP addresses** (testing):
```bash
# Docker containers get unique IPs
docker run --rm -it alpine sh -c "apk add curl && curl ..."
```

### Koios API Timeouts

**Symptom**: "Koios duplicate check failed" warnings or timeouts

**Cause**: Koios REST API slow or unavailable

**Solutions**:

1. **Check Koios status**:
```bash
curl https://api.koios.rest/api/v1/tip
```

2. **Use alternative Koios instance**:
```bash
export KOIOS_BASE_URL="https://preprod.koios.rest/api/v1"
# Restart server
```

3. **Disable duplicate checking** (development only):
```python
# In api_server.py, comment out:
# if koios_client:
#     existing = await koios_client.check_did_exists(...)
```

4. **Increase timeout**:
```python
# In koios_client.py
koios_client = KoiosClient(
    base_url=KOIOS_BASE_URL,
    timeout=30.0,  # Increase from default 10s
)
```

---

## Demo Wallet Issues

### Build Failures - TypeScript Errors

**Symptom**: `npm run build` fails with TypeScript compilation errors

**Cause**: Type mismatches or missing dependencies

**Solutions**:

1. **Clean install**:
```bash
cd demo-wallet/
rm -rf node_modules/ package-lock.json
HUSKY=0 npm install
```

2. **Check TypeScript configuration**:
```bash
npx tsc --noEmit
# Review errors and fix type issues
```

3. **Verify VS Code uses workspace TypeScript**:
- Open `.vscode/settings.json`
- Ensure `"typescript.tsdk": "demo-wallet/node_modules/typescript/lib"`

### Integration Tests Failing - API Connection

**Symptom**: Tests fail with "ECONNREFUSED" or "Cannot connect to API"

**Cause**: API server not running or wrong URL

**Solutions**:

1. **Start required servers**:
```bash
# Terminal 1: Basic API
python -m uvicorn core.api.api_server:app --host 0.0.0.0 --port 8000

# Terminal 2: Secure API
python -m uvicorn core.api.api_server_secure:app --host 0.0.0.0 --port 8001

# Terminal 3: Mock API
python -m uvicorn core.api.api_server_mock:app --host 0.0.0.0 --port 8002
```

2. **Check test environment variables**:
```bash
cd demo-wallet/
cat .env.test
# Verify URLs match running servers
```

3. **Run tests with API flag**:
```bash
RUN_API_TESTS=true npm test -- biometricDidService.integration.test.ts
```

### Android Build Failures

**Symptom**: Gradle build fails with JDK version errors

**Cause**: JDK version mismatch (requires JDK 21)

**Solutions**:

1. **Install OpenJDK 21**:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install openjdk-21-jdk

# Verify
java -version  # Should show "21.x.x"
```

2. **Set Gradle JDK path**:
```bash
cd demo-wallet/android/
echo "org.gradle.java.home=/usr/lib/jvm/java-21-openjdk-amd64" >> gradle.properties
```

3. **Sync Capacitor assets**:
```bash
cd demo-wallet/
npm run build:local
npx cap sync android
```

4. **Clean and rebuild**:
```bash
cd demo-wallet/android/
./gradlew clean assembleDebug
```

### Biometric Enrollment Failures

**Symptom**: "Enrollment failed" or DID generation errors in wallet

**Cause**: Invalid biometric data or API errors

**Solutions**:

1. **Check API server logs**:
```bash
tail -f /tmp/api_server_basic.log
# Look for errors during enrollment requests
```

2. **Validate biometric data format**:
```javascript
// In demo wallet, check finger data structure
const fingerData = {
  finger_id: "left_thumb",  // Must be valid enum
  minutiae: [[x, y, angle], ...],  // At least 10 minutiae
};
```

3. **Test with mock data**:
```bash
# Use mock API server which always succeeds
export API_URL="http://localhost:8002"
```

4. **Enable debug logging**:
```typescript
// In BiometricDidService.ts
console.log("Enrollment request:", JSON.stringify(request, null, 2));
```

---

## Deployment Issues

### Docker Compose Fails to Start

**Symptom**: `docker-compose up` fails or services crash

**Cause**: Missing environment variables or port conflicts

**Solutions**:

1. **Check environment files**:
```bash
# Ensure .env files exist
ls -la .env.development .env.production

# Copy from examples if missing
cp .env.example .env.development
```

2. **Verify required variables**:
```bash
# Check for required secrets
grep -E "SECRET|KEY|PASSWORD" .env.development
# Ensure no empty values
```

3. **Fix port conflicts**:
```bash
# Check what's using ports
lsof -i :8000
lsof -i :8001

# Kill conflicting processes or change ports in docker-compose.yml
```

4. **View service logs**:
```bash
docker-compose logs -f api-basic
docker-compose logs -f api-secure
```

### SSL Certificate Issues

**Symptom**: Let's Encrypt certificate renewal fails

**Cause**: DNS not pointing to server or rate limits

**Solutions**:

1. **Verify DNS**:
```bash
nslookup your-domain.com
# Should return your server IP
```

2. **Test ACME challenge**:
```bash
# Ensure /.well-known/acme-challenge/ is accessible
curl http://your-domain.com/.well-known/acme-challenge/test
```

3. **Check rate limits**:
- Let's Encrypt: 5 certificates per 7 days per domain
- Use staging environment for testing:
```bash
# In renew-ssl.sh
certbot renew --staging
```

4. **Manual renewal**:
```bash
./renew-ssl.sh --force
```

### Nginx Reverse Proxy Errors

**Symptom**: 502 Bad Gateway or connection refused

**Cause**: Backend servers not running or wrong upstream configuration

**Solutions**:

1. **Check upstream servers**:
```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
```

2. **Test nginx configuration**:
```bash
nginx -t
# Fix any syntax errors
```

3. **View nginx logs**:
```bash
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log
```

4. **Verify upstream in nginx.conf**:
```nginx
upstream api_backend {
    server localhost:8000;  # Check port matches
}
```

---

## Python SDK Issues

### Import Errors

**Symptom**: `ImportError: cannot import name 'FuzzyExtractor'`

**Cause**: SDK not installed or installed in wrong location

**Solutions**:

1. **Install SDK properly**:
```bash
cd sdk/
pip install -e .
```

2. **Verify installation**:
```bash
pip list | grep decentralized-did
# Should show: decentralized-did 1.1.0 /path/to/sdk/src
```

3. **Check Python path**:
```python
import sys
print("\n".join(sys.path))
# Should include /path/to/sdk/src
```

### Biometric Processing Errors

**Symptom**: "Quantization failed" or "Fuzzy extraction failed"

**Cause**: Invalid minutiae data or quality too low

**Solutions**:

1. **Validate minutiae format**:
```python
from decentralized_did.biometrics import Minutia

minutiae = [
    Minutia(x=10.0, y=20.0, angle=45.0),  # x, y in mm; angle in degrees
    # At least 10 minutiae required
]
```

2. **Check quality scores**:
```python
# Ensure quality >= 70 for production
if template.quality < 70:
    print("⚠️ Low quality biometric data")
```

3. **Enable verbose logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Cardano Integration Errors

**Symptom**: "Koios query failed" or blockchain errors

**Cause**: Network issues or invalid addresses

**Solutions**:

1. **Check network configuration**:
```python
from decentralized_did.cardano.koios_client import KoiosClient

client = KoiosClient(
    base_url="https://preprod.koios.rest/api/v1",
    timeout=30.0,
)
# Ensure using correct network (mainnet/preprod/testnet)
```

2. **Validate wallet addresses**:
```python
# Testnet: addr_test1...
# Mainnet: addr1...
# Stake: stake1... or stake_test1...
```

3. **Handle rate limits**:
```python
import time
from decentralized_did.cardano.koios_client import KoiosError

try:
    result = await client.query_address(address)
except KoiosError as e:
    if "rate limit" in str(e).lower():
        time.sleep(60)  # Wait 1 minute
        result = await client.query_address(address)
```

---

## Database and Blockchain Issues

### Koios API Down

**Symptom**: All blockchain queries failing

**Cause**: Koios REST API maintenance or outage

**Solutions**:

1. **Check Koios status**:
```bash
curl https://api.koios.rest/api/v1/tip
# Should return current tip
```

2. **Use alternative instance**:
```bash
# Preprod
export KOIOS_BASE_URL="https://preprod.koios.rest/api/v1"

# Guild-hosted
export KOIOS_BASE_URL="https://guild.koios.rest/api/v1"
```

3. **Implement fallback**:
```python
KOIOS_INSTANCES = [
    "https://api.koios.rest/api/v1",
    "https://preprod.koios.rest/api/v1",
    "https://guild.koios.rest/api/v1",
]

for url in KOIOS_INSTANCES:
    try:
        client = KoiosClient(base_url=url)
        result = await client.query_address(address)
        break
    except:
        continue
```

### Metadata Not Found on Chain

**Symptom**: "DID not found" errors during verification

**Cause**: Transaction not yet confirmed or wrong metadata label

**Solutions**:

1. **Check transaction status**:
```bash
# Use Cardano explorer
# Testnet: https://preprod.cardanoscan.io/transaction/<tx_hash>
# Mainnet: https://cardanoscan.io/transaction/<tx_hash>
```

2. **Verify metadata label**:
```bash
# Default label: 674
export KOIOS_METADATA_LABEL="674"

# Check what label was used in transaction
curl "https://api.koios.rest/api/v1/tx_metadata?_tx_hash=<tx_hash>"
```

3. **Wait for confirmation**:
```bash
# Transactions take 20-60 seconds to confirm
sleep 60
# Retry query
```

---

## Performance Issues

### Slow Enrollment Times

**Symptom**: Enrollment takes >1 second

**Cause**: Unoptimized biometric processing or network latency

**Solutions**:

1. **Enable caching**:
```python
from decentralized_did.cardano.cache import TTLCache

koios_client = KoiosClient(
    cache=TTLCache(default_ttl=300),  # 5-minute cache
)
```

2. **Use mock server for development**:
```bash
# Mock server has <10ms response times
python -m uvicorn core.api.api_server_mock:app --port 8002
```

3. **Optimize biometric parameters**:
```python
# Reduce minutiae count for faster processing
template = FingerTemplate(
    minutiae=minutiae[:15],  # Use fewer points
    grid_size=0.1,  # Larger grid = faster
)
```

4. **Profile performance**:
```bash
cd sdk/
python -m cProfile -s cumulative benchmark_api.py
```

### High Memory Usage

**Symptom**: Server using excessive RAM

**Cause**: Large biometric data or memory leaks

**Solutions**:

1. **Monitor memory**:
```bash
# Check process memory
ps aux | grep uvicorn

# Watch in real-time
watch 'ps aux | grep uvicorn'
```

2. **Limit workers**:
```bash
# Reduce number of workers
gunicorn --workers 2 ...  # Instead of 4
```

3. **Clear caches periodically**:
```python
# In api_server.py
@app.on_event("startup")
async def schedule_cache_clear():
    async def clear_cache():
        while True:
            await asyncio.sleep(3600)  # Every hour
            koios_client.cache.clear()
    asyncio.create_task(clear_cache())
```

### Database Query Slow

**Symptom**: Koios queries taking >5 seconds

**Cause**: Large dataset or missing indexes

**Solutions**:

1. **Use pagination**:
```python
# Limit results
results = await koios_client.query_metadata(
    label="674",
    limit=100,  # Don't fetch all at once
)
```

2. **Implement local caching**:
```python
from decentralized_did.storage import FileStorage

# Cache query results to disk
cache = FileStorage(base_path="/var/cache/did-metadata")
```

3. **Use Koios websockets** (advanced):
```python
# Real-time updates instead of polling
# See: https://api.koios.rest/#tag--WebSocket
```

---

## General Debugging Tips

### Enable Debug Logging

```bash
# Python SDK
export LOG_LEVEL=DEBUG
python your_script.py

# API servers
uvicorn core.api.api_server:app --log-level debug

# Demo wallet
export DEBUG=* npm start
```

### Inspect Network Traffic

```bash
# HTTP requests
mitmproxy

# API calls
tcpdump -i lo -A 'port 8000'

# Monitor in Chrome DevTools (demo wallet)
# F12 → Network tab
```

### Verify System Requirements

```bash
# Python version (requires 3.11+)
python --version

# Node version (requires 18+)
node --version

# Java version (requires 21 for Android)
java -version

# Docker version
docker --version
docker-compose --version
```

### Common Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 400 | Bad Request | Check request payload format |
| 401 | Unauthorized | Verify JWT token or API key |
| 403 | Forbidden | Check user permissions |
| 404 | Not Found | Verify endpoint URL |
| 409 | Conflict | DID already exists (duplicate) |
| 429 | Rate Limit | Wait and retry with backoff |
| 500 | Server Error | Check server logs |
| 502 | Bad Gateway | Backend server down |
| 503 | Service Unavailable | Server overloaded |

---

## Getting Help

### Log Collection

When reporting issues, provide:

1. **API server logs**:
```bash
tail -100 /tmp/api_server_basic.log > debug_logs.txt
```

2. **System information**:
```bash
uname -a
python --version
node --version
docker --version
```

3. **Error reproduction steps**:
```bash
# Exact commands that trigger the error
curl -X POST http://localhost:8000/api/biometric/generate ...
```

4. **Environment variables** (redact secrets):
```bash
env | grep -E "KOIOS|CARDANO|API" | sed 's/=.*/=***/'
```

### Community Resources

- **GitHub Issues**: https://github.com/FractionEstate/decentralized-did/issues
- **Documentation**: `/workspaces/decentralized-did/docs/`
- **Security**: See `docs/security/` for security-specific guides

### Emergency Contacts

For production outages:
1. Check system status page (if available)
2. Review incident response plan: `docs/operations/incident-response.md`
3. Follow escalation procedures

---

**Last Updated**: October 26, 2025
**Version**: 1.0.0
