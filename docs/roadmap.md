# Roadmap

## Current Sprint (Oct 2025) - DEMO-WALLET INTEGRATION COMPLETE ✅

### Phase 4: Biometric DID Wallet Integration (10/10 tasks COMPLETE)
- ✅ **COMPLETED**: Finalized the biometric metadata ingestion plan for the bundled `demo-wallet` (Veridian fork).
- ✅ **COMPLETED**: Defined the experimental CIP-30 bridge (store metadata bundle, surface approval UX, persist helper URI).
- ✅ **COMPLETED**: Published contributor guidance (`copilot-instructions.md`) and kept roadmap/docs cross-referenced.
- ✅ **COMPLETED**: Captured integration test scenarios that exercise Python CLI output against the wallet flow.
- ✅ **COMPLETED**: Delivered the CLI "demo-kit" packaging command so demo operators can share consistent artifacts.
- ✅ **COMPLETED**: Demo-wallet (Veridian) is 100% functional with biometric DID support (see `docs/demo-wallet-verification.md`).
- ✅ **COMPLETED**: Integrated live CLI enrollment/verification flows into demo-wallet UI.
  - Full enrollment flow (10-finger sequential capture with progress tracking)
  - Verification flows (unlock wallet + transaction signing)
  - Backend API server (FastAPI + mock data) at http://localhost:8000
  - All UI components complete (BiometricEnrollment, BiometricVerification)
  - Route integration (BIOMETRIC_ENROLLMENT path)
  - Storage integration (SecureStorage for encrypted helper data)
  - Bug fixes: 2 critical issues resolved (infinite loop, storage error)
  - Documentation: 4,500+ lines across 7 comprehensive guides
  - **Status**: Mock mode fully functional, ready for real hardware integration

### Next Phase: Production Hardening (In Progress)
- ✅ **COMPLETED**: WebAuthn biometric verification (Quick Win)
  - Browser-native biometric authentication (Touch ID, Face ID, Windows Hello)
  - Implementation complete: 275 lines of production code + 950 lines of documentation
  - Platform support: Mac, iOS, Windows, Android
  - Use cases: Wallet unlock + transaction signing (verification only)
  - Limitation: Cannot generate DIDs (requires raw minutiae from real sensors)
  - Documentation: `docs/webauthn-integration.md`
  - Completion summary: `docs/completion/webauthn-implementation-complete.md`
  - **Status**: Ready for device testing (Mac Touch ID, iOS Face ID, Windows Hello)
- 🔄 **IN PROGRESS**: Hardware integration (fingerprint sensors for DID generation)
  - Research complete: 4 strategies documented (WebAuthn, libfprint, Platform APIs, OpenCV)
  - Hardware recommendation: Eikon Touch 700 USB sensor ($25-30)
  - Implementation guide: `docs/fingerprint-sensor-integration.md` (1,043 lines)
  - See `docs/NEXT-STEPS.md` for detailed 2-week implementation plan
- ⏳ **PLANNED**: Upgrade API server from mock to real CLI integration
- ⏳ **PLANNED**: Security hardening (rate limiting, authentication, audit logging)
- ⏳ **PLANNED**: Performance optimization (caching, monitoring, connection pooling)
- ⏳ **PLANNED**: Automated testing (unit, integration, E2E tests)
- ⏳ **PLANNED**: Production deployment guide (Docker, Nginx, SSL/TLS)

## Near-Term (Quarter 1)
- Land biometric metadata storage and approval UI inside the demo wallet (peer connection + signing screens).
- Publish TypeScript bindings (or JSON schema) for wallet integrators beyond Veridian.
- Build automated fixtures that validate CLI-generated bundles round-trip inside the wallet (unit + e2e).
- Conduct informal security review with community experts focusing on helper data handling.

## Mid-Term (Quarter 2)
- Launch managed enrollment node with secure hardware support (YubiKey Bio, Apple Secure Enclave).
- Draft CIP for standardized biometric metadata structure.
- Build Plutus validator that requires matching biometric digest for access-controlled actions.
- Implement zero-knowledge proof flow for selective disclosure (e.g., age attestations).

## Long-Term (Quarter 3+)
- Formal audits of biometric pipeline and helper data storage.
- Multi-factor composability (biometric digest + social recovery + device attestations).
- Decentralized registry anchored on Cardano sidechain or Mithril snapshots.
- Explore interoperability with W3C DID Core and verifiable credentials.
