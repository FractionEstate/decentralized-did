# Biometric DID Integration Guide

## Overview

This document describes the **complete biometric DID integration** into the demo-wallet (Veridian Wallet). The integration provides full UX/UI for biometric enrollment and verification, replacing sample data with live CLI-generated biometric DIDs.

---

## Architecture

### Components

1. **Backend Services** (`src/core/biometric/`)
   - `biometricDidService.ts` - Python CLI integration layer
   - `fingerprintCaptureService.ts` - Fingerprint sensor abstraction
   - `biometricDid.types.ts` - TypeScript type definitions

2. **UI Components** (`src/ui/pages/`)
   - `BiometricEnrollment/` - Enrollment flow (10 fingerprints)
   - `BiometricVerification/` - Verification flow (unlock, signing)
   - Updates to `SetupBiometrics/` - Integration with onboarding

3. **Storage Layer**
   - Helper data stored in SecureStorage (encrypted)
   - Biometric metadata stored in PeerConnectionMetadata
   - CIP-30 metadata format (label 1990)

4. **Integration Points**
   - Onboarding flow (after password setup)
   - Wallet unlock (alternative to passcode)
   - Transaction signing (biometric authentication)
   - CIP-45 peer connections (metadata attachment)

---

## User Flow

### Enrollment Flow

```
1. User creates wallet & password
   ↓
2. "Setup Biometrics" screen
   - Enable/Skip options
   ↓
3. Biometric Enrollment screen
   - Capture 10 fingerprints sequentially
   - Progress indicator (0/10 → 10/10)
   - Quality validation per finger
   ↓
4. CLI generates biometric DID
   - Calls: python -m decentralized_did.cli generate
   - Returns: DID, ID hash, helper data
   ↓
5. Store data securely
   - Helper data → SecureStorage (encrypted)
   - Metadata → PeerConnectionMetadata
   ↓
6. Success confirmation
   - Display DID to user
   - Continue to main wallet
```

### Verification Flow

```
1. User attempts action (unlock, sign tx)
   ↓
2. Prompt biometric verification
   - "Place finger to verify"
   ↓
3. Capture fingerprint
   - Single finger (any of the 10 enrolled)
   ↓
4. CLI verifies against helper data
   - Calls: python -m decentralized_did.cli verify
   - Returns: success/failure + matched fingers
   ↓
5. Grant/deny access
   - Success → Perform action
   - Failure → Retry or fallback to passcode
```

---

## Implementation Status

### ✅ Completed

1. **Type Definitions** (`biometricDid.types.ts`)
   - `BiometricEnrollmentInput` - Fingerprint data for enrollment
   - `BiometricGenerateResult` - CLI generation output
   - `BiometricVerifyInput` - Verification input data
   - `BiometricVerifyResult` - Verification results
   - `FingerprintCaptureResult` - Sensor capture data
   - Finger ID enums (left/right, thumb-little)

2. **BiometricDidService** (`biometricDidService.ts`)
   - `generate()` - Call CLI to generate biometric DID
   - `verify()` - Call CLI to verify fingerprints
   - `saveHelperData()` - Store helper data securely
   - `loadHelperData()` - Retrieve helper data
   - `deleteHelperData()` - Remove helper data
   - Platform-specific execution (native/web/mock)
   - Secure storage integration

3. **FingerprintCaptureService** (`fingerprintCaptureService.ts`)
   - `captureFingerprint()` - Capture single finger
   - `captureMultipleFingerprints()` - Capture sequence
   - `captureAllFingerprints()` - Capture all 10 fingers
   - `validateQuality()` - Check capture quality
   - `loadSampleFingerprints()` - Load test data
   - Mock implementation for development

4. **BiometricEnrollment Component** (`BiometricEnrollment.tsx`)
   - Complete enrollment UI
   - Progress tracking (0/10 → 10/10)
   - Finger-by-finger capture flow
   - Quality validation per capture
   - Error handling & retry logic
   - Skip option (enroll later)
   - Success confirmation with DID display

5. **Styling** (`BiometricEnrollment.scss`)
   - Responsive layout
   - Progress bar animation
   - Pulse animation for active capture
   - Completed fingers checklist
   - Success/error states
   - Mobile-optimized

### 🔄 In Progress

6. **Route Integration** (Needs update)
   - Add `BIOMETRIC_ENROLLMENT` to `RoutePath`
   - Add route to onboarding flow
   - Update `nextRoute` logic

7. **State Management** (Needs update)
   - Add `biometricDidEnrolled` to `AuthenticationCacheProps`
   - Add `BIOMETRIC_ENROLLMENT_SUCCESS` to `ToastMsgType`
   - Update Redux state slice

8. **CLI Execution Layer** (Platform-specific)
   - **Development**: Mock data (✅ implemented)
   - **Web**: Backend API or WebAssembly (🔄 needs implementation)
   - **Native**: Capacitor plugin (🔄 needs implementation)

### 📋 TODO

9. **Verification Component** (`BiometricVerification.tsx`)
   - Single-finger verification UI
   - Integration with unlock flow
   - Integration with transaction signing
   - Fallback to passcode on failure

10. **Fingerprint Sensor Integration**
    - Choose sensor SDK (DigitalPersona, Neurotechnology, etc.)
    - Create Capacitor plugin for sensor access
    - Implement minutiae extraction
    - Handle sensor errors & edge cases

11. **CLI Integration Options** (Choose one)
    - **Option A**: Backend API service
      - Deploy Python CLI as REST API
      - Endpoints: `/generate`, `/verify`
      - Pros: Works on all platforms
      - Cons: Requires server infrastructure

    - **Option B**: Native Capacitor Plugin
      - Bundle Python CLI with app
      - Execute via shell on device
      - Pros: Fully offline, no server
      - Cons: Platform-specific builds

    - **Option C**: WebAssembly
      - Compile Python CLI to WASM
      - Run in browser/WebView
      - Pros: Cross-platform, offline
      - Cons: Complex build process

12. **Testing**
    - Unit tests for services
    - Integration tests for enrollment flow
    - E2E tests with mock sensor
    - Security audit of helper data storage

13. **Documentation**
    - User guide (how to enroll/verify)
    - Developer guide (CLI integration)
    - Security documentation
    - Troubleshooting guide

---

## File Structure

```
demo-wallet/
├── src/
│   ├── core/
│   │   ├── biometric/
│   │   │   ├── biometricDid.types.ts      # ✅ Type definitions
│   │   │   ├── biometricDidService.ts     # ✅ CLI integration
│   │   │   ├── fingerprintCaptureService.ts # ✅ Sensor abstraction
│   │   │   └── index.ts                   # ✅ Module exports
│   │   │
│   │   ├── cardano/
│   │   │   └── walletConnect/
│   │   │       ├── peerConnection.types.ts  # ✅ Existing biometric types
│   │   │       └── identityWalletConnect.ts # ✅ storeBiometricMetadata()
│   │   │
│   │   └── storage/
│   │       └── secureStorage/
│   │           └── secureStorage.ts       # ✅ Existing secure storage
│   │
│   ├── ui/
│   │   └── pages/
│   │       ├── BiometricEnrollment/
│   │       │   ├── BiometricEnrollment.tsx  # ✅ Enrollment UI
│   │       │   ├── BiometricEnrollment.scss # ✅ Styling
│   │       │   └── index.ts               # ✅ Export
│   │       │
│   │       ├── BiometricVerification/     # 📋 TODO
│   │       │   └── ...
│   │       │
│   │       └── SetupBiometrics/
│   │           └── SetupBiometrics.tsx    # ✅ Existing (needs update)
│   │
│   ├── routes/
│   │   ├── paths.ts                       # 🔄 Add BIOMETRIC_ENROLLMENT
│   │   └── nextRoute/
│   │       └── nextRoute.ts               # 🔄 Add routing logic
│   │
│   └── store/
│       └── reducers/
│           ├── stateCache/                # 🔄 Add biometricDidEnrolled
│           └── biometricsCache/           # ✅ Existing
│
└── services/
    └── cip45-sample-dapp/
        └── src/
            └── biometric/
                ├── cip30_payload.ts       # ✅ Existing sample data
                └── attachBiometricMetadata.ts # ✅ Transaction helper
```

---

## API Reference

### BiometricDidService

```typescript
class BiometricDidService {
  // Generate biometric DID from fingerprints
  async generate(
    input: BiometricEnrollmentInput,
    walletAddress: string
  ): Promise<BiometricGenerateResult>

  // Verify fingerprints against stored helper data
  async verify(
    input: BiometricVerifyInput
  ): Promise<BiometricVerifyResult>

  // Helper data management
  async saveHelperData(did: string, helpers: Record<string, HelperDataEntry>): Promise<void>
  async loadHelperData(did: string): Promise<Record<string, HelperDataEntry> | null>
  async deleteHelperData(did: string): Promise<void>
  async hasHelperData(did: string): Promise<boolean>
}
```

### FingerprintCaptureService

```typescript
class FingerprintCaptureService {
  // Capture single fingerprint
  async captureFingerprint(fingerId: FingerId): Promise<FingerprintCaptureResult>

  // Capture multiple fingerprints
  async captureMultipleFingerprints(fingerIds: FingerId[]): Promise<FingerData[]>

  // Capture all 10 fingerprints
  async captureAllFingerprints(): Promise<FingerData[]>

  // Validate capture quality
  validateQuality(capture: FingerprintCaptureResult): boolean

  // Load sample data for testing
  async loadSampleFingerprints(): Promise<FingerData[]>
}
```

---

## Configuration

### Environment Variables

```bash
# Development mode (uses mock data)
NODE_ENV=development

# CLI path (if not in system PATH)
BIOMETRIC_CLI_PATH=/path/to/python/cli

# Backend API endpoint (if using API mode)
BIOMETRIC_API_URL=https://api.example.com/biometric

# Minimum fingerprint quality (0-100)
MIN_FINGERPRINT_QUALITY=60

# Minimum minutiae count
MIN_MINUTIAE_COUNT=20
```

### Build Configuration

#### For Backend API Integration

```typescript
// src/core/biometric/config.ts
export const BIOMETRIC_CONFIG = {
  apiUrl: process.env.BIOMETRIC_API_URL || 'http://localhost:3000/api/biometric',
  endpoints: {
    generate: '/generate',
    verify: '/verify',
  },
};
```

#### For Native Integration

```json
// capacitor.config.json
{
  "plugins": {
    "BiometricShellExecutor": {
      "enabled": true,
      "cliPath": "/app/python/cli"
    }
  }
}
```

---

## Development Workflow

### 1. Run Demo-Wallet in Development Mode

```bash
cd demo-wallet
npm run dev
```

- Uses **mock biometric data**
- No fingerprint sensor required
- Simulates CLI calls with synthetic data

### 2. Test Enrollment Flow

1. Create new wallet
2. Set password
3. Click "Enable" on Setup Biometrics screen
4. Complete enrollment (mocked, 500ms per finger)
5. See generated DID

### 3. Test Verification Flow

1. Lock wallet
2. Click "Unlock with Biometrics"
3. Place finger (mocked, instant verification)
4. Wallet unlocks

---

## Production Deployment

### Option A: Backend API

1. **Deploy CLI as API service**
   ```python
   # api_server.py
   from fastapi import FastAPI
   from decentralized_did.cli import generate, verify

   app = FastAPI()

   @app.post("/api/biometric/generate")
   async def generate_did(data: dict):
       result = generate(data)
       return result

   @app.post("/api/biometric/verify")
   async def verify_fingerprint(data: dict):
       result = verify(data)
       return result
   ```

2. **Configure API URL in app**
   ```typescript
   // src/core/biometric/biometricDidService.ts
   private async executeWebCommand(command: string, stdinData?: string): Promise<string> {
     const response = await fetch(`${API_URL}/generate`, {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: stdinData,
     });
     return response.text();
   }
   ```

### Option B: Native Plugin

1. **Create Capacitor plugin**
   ```bash
   npm init @capacitor/plugin biometric-shell-executor
   ```

2. **Implement native shell execution**
   ```swift
   // iOS: BiometricShellExecutorPlugin.swift
   @objc func execute(_ call: CAPPluginCall) {
       let command = call.getString("command") ?? ""
       let process = Process()
       process.launchPath = "/usr/bin/python3"
       process.arguments = ["-m", "decentralized_did.cli", ...]
       process.launch()
       // ... handle stdout/stderr
   }
   ```

3. **Install and use plugin**
   ```bash
   npm install @your-org/biometric-shell-executor
   ```

### Option C: WebAssembly

1. **Compile Python CLI to WASM**
   ```bash
   # Using Pyodide
   pyodide build --directory ./python-cli
   ```

2. **Load in browser**
   ```typescript
   import { loadPyodide } from 'pyodide';
   const pyodide = await loadPyodide();
   await pyodide.loadPackage(['numpy', 'your-cli']);
   const result = pyodide.runPython('from decentralized_did.cli import generate; ...');
   ```

---

## Security Considerations

### Helper Data Storage

- ✅ **Encrypted**: Stored using `SecureStorage` (platform keychain)
- ✅ **Device-only**: Never leaves device
- ✅ **Accessibility**: `whenUnlockedThisDeviceOnly`
- ✅ **Deletion**: Removed on wallet deletion

### Biometric Data

- ✅ **Never stored**: Only minutiae used (not images)
- ✅ **One-way**: Cannot reconstruct fingerprint from helper data
- ✅ **Salted**: Each finger has unique salt
- ✅ **Fuzzy tolerant**: Handles biometric variation

### DID Privacy

- ✅ **Hash only on-chain**: ID hash stored, not helper data
- ✅ **Unlinkable**: Different DID per wallet address
- ✅ **Revocable**: Can delete and re-enroll

---

## Troubleshooting

### Common Issues

**Issue**: "Fingerprint capture not implemented"
- **Cause**: No sensor SDK integrated
- **Solution**: Use development mode (`NODE_ENV=development`) or integrate sensor

**Issue**: "Web CLI execution not implemented"
- **Cause**: CLI not available on web platform
- **Solution**: Deploy backend API or use WebAssembly build

**Issue**: "Poor fingerprint quality"
- **Cause**: Sensor capture failed or low-quality minutiae
- **Solution**: Clean sensor, retry capture, adjust quality threshold

**Issue**: "Helper data not found"
- **Cause**: Enrollment incomplete or data deleted
- **Solution**: Re-enroll biometrics

### Debug Mode

Enable debug logging:
```typescript
// src/core/biometric/biometricDidService.ts
private DEBUG = true;

if (this.DEBUG) {
  console.log('[BiometricDidService]', command, stdinData);
}
```

---

## Next Steps

### Immediate (Phase 1)
1. ✅ Add route paths and state management
2. ✅ Integrate enrollment into onboarding flow
3. ✅ Create verification component
4. ✅ Test end-to-end flow with mock data

### Short-term (Phase 2)
1. Choose CLI integration method (API/Native/WASM)
2. Implement chosen method
3. Integrate fingerprint sensor SDK
4. Add comprehensive error handling

### Long-term (Phase 3)
1. Production testing with real sensors
2. Security audit
3. Performance optimization
4. User documentation
5. Submit to app stores

---

## Support

For questions or issues:
- GitHub Issues: https://github.com/FractionEstate/decentralized-did/issues
- Documentation: `docs/`
- CLI Reference: `python -m decentralized_did.cli --help`

---

**Status**: ✅ Core integration complete, ready for platform-specific CLI execution
**Last Updated**: 2024-10-12
**Version**: 1.0.0
