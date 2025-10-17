# Post-Deployment Action Items
**Status**: Optional improvements (non-blocking)
**Timeline**: Phase 5 - Production Hardening

## Immediate (Within 1 Week of Deployment)

### 1. Monitoring Setup ⏱️ 2-4 hours
- [ ] Configure log aggregation (e.g., ELK stack, Splunk, or CloudWatch)
- [ ] Set up uptime monitoring (e.g., Pingdom, UptimeRobot)
- [ ] Create alert rules:
  - API error rate > 5%
  - Rate limit exceeded (frequent)
  - Biometric enrollment failures
  - Blockfrost API errors

### 2. Performance Baseline 📊 1-2 hours
- [ ] Record baseline metrics:
  - Average enrollment time
  - Average verification time
  - API response times (p50, p95, p99)
  - Memory usage
  - CPU usage
- [ ] Set performance thresholds for alerting

---

## Short-Term (Within 1 Month)

### 3. Replace Console Statements 🔧 2-4 hours
**Priority**: Medium (code quality)

**Files to update**:
```typescript
demo-wallet/src/core/biometric/fingerprintCaptureService.ts  (5 statements)
demo-wallet/src/core/biometric/biometricDidService.ts       (8 statements)
demo-wallet/src/core/agent/services/keriaNotificationService.ts (6 statements)
demo-wallet/src/core/agent/agent.ts                          (2 statements)
demo-wallet/src/ui/utils/error.ts                           (1 statement)
demo-wallet/src/utils/userFriendlyErrors.ts                 (2 statements)
```

**Recommended library**: Winston or Pino (both Apache 2.0)

**Example refactor**:
```typescript
// Before
console.error('WebAuthn enrollment failed:', error);

// After
import { logger } from './utils/logger';
logger.error('WebAuthn enrollment failed', {
  error: error.message,
  stack: error.stack,
  context: 'biometric_enrollment'
});
```

**Benefits**:
- Structured logging (JSON format)
- Log levels (debug, info, warn, error)
- Automatic timestamp, context
- Easier log aggregation and filtering

### 4. Add Unit Tests for Untested Modules 🧪 1-2 days
**Priority**: Medium (test coverage)

**Modules needing tests** (20 identified by audit):
- CLI tools (`src/decentralized_did/cli/*.py`)
- Legacy code (if still in use)
- Utility functions
- Edge case handlers

**Target coverage**: 80%+ (currently ~60-70%)

**Example test structure**:
```python
# tests/test_cli.py
def test_enrollment_cli_success():
    """Test CLI enrollment with valid data"""
    result = subprocess.run([
        'python', '-m', 'decentralized_did.cli.enroll',
        '--wallet-address', 'addr_test1...',
        '--minutiae-file', 'test_minutiae.json'
    ], capture_output=True)

    assert result.returncode == 0
    assert 'DID enrolled' in result.stdout.decode()
```

---

## Medium-Term (Within 3 Months)

### 5. Implement CIP-8 Wallet Signature Verification 🔐 4-8 hours
**Priority**: Low (optional feature, basic auth works)

**Current status**: Placeholder returns `True` (auth.py:422)

**Implementation plan**:
1. Add `pycardano` dependency (Apache 2.0)
2. Implement signature verification:
```python
from pycardano import Address, VerificationKey, PlutusData

async def verify_wallet_signature(
    self, address: str, signature: str, message: str
) -> bool:
    """Verify CIP-8 wallet signature"""
    try:
        # Parse address
        addr = Address.from_primitive(address)

        # Verify signature using payment verification key
        vkey = VerificationKey.from_cbor(signature)
        return vkey.verify(message.encode(), signature)
    except Exception as e:
        logger.error(f"CIP-8 verification failed: {e}")
        return False
```
3. Add tests for valid/invalid signatures
4. Update documentation

**Benefits**:
- Enables wallet-based authentication (alternative to JWT)
- Better UX for Cardano users (sign with wallet)
- Aligns with Cardano standards (CIP-8)

### 6. Performance Optimization 🚀 2-5 days
**Priority**: Low (current performance acceptable)

**Potential improvements**:
- **Caching layer**: Add Redis caching for:
  - DID lookups (TTL: 5 minutes)
  - Blockfrost responses (TTL: 1 minute)
  - Rate limit counters (already supported)

- **Database optimization**:
  - Add indexes for DID lookups
  - Use connection pooling
  - Implement read replicas

- **Biometric matching**:
  - Profile current performance
  - Optimize minutiae comparison algorithm
  - Consider hardware acceleration (if needed)

**When to implement**: Only if performance metrics show degradation or user complaints.

---

## Long-Term (Ongoing)

### 7. Code Cleanup 🧹 Ongoing
**Priority**: Low (maintenance)

**Tasks**:
- [ ] Remove obsolete TODO comments (verify TODO at auth.py:422 after CIP-8 implementation)
- [ ] Refactor functions >50 lines (improve readability)
- [ ] Consolidate duplicate error handling
- [ ] Update docstrings for API changes
- [ ] Keep dependencies up-to-date (security patches)

### 8. Security Hardening 🛡️ Ongoing
**Priority**: High (continuous)

**Tasks**:
- [ ] Regular security audits (quarterly)
- [ ] Dependency vulnerability scanning (automated)
- [ ] Penetration testing (annual)
- [ ] Update threat model as needed
- [ ] Review access logs for anomalies

### 9. Documentation Updates 📚 Ongoing
**Priority**: Medium (user support)

**Tasks**:
- [ ] Update API documentation as endpoints evolve
- [ ] Add troubleshooting guides based on support issues
- [ ] Create runbooks for common operations
- [ ] Maintain changelog for API versions
- [ ] User guides for demo wallet features

---

## Metrics to Track

### API Performance
- **Response times**: p50, p95, p99 (target: <200ms, <500ms, <1000ms)
- **Error rate**: (target: <1%)
- **Throughput**: requests/second (establish baseline)

### Biometric Operations
- **Enrollment success rate**: (target: >95%)
- **Verification accuracy**: (target: >99% true positives, <0.1% false positives)
- **Average enrollment time**: (target: <2 seconds)
- **Average verification time**: (target: <1 second)

### Security
- **Rate limit violations**: (monitor for abuse)
- **Authentication failures**: (monitor for attacks)
- **API key revocations**: (track lifecycle)

### Infrastructure
- **CPU usage**: (target: <70% avg, <90% peak)
- **Memory usage**: (target: <80% avg)
- **Disk I/O**: (monitor for bottlenecks)
- **Network bandwidth**: (monitor for DDoS)

---

## Decision Framework

**When to prioritize an action item**:
1. **High Priority**: Security issue, production bug, or performance degradation
2. **Medium Priority**: User-facing feature request, code quality improvement
3. **Low Priority**: Internal tooling, documentation, optimization

**Review cadence**:
- Weekly: Monitoring metrics, security alerts
- Monthly: Action item progress, new issues
- Quarterly: Strategic roadmap, major features

---

**Last Updated**: 2025-01-XX
**Owner**: Development Team
**Review Frequency**: Monthly
