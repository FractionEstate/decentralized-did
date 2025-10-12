# WebAuthn Manual Testing Checklist

**Date**: October 12, 2025
**Status**: Ready for Device Testing
**Estimated Time**: 30-45 minutes
**Demo-Wallet URL**: http://localhost:3003
**API Server**: http://localhost:8000 (must be running)

---

## Prerequisites

✅ **Before You Start**:
- [ ] Demo-wallet running: `cd demo-wallet && npm run dev`
- [ ] API server running: `python api_server_mock.py`
- [ ] Test device has biometric hardware (Touch ID, Face ID, Windows Hello, Fingerprint)
- [ ] Browser supports WebAuthn (Chrome, Safari, Edge)
- [ ] Browser console open for debugging (F12 → Console tab)

---

## Test 1: Check WebAuthn Availability

**Purpose**: Verify WebAuthn is detected correctly

**Steps**:
1. Open browser console (F12)
2. Navigate to http://localhost:3003
3. Run in console:
   ```javascript
   window.PublicKeyCredential !== undefined
   ```

**Expected Result**:
- Should show `true` on modern browsers
- Should show `false` on old browsers

**Pass**: ✅ / ❌

**Screenshot**: (Optional)

---

## Test 2: Check Biometric Type Detection

**Purpose**: Verify correct biometric name is detected

**Steps**:
1. Open browser console
2. Check platform detection:
   ```javascript
   navigator.userAgent
   ```
3. Expected biometric type based on platform:
   - **Mac**: "Touch ID"
   - **iOS**: "Touch ID / Face ID"
   - **Windows**: "Windows Hello"
   - **Android**: "Fingerprint"

**Expected Result**:
- Correct biometric name shown in UI buttons

**Your Device**: ________________
**Detected Type**: ________________
**Pass**: ✅ / ❌

---

## Test 3: WebAuthn Enrollment

**Purpose**: Test first-time biometric enrollment

**Steps**:
1. Navigate to Settings → Biometric
2. Click "Enable Biometric" (or similar)
3. Look for button with text like:
   - "Enable Touch ID"
   - "Enable Face ID"
   - "Enable Windows Hello"
4. Click the WebAuthn enrollment button
5. Browser shows native biometric prompt
6. Authenticate (place finger, look at camera, enter PIN)
7. Wait for success message

**Expected Result**:
- ✅ Browser shows platform biometric prompt
- ✅ Credential successfully created
- ✅ Success message displayed
- ✅ Navigate to next screen

**Result**:
- Biometric prompt shown: ✅ / ❌
- Enrollment succeeded: ✅ / ❌
- Success message: ✅ / ❌
- Any errors: ________________

**Pass**: ✅ / ❌

---

## Test 4: WebAuthn Wallet Unlock

**Purpose**: Test biometric verification for unlocking wallet

**Steps**:
1. Lock the wallet (Settings → Lock Wallet)
2. Navigate to Lock/Login page
3. Look for button like:
   - "Unlock with Touch ID"
   - "Unlock with Face ID"
   - "Unlock with Windows Hello"
4. Click the WebAuthn unlock button
5. Browser shows biometric prompt
6. Authenticate with correct biometric
7. Wait for wallet to unlock

**Expected Result**:
- ✅ Biometric prompt appears
- ✅ Verification completes in <3 seconds
- ✅ Wallet unlocks successfully
- ✅ Navigate to main wallet screen

**Result**:
- Prompt shown: ✅ / ❌
- Verification time: _______ seconds
- Unlock successful: ✅ / ❌
- Any errors: ________________

**Pass**: ✅ / ❌

---

## Test 5: Cancel Biometric Prompt

**Purpose**: Test graceful handling of user cancellation

**Steps**:
1. Lock wallet
2. Click WebAuthn unlock button
3. **Cancel** the biometric prompt (click Cancel or press Esc)

**Expected Result**:
- ✅ No crash or freeze
- ✅ Error message shown
- ✅ Can retry or use passcode
- ✅ Wallet stays locked

**Result**:
- Handled gracefully: ✅ / ❌
- Error message: ________________
- Can retry: ✅ / ❌

**Pass**: ✅ / ❌

---

## Test 6: Wrong Biometric (if possible)

**Purpose**: Test handling of authentication failure

**Steps**:
1. Lock wallet
2. Click WebAuthn unlock button
3. Try to authenticate with **wrong finger** (if multi-finger system)
4. Or try 3 times with incorrect authentication

**Expected Result**:
- ✅ Error message displayed
- ✅ Allow retry (up to 3 times)
- ✅ After 3 failures, suggest passcode
- ✅ Fallback option available

**Result**:
- Error handling: ✅ / ❌
- Retry allowed: ✅ / ❌
- Fallback shown: ✅ / ❌

**Pass**: ✅ / ❌

---

## Test 7: WebAuthn Transaction Signing

**Purpose**: Test biometric verification for signing transactions

**Steps**:
1. Create a test transaction (send ADA)
2. Navigate to transaction confirmation/signing page
3. Look for WebAuthn signing button:
   - "Sign with Touch ID"
   - "Sign with Face ID"
   - "Sign with Windows Hello"
4. Click the button
5. Authenticate with biometric
6. Wait for transaction to sign

**Expected Result**:
- ✅ Biometric prompt appears
- ✅ Verification completes quickly (<3 seconds)
- ✅ Transaction signs successfully
- ✅ Success message or transaction confirmation

**Result**:
- Prompt shown: ✅ / ❌
- Signing succeeded: ✅ / ❌
- Transaction confirmed: ✅ / ❌
- Any errors: ________________

**Pass**: ✅ / ❌

---

## Test 8: Re-Enrollment

**Purpose**: Test overwriting existing WebAuthn credential

**Steps**:
1. Complete Test 3 first (have existing enrollment)
2. Navigate back to biometric settings
3. Click enrollment button again
4. Authenticate with biometric

**Expected Result**:
- ✅ Re-enrollment works without errors
- ✅ Old credential replaced with new one
- ✅ No data corruption
- ✅ Verification still works after re-enrollment

**Result**:
- Re-enrollment succeeded: ✅ / ❌
- Verification works after: ✅ / ❌

**Pass**: ✅ / ❌

---

## Test 9: Offline Functionality

**Purpose**: Verify WebAuthn works without internet

**Steps**:
1. Disconnect from internet (turn off WiFi)
2. Try to unlock wallet with WebAuthn
3. Try to sign transaction with WebAuthn

**Expected Result**:
- ✅ WebAuthn still works (100% local)
- ✅ No network errors
- ✅ Same performance as online

**Result**:
- Works offline: ✅ / ❌
- No errors: ✅ / ❌

**Pass**: ✅ / ❌

---

## Test 10: Browser Console Errors

**Purpose**: Check for JavaScript errors

**Steps**:
1. Keep browser console open during all tests
2. Look for errors (red text) in console
3. Note any warnings (yellow text)

**Expected Result**:
- ✅ No critical errors
- ⚠️ Warnings are acceptable

**Result**:
- Any errors: ________________
- Any warnings: ________________

**Pass**: ✅ / ❌

---

## Summary

**Device Tested**: ________________
**Browser**: ________________
**OS**: ________________
**Biometric Type**: ________________

**Test Results**:
- Test 1 (Availability): ✅ / ❌
- Test 2 (Detection): ✅ / ❌
- Test 3 (Enrollment): ✅ / ❌
- Test 4 (Unlock): ✅ / ❌
- Test 5 (Cancel): ✅ / ❌
- Test 6 (Wrong Biometric): ✅ / ❌
- Test 7 (Transaction): ✅ / ❌
- Test 8 (Re-Enrollment): ✅ / ❌
- Test 9 (Offline): ✅ / ❌
- Test 10 (Console): ✅ / ❌

**Overall**: _____ / 10 tests passed

**Issues Found**: (list any problems)
1.
2.
3.

**Screenshots**: (attach any relevant screenshots)

---

## Next Steps

If all tests pass:
- ✅ Mark WebAuthn implementation as production-ready
- ✅ Document in user guide
- ✅ Add to release notes

If tests fail:
- ❌ Create bug reports for failed tests
- ❌ Fix issues
- ❌ Re-test

---

**Tester Name**: ________________
**Date**: ________________
**Time Spent**: _______ minutes
**Sign-off**: ________________
