# Performance Benchmarking Guide

This guide explains how to benchmark and optimize the performance of the Decentralized DID API servers to meet target response times.

## Overview

Performance benchmarking helps establish baseline metrics and identify optimization opportunities. This guide covers:

- Benchmarking methodology and tools
- Target performance metrics
- Profiling CPU, memory, and I/O
- Optimization techniques
- Continuous performance monitoring

## Performance Targets

| Operation | P50 | P95 | P99 | Max |
|-----------|-----|-----|-----|-----|
| Biometric Enrollment | < 100ms | < 150ms | < 300ms | < 500ms |
| Biometric Verification | < 50ms | < 75ms | < 150ms | < 300ms |
| Health Check | < 10ms | < 20ms | < 50ms | < 100ms |
| DID Generation | < 200ms | < 300ms | < 500ms | < 1000ms |

**System Requirements**:
- Throughput: > 1000 requests/second
- CPU Usage: < 70% under normal load
- Memory: < 2GB for 1000 concurrent users
- Error Rate: < 0.1%

## Benchmarking Tools

### 1. Apache Bench (ab)

Quick and simple HTTP benchmarking:

```bash
# Install
sudo apt-get install apache2-utils  # Linux
brew install ab                      # macOS

# Simple benchmark (100 requests, 10 concurrent)
ab -n 100 -c 10 http://localhost:8000/health

# POST request benchmark
ab -n 100 -c 10 -p payload.json -T application/json http://localhost:8000/api/v1/did/verify

# Create payload.json
cat > payload.json << EOF
{
  "wallet_address": "addr_test1qqz",
  "biometric_hash": "abcd1234...",
  "timestamp": 1697500000
}
EOF
```

### 2. wrk - High-Performance HTTP Benchmarking

More powerful than ab, with Lua scripting support:

```bash
# Install
sudo apt-get install wrk  # Linux
brew install wrk          # macOS

# Simple benchmark (10 threads, 100 connections, 30 seconds)
wrk -t10 -c100 -d30s http://localhost:8000/health

# With custom headers
wrk -t10 -c100 -d30s -H "X-API-Key: your-api-key" http://localhost:8000/health

# POST request with Lua script
wrk -t10 -c100 -d30s -s verify.lua http://localhost:8000/api/v1/did/verify

# Create verify.lua
cat > verify.lua << 'EOF'
wrk.method = "POST"
wrk.headers["Content-Type"] = "application/json"
wrk.body = '{"wallet_address":"addr_test1","biometric_hash":"hash123","timestamp":1697500000}'
EOF
```

### 3. Python Profiling Tools

#### cProfile - CPU Profiling

```bash
# Profile the API server
python -m cProfile -o profile.stats -m uvicorn src.decentralized_did.api.server:app --host 0.0.0.0 --port 8000

# Run some requests in another terminal
curl -X POST http://localhost:8000/api/v1/did/verify -H "Content-Type: application/json" -d '{"wallet_address":"addr","biometric_hash":"hash","timestamp":1697500000}'

# Stop server (Ctrl+C) and analyze
python -m pstats profile.stats
# In pstats shell:
# > sort cumulative
# > stats 20

# Or use snakeviz for visual analysis
pip install snakeviz
snakeviz profile.stats
```

#### line_profiler - Line-by-Line Profiling

```bash
# Install
pip install line_profiler

# Add @profile decorator to functions you want to profile
# In your code:
# @profile
# def generate_did(commitment: str) -> str:
#     ...

# Run with kernprof
kernprof -l -v src/decentralized_did/api/server.py

# View results
python -m line_profiler server.py.lprof
```

#### memory_profiler - Memory Usage

```bash
# Install
pip install memory_profiler

# Add @profile decorator
# In your code:
# from memory_profiler import profile
# @profile
# def expensive_function():
#     ...

# Run with memory profiler
python -m memory_profiler src/decentralized_did/api/server.py

# Or use mprof for graphical view
mprof run python -m uvicorn src.decentralized_did.api.server:app
mprof plot
```

### 4. py-spy - Statistical Profiler (No Code Changes)

```bash
# Install
pip install py-spy

# Profile a running process
py-spy top --pid <PID>

# Record flame graph
py-spy record -o profile.svg --pid <PID>

# Or start with profiling
py-spy record -o profile.svg -- python -m uvicorn src.decentralized_did.api.server:app
```

## Benchmarking Methodology

### 1. Baseline Benchmark

Establish baseline performance before optimization:

```bash
#!/bin/bash
# baseline-benchmark.sh

echo "=== Baseline Performance Benchmark ==="
echo "Starting API server..."

# Start server in background
python -m uvicorn src.decentralized_did.api.server:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!
sleep 5

echo "Running benchmarks..."

# Health check benchmark
echo "1. Health Check:"
wrk -t4 -c50 -d30s http://localhost:8000/health | tee results/baseline-health.txt

# Verification benchmark
echo "2. Biometric Verification:"
wrk -t4 -c50 -d30s -s scripts/verify.lua http://localhost:8000/api/v1/did/verify | tee results/baseline-verify.txt

# Enrollment benchmark
echo "3. Biometric Enrollment:"
wrk -t4 -c50 -d30s -s scripts/enroll.lua http://localhost:8000/api/v1/did/enroll | tee results/baseline-enroll.txt

# Stop server
kill $SERVER_PID

echo "=== Baseline benchmark complete ==="
echo "Results saved to results/"
```

### 2. Comparison Benchmark

Compare performance after optimization:

```bash
#!/bin/bash
# compare-benchmark.sh

echo "=== Performance Comparison ==="

# Run baseline
./baseline-benchmark.sh

# Apply optimization
echo "Applying optimization..."
# (Make your code changes here)

# Run optimized benchmark
echo "Running optimized benchmark..."
# (Same commands as baseline but save to different files)

# Compare results
echo "=== Comparison Results ==="
echo "Health Check:"
echo "  Baseline: $(grep 'Requests/sec' results/baseline-health.txt)"
echo "  Optimized: $(grep 'Requests/sec' results/optimized-health.txt)"
```

### 3. Continuous Benchmarking

Track performance over time:

```bash
#!/bin/bash
# continuous-benchmark.sh

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
RESULTS_DIR="results/$TIMESTAMP"

mkdir -p "$RESULTS_DIR"

# Run benchmarks
wrk -t4 -c50 -d30s http://localhost:8000/health > "$RESULTS_DIR/health.txt"
wrk -t4 -c50 -d30s -s scripts/verify.lua http://localhost:8000/api/v1/did/verify > "$RESULTS_DIR/verify.txt"

# Extract key metrics
echo "$TIMESTAMP,$(grep 'Requests/sec' $RESULTS_DIR/health.txt | awk '{print $2}')" >> metrics.csv

# Plot trends
python scripts/plot-metrics.py metrics.csv
```

## Profiling Workflow

### Step 1: Identify Hot Paths

```bash
# Profile with py-spy
py-spy record -o flamegraph.svg -- python -m uvicorn src.decentralized_did.api.server:app &
SERVER_PID=$!

# Generate load
wrk -t4 -c50 -d60s http://localhost:8000/api/v1/did/verify

# Stop profiling
kill $SERVER_PID

# Open flamegraph.svg in browser
```

**Analysis**:
- Look for wide bars (functions taking most time)
- Check for unexpected function calls
- Identify opportunities for caching or optimization

### Step 2: Profile Specific Functions

```python
# Add to src/decentralized_did/api/endpoints.py
from line_profiler import profile

@profile
def generate_did_endpoint(request: DIDRequest):
    # ... your code ...
    pass
```

```bash
# Run with line profiler
kernprof -l -v src/decentralized_did/api/server.py
```

**Analysis**:
- Find lines with high % Time
- Look for loops or repeated operations
- Identify I/O bottlenecks

### Step 3: Memory Profiling

```python
# Add to your code
from memory_profiler import profile

@profile
def process_biometric_data(data: bytes):
    # ... your code ...
    pass
```

```bash
# Run memory profiler
python -m memory_profiler src/decentralized_did/api/server.py
```

**Analysis**:
- Look for increasing memory usage
- Check for objects not being released
- Identify large allocations

## Optimization Techniques

### 1. Async/Await for I/O Operations

```python
# Before (blocking)
def verify_biometric(wallet: str, bio_hash: str):
    result = database.query(wallet)  # Blocks
    return result

# After (async)
async def verify_biometric(wallet: str, bio_hash: str):
    result = await database.async_query(wallet)  # Non-blocking
    return result
```

### 2. Caching Expensive Computations

```python
from functools import lru_cache
import hashlib

# Cache DID generation results
@lru_cache(maxsize=1000)
def generate_did_cached(commitment: str) -> str:
    # Expensive computation
    return hashlib.sha256(commitment.encode()).hexdigest()

# Or use Redis for distributed caching
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_cached_did(commitment: str) -> str | None:
    cached = redis_client.get(f"did:{commitment}")
    return cached.decode() if cached else None

def set_cached_did(commitment: str, did: str, ttl: int = 3600):
    redis_client.setex(f"did:{commitment}", ttl, did)
```

### 3. Database Query Optimization

```python
# Before: N+1 query problem
def get_users_with_dids():
    users = session.query(User).all()
    for user in users:
        user.did = session.query(DID).filter_by(user_id=user.id).first()
    return users

# After: Eager loading
def get_users_with_dids():
    return session.query(User).options(
        joinedload(User.did)
    ).all()

# Add indexes for frequently queried fields
# CREATE INDEX idx_wallet_address ON dids(wallet_address);
# CREATE INDEX idx_commitment ON dids(commitment);
```

### 4. Connection Pooling

```python
# Configure database connection pool
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    "postgresql://user:pass@localhost/db",
    poolclass=QueuePool,
    pool_size=20,          # Number of connections to keep
    max_overflow=10,       # Additional connections under load
    pool_timeout=30,       # Timeout waiting for connection
    pool_recycle=3600,     # Recycle connections after 1 hour
)
```

### 5. Response Compression

```python
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress responses > 1KB
```

### 6. Batch Processing

```python
# Before: Process one at a time
async def verify_multiple(requests: List[VerifyRequest]):
    results = []
    for req in requests:
        result = await verify_single(req)
        results.append(result)
    return results

# After: Batch processing
async def verify_multiple(requests: List[VerifyRequest]):
    import asyncio
    tasks = [verify_single(req) for req in requests]
    results = await asyncio.gather(*tasks)
    return results
```

### 7. Optimize Imports and Startup

```python
# Before: Import everything at module level
import numpy as np
import pandas as pd
import tensorflow as tf

def rarely_used_function():
    return np.array([1, 2, 3])

# After: Lazy import
def rarely_used_function():
    import numpy as np  # Only import when needed
    return np.array([1, 2, 3])
```

### 8. Use Efficient Data Structures

```python
# Before: List for membership testing (O(n))
enrolled_users = []  # List
if user_id in enrolled_users:  # O(n)
    pass

# After: Set for membership testing (O(1))
enrolled_users = set()  # Set
if user_id in enrolled_users:  # O(1)
    pass

# Use appropriate data structures
# - dict for key-value lookups: O(1)
# - set for membership tests: O(1)
# - list for ordered data: O(n)
# - deque for queue operations: O(1)
```

## Performance Monitoring

### 1. Application Metrics

```python
# Add Prometheus metrics
from prometheus_client import Counter, Histogram, make_asgi_app

# Metrics
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')

# Middleware to collect metrics
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    with request_duration.time():
        response = await call_next(request)
    request_count.labels(method=request.method, endpoint=request.url.path).inc()
    return response

# Expose metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

### 2. Resource Monitoring

```bash
# Monitor CPU and memory
#!/bin/bash
# monitor.sh

PID=$(pgrep -f "uvicorn.*server:app")

while true; do
    CPU=$(ps -p $PID -o %cpu --no-headers)
    MEM=$(ps -p $PID -o %mem --no-headers)
    TIMESTAMP=$(date +%Y-%m-%d\ %H:%M:%S)
    echo "$TIMESTAMP,$CPU,$MEM" >> monitoring.csv
    sleep 5
done
```

### 3. Distributed Tracing

```python
# Add OpenTelemetry instrumentation
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Initialize tracer
tracer = trace.get_tracer(__name__)

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# Add custom spans
@app.post("/api/v1/did/verify")
async def verify_endpoint(request: VerifyRequest):
    with tracer.start_as_current_span("verify_biometric"):
        result = await verify_biometric(request)
    return result
```

## Benchmarking Checklist

- [ ] Establish baseline metrics (before optimization)
- [ ] Profile CPU usage (identify hot paths)
- [ ] Profile memory usage (check for leaks)
- [ ] Profile I/O operations (database, network)
- [ ] Run load tests (1000+ concurrent users)
- [ ] Measure response times (P50, P95, P99)
- [ ] Check error rates (< 0.1%)
- [ ] Monitor resource usage (CPU, memory, network)
- [ ] Apply optimizations (one at a time)
- [ ] Re-benchmark after each optimization
- [ ] Document performance improvements
- [ ] Set up continuous monitoring

## Performance Targets Validation

Create `tests/test_performance.py`:

```python
"""Performance validation tests"""

import time
import pytest
from fastapi.testclient import TestClient
from src.decentralized_did.api.server import app


client = TestClient(app)


@pytest.mark.performance
def test_health_check_performance():
    """Health check should respond in < 20ms (P95)"""
    times = []
    for _ in range(100):
        start = time.perf_counter()
        response = client.get("/health")
        duration = (time.perf_counter() - start) * 1000  # ms
        times.append(duration)
        assert response.status_code == 200

    p95 = sorted(times)[94]  # 95th percentile
    assert p95 < 20, f"P95 response time {p95:.2f}ms exceeds 20ms target"


@pytest.mark.performance
def test_verification_performance():
    """Verification should respond in < 75ms (P95)"""
    times = []
    payload = {
        "wallet_address": "addr_test1",
        "biometric_hash": "hash123",
        "timestamp": int(time.time())
    }

    for _ in range(100):
        start = time.perf_counter()
        response = client.post("/api/v1/did/verify", json=payload)
        duration = (time.perf_counter() - start) * 1000  # ms
        times.append(duration)

    p95 = sorted(times)[94]  # 95th percentile
    assert p95 < 75, f"P95 response time {p95:.2f}ms exceeds 75ms target"
```

Run performance tests:

```bash
pytest tests/test_performance.py -v -m performance
```

## Troubleshooting Performance Issues

### Issue: High CPU Usage

**Diagnosis**:
```bash
# Profile CPU
py-spy top --pid $(pgrep -f uvicorn)
```

**Solutions**:
- Optimize hot path functions
- Use caching for expensive computations
- Implement async/await for I/O operations
- Scale horizontally (add more workers)

### Issue: High Memory Usage

**Diagnosis**:
```bash
# Profile memory
mprof run python -m uvicorn src.decentralized_did.api.server:app
mprof plot
```

**Solutions**:
- Fix memory leaks (use weak references)
- Implement cache eviction policies
- Use generators for large datasets
- Limit connection pool sizes

### Issue: Slow Response Times

**Diagnosis**:
```bash
# Profile with line profiler
kernprof -l -v src/decentralized_did/api/server.py
```

**Solutions**:
- Add database indexes
- Optimize queries (eager loading)
- Implement caching
- Use CDN for static assets
- Enable compression

## Next Steps

After completing performance benchmarking:

1. Document baseline metrics
2. Identify top 3 optimization opportunities
3. Apply optimizations incrementally
4. Re-benchmark after each change
5. Set up continuous monitoring
6. Complete [Security Testing Checklist](./security-testing-checklist.md)

## References

- [Python Profiling Tools](https://docs.python.org/3/library/profile.html)
- [FastAPI Performance](https://fastapi.tiangolo.com/deployment/concepts/)
- [wrk Documentation](https://github.com/wg/wrk)
- [py-spy Documentation](https://github.com/benfred/py-spy)
- [Flame Graphs](https://www.brendangregg.com/flamegraphs.html)
