# Demo Wallet Refactoring Plan
## 6 Main Pages Architecture

**Date:** 2025-11-05  
**Objective:** Refactor demo-wallet to properly support 6 main production-ready pages with clean architecture, proper state management, and consistent UX patterns.

---

## Current State Analysis

### ✅ Existing Pages (Implemented)
1. **Wallet (Tokens)** - `/tabs/tokens`
   - Balance display (ADA + native assets)
   - NFT gallery
   - Transaction history
   - **Issues**: Hardcoded demo address, no send/receive functionality

2. **Identity (Identifiers)** - `/tabs/identifiers`
   - DID management
   - Biometric enrollment integration
   - Group identifiers
   - **Issues**: Complex filters, scattered biometric logic

3. **Browser (DAppBrowser)** - `/tabs/dapp-browser`
   - Basic iframe-based browser
   - dApp suggestions
   - **Issues**: No CIP-30 wallet injection, limited security controls

4. **Governance** - `/tabs/governance`
   - DRep listing
   - Proposal viewing
   - Vote tracking
   - **Issues**: No actual voting functionality, placeholder data

5. **Staking** - `/tabs/staking`
   - Account info display
   - Pool listing
   - Rewards history
   - **Issues**: No delegation functionality, hardcoded stake address

6. **Settings** - `/tabs/menu`
   - Account management
   - Security settings
   - Feature navigation
   - **Issues**: Duplicate with legacy Menu page, scattered settings

### ❌ Legacy Pages (To Remove/Consolidate)
- Home `/tabs/home` → Consolidate into Wallet
- NFTs `/tabs/nfts` → Already integrated into Wallet
- Scan `/tabs/scan` → Keep as utility, not main tab
- Notifications `/tabs/notifications` → Keep as utility, not main tab
- Menu `/tabs/legacy-menu` → Remove, functionality in Settings

---

## Refactoring Strategy

### Phase 1: Navigation & Routing Cleanup
**Priority: HIGH**

#### 1.1 Update TabsMenu Configuration
- [x] Verify current 6-tab structure is correct
- [ ] Remove legacy route references
- [ ] Ensure Settings is properly mapped (not Menu)
- [ ] Update tab icons and labels

#### 1.2 Clean Up Route Definitions
- [ ] Remove `/tabs/home`, `/tabs/nfts` from main navigation
- [ ] Keep Scan and Notifications as secondary routes (accessible but not tabbed)
- [ ] Consolidate Settings/Menu into single Settings page

### Phase 2: Settings Page Consolidation
**Priority: HIGH**

#### 2.1 Merge Menu and Settings
- [ ] Keep Settings.tsx as primary implementation
- [ ] Migrate any missing Menu.tsx functionality to Settings
- [ ] Remove SubMenu complexity where unnecessary
- [ ] Add proper subsections:
  - Account (Profile, Connections, Wallet Connect)
  - Security (Passcode, Recovery, Biometrics)
  - Advanced (Link to other 5 main pages)
  - Support (Docs, Terms, Help, Version)

#### 2.2 Improve Settings Navigation
- [ ] Add back navigation from sub-pages
- [ ] Implement proper modal/slide patterns
- [ ] Add search/filter for settings items

### Phase 3: Wallet Page Enhancement
**Priority: HIGH**

#### 3.1 Remove Hardcoded Data
- [ ] Remove `DEMO_ADDRESS` constant
- [ ] Connect to actual wallet state from Redux
- [ ] Add wallet address selector if multiple addresses

#### 3.2 Add Core Functionality
- [ ] Implement "Send ADA" button with transaction builder
- [ ] Implement "Receive" button with address QR code
- [ ] Add "Copy Address" quick action
- [ ] Improve error handling for Koios API failures

#### 3.3 Enhance UI/UX
- [ ] Add pull-to-refresh on all tabs
- [ ] Improve loading skeletons
- [ ] Add empty states with helpful CTAs
- [ ] Optimize NFT image loading (lazy load + IPFS gateway fallback)

### Phase 4: Identity Page Cleanup
**Priority: MEDIUM**

#### 4.1 Simplify Biometric Integration
- [ ] Consolidate biometric enrollment flow
- [ ] Ensure DID generation uses SDK properly
- [ ] Add proper error handling for biometric failures
- [ ] Document SDK integration pattern

#### 4.2 Improve Identifier Management
- [ ] Simplify filters (Active, Archived, Groups)
- [ ] Add search functionality
- [ ] Improve card display with better metadata
- [ ] Add identifier export/backup feature

### Phase 5: Browser Page Upgrade
**Priority: MEDIUM**

#### 5.1 Implement CIP-30 Wallet Connector
- [ ] Create CIP-30 API shim for iframe injection
- [ ] Implement wallet.enable() flow with user approval
- [ ] Add getBalance(), getUsedAddresses(), getUnusedAddresses()
- [ ] Implement signTx() with transaction approval UI
- [ ] Add submitTx() with proper error handling

#### 5.2 Security Enhancements
- [ ] Add CSP headers for iframe sandboxing
- [ ] Implement dApp permission management
- [ ] Add connection whitelist/blacklist
- [ ] Show active permissions in dApp list

#### 5.3 UX Improvements
- [ ] Add bookmarks feature
- [ ] Implement browser history
- [ ] Add tab management (multiple dApps)
- [ ] Improve navigation controls (back/forward with iframe history API)

### Phase 6: Governance Page Completion
**Priority: MEDIUM**

#### 6.1 Connect to Real Data
- [ ] Integrate with Cardano governance endpoints (CIP-1694)
- [ ] Fetch proposals from actual on-chain data
- [ ] Display DRep information from metadata registry

#### 6.2 Implement Voting
- [ ] Add "Vote" button on proposals
- [ ] Build governance voting transaction
- [ ] Show vote confirmation modal
- [ ] Track user's voting history

#### 6.3 Delegation Management
- [ ] Add DRep delegation interface
- [ ] Show current delegation status
- [ ] Implement delegate/undelegate transactions

### Phase 7: Staking Page Completion
**Priority: MEDIUM**

#### 7.1 Connect to Wallet State
- [ ] Remove `DEMO_STAKE_ADDRESS`
- [ ] Derive stake address from wallet
- [ ] Show correct account balance

#### 7.2 Implement Delegation
- [ ] Add "Delegate to Pool" button
- [ ] Implement pool search/filter
- [ ] Build delegation certificate transaction
- [ ] Show delegation confirmation

#### 7.3 Rewards Management
- [ ] Add "Withdraw Rewards" button
- [ ] Calculate available rewards
- [ ] Build withdrawal transaction
- [ ] Show reward history with better formatting

### Phase 8: Shared Components
**Priority: LOW**

#### 8.1 Extract Common Patterns
- [ ] Create `<EmptyState>` component (icon, title, description, CTA)
- [ ] Create `<LoadingPlaceholder>` component (skeleton screens)
- [ ] Create `<ErrorDisplay>` component (error message, retry button)
- [ ] Create `<RefreshableContent>` wrapper (pull-to-refresh + auto-retry)

#### 8.2 Standardize Data Fetching
- [ ] Create custom hooks: `useTokens()`, `useStaking()`, `useGovernance()`
- [ ] Implement consistent loading/error states
- [ ] Add request caching and deduplication

### Phase 9: Testing & Documentation
**Priority: LOW**

#### 9.1 Add Tests
- [ ] Unit tests for each main page component
- [ ] Integration tests for wallet operations
- [ ] E2E tests for critical flows (send, delegate, vote)

#### 9.2 Update Documentation
- [ ] Update README with 6-page architecture overview
- [ ] Create user guides for each main feature
- [ ] Document component patterns and conventions
- [ ] Add developer setup guide

### Phase 10: Performance & Polish
**Priority: LOW**

#### 10.1 Optimize Performance
- [ ] Add React.memo to expensive components
- [ ] Implement virtual scrolling for long lists (transactions, NFTs)
- [ ] Optimize Redux selectors with reselect
- [ ] Code split pages for faster initial load

#### 10.2 Final Polish
- [ ] Add loading transitions
- [ ] Implement consistent error toasts
- [ ] Add haptic feedback for mobile
- [ ] Ensure WCAG 2.1 AA accessibility compliance

---

## Implementation Order

### Week 1 (High Priority)
1. ✅ Audit current pages (Task 1)
2. Settings page consolidation (Task 2)
3. Navigation cleanup (Task 8)
4. Wallet page enhancement (Task 3)

### Week 2 (Medium Priority)
5. Identity page cleanup (Task 4)
6. Browser CIP-30 integration (Task 5)
7. Governance voting (Task 6)
8. Staking delegation (Task 7)

### Week 3 (Low Priority - Polish)
9. Shared components extraction (Task 11)
10. Testing (Task 12)
11. Documentation (Task 13)
12. Performance optimization (Task 14)
13. Final validation (Task 15)

---

## Success Criteria

### Functional Requirements
- ✅ All 6 pages accessible via bottom tab navigation
- [ ] No hardcoded demo addresses in production code
- [ ] All pages connect to real wallet state
- [ ] Send/Receive/Delegate/Vote functionality works
- [ ] CIP-30 wallet connector functional in browser
- [ ] Proper error handling on all API calls
- [ ] Loading states for all async operations

### Code Quality
- [ ] Zero TypeScript errors
- [ ] All components properly typed
- [ ] Redux state properly structured
- [ ] No prop-drilling (use hooks/context where appropriate)
- [ ] Consistent naming conventions
- [ ] Proper code documentation

### UX Requirements
- [ ] Consistent design language across all 6 pages
- [ ] Smooth animations and transitions
- [ ] Responsive layouts (mobile-first)
- [ ] Accessible to screen readers
- [ ] Offline-capable where appropriate
- [ ] Fast page loads (<2s)

### Testing
- [ ] Unit test coverage >70%
- [ ] Integration tests for critical flows
- [ ] E2E tests for happy paths
- [ ] Manual QA checklist completed

---

## Notes

### Architectural Decisions
1. **Keep 6-page structure**: Wallet, Identity, Browser, Governance, Staking, Settings
2. **Consolidate Settings and Menu**: Use Settings.tsx, remove Menu.tsx
3. **Move Scan/Notifications to secondary**: Accessible via icons/links, not main tabs
4. **SDK Integration**: Always import from SDK, never reimplement biometric logic
5. **Production-ready**: No mock data, no placeholder implementations in prod builds

### Breaking Changes
- Removed `/tabs/home` as main tab (functionality in Wallet)
- Removed `/tabs/nfts` as main tab (integrated into Wallet)
- Consolidated `/tabs/menu` into `/tabs/menu` (Settings)
- Legacy routes still accessible via direct URL for backward compatibility

### Dependencies
- SDK v0.1.0+ (deterministic DID support)
- Koios API for Cardano data
- CIP-30 standard for wallet connector
- Ionic v7 components

---

## Open Questions

1. **CIP-30 Implementation**: Should we use a service worker or inject API directly into iframe?
   - **Decision**: Direct injection with postMessage bridge for better control

2. **Wallet Address Management**: Support multiple addresses or single address view?
   - **Decision**: Single address with future multi-address support

3. **Offline Support**: Which features should work offline?
   - **Decision**: Identity management and settings, others require network

4. **Theme Support**: Dark mode implementation priority?
   - **Decision**: Low priority, use system theme initially

---

## Migration Path

### For Existing Users
- No data loss: All identifiers, credentials, settings preserved
- Navigation changes: Old URLs redirect to new structure
- Settings location: Moved from "Menu" to "Settings" tab
- Features: All existing features remain accessible

### For Developers
- Import paths: Update any hardcoded `/tabs/menu` to `/tabs/menu`
- Component structure: Settings replaces Menu in TabsMenu config
- State management: No Redux state structure changes
- Testing: Update navigation tests to use new routes
