# Fix: "I know the PIN but it won't open"

## Problem
You're entering the correct 6-digit PIN on the "Welcome back" screen, but it's not unlocking the wallet.

## Most Likely Cause: **Lockout After Failed Attempts**

The wallet has security lockout after failed PIN attempts:
- **5 failed attempts** → Locked for **1 minute**
- **6 failed attempts** → Locked for **5 minutes**
- **7 failed attempts** → Locked for **10 minutes**
- **8 failed attempts** → Locked for **15 minutes**
- **9 failed attempts** → Locked for **60 minutes** (1 hour!)

Even if you're entering the correct PIN now, if you tried incorrect PINs before (or accidentally hit wrong numbers), you're temporarily locked out.

---

## Quick Fixes (Choose One)

### **Option 1: Check for Lockout Message** 👀

**Look at the screen carefully:**
- Does it say "Too many attempts" or "Try again in X minutes"?
- Is there a countdown timer?
- Are the PIN input buttons disabled/grayed out?

**If YES**: You're locked out. Either wait or use Option 2 below.

---

### **Option 2: Reset Login Attempts (FASTEST - 30 seconds)** 🚀

**This resets the failed attempt counter without losing your wallet:**

1. **Open Browser Console**
   - Press `F12` (or Right-click → Inspect)
   - Click "Console" tab

2. **Paste This Code** and press Enter:
   ```javascript
   // Reset login attempts - keeps your wallet data
   (async function() {
     const request = indexedDB.open('_ionickv/ionic-signinApp');
     request.onsuccess = function(e) {
       const db = e.target.result;
       const tx = db.transaction(['_ionickv'], 'readwrite');
       const store = tx.objectStore('_ionickv');
       const get = store.get('app.agent.basicStorage.login-metadata');
       get.onsuccess = function() {
         if (get.result) {
           get.result.content.attempts = 0;
           get.result.content.lockedUntil = Date.now();
           store.put(get.result);
           console.log('✅ Lockout reset! Press F5 to refresh.');
         } else {
           console.log('⚠️ No lockout found. Storage might be corrupted - use Option 3.');
         }
       };
     };
   })();
   ```

3. **Refresh the Page**
   - Press `F5` or `Ctrl+R` (Windows/Linux)
   - Or `Cmd+R` (Mac)

4. **Try Your PIN Again**
   - The lockout should be cleared
   - Enter your 6-digit PIN carefully

---

### **Option 3: Clear Storage & Start Fresh** 🔄

**If Option 2 doesn't work, or you want a clean start:**

1. **Open Browser Console** (F12 → Console tab)

2. **Paste This Code**:
   ```javascript
   // Nuclear option - clears everything
   localStorage.clear();
   sessionStorage.clear();
   indexedDB.databases().then(dbs => dbs.forEach(db => indexedDB.deleteDatabase(db.name)));
   console.log('✅ All storage cleared! Press F5 and go through onboarding again.');
   ```

3. **Refresh** (F5)

4. **Go Through Onboarding Again**
   - Set a new 6-digit PIN
   - Write it down this time!

---

### **Option 4: Wait It Out** ⏰

If you prefer not to use the console:

1. **Check how long you're locked out**:
   - 5 failed attempts = Wait 1 minute
   - 6 failed attempts = Wait 5 minutes
   - 7+ attempts = Wait 10+ minutes (check the on-screen message)

2. **Don't try entering the PIN while locked**
   - This can extend the lockout!

3. **After the lockout expires**:
   - The screen will automatically unlock
   - Enter your PIN carefully (you only get 5 attempts before another lockout!)

---

## Other Possible Issues

### **Issue: PIN is Actually Wrong**

**Test this:**
1. Use Option 2 above to reset the lockout
2. Try these common test PINs:
   - `193212` (from test files)
   - `123456` (common test PIN)
   - `000000` (sometimes used in testing)
3. If none work, use Option 3 to reset completely

### **Issue: Browser Storage Corrupted**

**Symptoms:**
- No lockout message shown
- PIN field accepts input but nothing happens
- Console shows errors like "Cannot read property of undefined"

**Fix:** Use Option 3 (clear all storage)

### **Issue: Dev Server Not Responding**

**Check:**
1. Open browser console (F12) - any JavaScript errors in red?
2. Is `http://localhost:3003/` still responding?
3. Check terminal - is webpack dev server still running?

**Fix:**
```bash
cd /workspaces/decentralized-did/demo-wallet
npm run dev
```

---

## Prevention Tips

### **To Avoid Future Lockouts:**

1. **Write Down Your PIN** during onboarding (it's just for testing)
2. **Use a Simple Test PIN**: `123456` or `193212`
3. **Enter PIN Carefully**: Each wrong attempt counts!
4. **If Unsure**: Use Option 3 (clear storage) instead of guessing

### **Remember:**
- **Passcode** = 6-digit PIN (e.g., `123456`) ← This is what the lock screen uses!
- **Password** = Complex alphanumeric (optional, set in Settings later)
- **Biometric** = Fingerprint/Face (optional, mobile only)

---

## Still Not Working?

If none of these work:

1. **Check Browser Console** (F12 → Console tab)
   - Copy any red error messages
   - Share them for debugging

2. **Check Network Tab** (F12 → Network tab)
   - Refresh the page
   - Are all files loading? (should be green 200 status codes)

3. **Try Different Browser**
   - Sometimes browser-specific issues occur
   - Try Chrome, Firefox, or Edge

4. **Check Dev Server**
   - Terminal should show "webpack compiled successfully"
   - If not, restart: `cd demo-wallet && npm run dev`

---

## Quick Reference

**Most Common Solution:**
```javascript
// Paste in console (F12) and press Enter
(async function() {
  const request = indexedDB.open('_ionickv/ionic-signinApp');
  request.onsuccess = function(e) {
    const db = e.target.result;
    const tx = db.transaction(['_ionickv'], 'readwrite');
    const store = tx.objectStore('_ionickv');
    const get = store.get('app.agent.basicStorage.login-metadata');
    get.onsuccess = function() {
      if (get.result) {
        get.result.content.attempts = 0;
        get.result.content.lockedUntil = Date.now();
        store.put(get.result);
        console.log('✅ Reset! Press F5.');
      }
    };
  };
})();
```

Then press **F5** to refresh and try your PIN again! 🚀

---

**Status:** After resetting the lockout, your correct PIN should work immediately. If it still doesn't work after Option 2, the PIN might be different than you think - use Option 3 to start fresh.
