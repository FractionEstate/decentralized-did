# Fast Onboarding Test Plan

**Date**: October 27, 2025
**Status**: Ready for Testing
**Implementation**: Complete ✅

---

## 🎯 Test Objectives

Verify that the Vespr-style fast onboarding works correctly:

1. Users can create wallet without forced seed phrase backup
2. Warning banner appears after fast onboarding
3. Deferred backup flow works correctly
4. Banner disappears after successful backup

---

## 📋 Test Scenarios

### Scenario 1: Fast Onboarding (New Feature) ⚡

**Objective**: Test the fast wallet creation flow

**Steps**:

1. Open app (fresh install or cleared data)
2. Should see WelcomeScreen with 3 buttons:
   - ✅ "Create Wallet" (primary button with fingerprint icon)
   - ✅ "Recover with Seed Phrase" (outline button with key icon)
   - ✅ "Recover with Biometry" (outline button with lock icon)
3. Click "Create Wallet"
4. Should navigate to BiometricScanScreen
5. Complete biometric enrollment (10 fingers or skip some)
6. Should see SuccessScreen immediately (skip seed phrase steps)
7. Navigate to Credentials/Identifiers tab
8. **Expected**: BackupWarningBanner should appear at top with:
   - ⚠️ Warning icon
   - "Backup your recovery phrase" heading
   - Explanation text
   - "Backup Now" button (warning color)
   - Dismiss X button

**Expected Results**:

- ✅ Fast flow completes in 2 steps (Welcome → Biometric → Success)
- ✅ Total time: ~2 minutes (vs 5 minutes traditional)
- ✅ Banner visible in all tabs
- ✅ Banner persists across app restarts (until backup complete)

**Test Data**:

- No seed phrase displayed during onboarding
- Seed phrase generated in background (stored encrypted)
- Flag `APP_SEED_PHRASE_BACKED_UP = "false"` stored in Agent.basicStorage

---

### Scenario 2: Deferred Backup Flow (New Feature) 💾

**Objective**: Test the backup now functionality

**Prerequisites**: Complete Scenario 1 (fast onboarding)

**Steps**:

1. From any tab, click "Backup Now" in banner
2. Should navigate to DeferredBackup page
3. **Display Step**:
   - Should see 12-word seed phrase (grid layout)
   - "View Recovery Phrase" button to reveal words
   - Warning message about importance
   - Checkbox: "I have written down my recovery phrase..."
   - "Continue to Verification" button (disabled until checkbox + words revealed)
4. Click "View Recovery Phrase" → Words should be visible
5. Check the confirmation checkbox
6. Click "Continue to Verification"
7. **Verify Step**:
   - Should see 3 word positions (e.g., Word #3, Word #7, Word #11)
   - Each has 4 button options (1 correct + 3 random words)
   - "Complete Backup" button (disabled until all 3 selected)
   - "Back" button to return to display
8. Select CORRECT words for all 3 positions
9. Click "Complete Backup"
10. Should see success toast: "✅ Recovery phrase backed up successfully!"
11. Should navigate back to tabs
12. **Expected**: Banner should be GONE

**Expected Results**:

- ✅ Seed phrase displayed correctly (same 12 words)
- ✅ Verification uses 3 random positions
- ✅ Each word has 4 shuffled options
- ✅ Correct selection → Success toast + banner disappears
- ✅ Flag `APP_SEED_PHRASE_BACKED_UP = "true"` stored
- ✅ Banner doesn't reappear on app restart

**Test Data**:

- Seed phrase: 12 words from BIP39 wordlist
- Verification positions: Random selection (e.g., [2, 6, 11])
- Options: 4 per word (1 correct + 3 random distractors)

---

### Scenario 3: Incorrect Verification (Error Handling) ❌

**Objective**: Test error handling for wrong word selection

**Prerequisites**: Complete Scenario 1, start Scenario 2

**Steps**:

1. Navigate to verification step (Scenario 2, steps 1-7)
2. Select INCORRECT word for at least one position
3. Click "Complete Backup"
4. Should see error toast: "❌ Incorrect words selected. Please try again."
5. **Expected**: Stay on verification page, try again
6. Select correct words
7. Click "Complete Backup"
8. Should succeed (Scenario 2, steps 10-12)

**Expected Results**:

- ✅ Error toast displayed for incorrect selection
- ✅ User can retry immediately
- ✅ No flag updated until success
- ✅ Banner still shows until success

---

### Scenario 4: Banner Dismiss & Persistence 🔄

**Objective**: Test temporary banner dismissal

**Prerequisites**: Complete Scenario 1 (fast onboarding)

**Steps**:

1. See banner in tabs (Scenario 1, step 8)
2. Click X (dismiss) button
3. **Expected**: Banner disappears
4. Navigate between tabs
5. **Expected**: Banner still gone (session)
6. Close app completely
7. Reopen app
8. **Expected**: Banner reappears (not permanently dismissed)

**Expected Results**:

- ✅ X button dismisses banner for current session
- ✅ Banner reappears on app restart
- ✅ Only way to permanently dismiss: Complete backup

---

### Scenario 5: Traditional Onboarding (Unchanged) 🔙

**Objective**: Verify traditional flow still works

**Steps**:

1. Open app (fresh install)
2. Click "Recover with Seed Phrase"
3. Should navigate to seed phrase entry screen
4. Enter existing 12-word seed phrase
5. Complete recovery flow
6. **Expected**: No banner appears (recovery assumes backup exists)

**Expected Results**:

- ✅ Traditional recovery flow unchanged
- ✅ No banner shown (recovery = already backed up)
- ✅ Flag not set (or set to "true")

---

### Scenario 6: Mobile Responsive Design 📱

**Objective**: Test on different viewports

**Viewports to Test**:

1. Mobile (375x667) - iPhone SE
2. Tablet (768x1024) - iPad
3. Desktop (1440x900) - Laptop

**Elements to Check**:

- BackupWarningBanner:
  - Mobile: Column layout, full-width button
  - Desktop: Row layout, button inline
- DeferredBackup page:
  - Word options: 2 columns mobile, 4 columns desktop
  - Seed phrase grid: Responsive padding
- WelcomeScreen:
  - 3 buttons stack vertically on mobile

**Expected Results**:

- ✅ All elements readable and accessible
- ✅ No overflow or clipping
- ✅ Touch targets ≥ 44px on mobile

---

## 🐛 Known Issues / Edge Cases

### Edge Case 1: Banner in Non-Tab Routes

**Issue**: Banner integrated in TabsMenu, not visible outside tabs
**Impact**: Low (backup only relevant after onboarding complete)
**Test**: Navigate to settings → Banner should show if integrated in parent layout

### Edge Case 2: Multiple Verification Attempts

**Issue**: No limit on retry attempts
**Impact**: Low (user can retry until correct)
**Future**: Consider adding attempt limit or "Show Recovery Phrase" button

### Edge Case 3: App Background/Foreground

**Issue**: Banner check runs on mount only
**Impact**: Low (user sees banner on next tab switch)
**Future**: Consider adding focus/visibility listener to re-check

---

## ✅ Pre-Test Checklist

Before running tests, verify:

- [ ] Webpack build successful (0 errors)
- [ ] Dev server running (`npm run dev`)
- [ ] Browser console open (check for errors)
- [ ] Network tab open (monitor API calls)
- [ ] Local storage cleared (fresh state)
- [ ] Test on Chrome, Firefox, Safari (if possible)

---

## 📊 Test Results Template

### Test Run #1

**Date**: ******\_\_\_\_******
**Tester**: ******\_\_\_\_******
**Environment**: Dev / Staging / Prod
**Browser**: Chrome / Firefox / Safari
**Viewport**: Mobile / Tablet / Desktop

| Scenario                  | Status | Notes |
| ------------------------- | ------ | ----- |
| 1. Fast Onboarding        | ⏳     |       |
| 2. Deferred Backup        | ⏳     |       |
| 3. Incorrect Verification | ⏳     |       |
| 4. Banner Dismiss         | ⏳     |       |
| 5. Traditional Onboarding | ⏳     |       |
| 6. Responsive Design      | ⏳     |       |

**Overall Result**: ⏳ PENDING / ✅ PASS / ❌ FAIL

**Bugs Found**:

1. ***
2. ***

**Notes**:

---

---

## 🚀 Automated Test Ideas (Future)

### Unit Tests

```typescript
// BackupWarningBanner.test.tsx
describe("BackupWarningBanner", () => {
  it("shows when seedPhraseBackedUp = false", async () => {
    // Mock Agent.agent.basicStorage.findById
    // Render component
    // Expect banner visible
  });

  it("hides when seedPhraseBackedUp = true", async () => {
    // Mock with "true" value
    // Render component
    // Expect banner hidden
  });

  it("navigates to DEFERRED_BACKUP on Backup Now click", () => {
    // Render component
    // Click "Backup Now"
    // Expect history.push called with RoutePath.DEFERRED_BACKUP
  });
});

// DeferredBackup.test.tsx
describe("DeferredBackup", () => {
  it("displays seed phrase correctly", async () => {
    // Mock Agent.agent.getBranAndMnemonic
    // Render component
    // Expect 12 words displayed
  });

  it("generates 3 random verification positions", async () => {
    // Render component
    // Expect 3 unique positions
    // Expect each has 4 options
  });

  it("marks backup complete on correct verification", async () => {
    // Render component
    // Select correct words
    // Click Complete Backup
    // Expect Agent.agent.basicStorage.createOrUpdateBasicRecord called
    // Expect value = "true"
  });
});
```

### E2E Tests (Playwright/WebDriverIO)

```typescript
test("fast onboarding with deferred backup", async ({ page }) => {
  // 1. Navigate to app
  await page.goto("/");

  // 2. Click "Create Wallet"
  await page.click('[data-testid="create-wallet-button"]');

  // 3. Complete biometrics (mock)
  // ... biometric enrollment steps

  // 4. Verify success
  await expect(page.locator('[data-testid="success-screen"]')).toBeVisible();

  // 5. Navigate to tabs
  await page.click('[href="/tabs/credentials"]');

  // 6. Verify banner shows
  await expect(page.locator(".backup-warning-banner")).toBeVisible();

  // 7. Click "Backup Now"
  await page.click('[data-testid="backup-now-button"]');

  // 8. Reveal seed phrase
  await page.click('[data-testid="reveal-seed-phrase"]');

  // 9. Confirm checkbox
  await page.click('[data-testid="confirmation-checkbox"]');

  // 10. Continue to verification
  await page.click('[data-testid="continue-verification"]');

  // 11. Select correct words (test data)
  // ... word selection logic

  // 12. Complete backup
  await page.click('[data-testid="complete-backup"]');

  // 13. Verify banner gone
  await expect(page.locator(".backup-warning-banner")).not.toBeVisible();
});
```

---

## 📝 Manual Test Execution

To run manual tests:

```bash
# 1. Start dev server
cd /workspaces/decentralized-did/demo-wallet
npm run dev

# 2. Open browser
# http://localhost:3003

# 3. Clear storage (fresh state)
# Browser DevTools → Application → Clear site data

# 4. Execute test scenarios above
# Document results in template

# 5. Check console for errors
# Browser DevTools → Console

# 6. Verify local storage
# Browser DevTools → Application → Local Storage
# Check for: APP_SEED_PHRASE_BACKED_UP key
```

---

**Next Steps**:

1. ✅ Implementation complete
2. ⏳ Manual testing (execute scenarios)
3. ⏳ Document bugs/issues
4. ⏳ Fix critical bugs
5. ⏳ Update documentation
6. ⏳ Deploy to staging
