# 🚀 Next Steps: Production Hardening & Hardware Integration

**Date**: October 12, 2025  
**Current Status**: ✅ Demo-Wallet Integration Complete (10/10 tasks)  
**Project Phase**: Transitioning from Mock Mode → Production Ready  

---

## Executive Summary

All core biometric DID functionality is complete and working in **mock mode**. The system is fully functional end-to-end with synthetic data. The next phase focuses on:

1. **Hardware Integration** - Connect real fingerprint sensors
2. **CLI Integration** - Upgrade from mock API to real Python CLI
3. **Production Hardening** - Security, performance, monitoring
4. **Testing & QA** - Automated tests, security audit
5. **Documentation** - User guides, API reference

---

## Immediate Next Steps (This Week)

### 1. Update Project Roadmap ✅ (5 minutes)

**Action**: Update `docs/roadmap.md` to reflect completion status

**Changes needed**:
```markdown
## Current Sprint (Oct 2025)
- ✅ **COMPLETED**: Integrate live CLI enrollment/verification flows into demo-wallet UI
  - Backend API server implemented (FastAPI + mock data)
  - Full enrollment flow (10 fingerprints)
  - Verification flows (unlock + transaction signing)
  - Mock mode fully functional
  - Ready for real CLI/sensor integration
```

**Status**: Ready to update

---

### 2. Hardware Purchase & Setup (1-2 days)

**Goal**: Acquire and test real fingerprint sensor hardware

#### Option A: USB Fingerprint Sensor (Recommended)

**Shopping List**:
- **Eikon Touch 700** USB sensor: $25-30 ([Amazon](https://amazon.com))
- OR **ZhongZhi USB FP Reader**: $15-20 ([AliExpress](https://aliexpress.com))
- OR **Futronic FS88**: $40 ([Amazon](https://amazon.com))

**Purchase Link References**:
- Search: "USB fingerprint sensor libfprint compatible"
- Verify: Check [libfprint supported devices](https://fprint.freedesktop.org/supported-devices.html)

**Setup Steps** (Ubuntu/Debian):
```bash
# 1. Install libfprint
sudo apt-get update
sudo apt-get install -y libfprint-2 libfprint-dev python3-fprint libusb-1.0-0-dev

# 2. Add user to plugdev group
sudo usermod -a -G plugdev $USER

# 3. Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# 4. Test sensor detection
fprintd-list $USER
lsusb | grep -i finger

# 5. Install NBIS (minutiae extraction)
cd /tmp
git clone https://github.com/lessandro/nbis
cd nbis
./setup.sh /usr/local --without-X11
make
sudo make install

# 6. Verify installation
which mindtct  # Should output: /usr/local/bin/mindtct

# 7. Test NBIS
mindtct --help
```

**Expected Time**: 2-3 hours (including shipping wait time)

---

#### Option B: WebAuthn (Browser-Native) - Quick Win

**Goal**: Add verification without hardware purchase

**Implementation** (2-3 hours):
```typescript
// In demo-wallet/src/core/biometric/fingerprintCaptureService.ts

async captureWithWebAuthn(fingerId: string): Promise<FingerprintCapture> {
  if (!window.PublicKeyCredential) {
    throw new Error('WebAuthn not supported in this browser');
  }
  
  try {
    const credential = await navigator.credentials.create({
      publicKey: {
        challenge: crypto.getRandomValues(new Uint8Array(32)),
        rp: { name: "Biometric DID Wallet" },
        user: {
          id: crypto.getRandomValues(new Uint8Array(16)),
          name: fingerId,
          displayName: `Finger: ${fingerId}`
        },
        pubKeyCredParams: [{ alg: -7, type: "public-key" }],
        authenticatorSelection: {
          authenticatorAttachment: "platform", // Built-in sensor
          userVerification: "required"
        }
      }
    });
    
    // Note: WebAuthn doesn't provide raw minutiae
    // This is suitable for VERIFICATION only, not enrollment
    return {
      fingerId,
      quality: 1.0,
      minutiae: [], // WebAuthn doesn't expose raw data
      timestamp: Date.now(),
      source: 'webauthn'
    };
  } catch (error) {
    throw new Error(`WebAuthn capture failed: ${error.message}`);
  }
}
```

**Use Case**: Unlock wallet with Touch ID / Face ID / Windows Hello  
**Limitation**: Can't generate DID (no raw minutiae), verification only

**Status**: Can implement immediately, no hardware needed

---

### 3. Upgrade API Server to Real CLI (1 day)

**Goal**: Replace mock data with real Python CLI calls

**File to update**: `api_server_mock.py` → `api_server.py`

**Implementation**:

```python
# In api_server.py (upgrade from mock)

import subprocess
import json
import tempfile
from pathlib import Path

class BiometricCLI:
    """Real Python CLI integration"""
    
    def __init__(self, cli_path: str = "python -m decentralized_did.cli"):
        self.cli_path = cli_path
    
    async def generate(self, fingers: List[FingerData], wallet_address: str, 
                      storage: str = "inline") -> GenerateResponse:
        """Call real CLI generate command"""
        
        # Write input to temp file
        input_data = {
            "version": "1.0",
            "fingers": [
                {
                    "finger_id": f.finger_id,
                    "minutiae": [[m.x, m.y, m.angle, m.type] for m in f.minutiae]
                }
                for f in fingers
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(input_data, f)
            input_file = f.name
        
        try:
            # Call CLI
            cmd = [
                *self.cli_path.split(),
                'generate',
                '--input', input_file,
                '--wallet', wallet_address,
                '--storage', storage,
                '--format', 'json',
                '--json-output'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )
            
            # Parse output
            output = json.loads(result.stdout)
            
            return GenerateResponse(
                did=output['did'],
                id_hash=output['id_hash'],
                helpers=output['helpers'],
                metadata=output['metadata'],
                storage_reference=output.get('storage_reference')
            )
            
        finally:
            Path(input_file).unlink(missing_ok=True)
    
    async def verify(self, fingers: List[FingerData], helpers: List[HelperDataEntry],
                     expected_id_hash: str) -> VerifyResponse:
        """Call real CLI verify command"""
        
        # Similar implementation for verify command
        # ... (see api_server_mock.py for structure)
        pass

# Update endpoints to use real CLI
cli = BiometricCLI()

@app.post("/api/biometric/generate")
async def generate_did(request: GenerateRequest):
    """Generate DID using real Python CLI"""
    try:
        result = await cli.generate(
            fingers=request.fingers,
            wallet_address=request.wallet_address,
            storage=request.storage
        )
        return result
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"CLI generation failed: {e.stderr}"
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="CLI generation timed out (>30s)"
        )
```

**Testing**:
```bash
# 1. Start upgraded API server
python api_server.py

# 2. Test with curl
curl -X POST http://localhost:8000/api/biometric/generate \
  -H "Content-Type: application/json" \
  -d @test_input.json

# 3. Verify real CLI was called
# Should see Python CLI output in logs
```

**Expected Time**: 4-6 hours (including testing)

---

### 4. Integrate libfprint Sensor Capture (1-2 days)

**Goal**: Capture real fingerprints from USB sensor

**File to create**: `api_server_sensors.py` (sensor capture module)

**Implementation**:

```python
# api_server_sensors.py

import fprint
import numpy as np
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple

class FingerprintSensor:
    """libfprint sensor integration"""
    
    def __init__(self):
        try:
            self.ctx = fprint.Context()
            self.devices = list(self.ctx.devices())
            
            if not self.devices:
                print("⚠️  No fingerprint devices found. Using mock mode.")
                self.mock_mode = True
            else:
                print(f"✅ Found {len(self.devices)} fingerprint device(s):")
                for i, dev in enumerate(self.devices):
                    print(f"   {i+1}. {dev.name} (driver: {dev.driver})")
                self.mock_mode = False
        except Exception as e:
            print(f"⚠️  Failed to initialize libfprint: {e}")
            self.mock_mode = True
    
    def capture_fingerprint(self, finger_id: str) -> np.ndarray:
        """Capture fingerprint image from USB sensor"""
        
        if self.mock_mode:
            # Fallback to mock data
            return self._generate_mock_image()
        
        device = self.devices[0]
        device.open()
        
        try:
            print(f"📍 Place {finger_id} on sensor...")
            
            # Capture image
            image = device.enroll_image()
            
            # Convert to numpy array
            img_array = np.frombuffer(image.data, dtype=np.uint8)
            img_array = img_array.reshape((image.height, image.width))
            
            print(f"✅ Captured {finger_id}: {image.width}x{image.height} pixels")
            
            return img_array
            
        finally:
            device.close()
    
    def extract_minutiae(self, image: np.ndarray) -> List[Tuple[float, float, float]]:
        """Extract minutiae using NBIS mindtct"""
        
        # Save image to temp file
        with tempfile.NamedTemporaryFile(suffix='.pgm', delete=False) as f:
            # Convert numpy array to PGM format
            height, width = image.shape
            f.write(f"P5\n{width} {height}\n255\n".encode())
            f.write(image.tobytes())
            img_path = f.name
        
        try:
            # Run NBIS mindtct
            output_prefix = img_path.replace('.pgm', '')
            
            result = subprocess.run(
                ['mindtct', img_path, output_prefix],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                raise Exception(f"NBIS extraction failed: {result.stderr}")
            
            # Parse XYT file (minutiae coordinates)
            minutiae = []
            xyt_file = f"{output_prefix}.xyt"
            
            with open(xyt_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split()
                        if len(parts) >= 3:
                            x, y, theta = map(float, parts[:3])
                            # Normalize to 0-1 range and 0-360 degrees
                            minutiae.append((x / 500.0, y / 500.0, theta))
            
            # Cleanup NBIS output files
            for ext in ['.xyt', '.brw', '.dm', '.hcm', '.lcm', '.lfm', '.min', '.qm']:
                Path(f"{output_prefix}{ext}").unlink(missing_ok=True)
            
            print(f"✅ Extracted {len(minutiae)} minutiae points")
            
            return minutiae
            
        finally:
            Path(img_path).unlink(missing_ok=True)
    
    def capture_and_extract(self, finger_id: str) -> List[List[float]]:
        """Capture fingerprint and extract minutiae (one call)"""
        
        if self.mock_mode:
            return self._generate_mock_minutiae(finger_id)
        
        # Capture image
        image = self.capture_fingerprint(finger_id)
        
        # Extract minutiae
        minutiae = self.extract_minutiae(image)
        
        # Convert to format expected by CLI
        return [[x, y, angle] for x, y, angle in minutiae]
    
    def _generate_mock_minutiae(self, finger_id: str) -> List[List[float]]:
        """Generate mock minutiae for testing"""
        import hashlib
        import random
        
        # Deterministic seed based on finger_id
        seed = int(hashlib.md5(finger_id.encode()).hexdigest()[:8], 16)
        random.seed(seed)
        
        # Generate 20-40 minutiae points
        num_points = random.randint(20, 40)
        minutiae = []
        
        for _ in range(num_points):
            x = random.random()
            y = random.random()
            angle = random.random() * 360
            minutiae.append([x, y, angle])
        
        return minutiae

# Global sensor instance
fingerprint_sensor = FingerprintSensor()

# Add new endpoint to API server
@app.post("/api/biometric/capture")
async def capture_fingerprint(request: dict):
    """Capture fingerprint from hardware sensor"""
    try:
        finger_id = request.get('finger_id', 'unknown')
        minutiae = fingerprint_sensor.capture_and_extract(finger_id)
        
        return {
            "finger_id": finger_id,
            "minutiae": minutiae,
            "quality": 0.85,  # TODO: Implement quality assessment
            "sensor_type": "libfprint" if not fingerprint_sensor.mock_mode else "mock"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Update demo-wallet** to call capture endpoint:

```typescript
// In fingerprintCaptureService.ts

async captureFingerprint(fingerId: FingerId): Promise<FingerprintCapture> {
  const API_BASE_URL = process.env.BIOMETRIC_API_URL || "http://localhost:8000";
  
  if (process.env.NODE_ENV === "development" && !process.env.USE_REAL_SENSOR) {
    // Use mock data
    return this.captureMockFingerprint(fingerId);
  }
  
  try {
    // Call real sensor via API
    const response = await fetch(`${API_BASE_URL}/api/biometric/capture`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ finger_id: fingerId }),
    });
    
    if (!response.ok) {
      throw new Error(`Capture failed: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    return {
      fingerId: data.finger_id,
      minutiae: data.minutiae.map(([x, y, angle]: number[]) => ({
        x, y, angle, type: 'ending' // Default type
      })),
      quality: data.quality,
      timestamp: Date.now(),
    };
  } catch (error) {
    console.error("Real sensor capture failed, falling back to mock:", error);
    return this.captureMockFingerprint(fingerId);
  }
}
```

**Testing**:
```bash
# 1. Start API server with sensor support
python api_server.py  # Now includes sensor capture

# 2. Test sensor capture
curl -X POST http://localhost:8000/api/biometric/capture \
  -H "Content-Type: application/json" \
  -d '{"finger_id":"left_thumb"}'
# Should prompt "Place left_thumb on sensor..."

# 3. Start demo-wallet with real sensor
cd demo-wallet
export USE_REAL_SENSOR=true
export BIOMETRIC_API_URL=http://localhost:8000
npm run dev

# 4. Test enrollment with real sensor
# Navigate to enrollment → Place fingers on sensor when prompted
```

**Expected Time**: 8-12 hours (including hardware setup and testing)

---

## Production Hardening (1-2 Weeks)

### 5. Security Hardening

**Goals**:
- Add rate limiting to API endpoints
- Implement authentication/authorization
- Add audit logging
- Enable HTTPS

**Implementation**:

```python
# Add to api_server.py

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Audit logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/biometric-api/audit.log'),
        logging.StreamHandler()
    ]
)
audit_logger = logging.getLogger('audit')

# Add rate limits to endpoints
@app.post("/api/biometric/generate")
@limiter.limit("10/minute")  # Max 10 enrollments per minute
async def generate_did(request: GenerateRequest):
    audit_logger.info(f"Generate request from {get_remote_address()}")
    # ... existing code ...

@app.post("/api/biometric/verify")
@limiter.limit("30/minute")  # Max 30 verifications per minute
async def verify_biometric(request: VerifyRequest):
    audit_logger.info(f"Verify request from {get_remote_address()}")
    # ... existing code ...

# Add authentication (API key)
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != os.getenv("BIOMETRIC_API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

# Protect endpoints
@app.post("/api/biometric/generate", dependencies=[Depends(verify_api_key)])
async def generate_did(request: GenerateRequest):
    # ... existing code ...
```

**Configuration**:
```bash
# .env file
BIOMETRIC_API_KEY=your-secret-key-here
RATE_LIMIT_ENABLED=true
AUDIT_LOG_PATH=/var/log/biometric-api/audit.log
```

**Expected Time**: 1-2 days

---

### 6. Performance Optimization

**Goals**:
- Add caching for repeated operations
- Optimize CLI execution
- Add connection pooling
- Monitor performance metrics

**Implementation**:

```python
# Add caching
from functools import lru_cache
import redis

# Redis cache for helper data
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

@app.post("/api/biometric/verify")
async def verify_biometric(request: VerifyRequest):
    # Check cache for recent verification
    cache_key = f"verify:{request.expected_id_hash}:{hash(str(request.fingers))}"
    cached_result = redis_client.get(cache_key)
    
    if cached_result:
        return json.loads(cached_result)
    
    # Perform verification
    result = await cli.verify(...)
    
    # Cache result for 5 minutes
    redis_client.setex(cache_key, 300, json.dumps(result))
    
    return result

# Add performance monitoring
from prometheus_client import Counter, Histogram, start_http_server

# Metrics
generate_requests = Counter('biometric_generate_requests_total', 'Total generate requests')
generate_duration = Histogram('biometric_generate_duration_seconds', 'Generate request duration')
verify_requests = Counter('biometric_verify_requests_total', 'Total verify requests')
verify_duration = Histogram('biometric_verify_duration_seconds', 'Verify request duration')

@app.post("/api/biometric/generate")
async def generate_did(request: GenerateRequest):
    generate_requests.inc()
    
    with generate_duration.time():
        result = await cli.generate(...)
    
    return result

# Start Prometheus metrics server
start_http_server(9090)
```

**Expected Time**: 2-3 days

---

### 7. Automated Testing

**Goals**:
- Add unit tests for API endpoints
- Add integration tests with real CLI
- Add E2E tests with demo-wallet
- Set up CI/CD pipeline

**Implementation**:

```python
# tests/test_api.py

import pytest
from fastapi.testclient import TestClient
from api_server import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_generate_endpoint():
    request_data = {
        "fingers": [
            {
                "finger_id": "left_thumb",
                "minutiae": [[0.5, 0.5, 90, "ending"] for _ in range(20)]
            }
        ],
        "wallet_address": "addr1test123",
        "storage": "inline"
    }
    
    response = client.post("/api/biometric/generate", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "did" in data
    assert data["did"].startswith("did:cardano:")
    assert "helpers" in data

def test_verify_endpoint():
    # First generate
    generate_response = client.post("/api/biometric/generate", json={...})
    did_data = generate_response.json()
    
    # Then verify
    verify_response = client.post("/api/biometric/verify", json={
        "fingers": [...],  # Same fingers
        "helpers": did_data["helpers"],
        "expected_id_hash": did_data["id_hash"]
    })
    
    assert verify_response.status_code == 200
    assert verify_response.json()["success"] is True

def test_rate_limiting():
    # Make 11 requests (limit is 10/minute)
    for i in range(11):
        response = client.post("/api/biometric/generate", json={...})
        if i < 10:
            assert response.status_code == 200
        else:
            assert response.status_code == 429  # Rate limit exceeded

# Run tests
# pytest tests/test_api.py -v
```

**CI/CD Pipeline** (GitHub Actions):

```yaml
# .github/workflows/test-api.yml

name: API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r api_requirements.txt
        pip install pytest pytest-cov
    
    - name: Run API tests
      run: |
        pytest tests/test_api.py -v --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

**Expected Time**: 3-4 days

---

### 8. Documentation & User Guides

**Goals**:
- Write production deployment guide
- Create API reference documentation
- Write user manual for enrollment/verification
- Create troubleshooting guide

**Documents to create**:

1. **`docs/deployment/production-deployment.md`**
   - Docker deployment
   - Nginx reverse proxy
   - SSL/TLS configuration
   - Environment variables
   - Monitoring setup

2. **`docs/api/api-reference.md`**
   - Complete endpoint documentation
   - Request/response schemas
   - Error codes
   - Rate limits
   - Authentication

3. **`docs/user-guide/enrollment.md`**
   - Step-by-step enrollment guide
   - Quality tips
   - Troubleshooting
   - Best practices

4. **`docs/user-guide/verification.md`**
   - Unlock wallet guide
   - Transaction signing guide
   - Recovery options
   - Security tips

**Expected Time**: 2-3 days

---

## Timeline Summary

### Week 1: Hardware & Core Integration
- **Day 1**: Purchase hardware ($25), update roadmap, implement WebAuthn
- **Day 2-3**: Hardware setup (libfprint + NBIS), test sensor
- **Day 4-5**: Upgrade API server, integrate sensor capture
- **Day 6-7**: End-to-end testing with real hardware

### Week 2: Production Hardening
- **Day 8-9**: Security hardening (rate limits, auth, audit logs)
- **Day 10-11**: Performance optimization (caching, monitoring)
- **Day 12-13**: Automated testing (unit, integration, E2E)
- **Day 14**: Documentation and final review

**Total Time**: ~2 weeks for full production readiness

---

## Success Criteria

### Immediate (Week 1)
- ✅ Real fingerprint sensor working
- ✅ NBIS minutiae extraction functional
- ✅ API server upgraded to real CLI
- ✅ Demo-wallet enrollment with real sensor
- ✅ End-to-end test passing

### Production Ready (Week 2)
- ✅ Rate limiting implemented
- ✅ Authentication/authorization added
- ✅ Audit logging functional
- ✅ HTTPS enabled
- ✅ Caching implemented
- ✅ Monitoring dashboards created
- ✅ Automated tests passing
- ✅ Documentation complete

---

## Resources & Links

### Hardware
- **Eikon Touch 700**: [Amazon Search](https://www.amazon.com/s?k=eikon+touch+700)
- **ZhongZhi USB**: [AliExpress Search](https://www.aliexpress.com/wholesale?SearchText=usb+fingerprint+reader)
- **libfprint Supported Devices**: https://fprint.freedesktop.org/supported-devices.html

### Software
- **libfprint**: https://gitlab.freedesktop.org/libfprint/libfprint
- **NBIS**: https://github.com/lessandro/nbis
- **Python libfprint bindings**: `pip install python-fprint`
- **FastAPI**: https://fastapi.tiangolo.com/
- **Uvicorn**: https://www.uvicorn.org/

### Documentation
- **WebAuthn API**: https://developer.mozilla.org/en-US/docs/Web/API/Web_Authentication_API
- **Capacitor Plugins**: https://capacitorjs.com/docs/plugins
- **OpenCV**: https://docs.opencv.org/

---

## Questions & Decision Points

### Question 1: Which hardware to purchase first?

**Options**:
- **A. Eikon Touch 700** ($25-30) - Most recommended, best compatibility
- **B. ZhongZhi Generic** ($15-20) - Cheapest, good for testing
- **C. Futronic FS88** ($40) - Highest quality, best for production
- **D. Skip hardware, use WebAuthn** - No cost, verification only

**Recommendation**: Start with **Option A (Eikon Touch 700)** for best balance of price/quality/compatibility.

---

### Question 2: When to implement production features?

**Options**:
- **A. Immediate** - Implement all security/performance features now
- **B. Phased** - Basic hardware integration first, then harden
- **C. Deferred** - Stay in mock mode until user testing complete

**Recommendation**: **Option B (Phased)** - Get hardware working first (Week 1), then production hardening (Week 2).

---

### Question 3: Should we implement all sensor strategies?

**Options**:
- **A. All four** - WebAuthn, libfprint, Platform APIs, OpenCV
- **B. Two primary** - libfprint (enrollment) + WebAuthn (verification)
- **C. One only** - Focus on libfprint only

**Recommendation**: **Option B (Two primary)** - libfprint for enrollment, WebAuthn for verification. Add others as needed.

---

## Next Command

What would you like to focus on?

1. **"Update roadmap"** - Reflect completion status in docs/roadmap.md
2. **"Purchase hardware"** - Get shopping links and setup guide
3. **"Implement WebAuthn"** - Quick win, add verification without hardware
4. **"Upgrade API server"** - Replace mock with real CLI
5. **"Production checklist"** - Create detailed deployment plan
6. **"Start testing"** - Write automated test suite

**Recommended**: Start with **"Update roadmap"** (5 min) then **"Purchase hardware"** (Day 1).

---

**Ready to proceed?** Choose your next action or say "proceed" to continue with the recommended path.
