# CIP-30/CIP-45 + Hardware Wallet Implementation Status

**Date**: 2025-11-03
**Status**: Phase 1 - Dependencies Installed, Implementation Ready
**Estimated Time**: 2-3 weeks for full implementation

## Overview

This document tracks the implementation of best-in-class CIP-30/CIP-45 wallet APIs with hardware wallet support (Keystone, Ledger, Trezor). Based on comprehensive research of Veridian wallet patterns and hardware wallet integration approaches documented in `docs/CIP30-HARDWARE-WALLET-RESEARCH.md`.

---

## ✅ Phase 0: Research & Planning (COMPLETE)

**Status**: DONE
**Completed**: 2025-11-03

### Accomplishments

1. **Veridian Wallet Analysis** - Analyzed 100+ code excerpts from Cardano Foundation's reference implementation
   - ✅ Identified event-driven approval pattern (1-hour timeout)
   - ✅ Documented PeerConnection singleton pattern
   - ✅ Documented connection metadata storage
   - ✅ **CRITICAL FINDING**: Veridian implements CIP-45 P2P but NOT CIP-30 transaction methods (only KERI identity)

2. **Hardware Wallet Research** - Analyzed integration patterns for 3 wallet types
   - ✅ Keystone: QR-based air-gapped signing with UR encoding
   - ✅ Ledger: USB/WebUSB integration with Cardano app
   - ✅ Trezor: USB integration with Trezor Connect library

3. **Architecture Design** - Created hybrid approach supporting both iframe and P2P connections
   - ✅ Designed abstract `HardwareWallet` interface
   - ✅ Defined CIP-30 API implementation strategy
   - ✅ Planned CIP-30 injection protocol for iframe `window.cardano` object
   - ✅ Created component breakdown and dependency list

4. **Documentation** - Comprehensive implementation blueprint created
   - ✅ Created `docs/CIP30-HARDWARE-WALLET-RESEARCH.md` (650 lines)
   - ✅ Documented all patterns with code examples
   - ✅ Created 4-phase implementation plan
   - ✅ Listed all security considerations

---

## ✅ Phase 0.5: Dependencies Installation (COMPLETE)

**Status**: DONE
**Completed**: 2025-11-03
**Time Taken**: 30 minutes

### Dependencies Installed

```json
{
  "@emurgo/cardano-serialization-lib-browser": "^12.1.1",
  "@fabianbormann/cardano-peer-connect": "^3.0.0",
  "@keystonehq/bc-ur-registry-cardano": "^1.0.0",
  "@keystonehq/animated-qr": "^0.8.0",
  "react-qr-code": "^2.0.15",
  "@ledgerhq/hw-transport-webusb": "^6.29.4",
  "@cardano-foundation/ledgerjs-hw-app-cardano": "^7.2.1",
  "trezor-connect": "^8.2.12"
}
```

### Build Verification

- ✅ **Build Status**: SUCCESS (78.4 seconds, 0 errors)
- ✅ **Bundle Size**: 5.45 MiB (expected warnings for large bundles)
- ✅ **Service Worker**: Precaching 49 URLs (7.36 MB)
- ✅ **No TypeScript Errors**: All types resolved correctly

---

## 🔄 Phase 1: Full CIP-30 API Implementation (IN PROGRESS)

**Status**: READY TO START
**Estimated Time**: 3-5 days
**Target Completion**: 2025-11-08

### Objectives

Implement all CIP-30 methods to replace stubs in Veridian's implementation. Current state in `demo-wallet/src/core/cardano/cip30/` has basic structure but needs complete implementation.

### Tasks

#### 1.1 Setup Cardano Serialization Library (CSL) Integration
- [ ] Create CSL utility wrapper in `src/core/cardano/csl/`
- [ ] Implement CBOR encoding/decoding helpers
- [ ] Add type definitions for CSL objects
- [ ] Write unit tests for CSL utilities

**Files to Create**:
```
src/core/cardano/csl/
├── index.ts                 # Main CSL exports
├── transaction.ts           # Transaction building utilities
├── address.ts               # Address utilities
├── value.ts                 # ADA/token value utilities
└── serialization.ts         # CBOR encoding/decoding
```

#### 1.2 Implement Core CIP-30 Methods
- [ ] `getNetworkId(): Promise<number>`
- [ ] `getUtxos(amount?: string, paginate?: Paginate): Promise<string[] | null>`
- [ ] `getBalance(): Promise<string>`
- [ ] `getUsedAddresses(paginate?: Paginate): Promise<string[]>`
- [ ] `getUnusedAddresses(): Promise<string[]>`
- [ ] `getChangeAddress(): Promise<string>`
- [ ] `getRewardAddresses(): Promise<string[]>`
- [ ] `signTx(tx: string, partialSign: boolean): Promise<string>`
- [ ] `signData(addr: string, payload: string): Promise<Cip30DataSignature>`
- [ ] `submitTx(tx: string): Promise<string>`

**Files to Edit**:
```
src/core/cardano/cip30/
├── api.ts                   # Main API implementation (replace stubs)
├── types.ts                 # CIP-30 type definitions
└── errors.ts                # CIP-30 error types
```

#### 1.3 Transaction Builder
- [ ] Create transaction builder service
- [ ] Implement input selection algorithm
- [ ] Add fee calculation (using Cardano constants)
- [ ] Support multi-asset transactions
- [ ] Add metadata support
- [ ] Write transaction builder tests

**Files to Create**:
```
src/core/services/transaction/
├── TransactionBuilder.ts    # Main transaction builder
├── InputSelector.ts         # UTXO selection algorithm
├── FeeCalculator.ts         # Fee estimation
└── MetadataBuilder.ts       # Transaction metadata
```

#### 1.4 Integration with Existing Services
- [ ] Connect to `TokenService` for balance queries
- [ ] Connect to `AddressService` for address management
- [ ] Connect to `WalletService` for signing operations
- [ ] Update `TransactionPreview` component to use new API
- [ ] Add error handling and logging

**Files to Edit**:
```
src/core/services/
├── TokenService.ts          # Token/balance queries
├── AddressService.ts        # Address management
└── WalletService.ts         # Signing operations
```

#### 1.5 Testing
- [ ] Unit tests for each CIP-30 method
- [ ] Integration tests with mock blockchain data
- [ ] Test with real dApp (CIP-45 sample dApp)
- [ ] Test transaction signing flow end-to-end
- [ ] Performance testing (signing speed, balance queries)

**Files to Create**:
```
tests/core/cardano/cip30/
├── api.test.ts
├── transaction.test.ts
└── integration.test.ts
```

### Success Criteria

- ✅ All CIP-30 methods implemented and functional
- ✅ Transactions can be built, signed, and submitted
- ✅ Balance and UTXO queries return correct data
- ✅ Address management works for used/unused addresses
- ✅ Integration tests pass with 100% coverage
- ✅ CIP-45 sample dApp can connect and perform transactions

---

## 📋 Phase 2: CIP-30 Injection Protocol (PLANNED)

**Status**: NOT STARTED
**Estimated Time**: 2-3 days
**Dependencies**: Phase 1 complete
**Target Completion**: 2025-11-11

### Objectives

Implement the `window.cardano` injection protocol to allow iframe-based dApps to interact with the wallet. This is the standard way web dApps discover and connect to Cardano wallets.

### Tasks

#### 2.1 Design postMessage Protocol
- [ ] Define message types (request/response/error)
- [ ] Create message serialization format
- [ ] Design timeout and retry logic
- [ ] Add message validation and sanitization
- [ ] Document protocol specification

**Files to Create**:
```
src/core/cardano/injection/
├── protocol.ts              # postMessage protocol definition
├── messages.ts              # Message types and validation
├── serialization.ts         # Message serialization
└── README.md                # Protocol documentation
```

#### 2.2 Implement Wallet API Injection
- [ ] Create `CardanoWalletAPI` class for `window.cardano` object
- [ ] Implement `enable()` method (returns CIP-30 API)
- [ ] Implement `isEnabled()` method
- [ ] Add wallet identification (`name`, `icon`, `apiVersion`)
- [ ] Inject API into iframe sandbox

**Files to Create**:
```
src/core/cardano/injection/
├── WalletAPI.ts             # window.cardano implementation
├── injector.ts              # API injection logic
└── sandbox.ts               # iframe sandbox utilities
```

#### 2.3 Connection Approval Flow
- [ ] Adopt Veridian's event-driven approval pattern
- [ ] Create connection approval UI component
- [ ] Implement 1-hour timeout for approval
- [ ] Store approved connections (metadata storage)
- [ ] Add connection revocation functionality

**Files to Create**:
```
src/ui/components/dapp/
├── ConnectionApproval.tsx   # Approval dialog component
├── ConnectionList.tsx       # List of connected dApps
└── ConnectionManager.ts     # Connection state management
```

#### 2.4 Request Handling
- [ ] Route postMessage requests to CIP-30 API
- [ ] Implement request queueing (one at a time)
- [ ] Add user approval for sensitive operations (signTx, signData)
- [ ] Implement response/error handling
- [ ] Add logging for security audits

**Files to Create**:
```
src/core/cardano/injection/
├── RequestHandler.ts        # postMessage request router
├── RequestQueue.ts          # Request queueing logic
├── ApprovalManager.ts       # User approval for sensitive ops
└── SecurityLogger.ts        # Security audit logging
```

#### 2.5 iframe Sandbox Configuration
- [ ] Configure Content Security Policy (CSP)
- [ ] Set iframe sandbox attributes
- [ ] Implement origin validation
- [ ] Add rate limiting
- [ ] Test with malicious dApp scenarios

**Files to Edit**:
```
src/ui/components/dapp/
├── DAppBrowser.tsx          # iframe configuration
└── SecurityPolicy.ts        # CSP and sandbox rules
```

#### 2.6 Testing
- [ ] Unit tests for postMessage protocol
- [ ] Integration tests with iframe dApps
- [ ] Security tests (XSS, CSRF, clickjacking)
- [ ] Test with real dApps (Minswap, JPG.store)
- [ ] Performance testing (connection speed, request latency)

**Files to Create**:
```
tests/core/cardano/injection/
├── protocol.test.ts
├── security.test.ts
└── integration.test.ts
```

### Success Criteria

- ✅ dApps can discover wallet via `window.cardano`
- ✅ Connection approval flow works correctly
- ✅ All CIP-30 methods accessible via injection
- ✅ postMessage protocol is secure (CSP, sandbox, validation)
- ✅ Approval requests timeout after 1 hour
- ✅ Connection metadata stored and manageable
- ✅ Real dApps (Minswap, JPG.store) can connect successfully

---

## 📋 Phase 3: Hardware Wallet Support (PLANNED)

**Status**: NOT STARTED
**Estimated Time**: 5-7 days
**Dependencies**: Phase 1 complete
**Target Completion**: 2025-11-18

### Objectives

Implement support for 3 hardware wallet types: Keystone (QR-based air-gapped), Ledger (USB), and Trezor (USB). Allow users to sign transactions securely with hardware devices.

### Tasks

#### 3.1 Abstract Hardware Wallet Interface
- [ ] Create `HardwareWallet` abstract class
- [ ] Define common methods (connect, disconnect, getExtendedPublicKey, signTransaction, signMessage)
- [ ] Add wallet type detection
- [ ] Implement connection state management
- [ ] Add error handling and recovery

**Files to Create**:
```
src/core/hardware/
├── HardwareWallet.ts        # Abstract base class
├── types.ts                 # Hardware wallet types
├── errors.ts                # Hardware wallet errors
└── manager.ts               # HardwareWalletManager singleton
```

#### 3.2 Keystone Wallet Implementation (QR-based)
- [ ] Implement `KeystoneWallet` class
- [ ] Add UR encoding/decoding for transactions
- [ ] Create animated QR code display component
- [ ] Implement QR code scanning (using existing Capacitor barcode scanner)
- [ ] Add signing flow UI
- [ ] Test with Keystone device

**Files to Create**:
```
src/core/hardware/keystone/
├── KeystoneWallet.ts        # Keystone implementation
├── UREncoder.ts             # UR encoding utilities
├── URDecoder.ts             # UR decoding utilities
└── QRCodeHandler.ts         # QR code display/scan logic

src/ui/components/hardware/keystone/
├── AnimatedQRDisplay.tsx    # Displays animated QR codes
├── QRScanner.tsx            # Scans signed transaction QR
└── KeystoneSignFlow.tsx     # Full signing flow UI
```

#### 3.3 Ledger Wallet Implementation (USB)
- [ ] Implement `LedgerWallet` class
- [ ] Add WebUSB transport layer
- [ ] Integrate Cardano Foundation's Ledger library
- [ ] Create Ledger connection UI
- [ ] Add signing flow UI
- [ ] Test with Ledger device

**Files to Create**:
```
src/core/hardware/ledger/
├── LedgerWallet.ts          # Ledger implementation
├── transport.ts             # WebUSB transport utilities
└── cardanoApp.ts            # Cardano app integration

src/ui/components/hardware/ledger/
├── LedgerConnect.tsx        # Connection UI
└── LedgerSignFlow.tsx       # Signing flow UI
```

#### 3.4 Trezor Wallet Implementation (USB)
- [ ] Implement `TrezorWallet` class
- [ ] Integrate Trezor Connect library
- [ ] Create Trezor connection UI
- [ ] Add signing flow UI
- [ ] Test with Trezor device

**Files to Create**:
```
src/core/hardware/trezor/
├── TrezorWallet.ts          # Trezor implementation
└── trezorConnect.ts         # Trezor Connect integration

src/ui/components/hardware/trezor/
├── TrezorConnect.tsx        # Connection UI
└── TrezorSignFlow.tsx       # Signing flow UI
```

#### 3.5 Hardware Wallet Manager
- [ ] Create `HardwareWalletManager` singleton
- [ ] Implement wallet type selection UI
- [ ] Add wallet connection management
- [ ] Implement smart signing strategy (hot wallet vs hardware based on amount)
- [ ] Add wallet status tracking
- [ ] Implement error recovery

**Files to Create**:
```
src/core/hardware/
├── manager.ts               # HardwareWalletManager singleton
├── WalletSelector.ts        # Wallet type selection logic
└── SmartSigning.ts          # Auto-select wallet based on amount

src/ui/components/hardware/
├── WalletSelector.tsx       # Wallet selection UI
├── WalletStatus.tsx         # Connection status indicator
└── HardwareSignFlow.tsx     # Unified signing flow
```

#### 3.6 Integration with CIP-30 API
- [ ] Update `signTx()` to support hardware wallets
- [ ] Update `signData()` to support hardware wallets
- [ ] Add hardware wallet selection to TransactionPreview
- [ ] Implement address derivation from hardware wallet
- [ ] Add hardware wallet to wallet list UI

**Files to Edit**:
```
src/core/cardano/cip30/
└── api.ts                   # Add hardware wallet support

src/ui/components/wallet/
└── TransactionPreview.tsx   # Add hardware wallet option
```

#### 3.7 Testing
- [ ] Unit tests for each hardware wallet implementation
- [ ] Integration tests with mock hardware devices
- [ ] E2E tests with real hardware devices
- [ ] Security testing (man-in-the-middle, QR tampering)
- [ ] Performance testing (signing speed, connection time)

**Files to Create**:
```
tests/core/hardware/
├── keystone.test.ts
├── ledger.test.ts
├── trezor.test.ts
└── integration.test.ts
```

### Success Criteria

- ✅ All 3 hardware wallet types supported
- ✅ QR-based signing works with Keystone
- ✅ USB signing works with Ledger and Trezor
- ✅ Hardware wallet addresses can be derived
- ✅ Transactions can be signed with hardware devices
- ✅ Smart signing strategy works (auto-select based on amount)
- ✅ Error handling and recovery works correctly
- ✅ Security tests pass (no QR tampering, secure USB connection)

---

## 📋 Phase 4: Integration & Testing (PLANNED)

**Status**: NOT STARTED
**Estimated Time**: 2-3 days
**Dependencies**: Phases 1-3 complete
**Target Completion**: 2025-11-21

### Objectives

Comprehensive E2E testing, security auditing, performance optimization, and production readiness validation.

### Tasks

#### 4.1 End-to-End Testing
- [ ] Full dApp browser flow (connect → sign → submit)
- [ ] CIP-45 P2P connection flow (QR code → sign → verify)
- [ ] Hardware wallet signing flow for all 3 types
- [ ] Multi-wallet scenario testing (switch between hot/hardware)
- [ ] Error recovery testing (disconnect, timeout, rejection)

**Files to Create**:
```
tests/e2e/
├── dapp-browser.spec.ts     # Playwright E2E tests
├── cip45-p2p.spec.ts        # P2P connection tests
├── hardware-wallets.spec.ts # Hardware wallet E2E tests
└── scenarios.spec.ts        # Complex scenarios
```

#### 4.2 Security Auditing
- [ ] CSP policy validation
- [ ] iframe sandbox testing
- [ ] Origin validation testing
- [ ] Rate limiting validation
- [ ] Transaction validation (amount, recipient, metadata)
- [ ] QR code tampering tests
- [ ] Man-in-the-middle attack tests
- [ ] Audit logging verification

**Files to Create**:
```
tests/security/
├── csp.test.ts
├── sandbox.test.ts
├── validation.test.ts
├── rate-limiting.test.ts
└── attack-scenarios.test.ts
```

#### 4.3 Performance Optimization
- [ ] Bundle size optimization (code splitting, tree shaking)
- [ ] Transaction signing speed optimization
- [ ] Balance query performance
- [ ] Connection time optimization
- [ ] Memory usage profiling
- [ ] Network request optimization

**Tasks**:
- Run Lighthouse audits
- Profile with Chrome DevTools
- Optimize bundle splitting
- Add lazy loading for hardware wallet libraries
- Implement request caching

#### 4.4 Documentation Updates
- [ ] Update `docs/cardano-integration.md`
- [ ] Update `docs/wallet-integration.md`
- [ ] Create `docs/HARDWARE-WALLETS.md` user guide
- [ ] Update API documentation in code
- [ ] Create developer guide for dApp integration
- [ ] Add troubleshooting guide

**Files to Create/Edit**:
```
docs/
├── cardano-integration.md   # Update with CIP-30 details
├── wallet-integration.md    # Update with injection protocol
├── HARDWARE-WALLETS.md      # New: Hardware wallet user guide
├── DAPP-INTEGRATION.md      # New: Guide for dApp developers
└── TROUBLESHOOTING.md       # New: Common issues and solutions
```

#### 4.5 Production Readiness
- [ ] Feature flags for gradual rollout
- [ ] Error monitoring integration (Sentry)
- [ ] Analytics integration (user consent)
- [ ] Production build testing
- [ ] Android APK testing
- [ ] iOS build preparation (if applicable)

**Files to Create/Edit**:
```
src/config/
├── featureFlags.ts          # Feature flag configuration
└── monitoring.ts            # Error monitoring setup
```

### Success Criteria

- ✅ All E2E tests pass (100% success rate)
- ✅ Security audits pass (no critical/high vulnerabilities)
- ✅ Performance metrics meet targets (< 3s page load, < 1s signing)
- ✅ Documentation complete and reviewed
- ✅ Production build successful
- ✅ Android APK builds and installs correctly
- ✅ Feature flags configured for gradual rollout

---

## 📊 Overall Progress Tracker

### Phase Summary

| Phase | Status | Estimated Time | Actual Time | Completion |
|-------|--------|----------------|-------------|------------|
| Phase 0: Research & Planning | ✅ DONE | 1 day | 1 day | 100% |
| Phase 0.5: Dependencies | ✅ DONE | 30 min | 30 min | 100% |
| Phase 1: CIP-30 API | 🔄 READY | 3-5 days | TBD | 0% |
| Phase 2: Injection Protocol | 📋 PLANNED | 2-3 days | TBD | 0% |
| Phase 3: Hardware Wallets | 📋 PLANNED | 5-7 days | TBD | 0% |
| Phase 4: Integration & Testing | 📋 PLANNED | 2-3 days | TBD | 0% |
| **TOTAL** | | **2-3 weeks** | **1.5 days** | **10%** |

### Key Milestones

- ✅ **2025-11-03**: Research complete, dependencies installed
- 🎯 **2025-11-08**: Phase 1 complete (CIP-30 API functional)
- 🎯 **2025-11-11**: Phase 2 complete (dApps can inject and connect)
- 🎯 **2025-11-18**: Phase 3 complete (Hardware wallets working)
- 🎯 **2025-11-21**: Phase 4 complete (Production ready)

---

## 🔍 Critical Findings from Research

### What Works Well in Veridian (TO ADOPT)

1. **Event-Driven Approval Pattern** ✅
   - Clean separation between wallet logic and UI
   - 1-hour timeout prevents indefinite blocking
   - Callback-based approval is intuitive

2. **PeerConnection Singleton** ✅
   - Centralized dApp connection management
   - Connection metadata storage
   - Disconnect/reconnect handling

3. **Connection Metadata Storage** ✅
   - Track dApp name, URL, icon
   - Store selected user identifier
   - Enable connection revocation

### What Needs Improvement (GAPS IN VERIDIAN)

1. **CIP-30 Transaction Methods** ❌
   - Veridian stubs out signTx, signData, submitTx
   - We MUST implement full CIP-30 API with CSL
   - Transaction building and fee calculation needed

2. **iframe Injection Protocol** ❌
   - Veridian focuses on P2P only
   - We need window.cardano injection for standard dApps
   - postMessage protocol required

3. **Hardware Wallet Support** ❌
   - Not in Veridian scope
   - We add Keystone/Ledger/Trezor support
   - QR-based + USB integration

---

## 📚 Related Documentation

- **Research Document**: `docs/CIP30-HARDWARE-WALLET-RESEARCH.md` (650 lines, comprehensive patterns and code examples)
- **Wallet Integration**: `docs/wallet-integration.md` (existing integration docs)
- **Cardano Integration**: `docs/cardano-integration.md` (Cardano-specific implementation)
- **Roadmap**: `docs/roadmap.md` (project roadmap and sprint planning)

---

## 🚀 Next Steps

1. **Immediate** (Today, 2025-11-03):
   - ✅ Dependencies installed
   - ✅ Build verified
   - ⏳ Start Phase 1: Create CSL utilities wrapper

2. **This Week** (2025-11-04 to 2025-11-08):
   - Implement all CIP-30 methods
   - Build transaction builder
   - Test with CIP-45 sample dApp

3. **Next Week** (2025-11-11 to 2025-11-15):
   - Implement CIP-30 injection protocol
   - Create connection approval UI
   - Test with real dApps (Minswap, JPG.store)

4. **Week 3** (2025-11-18 to 2025-11-21):
   - Implement hardware wallet support
   - E2E testing and security audits
   - Production readiness validation

---

## 💡 Implementation Tips

### From Veridian Research

1. **Use Event-Driven Approval**: Adopt Veridian's pattern for clean UI separation
2. **Timeout Handling**: 1-hour max for approval requests to prevent indefinite blocks
3. **Connection Metadata**: Store dApp info (name, URL, icon) for better UX
4. **Singleton Pattern**: Use singleton for PeerConnection and HardwareWalletManager

### Security Best Practices

1. **Transaction Validation**: ALWAYS validate transaction before signing (amount, recipient, metadata)
2. **CSP Policy**: Strict Content Security Policy for iframe sandbox
3. **Origin Validation**: Verify dApp origin before allowing connection
4. **Rate Limiting**: Prevent abuse with rate limits on API calls
5. **Audit Logging**: Log all sensitive operations for security audits

### Performance Optimization

1. **Code Splitting**: Lazy load hardware wallet libraries (only load when needed)
2. **Request Caching**: Cache balance/UTXO queries to reduce network calls
3. **Bundle Size**: Keep main bundle < 1 MB (use dynamic imports)
4. **Signing Speed**: Optimize transaction building (target < 1 second)

---

## 📞 Support & Resources

- **Veridian Wallet**: https://github.com/cardano-foundation/veridian-wallet
- **CIP-30 Specification**: https://cips.cardano.org/cip/CIP-30
- **CIP-45 Specification**: https://cips.cardano.org/cip/CIP-45
- **Cardano Serialization Library**: https://github.com/Emurgo/cardano-serialization-lib
- **Keystone SDK**: https://github.com/KeystoneHQ/Keystone-SDK
- **Ledger Cardano App**: https://github.com/cardano-foundation/ledgerjs-hw-app-cardano
- **Trezor Connect**: https://github.com/trezor/trezor-suite

---

**Last Updated**: 2025-11-03
**Next Review**: 2025-11-08 (after Phase 1 completion)
