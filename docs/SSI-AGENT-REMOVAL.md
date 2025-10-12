# SSI Agent Removal Documentation

**Date**: October 12, 2025
**Reason**: Biometric DID wallet doesn't use Hyperledger Aries SSI Agent
**Impact**: No functionality loss - routing already bypassed in commit `eab8b68`

---

## Why We're Removing SSI Agent

### Background
The demo-wallet is based on Cardano Foundation's Veridian wallet, which includes integration with Hyperledger Aries for SSI (Self-Sovereign Identity) agent functionality. However, our **Biometric DID** approach doesn't require an external SSI agent.

### Previous Fix (Commit eab8b68)
We already bypassed the SSI Agent in the onboarding flow:
```typescript
// Before: Users routed to SSI Agent setup after seed phrase
if (authentication.seedPhraseIsSet) {
  path = RoutePath.SSI_AGENT; // ❌ Confusing for users
}

// After: Users go directly to main app
if (authentication.seedPhraseIsSet) {
  path = RoutePath.TABS_MENU; // ✅ Direct to wallet
}
```

### Current State
- **Routing**: SSI Agent completely bypassed ✅
- **UI Components**: Still present but unused ⚠️
- **Route Definition**: Still registered but unreachable ⚠️
- **Tests**: Still present but testing dead code ⚠️

---

## Files Being Removed

### 1. UI Component Files (5 files, ~1,200+ lines)

#### `/demo-wallet/src/ui/pages/CreateSSIAgent/CreateSSIAgent.tsx`
- **Lines**: 558 lines
- **Purpose**: Main SSI Agent setup component
- **Dependencies**:
  - Agent.agent.config (SSI agent configuration)
  - ConfigurationService (boot/connect URLs)
  - Various UI components
- **Why Unused**: Route bypassed, never reached in normal flow

#### `/demo-wallet/src/ui/pages/CreateSSIAgent/CreateSSIAgent.test.tsx`
- **Lines**: ~500 lines
- **Purpose**: Unit tests for CreateSSIAgent
- **Why Unused**: Tests dead code

#### `/demo-wallet/src/ui/pages/CreateSSIAgent/CreateSSIAgent.scss`
- **Lines**: ~50 lines
- **Purpose**: Styles for SSI Agent page
- **Why Unused**: Component never rendered

#### `/demo-wallet/src/ui/pages/CreateSSIAgent/CreateSSIAgent.types.ts`
- **Lines**: ~20 lines
- **Purpose**: TypeScript types for SSI Agent
- **Why Unused**: Component never used

#### `/demo-wallet/src/ui/pages/CreateSSIAgent/index.ts`
- **Lines**: 1 line
- **Purpose**: Barrel export
- **Why Unused**: No imports needed

**Total**: ~1,129 lines of unused code

---

### 2. Route Definitions (2 files, ~50 lines)

#### `/demo-wallet/src/routes/index.tsx`
**Removing**:
```typescript
import { CreateSSIAgent } from "../ui/pages/CreateSSIAgent";

<Route
  path={RoutePath.SSI_AGENT}
  component={CreateSSIAgent}
  exact
/>
```
- **Impact**: Route definition removed (already unreachable)

#### `/demo-wallet/src/routes/paths.ts`
**Keeping** (referenced in other places):
```typescript
SSI_AGENT = "/ssiagent", // Keep for backwards compatibility
```
- **Note**: Path enum kept but route never registered

---

### 3. Route Logic (1 file, ~10 lines)

#### `/demo-wallet/src/routes/nextRoute/nextRoute.ts`
**Removing**:
```typescript
const getNextCreateSSIAgentRoute = () => {
  return RoutePath.TABS_MENU;
};

// In exports:
getNextCreateSSIAgentRoute,
```
- **Impact**: Function removed (never called)

---

### 4. Test Files (1 file, ~20 lines)

#### `/demo-wallet/src/routes/nextRoute/nextRoute.test.ts`
**Removing**:
```typescript
import { getNextCreateSSIAgentRoute } from "./nextRoute";

describe("getNextCreateSSIAgentRoute", () => {
  it("should return TABS_MENU", () => {
    const result = getNextCreateSSIAgentRoute();
    expect(result).toBe(RoutePath.TABS_MENU);
  });
});
```
- **Impact**: Test removed (function removed)

---

## What We're Keeping

### Route Path Enum
**File**: `/demo-wallet/src/routes/paths.ts`
```typescript
SSI_AGENT = "/ssiagent", // Kept for backwards compatibility
```
**Reason**:
- May be referenced in stored user data
- Prevents routing errors if old links exist
- Can be removed in future major version

### Routing Logic Comments
**File**: `/demo-wallet/src/routes/nextRoute/nextRoute.ts`
```typescript
// BIOMETRIC DID: Skip SSI Agent entirely - we don't use Hyperledger Aries
if (authentication.seedPhraseIsSet) {
  path = RoutePath.TABS_MENU;
}
```
**Reason**: Documents why SSI Agent is skipped

---

## Migration Path

### For Users
- **No impact**: Users never see SSI Agent page
- **Flow unchanged**: Onboarding → Seed Phrase → Main App
- **Data safe**: No SSI Agent data was ever stored

### For Developers
- **Remove imports**: Delete `CreateSSIAgent` imports from route files
- **Update tests**: Remove tests for `getNextCreateSSIAgentRoute`
- **Documentation**: This file serves as historical record

---

## Verification Steps

After removal, verify:
1. ✅ App compiles without errors
2. ✅ Onboarding flow works (SimplifiedOnboarding → TABS_MENU)
3. ✅ No broken imports
4. ✅ No TypeScript errors
5. ✅ Tests pass (excluding removed tests)
6. ✅ Bundle size reduced by ~50KB (estimated)

---

## Cleanup Commands

```bash
# 1. Remove CreateSSIAgent directory
rm -rf demo-wallet/src/ui/pages/CreateSSIAgent/

# 2. Remove import from routes
# Edit: demo-wallet/src/routes/index.tsx
# Remove: import { CreateSSIAgent } from "../ui/pages/CreateSSIAgent";
# Remove: <Route path={RoutePath.SSI_AGENT} component={CreateSSIAgent} exact />

# 3. Remove routing function
# Edit: demo-wallet/src/routes/nextRoute/nextRoute.ts
# Remove: const getNextCreateSSIAgentRoute = () => { ... }
# Remove: export { getNextCreateSSIAgentRoute }

# 4. Remove test
# Edit: demo-wallet/src/routes/nextRoute/nextRoute.test.ts
# Remove: test for getNextCreateSSIAgentRoute

# 5. Verify build
cd demo-wallet
npm run build

# 6. Verify tests
npm test
```

---

## Related Commits

- **eab8b68**: Skip SSI Agent setup in onboarding flow
  - Bypassed SSI Agent routing
  - Users go directly to TABS_MENU

- **4430001**: Phase 2 UX polish
  - Hidden Credentials tab
  - User-friendly error messages

- **This commit**: Remove SSI Agent UI components
  - Delete ~1,200 lines of unused code
  - Clean up imports and routes
  - Document removal for future reference

---

## Future Considerations

### If SSI Agent Needed Later
1. Restore files from git history:
   ```bash
   git checkout eab8b68 -- demo-wallet/src/ui/pages/CreateSSIAgent/
   ```
2. Re-add route registration
3. Update routing logic to include SSI Agent step
4. Configure Hyperledger Aries connection

### Alternative: Biometric DID Integration
Our approach uses **biometric templates** instead of SSI Agent:
- Fingerprint data → Biometric DID
- Seed phrase → Cardano wallet
- No external SSI agent required
- Simpler user experience

---

## Summary

**Removed**:
- ❌ CreateSSIAgent component (558 lines)
- ❌ CreateSSIAgent tests (500 lines)
- ❌ CreateSSIAgent styles (50 lines)
- ❌ CreateSSIAgent types (20 lines)
- ❌ Route registration (5 lines)
- ❌ Routing function (10 lines)
- ❌ Test for routing function (20 lines)

**Total Removed**: ~1,163 lines of unused code

**Kept**:
- ✅ SSI_AGENT path enum (backwards compatibility)
- ✅ Comments explaining why SSI Agent is skipped
- ✅ This documentation for future reference

**Impact**:
- ✅ No functionality loss
- ✅ Cleaner codebase
- ✅ Reduced bundle size
- ✅ Easier maintenance
- ✅ Less confusion for developers

---

**Status**: ⏳ Ready to Execute
**Risk**: 🟢 Low (code already bypassed)
**Benefit**: 🟢 High (cleaner codebase, smaller bundle)
