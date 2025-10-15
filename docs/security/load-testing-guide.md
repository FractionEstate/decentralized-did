# Load Testing Guide

This guide explains how to perform load testing on the Decentralized DID API servers to validate performance under high concurrency and identify bottlenecks.

## Overview

Load testing helps ensure the API can handle production traffic levels. This guide covers:

- Installing and configuring load testing tools (Locust and k6)
- Creating test scenarios for biometric enrollment and verification
- Running load tests with 1000+ concurrent users
- Collecting and analyzing performance metrics
- Identifying and resolving bottlenecks

## Performance Targets

Based on Phase 4.6 requirements:

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| Enrollment Response Time | < 150ms (p95) | < 300ms (p99) |
| Verification Response Time | < 75ms (p95) | < 150ms (p99) |
| Throughput | > 1000 req/s | > 500 req/s |
| Error Rate | < 0.1% | < 1% |
| Concurrent Users | 1000+ | 500+ |

## Prerequisites

- API server running with production configuration
- Load testing tool installed (Locust or k6)
- Sufficient system resources (CPU, memory, network)
- Test biometric data prepared

## Option 1: Locust (Python-based)

### Installation

```bash
# Install Locust
pip install locust

# Verify installation
locust --version
```

### Create Test Script

Create `tests/load/locustfile.py`:

```python
"""
Locust load testing script for Decentralized DID API

Run with:
    locust -f tests/load/locustfile.py --host=http://localhost:8000
"""

import random
import time
from locust import HttpUser, task, between, events
import hashlib


class DIDAPIUser(HttpUser):
    """Simulates a user interacting with the DID API"""

    # Wait 1-3 seconds between requests
    wait_time = between(1, 3)

    def on_start(self):
        """Called when a user starts"""
        # Generate test data for this user
        self.wallet_address = f"addr_test1{random.randint(100000, 999999)}"
        self.biometric_hash = hashlib.sha256(
            f"biometric_data_{random.randint(1, 100000)}".encode()
        ).hexdigest()

    @task(3)  # Weight: 3 (75% of requests)
    def verify_biometric(self):
        """Test biometric verification endpoint"""
        payload = {
            "wallet_address": self.wallet_address,
            "biometric_hash": self.biometric_hash,
            "timestamp": int(time.time())
        }

        with self.client.post(
            "/api/v1/did/verify",
            json=payload,
            catch_response=True,
            name="verify_biometric"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                # Expected for non-enrolled users
                response.success()
            elif response.status_code == 429:
                # Rate limited - expected under load
                response.failure("Rate limited")
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)  # Weight: 1 (25% of requests)
    def enroll_biometric(self):
        """Test biometric enrollment endpoint"""
        # Generate unique data for each enrollment
        wallet = f"addr_test1{random.randint(100000, 999999)}"
        bio_hash = hashlib.sha256(
            f"biometric_{random.randint(1, 100000)}".encode()
        ).hexdigest()

        payload = {
            "wallet_address": wallet,
            "biometric_hash": bio_hash,
            "metadata": {
                "device_id": f"device_{random.randint(1, 1000)}",
                "enrollment_type": "test"
            }
        }

        with self.client.post(
            "/api/v1/did/enroll",
            json=payload,
            catch_response=True,
            name="enroll_biometric"
        ) as response:
            if response.status_code == 201:
                response.success()
            elif response.status_code == 409:
                # Duplicate enrollment - expected
                response.success()
            elif response.status_code == 429:
                # Rate limited - expected under load
                response.failure("Rate limited")
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(5)  # Weight: 5 (high frequency)
    def health_check(self):
        """Test health check endpoint"""
        with self.client.get(
            "/health",
            catch_response=True,
            name="health_check"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the test starts"""
    print("🚀 Starting load test...")
    print(f"Target: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the test stops"""
    print("\n✅ Load test complete!")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Failures: {environment.stats.total.num_failures}")
    print(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
    print(f"P95 response time: {environment.stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"P99 response time: {environment.stats.total.get_response_time_percentile(0.99):.2f}ms")
    print(f"RPS: {environment.stats.total.total_rps:.2f}")
```

### Run Load Tests

#### Quick Test (50 users, 1 minute)

```bash
# Test with 50 users ramping up over 10 seconds
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users 50 \
    --spawn-rate 5 \
    --run-time 1m \
    --headless \
    --html reports/load-test-50users.html
```

#### Medium Test (500 users, 5 minutes)

```bash
# Test with 500 users ramping up over 1 minute
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users 500 \
    --spawn-rate 10 \
    --run-time 5m \
    --headless \
    --html reports/load-test-500users.html
```

#### Full Load Test (1000 users, 10 minutes)

```bash
# Test with 1000 users ramping up over 2 minutes
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users 1000 \
    --spawn-rate 10 \
    --run-time 10m \
    --headless \
    --html reports/load-test-1000users.html \
    --csv reports/load-test-1000users
```

#### Interactive Web UI

```bash
# Start Locust with web UI
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Open browser to http://localhost:8089
# Configure users and spawn rate in the UI
```

## Option 2: k6 (Go-based, high performance)

### Installation

```bash
# Linux
wget https://github.com/grafana/k6/releases/download/v0.48.0/k6-v0.48.0-linux-amd64.tar.gz
tar -xzf k6-v0.48.0-linux-amd64.tar.gz
sudo mv k6-v0.48.0-linux-amd64/k6 /usr/local/bin/

# macOS
brew install k6

# Verify installation
k6 version
```

### Create Test Script

Create `tests/load/k6-test.js`:

```javascript
/**
 * k6 load testing script for Decentralized DID API
 *
 * Run with:
 *   k6 run tests/load/k6-test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const enrollmentDuration = new Trend('enrollment_duration');
const verificationDuration = new Trend('verification_duration');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 100 },   // Ramp up to 100 users
    { duration: '3m', target: 500 },   // Ramp up to 500 users
    { duration: '3m', target: 1000 },  // Ramp up to 1000 users
    { duration: '2m', target: 1000 },  // Stay at 1000 users
    { duration: '2m', target: 0 },     // Ramp down to 0 users
  ],
  thresholds: {
    'http_req_duration': ['p(95)<150', 'p(99)<300'],  // 95% < 150ms, 99% < 300ms
    'http_req_failed': ['rate<0.01'],                  // Error rate < 1%
    'errors': ['rate<0.01'],                           // Custom error rate < 1%
    'enrollment_duration': ['p(95)<150'],              // Enrollment p95 < 150ms
    'verification_duration': ['p(95)<75'],             // Verification p95 < 75ms
  },
};

const BASE_URL = __ENV.API_URL || 'http://localhost:8000';

// Generate random data
function randomString(length) {
  const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

function randomWalletAddress() {
  return `addr_test1${randomString(50)}`;
}

function randomBiometricHash() {
  return randomString(64); // SHA256 length
}

// Test scenarios
export default function () {
  // 1. Health check (20% of requests)
  if (Math.random() < 0.2) {
    const healthRes = http.get(`${BASE_URL}/health`);
    check(healthRes, {
      'health check status is 200': (r) => r.status === 200,
    });
    errorRate.add(healthRes.status !== 200);
  }

  // 2. Biometric enrollment (20% of requests)
  if (Math.random() < 0.2) {
    const enrollPayload = JSON.stringify({
      wallet_address: randomWalletAddress(),
      biometric_hash: randomBiometricHash(),
      metadata: {
        device_id: `device_${Math.floor(Math.random() * 1000)}`,
        enrollment_type: 'test',
      },
    });

    const enrollRes = http.post(
      `${BASE_URL}/api/v1/did/enroll`,
      enrollPayload,
      { headers: { 'Content-Type': 'application/json' } }
    );

    enrollmentDuration.add(enrollRes.timings.duration);

    check(enrollRes, {
      'enrollment status is 201 or 409': (r) => r.status === 201 || r.status === 409,
    });

    errorRate.add(enrollRes.status !== 201 && enrollRes.status !== 409 && enrollRes.status !== 429);
  }

  // 3. Biometric verification (60% of requests)
  if (Math.random() < 0.6) {
    const verifyPayload = JSON.stringify({
      wallet_address: randomWalletAddress(),
      biometric_hash: randomBiometricHash(),
      timestamp: Math.floor(Date.now() / 1000),
    });

    const verifyRes = http.post(
      `${BASE_URL}/api/v1/did/verify`,
      verifyPayload,
      { headers: { 'Content-Type': 'application/json' } }
    );

    verificationDuration.add(verifyRes.timings.duration);

    check(verifyRes, {
      'verification status is 200 or 401': (r) => r.status === 200 || r.status === 401,
    });

    errorRate.add(verifyRes.status !== 200 && verifyRes.status !== 401 && verifyRes.status !== 429);
  }

  // Think time between requests
  sleep(Math.random() * 2 + 1); // 1-3 seconds
}

// Setup function (runs once at start)
export function setup() {
  console.log('🚀 Starting k6 load test...');
  console.log(`Target: ${BASE_URL}`);
}

// Teardown function (runs once at end)
export function teardown(data) {
  console.log('✅ Load test complete!');
}
```

### Run k6 Tests

#### Quick Test (50 users)

```bash
k6 run --vus 50 --duration 1m tests/load/k6-test.js
```

#### Medium Test (500 users)

```bash
k6 run --vus 500 --duration 5m tests/load/k6-test.js
```

#### Full Load Test (1000 users)

```bash
k6 run tests/load/k6-test.js --out json=reports/k6-results.json
```

#### Cloud Test with k6 Cloud

```bash
# Sign up for free k6 Cloud account
k6 login cloud

# Run test in the cloud
k6 cloud tests/load/k6-test.js
```

## Analyzing Results

### Key Metrics to Monitor

1. **Response Time**:
   - P50 (median): Should be < 50ms for verification, < 100ms for enrollment
   - P95: Should be < 75ms for verification, < 150ms for enrollment
   - P99: Should be < 150ms for verification, < 300ms for enrollment

2. **Throughput**:
   - Requests per second (RPS): Should handle > 1000 RPS
   - Successful requests: Should be > 99%
   - Failed requests: Should be < 1%

3. **Error Rate**:
   - HTTP 429 (rate limited): Expected under heavy load
   - HTTP 500 (server error): Should be 0%
   - HTTP 4xx (client error): Check if legitimate validation errors

4. **Resource Usage**:
   - CPU utilization: Monitor with `top` or `htop`
   - Memory usage: Should be stable, no memory leaks
   - Network bandwidth: Monitor with `iftop` or `nethogs`

### Locust Report Analysis

Open the generated HTML report (`reports/load-test-1000users.html`):

- **Statistics Table**: Shows aggregated metrics per endpoint
- **Charts**: Visualize response times, RPS, and user count over time
- **Failures**: Lists all failed requests with reasons
- **Download Data**: Export raw CSV data for further analysis

### k6 Report Analysis

Review the terminal output:

```
✓ health check status is 200
✓ enrollment status is 201 or 409
✓ verification status is 200 or 401

checks.........................: 99.87% ✓ 29961    ✗ 39
data_received..................: 15 MB  25 kB/s
data_sent......................: 12 MB  20 kB/s
enrollment_duration............: avg=125ms min=45ms med=110ms max=450ms p(95)=180ms p(99)=250ms
verification_duration..........: avg=62ms  min=20ms med=55ms  max=220ms p(95)=95ms  p(99)=140ms
errors.........................: 0.13%  ✓ 39       ✗ 29961
http_req_blocked...............: avg=1.2ms min=0µs  med=0µs   max=250ms p(95)=5ms   p(99)=12ms
http_req_connecting............: avg=0.8ms min=0µs  med=0µs   max=180ms p(95)=3ms   p(99)=8ms
http_req_duration..............: avg=85ms  min=20ms med=75ms  max=450ms p(95)=140ms p(99)=220ms
http_req_failed................: 0.13%  ✓ 39       ✗ 29961
http_req_receiving.............: avg=0.3ms min=0µs  med=0.2ms max=15ms  p(95)=0.8ms p(99)=2ms
http_req_sending...............: avg=0.2ms min=0µs  med=0.1ms max=12ms  p(95)=0.5ms p(99)=1.5ms
http_req_tls_handshaking.......: avg=0ms   min=0µs  med=0µs   max=0µs   p(95)=0µs   p(99)=0µs
http_req_waiting...............: avg=84.5ms min=20ms med=74.5ms max=445ms p(95)=139ms p(99)=218ms
http_reqs......................: 30000  50/s
iteration_duration.............: avg=2.1s  min=1s   med=2s    max=5s    p(95)=3.5s  p(99)=4.2s
iterations.....................: 30000  50/s
vus............................: 1000   min=1      max=1000
vus_max........................: 1000   min=1000   max=1000
```

## Identifying Bottlenecks

### CPU Bottleneck

**Symptoms**:
- High CPU usage (> 90%)
- Increasing response times as load increases
- System becomes unresponsive

**Solutions**:
```bash
# Profile Python code
python -m cProfile -o profile.stats src/decentralized_did/api/server.py

# Analyze with snakeviz
pip install snakeviz
snakeviz profile.stats

# Optimize hot paths:
# - Use async/await for I/O operations
# - Implement caching for expensive computations
# - Use more efficient algorithms
```

### Memory Bottleneck

**Symptoms**:
- Increasing memory usage over time
- Out of memory errors
- System starts swapping

**Solutions**:
```bash
# Profile memory usage
pip install memory_profiler
python -m memory_profiler src/decentralized_did/api/server.py

# Check for memory leaks
pip install objgraph
# Add to code:
# import objgraph
# objgraph.show_most_common_types()

# Solutions:
# - Implement proper connection pooling
# - Clear caches periodically
# - Use generators for large datasets
```

### Network Bottleneck

**Symptoms**:
- High network latency
- Packet loss
- Connection timeouts

**Solutions**:
```bash
# Check network stats
netstat -s | grep -i error
ifconfig | grep -i error

# Monitor bandwidth
iftop -i eth0

# Solutions:
# - Optimize payload sizes (compression)
# - Use HTTP/2 or HTTP/3
# - Implement CDN for static assets
```

### Database Bottleneck

**Symptoms**:
- Slow query times
- Connection pool exhaustion
- Lock contention

**Solutions**:
```bash
# Profile database queries
# Add query logging in production

# Solutions:
# - Add indexes on frequently queried fields
# - Implement query caching
# - Use connection pooling
# - Optimize slow queries
```

## Performance Optimization Tips

1. **Use Production Server**: Run with Gunicorn or similar ASGI server
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.decentralized_did.api.server:app
   ```

2. **Enable Compression**: Reduce payload sizes
   ```python
   from fastapi.middleware.gzip import GZipMiddleware
   app.add_middleware(GZipMiddleware, minimum_size=1000)
   ```

3. **Implement Caching**: Cache expensive computations
   ```python
   from functools import lru_cache

   @lru_cache(maxsize=1000)
   def expensive_computation(param):
       # ...
   ```

4. **Optimize Logging**: Reduce logging overhead in production
   ```python
   # Use structured logging
   # Log at INFO level or higher in production
   # Use async logging for high-throughput
   ```

5. **Connection Pooling**: Reuse database connections
   ```python
   # Configure connection pool size
   # Set max connections based on load
   ```

## CI/CD Integration

Add to `.github/workflows/load-test.yml`:

```yaml
name: Load Test

on:
  workflow_dispatch:
    inputs:
      users:
        description: 'Number of concurrent users'
        required: true
        default: '100'
      duration:
        description: 'Test duration (e.g., 5m, 10m)'
        required: true
        default: '5m'

jobs:
  load-test:
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
        pip install locust

    - name: Start API server
      run: |
        uvicorn src.decentralized_did.api.server:app --host 0.0.0.0 --port 8000 &
        sleep 5

    - name: Run load test
      run: |
        locust -f tests/load/locustfile.py \
          --host=http://localhost:8000 \
          --users ${{ github.event.inputs.users }} \
          --spawn-rate 10 \
          --run-time ${{ github.event.inputs.duration }} \
          --headless \
          --html reports/load-test-report.html \
          --csv reports/load-test

    - name: Upload results
      uses: actions/upload-artifact@v4
      with:
        name: load-test-results
        path: reports/
```

## Next Steps

After completing load testing:

1. Review performance metrics against targets
2. Identify and resolve bottlenecks
3. Optimize code based on profiling results
4. Run tests again to validate improvements
5. Document performance characteristics
6. Proceed to [Performance Benchmarking Guide](./performance-benchmarking.md)
7. Complete [Security Testing Checklist](./security-testing-checklist.md)

## References

- [Locust Documentation](https://docs.locust.io/)
- [k6 Documentation](https://k6.io/docs/)
- [Load Testing Best Practices](https://loadtesting.best/)
- [FastAPI Performance Tips](https://fastapi.tiangolo.com/deployment/concepts/)
