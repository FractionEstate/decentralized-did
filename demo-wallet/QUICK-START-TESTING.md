# 🚀 Quick Start - Testing Fast Onboarding

**Dev Server**: ✅ RUNNING
**URL**: http://localhost:3003
**Status**: Ready for manual testing

---

## 🎯 Quick Test (5 minutes)

### Test 1: Fast Onboarding ⚡

1. **Open browser**: http://localhost:3003
2. **Clear storage**: DevTools → Application → Clear site data
3. **Refresh page**
4. **See WelcomeScreen** with 3 buttons:
   - [ ] ✅ "Create Wallet" (primary, fingerprint icon)
   - [ ] ✅ "Recover with Seed Phrase" (outline, key icon)
   - [ ] ✅ "Recover with Biometry" (outline, lock icon)
5. **Click "Create Wallet"**
6. **Complete biometric enrollment** (or skip)
7. **Verify**:
   - [ ] ✅ Success screen appears immediately
   - [ ] ✅ No seed phrase display (skipped)
   - [ ] ✅ Total time: ~2 minutes

### Test 2: Banner Appears 🔔

8. **Navigate to Credentials tab**
9. **Verify**:
   - [ ] ✅ Banner shows above tabs
   - [ ] ✅ Warning icon + text visible
   - [ ] ✅ "Backup Now" button (orange/warning color)
   - [ ] ✅ Dismiss X button

### Test 3: Deferred Backup 💾

10. **Click "Backup Now"** in banner
11. **Display Step**:
    - [ ] ✅ See 12-word seed phrase (hidden initially)
    - [ ] ✅ Click "View Recovery Phrase" → Words visible
    - [ ] ✅ Warning message shown
    - [ ] ✅ Checkbox: "I have written down..."
    - [ ] ✅ Check checkbox
    - [ ] ✅ "Continue to Verification" enabled
12. **Click "Continue to Verification"**
13. **Verify Step**:
    - [ ] ✅ See 3 word positions (e.g., Word #3, #7, #11)
    - [ ] ✅ Each has 4 button options
    - [ ] ✅ Select CORRECT words (check against display step)
    - [ ] ✅ "Complete Backup" enabled after all 3 selected
14. **Click "Complete Backup"**
15. **Verify**:
    - [ ] ✅ Success toast appears
    - [ ] ✅ Navigate back to tabs
    - [ ] ✅ Banner is GONE

### Test 4: Banner Persistence 🔄

16. **Close app/tab completely**
17. **Reopen** http://localhost:3003
18. **Verify**:
    - [ ] ✅ Banner does NOT reappear (backup complete)

---

## 🐛 Common Issues

### Issue: Banner doesn't show

**Solution**: Check browser console for errors, verify localStorage has `APP_SEED_PHRASE_BACKED_UP = "false"`

### Issue: Verification fails with correct words

**Solution**: Check browser console, words should match exactly (case-sensitive)

### Issue: Build errors

**Solution**: Run `npm run build:local` to check for TypeScript errors

---

## 📊 Expected Results

| Test            | Expected              | Time |
| --------------- | --------------------- | ---- |
| Fast Onboarding | 2 steps, ~2 min       | ✅   |
| Banner Appears  | Visible in tabs       | ✅   |
| Deferred Backup | Show + verify works   | ✅   |
| Banner Gone     | After backup complete | ✅   |

---

## 🔍 Detailed Testing

For comprehensive testing, see:

- **`FAST-ONBOARDING-TEST-PLAN.md`** - 6 detailed scenarios
- **`FAST-ONBOARDING-IMPLEMENTATION.md`** - Technical details
- **`FAST-ONBOARDING-SUMMARY.md`** - Executive summary

---

## 🛠️ Dev Tools Checklist

### Browser Console

```javascript
// Check storage flag
localStorage.getItem("APP_SEED_PHRASE_BACKED_UP");
// Should be "false" after fast onboarding
// Should be "true" after backup complete

// Clear storage (for re-testing)
localStorage.clear();
```

### Network Tab

- Check for API calls (currently mock data)
- Verify no errors

### Responsive Design

Test viewports:

- Mobile: 375x667 (iPhone SE)
- Tablet: 768x1024 (iPad)
- Desktop: 1440x900 (Laptop)

---

## ✅ Success Checklist

After testing, verify:

- [ ] Fast onboarding completes in ~2 min
- [ ] Banner shows/hides correctly
- [ ] Verification works with correct words
- [ ] Verification fails with incorrect words
- [ ] Banner persists until backup complete
- [ ] Design is responsive (mobile, tablet, desktop)
- [ ] No console errors
- [ ] All text is readable

---

**Next**: Document bugs → Fix critical issues → Deploy to staging

**Happy Testing! 🎉**
