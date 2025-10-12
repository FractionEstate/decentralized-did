# Biometric DID LockPage Integration

## Overview

The LockPage now supports biometric fingerprint verification as an alternative to passcode-based wallet unlock. This integration provides users with a seamless, secure way to access their wallet using their enrolled biometric DID.

## Features

### 1. Biometric Unlock Option

When a user has enrolled their biometric DID:
- A prominent "Unlock with Fingerprint" button appears on the LockPage
- The button is only displayed when `biometricDidEnrolled` is true
- Users can choose between passcode or biometric unlock

### 2. BiometricVerification Component Integration

The LockPage integrates the `BiometricVerification` component in `Unlock` mode:

```tsx
<BiometricVerification
  mode={VerificationMode.Unlock}
  did={biometricDid}
  onSuccess={handleBiometricVerificationSuccess}
  onFailure={handleBiometricVerificationFailure}
  onCancel={handleBiometricVerificationCancel}
/>
```

### 3. Seamless State Management

**States:**
- Normal LockPage: Shows passcode entry + biometric button
- Biometric Verification: Shows fingerprint capture UI
- Locked: Shows MaxLoginAttemptAlert (no changes)

**State Flow:**
```
LockPage (passcode entry)
  ↓ User clicks "Unlock with Fingerprint"
BiometricVerification (fingerprint capture)
  ↓ Success
Wallet Unlocked (login dispatched)
  ↓ Failure
BiometricVerification (retry, up to 3 attempts)
  ↓ Cancel
LockPage (back to passcode entry)
```

## Implementation Details

### New State Variables

```typescript
const [showBiometricVerification, setShowBiometricVerification] = useState(false);
const [biometricDid, setBiometricDid] = useState<string | null>(null);
```

### DID Loading

On component mount, the LockPage loads the current user's biometric DID:

```typescript
const loadBiometricDid = async () => {
  try {
    const did = await biometricDidService.getCurrentDid();
    setBiometricDid(did);
  } catch (error) {
    console.error("Failed to load biometric DID:", error);
  }
};
```

### Event Handlers

**1. Start Biometric Verification**
```typescript
const handleBiometricDidUnlock = () => {
  setShowBiometricVerification(true);
};
```

**2. Verification Success**
```typescript
const handleBiometricVerificationSuccess = async () => {
  await resetLoginAttempt();
  dispatch(login());
  dispatch(setFirstAppLaunchComplete());
  setShowBiometricVerification(false);
};
```

**3. Verification Failure**
```typescript
const handleBiometricVerificationFailure = (error: string) => {
  console.error("Biometric verification failed:", error);
  // Keep verification UI open for retry (component handles attempt count)
};
```

**4. Verification Cancel**
```typescript
const handleBiometricVerificationCancel = () => {
  setShowBiometricVerification(false);
};
```

## UI Components

### Biometric Unlock Button

Located between the description and PasscodeModule:

```tsx
{biometricDid && authentication.biometricDidEnrolled && (
  <div className="biometric-unlock-option">
    <button
      className="biometric-unlock-button"
      onClick={handleBiometricDidUnlock}
      data-testid="biometric-unlock-button"
    >
      <IonIcon icon={fingerPrintSharp} />
      <span>{i18n.t("biometric.verification.unlock.button")}</span>
    </button>
  </div>
)}
```

### Styling

```scss
.biometric-unlock-option {
  width: 100%;
  display: flex;
  justify-content: center;
  margin: 2rem 0 1rem;

  .biometric-unlock-button {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem 2rem;
    background: var(--ion-color-primary);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

    ion-icon {
      font-size: 1.5rem;
    }

    &:hover {
      background: var(--ion-color-primary-shade);
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    &:active {
      transform: translateY(0);
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
    }
  }
}
```

## BiometricDidService Updates

### New Methods

**1. Save Current DID**
```typescript
async saveCurrentDid(did: string): Promise<void>
```
Stores the current user's biometric DID in SecureStorage for quick access.

**2. Get Current DID**
```typescript
async getCurrentDid(): Promise<string | null>
```
Retrieves the current user's biometric DID from SecureStorage.

**3. Delete Current DID**
```typescript
async deleteCurrentDid(): Promise<void>
```
Removes the current user's biometric DID from storage.

### Storage Key

```typescript
const CURRENT_DID_KEY = "biometric_current_did";
```

## Translations

New translation added to `en.json`:

```json
{
  "biometric": {
    "verification": {
      "unlock": {
        "title": "Unlock with Biometric",
        "description": "Place your finger on the sensor to unlock your wallet.",
        "button": "Unlock with Fingerprint"
      }
    }
  }
}
```

## User Experience Flow

### First-Time Setup

1. User creates wallet and sets passcode
2. User enables biometric DID in onboarding
3. BiometricEnrollment captures 10 fingerprints
4. System generates DID and stores it:
   - Helper data in SecureStorage
   - Current DID in SecureStorage
   - Metadata in PeerConnectionMetadata
   - `biometricDidEnrolled` flag set to true

### Subsequent Unlocks

**Option 1: Biometric Unlock**
1. LockPage displays "Unlock with Fingerprint" button
2. User clicks button
3. BiometricVerification component appears
4. User places finger on sensor (mock in dev mode)
5. System verifies fingerprint against helper data
6. On success: Wallet unlocks immediately
7. On failure: User can retry (up to 3 attempts) or cancel

**Option 2: Passcode Unlock**
1. User ignores biometric button
2. User enters 6-digit passcode as normal
3. Wallet unlocks if passcode is correct

### Fallback Scenarios

**Max Attempts Exceeded**
- After 3 failed biometric attempts
- BiometricVerification shows "Use Passcode Instead" button
- User clicks to return to passcode entry

**Cancel Biometric**
- User can cancel at any time
- Returns to normal LockPage with passcode entry
- Biometric button remains available

**Biometric Not Enrolled**
- No biometric button displayed
- Only passcode entry available
- User can enroll later via settings (future feature)

## Security Considerations

### 1. DID Storage

The current DID is stored in SecureStorage:
- **iOS**: iOS Keychain with `kSecAttrAccessibleWhenUnlockedThisDeviceOnly`
- **Android**: Android Keystore with `WHEN_UNLOCKED`
- **Platform security**: Hardware-backed encryption where available

### 2. Helper Data Protection

Helper data (fuzzy vault parameters) are stored separately:
- Key: `biometric_helpers_{did}`
- Same SecureStorage protection as DID
- Cannot reconstruct original fingerprints
- Required for verification but useless without live fingerprint

### 3. Authentication Flow

The biometric verification:
1. Loads helper data from secure storage
2. Captures live fingerprint (not stored)
3. Verifies match using Python CLI
4. Discards captured fingerprint immediately
5. Only returns success/failure (no biometric data transmitted)

### 4. Login Attempt Tracking

Biometric verification resets login attempts on success:
```typescript
await resetLoginAttempt();
```

This prevents lockout due to previous failed passcode attempts.

## Testing

### Development Mode (Mock)

```bash
cd demo-wallet
npm run dev
# Open http://localhost:3003

# Test flow:
# 1. Create wallet + set passcode
# 2. Enable biometrics in onboarding
# 3. Complete enrollment (mock data)
# 4. Lock wallet (logout)
# 5. Click "Unlock with Fingerprint"
# 6. See mock verification succeed
```

### Test Scenarios

**1. Successful Unlock**
- Click "Unlock with Fingerprint"
- Mock verification succeeds automatically
- Wallet unlocks

**2. Failed Verification**
- Modify mock service to return failure
- Retry option appears
- After 3 attempts, forced to passcode

**3. Cancel Verification**
- Click "Unlock with Fingerprint"
- Click "Cancel" button
- Return to passcode entry

**4. No Biometric Enrolled**
- Create wallet without biometric
- LockPage shows only passcode
- No biometric button visible

## Future Enhancements

### 1. Transaction Signing Integration

Add biometric verification to transaction flows:
```tsx
<BiometricVerification
  mode={VerificationMode.TransactionSign}
  did={biometricDid}
  onSuccess={() => signAndBroadcastTransaction()}
  onFailure={(error) => showError(error)}
  onCancel={() => showPasscodePrompt()}
/>
```

### 2. Re-enrollment

Allow users to re-enroll from settings:
- Navigate to Settings → Security → Biometric DID
- Delete existing enrollment
- Capture new fingerprints
- Generate new DID

### 3. Multiple DIDs

Support multiple biometric DIDs per wallet:
- Primary DID for unlock
- Secondary DID for transactions
- Different finger combinations

### 4. Biometric Settings

Add settings page for biometric management:
- View enrolled DID
- Re-enroll option
- Delete enrollment
- View enrollment date
- Configure verification sensitivity

## Troubleshooting

### Button Not Showing

**Check:**
1. `authentication.biometricDidEnrolled === true`
2. `biometricDid !== null`
3. User completed enrollment successfully

**Fix:**
```typescript
// Check state in Redux DevTools
stateCache.authentication.biometricDidEnrolled

// Check SecureStorage
await biometricDidService.getCurrentDid()
```

### Verification Always Fails

**Check:**
1. Helper data exists: `await biometricDidService.hasHelperData(did)`
2. DID format correct: `did:cardano:addr_test1...#hashvalue`
3. Mock mode enabled: `NODE_ENV=development`

**Fix:**
```typescript
// Verify helper data
const helpers = await biometricDidService.loadHelperData(did);
console.log("Helpers:", helpers);

// Check CLI execution mode
// In biometricDidService.ts, check executeCommand() path
```

### Unlock Doesn't Work

**Check:**
1. `handleBiometricVerificationSuccess` called
2. `dispatch(login())` executed
3. Redux state updated

**Fix:**
```typescript
// Add logging
const handleBiometricVerificationSuccess = async () => {
  console.log("Biometric verification success");
  await resetLoginAttempt();
  dispatch(login());
  dispatch(setFirstAppLaunchComplete());
  setShowBiometricVerification(false);
};
```

## Files Modified

### Core Services
- `demo-wallet/src/core/biometric/biometricDidService.ts`
  - Added `saveCurrentDid()`, `getCurrentDid()`, `deleteCurrentDid()`
  - Added `CURRENT_DID_KEY` constant

### UI Components
- `demo-wallet/src/ui/pages/LockPage/LockPage.tsx`
  - Imported `BiometricVerification` and `biometricDidService`
  - Added state: `showBiometricVerification`, `biometricDid`
  - Added handlers for verification success/failure/cancel
  - Added conditional rendering for biometric unlock button
  - Added conditional rendering for BiometricVerification component

- `demo-wallet/src/ui/pages/LockPage/LockPage.scss`
  - Added `.biometric-unlock-option` styles
  - Added `.biometric-unlock-button` styles with hover/active states

- `demo-wallet/src/ui/pages/BiometricEnrollment/BiometricEnrollment.tsx`
  - Added call to `saveCurrentDid()` after successful enrollment

### Translations
- `demo-wallet/src/locales/en/en.json`
  - Added `biometric.verification.unlock.button`

## Summary

The LockPage biometric integration provides:
- ✅ Seamless alternative to passcode unlock
- ✅ Secure DID storage and retrieval
- ✅ Fallback to passcode on failure
- ✅ 3-attempt retry logic
- ✅ User-friendly UI with clear feedback
- ✅ Full integration with existing authentication flow
- ✅ Mock mode for development without hardware

**Next Steps:**
1. Add biometric verification to transaction signing
2. Implement settings page for biometric management
3. Add production CLI execution method
4. Integrate real fingerprint sensors
