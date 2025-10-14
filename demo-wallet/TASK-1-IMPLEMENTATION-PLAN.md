# Task 1: Demo Wallet Migration to Deterministic DIDs

**Status**: 🟢 IN PROGRESS
**Started**: October 14, 2025
**Estimated Duration**: 3-4 days
**Dependencies**: None

---

## 🎯 Objective

Migrate demo wallet from **legacy wallet-based DID format** to **deterministic DID format**:

- **Legacy format** (Phase 4.4): `did:cardano:{wallet_address}#{id_hash}` ❌ VULNERABLE
- **Deterministic format** (Phase 4.5): `did:cardano:mainnet:{base58_hash}` ✅ SYBIL-RESISTANT

---

## 📋 Task Breakdown

### Day 1: Core Logic (4-6 hours)

#### 1.1 Install Dependencies ✅

```bash
cd demo-wallet
npm install blakejs bs58 @types/bs58
```

#### 1.2 Update biometricDidService.ts Core Logic

**File**: `src/core/biometric/biometricDidService.ts`

**Changes**:

1. Add imports for Blake2b and Base58
2. Add `generateDeterministicDID()` helper function
3. Update `transformGenerateResult()` to use deterministic DIDs
4. Remove wallet address from DID identifier construction
5. Keep wallet address in metadata only

**Key Change** (Line 365):

```typescript
// OLD (legacy format - REMOVE):
const did = cliOutput.did || `did:cardano:${walletAddress}#${idHash}`;

// NEW (deterministic format):
const did = cliOutput.did; // API already returns deterministic format
// Fallback only for mock/dev mode:
if (!did && process.env.NODE_ENV === "development") {
  did = await this.generateDeterministicDID(commitment, "mainnet");
}
```

#### 1.3 Update API Integration

**File**: `src/core/biometric/biometricDidService.ts`

**Changes**:

1. API `/api/biometric/generate` already returns deterministic DID ✅
2. Remove wallet_address from DID identifier (keep in metadata)
3. Update response parsing to expect deterministic format

---

### Day 1-2: Storage Layer (2-3 hours)

#### 2.1 Update SecureStorage DID Handling

**File**: `src/core/storage/secureStorage/secureStorage.ts`

**Changes**:

1. Remove wallet address extraction from DID parsing
2. Update DID validation regex:
   - OLD: `^did:cardano:addr[a-zA-Z0-9_]+#[a-zA-Z0-9]+$`
   - NEW: `^did:cardano:(mainnet|testnet):[a-zA-Z0-9]+$`
3. Update storage keys (if using DID as key, ensure compatibility)

#### 2.2 Data Migration (if needed)

- Check if any existing DIDs need migration
- Provide migration utility (or just re-enroll users)
- **Recommendation**: Fresh start (wallet is in development)

---

### Day 2: UI Components (3-4 hours)

#### 3.1 Update BiometricEnrollment Component

**File**: `src/ui-components/biometric/BiometricEnrollment.tsx`

**Changes**:

1. Update DID display (show deterministic format)
2. Remove wallet address from DID identifier display
3. Update success messages
4. Update enrollment flow to handle deterministic DIDs

**Visual Changes**:

```tsx
// OLD display:
<IonText>DID: did:cardano:addr1...xyz#abc123</IonText>

// NEW display:
<IonText>DID: did:cardano:mainnet:4ApYK4gyR9...</IonText>
<IonNote>Controller: addr1...xyz</IonNote>
```

#### 3.2 Update BiometricVerification Component

**File**: `src/ui-components/biometric/BiometricVerification.tsx`

**Changes**:

1. Update verification flow for deterministic DIDs
2. Update DID display
3. Update error messages

---

### Day 2-3: Types and Models (1-2 hours)

#### 4.1 Update Type Definitions

**File**: `src/core/biometric/biometricDid.types.ts`

**Changes**:

```typescript
// Update BiometricGenerateResult interface
export interface BiometricGenerateResult {
  did: string; // Now deterministic format
  id_hash?: string; // Optional (not used in deterministic format)
  wallet_address: string; // Still in metadata, not in DID identifier
  helpers: Record<string, HelperDataEntry>;
  metadata_cip30_inline: {
    version: 1.1; // Updated to v1.1
    controllers: string[]; // Multi-controller support
    biometric: {
      commitment: string; // Base58 encoded
      helperStorage: "inline" | "external";
      helperData?: Record<string, HelperDataEntry>;
    };
    enrollmentTimestamp: string; // ISO 8601
    revoked?: boolean;
  };
}
```

---

### Day 3-4: Testing (6-8 hours)

#### 5.1 Unit Tests

**Files**:

- `tests/unit/biometricDidService.test.ts` (create if doesn't exist)

**Test Cases**:

1. ✅ `generateDeterministicDID()` produces correct format
2. ✅ Same commitment produces same DID (deterministic)
3. ✅ Different commitments produce different DIDs
4. ✅ DID format matches regex: `^did:cardano:(mainnet|testnet):[a-zA-Z0-9]+$`
5. ✅ No wallet address in DID identifier
6. ✅ Wallet address preserved in metadata

#### 5.2 Integration Tests

**Files**:

- `tests/integration/biometric-api.test.ts` (create if doesn't exist)

**Test Cases**:

1. ✅ API returns deterministic DID
2. ✅ Enrollment flow works with all 3 API servers (basic, secure, mock)
3. ✅ Storage saves and retrieves deterministic DIDs
4. ✅ Verification flow works with deterministic DIDs

#### 5.3 E2E Tests

**Files**:

- `tests/e2e/biometric-enrollment.spec.ts`
- `tests/e2e/biometric-verification.spec.ts`

**Test Cases**:

1. ✅ User can enroll with WebAuthn biometrics
2. ✅ DID displayed is deterministic format
3. ✅ No wallet address visible in DID identifier
4. ✅ Enrollment succeeds with all API servers
5. ✅ User can verify after enrollment
6. ✅ Verification succeeds with correct biometrics
7. ✅ Verification fails with incorrect biometrics

#### 5.4 Manual Testing

**Browsers**: Chrome, Firefox, Safari, Edge
**Platforms**: Web (all browsers), iOS (if available), Android (if available)

**Test Scenarios**:

1. Fresh enrollment with WebAuthn
2. Verification after enrollment
3. Multiple enrollments (different users)
4. Error handling (network failures, API errors)
5. UI display (DID format, success messages)

---

## 🔧 Implementation Steps (Sequential)

### Step 1: Install Dependencies (5 minutes)

```bash
cd /workspaces/decentralized-did/demo-wallet
npm install blakejs bs58 @types/bs58
```

### Step 2: Update biometricDidService.ts (1-2 hours)

```bash
# Edit src/core/biometric/biometricDidService.ts
# Add deterministic DID generation logic
# Update transformGenerateResult()
# Remove wallet address from DID construction
```

### Step 3: Update Storage Layer (30-60 minutes)

```bash
# Edit src/core/storage/secureStorage/secureStorage.ts
# Update DID validation regex
# Test storage with new format
```

### Step 4: Update UI Components (2-3 hours)

```bash
# Edit src/ui-components/biometric/BiometricEnrollment.tsx
# Edit src/ui-components/biometric/BiometricVerification.tsx
# Update displays and messages
```

### Step 5: Update Types (30 minutes)

```bash
# Edit src/core/biometric/biometricDid.types.ts
# Update interfaces for deterministic format
```

### Step 6: Write Unit Tests (2-3 hours)

```bash
# Create/update tests/unit/biometricDidService.test.ts
# Test deterministic generation
# Test Sybil resistance (same commitment = same DID)
```

### Step 7: Write Integration Tests (2-3 hours)

```bash
# Create/update tests/integration/biometric-api.test.ts
# Test API integration
# Test storage integration
```

### Step 8: Update E2E Tests (2-3 hours)

```bash
# Update tests/e2e/biometric-enrollment.spec.ts
# Update tests/e2e/biometric-verification.spec.ts
# Test full user flows
```

### Step 9: Manual Testing (2-3 hours)

```bash
# Start dev server: npm run dev
# Test enrollment flow
# Test verification flow
# Test all browsers
# Document issues
```

### Step 10: Fix Bugs and Refinements (1-2 hours)

```bash
# Address issues found in testing
# Polish UI/UX
# Update documentation
```

---

## ✅ Success Criteria

### Functional Requirements

- ✅ Demo wallet generates deterministic DIDs
- ✅ NO wallet addresses in DID identifiers
- ✅ Enrollment works with all 3 API servers (basic, secure, mock)
- ✅ Verification flows work correctly
- ✅ Storage handles new DID format
- ✅ All tests passing (unit + integration + E2E)

### Non-Functional Requirements

- ✅ Performance: Same or better than legacy format
- ✅ Security: Sybil resistance enforced
- ✅ Privacy: No wallet addresses exposed in DIDs
- ✅ UX: Smooth enrollment and verification flows
- ✅ Compatibility: Works on all target platforms (web, iOS, Android)

### Code Quality

- ✅ TypeScript types updated and correct
- ✅ No ESLint errors
- ✅ Code formatted with Prettier
- ✅ Comprehensive test coverage (>80%)
- ✅ Documentation updated

---

## 🚧 Risks and Mitigations

### Risk 1: Breaking Existing Functionality

**Likelihood**: MEDIUM
**Impact**: HIGH
**Mitigation**:

- Incremental changes with testing after each step
- Feature flags for rollback (if needed)
- Comprehensive test suite
- Code review before merge

### Risk 2: API Response Format Mismatch

**Likelihood**: LOW (API already updated)
**Impact**: MEDIUM
**Mitigation**:

- API already returns deterministic DIDs (verified in api_server.py)
- Integration tests will catch any issues
- Mock mode provides fallback

### Risk 3: Storage Migration Issues

**Likelihood**: LOW (wallet is in development)
**Impact**: MEDIUM
**Mitigation**:

- Fresh start recommended (no production data)
- Clear old storage if needed
- Provide migration utility if users have enrolled

---

## 📝 Files to Modify

### Core Logic (PRIORITY: HIGH)

1. ✅ `demo-wallet/src/core/biometric/biometricDidService.ts` - Main service
2. ✅ `demo-wallet/src/core/biometric/biometricDid.types.ts` - Type definitions
3. ✅ `demo-wallet/src/core/storage/secureStorage/secureStorage.ts` - Storage layer

### UI Components (PRIORITY: HIGH)

4. ✅ `demo-wallet/src/ui-components/biometric/BiometricEnrollment.tsx` - Enrollment UI
5. ✅ `demo-wallet/src/ui-components/biometric/BiometricVerification.tsx` - Verification UI

### Tests (PRIORITY: MEDIUM)

6. ✅ `demo-wallet/tests/unit/biometricDidService.test.ts` - Unit tests (create)
7. ✅ `demo-wallet/tests/integration/biometric-api.test.ts` - Integration tests (create)
8. ✅ `demo-wallet/tests/e2e/biometric-enrollment.spec.ts` - E2E enrollment (update)
9. ✅ `demo-wallet/tests/e2e/biometric-verification.spec.ts` - E2E verification (update)

### Documentation (PRIORITY: LOW)

10. ✅ `demo-wallet/README.md` - Wallet documentation (update)
11. ✅ `docs/wallet-integration.md` - Integration guide (update)

---

## 📊 Progress Tracking

### Day 1 (October 14, 2025)

- [x] Create implementation plan
- [ ] Install dependencies (blakejs, bs58, @types/bs58)
- [ ] Add generateDeterministicDID() to biometricDidService.ts
- [ ] Update transformGenerateResult() to use deterministic format
- [ ] Test core logic changes

### Day 2

- [ ] Update SecureStorage DID validation
- [ ] Update BiometricEnrollment.tsx UI
- [ ] Update BiometricVerification.tsx UI
- [ ] Update type definitions

### Day 3

- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Update E2E tests
- [ ] Run full test suite

### Day 4

- [ ] Manual testing (all browsers)
- [ ] Fix bugs found in testing
- [ ] Code review and refinements
- [ ] Update documentation
- [ ] Mark Task 1 complete ✅

---

## 🔗 Related Documents

- **Phase 4.6 Plan**: `docs/PHASE-4.6-PLAN.md`
- **Action Plan**: `docs/OPTIONS-1-2-3-ACTION-PLAN.md`
- **Executive Summary**: `docs/PHASE-4.6-EXECUTIVE-SUMMARY.md`
- **API Documentation**: API servers already use Phase 4.5 deterministic format

---

**Next Action**: Install npm dependencies and begin core logic implementation.
