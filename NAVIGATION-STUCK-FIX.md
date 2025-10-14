# Diagnostic: "Not Progressing to Next Phase" Issue

## Problem
After entering the correct PIN on the lock screen, the app accepts it but doesn't navigate forward.

## Root Causes & Solutions

### **Diagnosis Steps:**

Open browser console (F12 → Console) and run these commands:

#### 1. Check if PIN was accepted:
```javascript
// Check authentication state
const state = window.store?.getState?.();
console.log('🔍 Authentication State:', {
  loggedIn: state?.stateCache?.authentication?.loggedIn,
  loginAttempts: state?.stateCache?.authentication?.loginAttempt?.attempts,
  currentRoute: state?.stateCache?.currentRoute
});
```

**Expected Result**: After successful PIN, `loggedIn` should be `true`

---

#### 2. Check if Redux store is accessible:
```javascript
// Verify Redux store is available
if (window.store) {
  console.log('✅ Redux store found');
  console.log('Current state:', window.store.getState());
} else {
  console.error('❌ Redux store not found in window object');
  console.log('💡 Store might not be exposed in development mode');
}
```

---

#### 3. Force navigation if stuck:
```javascript
// Manual navigation after successful login
// This bypasses any React rendering issues
window.location.hash = '#/tabs/identifiers';
// OR
window.location.href = 'http://localhost:3003/#/tabs/identifiers';
```

---

### **Common Causes:**

#### **Cause 1: React Not Re-rendering**
**Symptom**: `loggedIn` is `true` but LockPage still visible

**Fix**:
```javascript
// Force React to re-render by triggering a state update
const event = new Event('popstate');
window.dispatchEvent(event);
```

---

#### **Cause 2: Router Not Initialized**
**Symptom**: No route configured, app shows blank or spinning

**Check**:
```javascript
// Check if routes are configured
const routes = document.querySelectorAll('[role="main"]');
console.log('Routes found:', routes.length);
```

**Fix**: Refresh the page (F5)

---

#### **Cause 3: Current Route is Public**
**Symptom**: Lock page checks if route is public and stays visible

**Check**:
```javascript
// Check current route
console.log('Current path:', window.location.hash);
console.log('Is public route:', [
  '/onboarding',
  '/simplified-onboarding',
  '/set-passcode',
  '/generate-seed-phrase',
  '/verify-recovery-seed-phrase'
].some(path => window.location.hash.includes(path)));
```

**Fix**: Navigate to protected route manually
```javascript
window.location.hash = '#/tabs/identifiers';
```

---

#### **Cause 4: Initialization Not Complete**
**Symptom**: App still initializing, waiting for Agent setup

**Check**:
```javascript
// Check initialization phase
const state = window.store?.getState?.();
console.log('Initialization phase:', state?.stateCache?.initializationPhase);
// Should be: 'complete' or 'agent-configured'
```

**Fix**: Wait for initialization to complete, or refresh

---

### **Immediate Fix - Force Navigate:**

If you just want to get unstuck RIGHT NOW:

```javascript
// Clear lock state and navigate
localStorage.setItem('authentication.loggedIn', 'true');
window.location.hash = '#/tabs/identifiers';
window.location.reload();
```

---

### **Permanent Fix Needed in Code:**

The issue might be that after `dispatch(login())`, there's no explicit navigation happening. The LockPage should disappear (it checks `authentication.loggedIn`), but if React isn't re-rendering or the router isn't updating, you stay stuck.

**Possible code fix in LockPage.tsx:**

After successful PIN verification, add explicit navigation:

```typescript
// In handlePinChange function, after dispatch(login()):
if (verified) {
  await resetLoginAttempt();
  dispatch(login());
  dispatch(setFirstAppLaunchComplete());
  handleClearState();

  // ADD THIS: Explicit navigation
  const targetRoute = authentication.routes?.[0]?.path || RoutePath.TABS_MENU;
  router.push(targetRoute);
}
```

---

### **Debug Script - Comprehensive Check:**

Paste this in console to see everything:

```javascript
(async function diagnose() {
  console.log('🔍 WALLET DIAGNOSTIC REPORT');
  console.log('============================\n');

  // 1. Check Redux Store
  const hasStore = !!window.store;
  console.log('1️⃣ Redux Store:', hasStore ? '✅ Found' : '❌ Not Found');

  if (hasStore) {
    const state = window.store.getState();

    // 2. Check Authentication
    console.log('\n2️⃣ Authentication:');
    console.log('  - Logged In:', state.stateCache?.authentication?.loggedIn ? '✅ Yes' : '❌ No');
    console.log('  - Login Attempts:', state.stateCache?.authentication?.loginAttempt?.attempts || 0);
    console.log('  - First Launch:', state.stateCache?.authentication?.firstAppLaunch);

    // 3. Check Initialization
    console.log('\n3️⃣ Initialization:');
    console.log('  - Phase:', state.stateCache?.initializationPhase || 'unknown');

    // 4. Check Routes
    console.log('\n4️⃣ Routing:');
    console.log('  - Current Route:', state.stateCache?.currentRoute?.path || 'none');
    console.log('  - URL Hash:', window.location.hash);
    console.log('  - Routes Array:', state.stateCache?.routes?.length || 0, 'routes');
  }

  // 5. Check DOM
  console.log('\n5️⃣ DOM State:');
  const lockPage = document.querySelector('[data-testid*="lock"]');
  console.log('  - Lock Page Visible:', lockPage ? '❌ Yes (stuck!)' : '✅ No');
  const mainContent = document.querySelector('[role="main"]');
  console.log('  - Main Content:', mainContent ? '✅ Found' : '❌ Not Found');

  // 6. Suggestions
  console.log('\n6️⃣ SUGGESTIONS:');
  if (hasStore) {
    const state = window.store.getState();
    if (state.stateCache?.authentication?.loggedIn && lockPage) {
      console.log('  ⚠️ ISSUE: Logged in but lock page still visible!');
      console.log('  💡 FIX: Run this command:');
      console.log('     window.location.hash = "#/tabs/identifiers"; window.location.reload();');
    } else if (!state.stateCache?.authentication?.loggedIn) {
      console.log('  ⚠️ ISSUE: Not logged in yet');
      console.log('  💡 Try entering your 6-digit PIN again');
    }
  }

  console.log('\n============================');
})();
```

---

## Quick Fixes (Choose One):

### **Fix 1: Force Navigate (Fastest)**
```javascript
window.location.hash = '#/tabs/identifiers';
```

### **Fix 2: Reset Everything**
```javascript
localStorage.clear();
sessionStorage.clear();
window.location.reload();
```

### **Fix 3: Clear Lock State**
```javascript
(async function() {
  const r = indexedDB.open('_ionickv/idw');
  r.onsuccess = e => {
    const d = e.target.result;
    const t = d.transaction(['_ionickv'], 'readwrite');
    const s = t.objectStore('_ionickv');
    const g = s.get('app.agent.basicStorage.login-metadata');
    g.onsuccess = () => {
      if(g.result) {
        g.result.content.attempts = 0;
        s.put(g.result);
      }
    };
  };

  // Also update Redux state
  if (window.store) {
    window.store.dispatch({ type: 'stateCache/login' });
  }

  console.log('✅ State reset. Refreshing...');
  setTimeout(() => window.location.reload(), 1000);
})();
```

---

## Next Steps:

1. **Run the diagnostic script** above to see what's stuck
2. **Try Fix 1** (force navigate) to get unstuck immediately
3. **Report the console output** so I can identify the root cause
4. **I'll create a proper fix** in the code to prevent this in the future

---

**Status**: This diagnostic will show exactly where you're stuck and provide an immediate workaround while we identify the root cause for a permanent fix.
