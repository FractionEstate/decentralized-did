# Loading States Implementation Guide

## Overview
This guide shows how to add loading states to components to provide clear user feedback during async operations.

## Why Loading States Matter
- **User Trust**: Users know the app is working, not frozen
- **Prevent Double-Clicks**: Disabled buttons during operations
- **Clear Feedback**: Shows what's happening ("Creating wallet...", "Sending payment...")
- **Error Context**: Users understand when something fails

## Pattern: The Standard Approach

```typescript
import { useState } from 'react';
import { useIonToast } from '@ionic/react';
import { 
  LOADING_MESSAGES, 
  SUCCESS_MESSAGES,
  showErrorToast 
} from '../../../utils/userFriendlyErrors';

const MyComponent = () => {
  const [showToast] = useIonToast();
  const [isLoading, setIsLoading] = useState(false);

  const handleAsyncOperation = async () => {
    // 1. Prevent double-clicks
    if (isLoading) return;
    
    // 2. Show loading state
    setIsLoading(true);
    showToast({
      message: LOADING_MESSAGES.saving,
      duration: 0, // Infinite - will dismiss manually
      position: 'top',
      color: 'primary',
    });

    try {
      // 3. Perform async operation
      await someAsyncFunction();

      // 4. Show success message
      await showToast({
        message: SUCCESS_MESSAGES.saved,
        duration: 2000,
        position: 'top',
        color: 'success',
      });
    } catch (error) {
      // 5. Show user-friendly error
      showErrorToast(error, showToast, 'async_operation');
    } finally {
      // 6. Always reset loading state
      setIsLoading(false);
    }
  };

  return (
    <IonButton 
      onClick={handleAsyncOperation}
      disabled={isLoading}
    >
      {isLoading ? (
        <>
          <IonSpinner name="crescent" /> Loading...
        </>
      ) : (
        'Save'
      )}
    </IonButton>
  );
};
```

## Available Messages

### Loading Messages (from `userFriendlyErrors.ts`)
```typescript
LOADING_MESSAGES = {
  scanning: 'Scanning fingerprint...',
  verifying: 'Verifying identity...',
  creating_wallet: 'Creating your wallet...',
  sending: 'Sending payment...',
  loading_wallet: 'Loading wallet...',
  loading: 'Loading...',
  saving: 'Saving...',
  processing: 'Processing...',
}
```

### Success Messages
```typescript
SUCCESS_MESSAGES = {
  biometric_enrolled: '✓ Fingerprint saved successfully!',
  biometric_verified: '✓ Identity confirmed!',
  wallet_created: '✓ Wallet created successfully!',
  transaction_sent: '✓ Payment sent!',
  transaction_confirmed: '✓ Payment confirmed!',
  saved: '✓ Saved successfully!',
  copied: '✓ Copied to clipboard!',
  updated: '✓ Updated successfully!',
  deleted: '✓ Deleted successfully!',
  onboarding_complete: '🎉 You\'re all set! Welcome!',
  seed_phrase_saved: '✓ Recovery words saved!',
  security_setup: '✓ Security setup complete!',
}
```

## Common Patterns

### Pattern 1: Button with Spinner
```tsx
<IonButton 
  onClick={handleAction}
  disabled={isLoading}
>
  {isLoading && <IonSpinner name="crescent" />}
  {isLoading ? 'Creating...' : 'Create Wallet'}
</IonButton>
```

### Pattern 2: Full-Page Spinner
```tsx
{isLoading && (
  <div className="loading-overlay">
    <IonSpinner name="circular" />
    <p>{LOADING_MESSAGES.loading_wallet}</p>
  </div>
)}
```

### Pattern 3: Inline Spinner
```tsx
<div className="status">
  {isLoading ? (
    <>
      <IonSpinner name="dots" />
      <span>{LOADING_MESSAGES.processing}</span>
    </>
  ) : (
    <span>Ready</span>
  )}
</div>
```

### Pattern 4: List with Loading State
```tsx
{isLoading ? (
  <div className="loading-container">
    <IonSpinner />
    <p>Loading items...</p>
  </div>
) : items.length === 0 ? (
  <p>No items found</p>
) : (
  <IonList>
    {items.map(item => <IonItem key={item.id}>{item.name}</IonItem>)}
  </IonList>
)}
```

## Real-World Examples

### Example 1: Create Identifier (Wallet)
**Before**:
```typescript
const handleCreate = async () => {
  try {
    const { identifier } = await Agent.agent.identifiers.createIdentifier(metadata);
    dispatch(setToastMsg(ToastMsgType.IDENTIFIER_CREATED));
  } catch (e) {
    showError("Unable to create identifier", e, dispatch);
  }
};
```

**After**:
```typescript
const [isCreating, setIsCreating] = useState(false);
const [showToast] = useIonToast();

const handleCreate = async () => {
  if (isCreating) return; // Prevent double-clicks
  
  setIsCreating(true);
  showToast({
    message: LOADING_MESSAGES.creating_wallet,
    duration: 0,
    position: 'top',
    color: 'primary',
  });

  try {
    const { identifier } = await Agent.agent.identifiers.createIdentifier(metadata);
    
    await showToast({
      message: SUCCESS_MESSAGES.wallet_created,
      duration: 2000,
      position: 'top',
      color: 'success',
    });
  } catch (e) {
    showErrorToast(e, showToast, 'create_identifier');
  } finally {
    setIsCreating(false);
  }
};

// In JSX:
<IonButton onClick={handleCreate} disabled={isCreating}>
  {isCreating && <IonSpinner name="crescent" />}
  {isCreating ? 'Creating...' : 'Create Wallet'}
</IonButton>
```

### Example 2: Biometric Scan
**Before**:
```typescript
const scanFingerprint = async () => {
  try {
    const result = await BiometricService.scan();
    onSuccess(result);
  } catch (error) {
    console.error('Scan failed:', error);
  }
};
```

**After**:
```typescript
const [isScanning, setIsScanning] = useState(false);
const [showToast] = useIonToast();

const scanFingerprint = async () => {
  if (isScanning) return;
  
  setIsScanning(true);
  showToast({
    message: LOADING_MESSAGES.scanning,
    duration: 0,
    position: 'top',
    color: 'primary',
  });

  try {
    const result = await BiometricService.scan();
    
    await showToast({
      message: SUCCESS_MESSAGES.biometric_verified,
      duration: 1500,
      position: 'top',
      color: 'success',
    });
    
    onSuccess(result);
  } catch (error) {
    showErrorToast(error, showToast, 'biometric_scan');
  } finally {
    setIsScanning(false);
  }
};
```

### Example 3: Send Transaction
**Before**:
```typescript
const sendTransaction = async (amount: number, address: string) => {
  try {
    await WalletService.send(amount, address);
    alert('Sent!');
  } catch (error) {
    alert('Failed: ' + error);
  }
};
```

**After**:
```typescript
const [isSending, setIsSending] = useState(false);
const [showToast] = useIonToast();

const sendTransaction = async (amount: number, address: string) => {
  if (isSending) return;
  
  setIsSending(true);
  showToast({
    message: LOADING_MESSAGES.sending,
    duration: 0,
    position: 'top',
    color: 'primary',
  });

  try {
    await WalletService.send(amount, address);
    
    await showToast({
      message: SUCCESS_MESSAGES.transaction_sent,
      duration: 2000,
      position: 'top',
      color: 'success',
    });
  } catch (error) {
    showErrorToast(error, showToast, 'send_transaction');
  } finally {
    setIsSending(false);
  }
};
```

## Checklist for Adding Loading States

- [ ] Import `useState`, `useIonToast`, loading/success messages
- [ ] Add `isLoading` state variable
- [ ] Check `isLoading` at function start (prevent double-clicks)
- [ ] Set `isLoading = true` before async operation
- [ ] Show loading toast with `duration: 0`
- [ ] Perform async operation in try block
- [ ] Show success toast in try block (after success)
- [ ] Use `showErrorToast()` in catch block
- [ ] Reset `isLoading = false` in finally block
- [ ] Disable button with `disabled={isLoading}`
- [ ] Show spinner in button with conditional rendering
- [ ] Test: Click button, see loading state, see success/error

## Common Mistakes to Avoid

### ❌ Mistake 1: Forgetting `finally`
```typescript
// BAD - loading state never resets if error occurs
try {
  await api();
  setIsLoading(false); // Only runs on success
} catch (e) {
  handleError(e);
}
```

```typescript
// GOOD - loading state always resets
try {
  await api();
} catch (e) {
  handleError(e);
} finally {
  setIsLoading(false); // Always runs
}
```

### ❌ Mistake 2: Not Preventing Double-Clicks
```typescript
// BAD - user can click repeatedly
const handleAction = async () => {
  setIsLoading(true);
  await api();
  setIsLoading(false);
};
```

```typescript
// GOOD - early return if already loading
const handleAction = async () => {
  if (isLoading) return; // Prevent double execution
  setIsLoading(true);
  await api();
  setIsLoading(false);
};
```

### ❌ Mistake 3: Not Disabling Button
```tsx
// BAD - button clickable while loading
<IonButton onClick={handleAction}>
  {isLoading ? 'Loading...' : 'Submit'}
</IonButton>
```

```tsx
// GOOD - button disabled during loading
<IonButton onClick={handleAction} disabled={isLoading}>
  {isLoading ? 'Loading...' : 'Submit'}
</IonButton>
```

### ❌ Mistake 4: Infinite Toast
```typescript
// BAD - loading toast never dismissed
showToast({
  message: LOADING_MESSAGES.saving,
  duration: 0, // Infinite
});
await api();
// No dismissal - toast stays forever!
```

```typescript
// GOOD - show new toast that replaces loading toast
showToast({
  message: LOADING_MESSAGES.saving,
  duration: 0,
});
await api();
await showToast({
  message: SUCCESS_MESSAGES.saved,
  duration: 2000, // Auto-dismisses
});
```

## Priority Components for Loading States

1. **CreateIdentifier** - Wallet creation (high visibility)
2. **SimplifiedOnboarding** - Already done ✅
3. **Credentials** - Loading credentials list
4. **Identifiers** - Loading identifiers list
5. **SetupBiometrics** - Biometric enrollment
6. **VerifyPasscode** - Authentication
7. **Transaction components** - Sending/receiving funds

## Testing Checklist

After adding loading states, test:
- [ ] Click button → See loading spinner
- [ ] Loading message appears in toast
- [ ] Button is disabled during operation
- [ ] Success message appears after completion
- [ ] Error message appears if operation fails
- [ ] Loading state resets after error
- [ ] Double-clicking doesn't cause double execution
- [ ] Loading state works on slow network (throttle to 3G in DevTools)

---

**Last Updated**: October 12, 2025  
**Related Files**: 
- `demo-wallet/src/utils/userFriendlyErrors.ts` (utility)
- `demo-wallet/src/ui/pages/SimplifiedOnboarding/SimplifiedOnboarding.tsx` (example)
