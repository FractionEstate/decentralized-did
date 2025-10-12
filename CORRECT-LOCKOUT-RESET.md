# CORRECT CODE - Reset Login Lockout

## The Problem
You're locked out after multiple failed PIN attempts. The wallet won't accept your PIN even if it's correct.

## The Fix - Correct Database Name

The wallet uses IndexedDB database named **`_ionickv/idw`** (not `ionic-signinApp`).

---

## ✅ CORRECT Reset Code

**Open Browser Console (F12 → Console tab) and paste this:**

```javascript
// CORRECT CODE - Reset login attempts lockout
(async function resetLockout() {
  try {
    // Open the correct database: _ionickv/idw
    const dbRequest = indexedDB.open('_ionickv/idw');

    dbRequest.onerror = function() {
      console.error('❌ Could not open database _ionickv/idw');
      console.log('💡 Try clearing all storage instead (see Option B below)');
    };

    dbRequest.onsuccess = function(event) {
      console.log('✅ Database opened successfully');
      const db = event.target.result;

      // Check if the objectStore exists
      if (!db.objectStoreNames.contains('_ionickv')) {
        console.error('❌ Object store "_ionickv" not found');
        console.log('💡 Database might be empty. Try clearing storage (Option B)');
        return;
      }

      const transaction = db.transaction(['_ionickv'], 'readwrite');
      const store = transaction.objectStore('_ionickv');

      // Get login metadata
      const getRequest = store.get('app.agent.basicStorage.login-metadata');

      getRequest.onerror = function() {
        console.error('❌ Could not read login metadata');
      };

      getRequest.onsuccess = function() {
        const data = getRequest.result;

        if (!data) {
          console.log('⚠️ No login metadata found - wallet might not be initialized');
          console.log('💡 Try going through onboarding again (clear storage first)');
          return;
        }

        console.log('📊 Current login attempts:', data.content.attempts);
        console.log('🔒 Locked until:', new Date(data.content.lockedUntil).toLocaleString());

        // Reset the attempts
        data.content.attempts = 0;
        data.content.lockedUntil = Date.now();

        const putRequest = store.put(data);

        putRequest.onerror = function() {
          console.error('❌ Could not update login metadata');
        };

        putRequest.onsuccess = function() {
          console.log('✅✅✅ LOCKOUT RESET SUCCESSFUL! ✅✅✅');
          console.log('');
          console.log('👉 Press F5 to refresh the page');
          console.log('👉 Then try your 6-digit PIN again');
          console.log('');
          console.log('⚠️ You have 5 attempts before being locked out again!');
        };
      };
    };
  } catch (error) {
    console.error('❌ Error:', error);
    console.log('💡 Try Option B: Clear all storage');
  }
})();
```

**After running the code:**
1. You should see `✅✅✅ LOCKOUT RESET SUCCESSFUL!`
2. Press **F5** to refresh
3. Enter your PIN carefully (you get 5 attempts)

---

## Option B: If Option A Doesn't Work - Clear All Storage

If the reset code above doesn't work or shows errors, clear everything:

```javascript
// Clear all storage - will require going through onboarding again
(async function clearAll() {
  console.log('🗑️ Clearing all storage...');

  localStorage.clear();
  sessionStorage.clear();

  const databases = await indexedDB.databases();
  console.log('📊 Found databases:', databases.map(db => db.name).join(', '));

  for (const db of databases) {
    indexedDB.deleteDatabase(db.name);
    console.log('🗑️ Deleted:', db.name);
  }

  console.log('');
  console.log('✅ All storage cleared!');
  console.log('👉 Press F5 to refresh');
  console.log('👉 Go through onboarding and set a new PIN');
  console.log('💡 Suggested test PIN: 123456 (easy to remember)');
})();
```

Then press **F5** and set up the wallet again with a fresh PIN.

---

## Quick Reference

### **Just Reset Lockout (keeps wallet):**
```javascript
(async function() { const r = indexedDB.open('_ionickv/idw'); r.onsuccess = e => { const d = e.target.result; const t = d.transaction(['_ionickv'], 'readwrite'); const s = t.objectStore('_ionickv'); const g = s.get('app.agent.basicStorage.login-metadata'); g.onsuccess = () => { if(g.result) { g.result.content.attempts = 0; g.result.content.lockedUntil = Date.now(); s.put(g.result); console.log('✅ Reset! Press F5'); } }; }; })();
```

### **Clear Everything (fresh start):**
```javascript
(async function() { localStorage.clear(); sessionStorage.clear(); (await indexedDB.databases()).forEach(db => indexedDB.deleteDatabase(db.name)); console.log('✅ Cleared! Press F5'); })();
```

---

## Verification

After resetting, you can verify it worked:

```javascript
// Check current login attempts
(async function() {
  const r = indexedDB.open('_ionickv/idw');
  r.onsuccess = e => {
    const d = e.target.result;
    const t = d.transaction(['_ionickv'], 'readonly');
    const s = t.objectStore('_ionickv');
    const g = s.get('app.agent.basicStorage.login-metadata');
    g.onsuccess = () => {
      if(g.result) {
        console.log('📊 Attempts:', g.result.content.attempts);
        console.log('🔒 Locked until:', new Date(g.result.content.lockedUntil).toLocaleString());
      }
    };
  };
})();
```

Should show: `Attempts: 0`

---

## Remember

- **Database name**: `_ionickv/idw` (not `ionic-signinApp`)
- **Object store**: `_ionickv`
- **Key**: `app.agent.basicStorage.login-metadata`
- **PIN**: 6 digits (e.g., `123456`, not a complex password)
- **Attempts**: You get 5 tries before lockout

---

**Status:** The correct code above will reset your lockout counter. Press F5 after running it, then try your PIN! 🚀
