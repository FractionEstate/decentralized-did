# Wallet Reset Instructions - "Welcome Back" Lock Screen

## Problem
You're stuck at the "Welcome back" screen and no passcode works. This happens because:
- The wallet expects a **6-digit PIN** (not a complex password)
- Browser storage has partial/test data from previous sessions
- You don't remember setting a passcode during onboarding

## Solution: Reset Wallet to Start Fresh

### Method 1: Clear Browser Storage (RECOMMENDED - Quick)

1. **Open Browser DevTools**
   - Press `F12` or Right-click → Inspect
   - Or press `Ctrl+Shift+I` (Windows/Linux) or `Cmd+Option+I` (Mac)

2. **Go to Application Tab**
   - Click "Application" in the top menu of DevTools
   - (If you don't see it, click the `>>` icon to show more tabs)

3. **Clear All Storage**
   - In the left sidebar, find "Storage" section
   - Click "Clear site data" button
   - OR manually clear:
     - **Local Storage** → `http://localhost:3003` → Right-click → Clear
     - **Session Storage** → `http://localhost:3003` → Right-click → Clear
     - **IndexedDB** → Expand → Right-click each database → Delete
     - **Cookies** → `http://localhost:3003` → Right-click → Clear

4. **Refresh the Page**
   - Press `F5` or `Ctrl+R` (Windows/Linux) or `Cmd+R` (Mac)
   - You should now see the initial onboarding screen (Welcome screen)

---

### Method 2: Clear Storage via Console (FASTEST)

1. **Open Browser Console**
   - Press `F12` → Click "Console" tab

2. **Run This Command**
   ```javascript
   // Clear all storage
   localStorage.clear();
   sessionStorage.clear();
   indexedDB.databases().then(dbs => {
     dbs.forEach(db => indexedDB.deleteDatabase(db.name));
   });

   // Clear cookies for localhost:3003
   document.cookie.split(";").forEach(c => {
     document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
   });

   console.log("✅ Storage cleared! Refresh the page (F5) to start fresh.");
   ```

3. **Refresh the Page**
   - Press `F5`
   - Should now show onboarding

---

### Method 3: Use "Forgot Passcode" Button

**If you see a "Forgot?" or "Forgot Passcode?" button on the lock screen:**

1. Click the "Forgot?" link/button
2. You'll be asked to verify your **seed phrase** (12-24 words)
3. If you have the seed phrase, enter it to reset your passcode
4. If you DON'T have the seed phrase:
   - Use Method 1 or 2 above to completely reset
   - You'll lose any wallet data (this is a dev/test wallet anyway)

---

## After Reset: Set Your Passcode Correctly

### During Onboarding (SimplifiedOnboarding Flow):

1. **Welcome Screen**
   - Click "Get Started" or "Create Wallet"

2. **Biometric Setup Screen** (if shown)
   - You can skip biometrics for now
   - Or set up fingerprint/face if on mobile device

3. **Set Passcode Screen**
   - Enter a **6-digit PIN** (e.g., `123456` for testing)
   - Re-enter the same 6-digit PIN to confirm
   - **REMEMBER THIS PIN!** Write it down for testing

4. **Success Screen**
   - You'll see "Wallet created successfully!"
   - You can now access the wallet

### Important Notes:

- **Passcode** = 6-digit PIN (e.g., `193212`, `123456`)
- **Password** = Complex alphanumeric password (optional, can be enabled later in Settings)
- **Biometric** = Fingerprint/Face ID (optional, can be enabled later)

The "Welcome back" lock screen ONLY accepts the **6-digit passcode**, not the password!

---

## Testing/Development Passcode

If you need a standard passcode for testing:
- **Test PIN**: `193212` (used in some test files)
- **Easy PIN**: `123456` (easy to remember)
- **Your PIN**: Choose any 6-digit number you'll remember

**Set this during the onboarding "Set Passcode" screen!**

---

## Troubleshooting

### "I cleared storage but still see lock screen"
- Try **hard refresh**: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
- Or close the browser tab completely and reopen http://localhost:3003/

### "I don't see Application tab in DevTools"
- Click the `>>` icon in DevTools top menu
- Select "Application" from the dropdown

### "IndexedDB won't delete"
- Close all tabs with `localhost:3003`
- Open a new tab
- Run the console command (Method 2)
- Then reopen the wallet

### "Lock screen has no 'Forgot' button"
- Use Method 1 or 2 to clear storage completely
- This is the fastest way to reset for development

---

## For Future Testing

To avoid this issue:
1. **Remember your 6-digit PIN** during onboarding
2. Write it down (it's just for testing)
3. Use a standard test PIN like `193212` or `123456`
4. If you mess up, use Method 2 (console command) to quickly reset

---

## Technical Details (for developers)

The wallet uses:
- **KeyStoreKeys.APP_PASSCODE**: 6-digit PIN for app lock (what the "Welcome back" screen uses)
- **KeyStoreKeys.APP_OP_PASSWORD**: Optional complex password (for sensitive operations, set in Settings)
- **Biometrics**: Optional fingerprint/face authentication (mobile only)

The LockPage specifically checks `APP_PASSCODE` - this is why your password doesn't work!

---

**Status**: After clearing storage and going through onboarding with a fresh 6-digit PIN, you should be able to unlock the wallet! 🚀
