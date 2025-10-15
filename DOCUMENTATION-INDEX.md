# Documentation Index

Quick reference guide for navigating the Decentralized DID project documentation.

**Last Updated**: October 15, 2025

---

## 🚀 Quick Start

- **New to the project?** Start with [README.md](README.md)
- **API security complete?** See [TASK-3-COMPLETION-SUMMARY.md](docs/TASK-3-COMPLETION-SUMMARY.md)
- **Current status?** Check [PROJECT-STATUS.md](docs/PROJECT-STATUS.md)
- **Task tracking?** View [.github/tasks.md](.github/tasks.md)

---

## 📋 Core Documentation

### Project Overview
- [README.md](README.md) - Main project documentation
- [docs/PROJECT-STATUS.md](docs/PROJECT-STATUS.md) - Current project status
- [docs/roadmap.md](docs/roadmap.md) - Development roadmap
- [docs/PHASE-4.6-EXECUTIVE-SUMMARY.md](docs/PHASE-4.6-EXECUTIVE-SUMMARY.md) - Executive overview
- [docs/PHASE-4.6-PLAN.md](docs/PHASE-4.6-PLAN.md) - Phase 4.6 detailed plan

### Task Completion Summaries
- [docs/TASK-3-COMPLETION-SUMMARY.md](docs/TASK-3-COMPLETION-SUMMARY.md) - API Server Security Hardening (100% complete)
- [.github/tasks.md](.github/tasks.md) - Active task tracking and progress

---

## 🏗️ Architecture & Design

### System Architecture
- [docs/architecture.md](docs/architecture.md) - Overall system architecture
- [docs/requirements.md](docs/requirements.md) - Functional and non-functional requirements
- [docs/design/](docs/design/) - Detailed design documents
- [docs/research/](docs/research/) - Research and analysis documentation

### Security & Privacy
- [docs/privacy-security.md](docs/privacy-security.md) - Privacy and security policies
- [docs/sybil-resistance-design.md](docs/sybil-resistance-design.md) - Sybil resistance architecture
- [docs/tamper-proof-identity-security.md](docs/tamper-proof-identity-security.md) - Tamper-proof design

---

## 🔐 Security Documentation

**Location**: [docs/security/](docs/security/)

### Security Testing Guides
- [docs/security/owasp-zap-guide.md](docs/security/owasp-zap-guide.md) - OWASP ZAP security scanning
- [docs/security/load-testing-guide.md](docs/security/load-testing-guide.md) - Load testing (1000+ concurrent users)
- [docs/security/performance-benchmarking.md](docs/security/performance-benchmarking.md) - Performance optimization
- [docs/security/security-testing-checklist.md](docs/security/security-testing-checklist.md) - OWASP API Top 10 checklist

### Security Features Implemented
- Rate limiting (5 policies, sliding window)
- Authentication (JWT + API keys)
- Authorization (RBAC)
- Input validation & sanitization
- Security headers (HSTS, CSP, X-Frame-Options, etc.)
- Audit logging (PII sanitization)
- Error handling (50+ error codes)

---

## 🔗 Integration Guides

### SDK & API Integration
- [docs/SDK.md](docs/SDK.md) - Python SDK documentation and API reference
- [docs/cardano-integration.md](docs/cardano-integration.md) - Cardano blockchain integration
- [docs/wallet-integration.md](docs/wallet-integration.md) - Wallet integration guide

### Biometric Integration
- [docs/biometric-did-integration.md](docs/biometric-did-integration.md) - DID generation from biometrics
- [docs/fingerprint-sensor-integration.md](docs/fingerprint-sensor-integration.md) - Hardware sensor integration
- [docs/webauthn-integration.md](docs/webauthn-integration.md) - WebAuthn integration
- [docs/biometric-lockpage-integration.md](docs/biometric-lockpage-integration.md) - Lock page integration
- [docs/biometric-transaction-signing.md](docs/biometric-transaction-signing.md) - Transaction signing

### Demo Wallet
- [docs/demo-wallet-verification.md](docs/demo-wallet-verification.md) - Demo wallet verification guide
- [docs/mobile-enrollment-architecture.md](docs/mobile-enrollment-architecture.md) - Mobile enrollment architecture
- [demo-wallet/README.md](demo-wallet/README.md) - Demo wallet documentation

---

## 🛠️ Technical Implementation

### Development Guides
- [docs/cli-execution-implementation.md](docs/cli-execution-implementation.md) - CLI implementation
- [docs/testnet-deployment-guide.md](docs/testnet-deployment-guide.md) - Testnet deployment
- [docs/DEPLOYMENT-QUICKSTART.md](docs/DEPLOYMENT-QUICKSTART.md) - Quick deployment guide

### Testing
- [docs/testing/](docs/testing/) - Testing documentation
- [tests/](tests/) - Test suite (307 tests, 100% passing)
- Run tests: `pytest tests/ -v`

---

## 📊 Governance & Business

### Project Governance
- [docs/governance.md](docs/governance.md) - Project governance model
- [docs/proposal.md](docs/proposal.md) - Original project proposal
- [docs/faq.md](docs/faq.md) - Frequently asked questions

### Business & Outreach
- [docs/pitch-outline.md](docs/pitch-outline.md) - Pitch deck outline
- [docs/hackathon-playbook.md](docs/hackathon-playbook.md) - Hackathon participation guide

---

## 📁 Directory Structure

```
decentralized-did/
├── README.md                    # Main project documentation
├── DOCUMENTATION-INDEX.md       # This file
├── .github/
│   ├── tasks.md                # Task tracking
│   └── copilot-instructions.md # Copilot working agreement
├── docs/
│   ├── TASK-3-COMPLETION-SUMMARY.md  # API security complete
│   ├── PROJECT-STATUS.md             # Current status
│   ├── roadmap.md                    # Development roadmap
│   ├── architecture.md               # System architecture
│   ├── requirements.md               # Requirements
│   ├── SDK.md                        # Python SDK docs
│   ├── security/                     # Security guides
│   │   ├── owasp-zap-guide.md
│   │   ├── load-testing-guide.md
│   │   ├── performance-benchmarking.md
│   │   └── security-testing-checklist.md
│   ├── design/                       # Design documents
│   ├── research/                     # Research docs
│   ├── testing/                      # Testing docs
│   ├── deployment/                   # Deployment guides
│   └── ...                           # Other guides
├── src/
│   └── decentralized_did/           # Python package
│       ├── api/                     # API server modules
│       ├── did/                     # DID generation
│       ├── cardano/                 # Cardano integration
│       └── ...
├── tests/                           # Test suite (307 tests)
├── demo-wallet/                     # Demo wallet (React/TypeScript)
└── examples/                        # Example code
```

---

## 🎯 Current Project Status (October 15, 2025)

### ✅ Completed
- **Task 2**: API Server Security Hardening (100%)
  - 7 phases complete (35 hours, 307 tests)
  - Production-ready security controls
  - OWASP API Security Top 10 compliance
  - Comprehensive security testing documentation

- **Task 3**: Documentation Cleanup (100%)
  - Removed 39 obsolete files (~16,279 lines)
  - Clean, well-organized documentation structure

### 🔄 In Progress
- **Task 1**: Update Demo Wallet for Deterministic DIDs (60%)
  - Core logic complete (100%)
  - Remaining: Integration tests, E2E tests, manual testing
  - Est. completion: 1.5-2 days

### ⏳ Upcoming
- **Task 4**: Integration Testing (5-6 days)
- **Task 5**: Production Deployment Guide (3-4 days)
- **Task 6**: Documentation Updates (3-4 days)

---

## 🔍 Finding What You Need

### I want to...

**...understand the system architecture**
→ Start with [docs/architecture.md](docs/architecture.md)

**...integrate biometric authentication**
→ See [docs/biometric-did-integration.md](docs/biometric-did-integration.md)

**...use the Python SDK**
→ Read [docs/SDK.md](docs/SDK.md)

**...integrate with Cardano**
→ Check [docs/cardano-integration.md](docs/cardano-integration.md)

**...deploy to production**
→ Follow [docs/testnet-deployment-guide.md](docs/testnet-deployment-guide.md) and [docs/DEPLOYMENT-QUICKSTART.md](docs/DEPLOYMENT-QUICKSTART.md)

**...run security tests**
→ Use guides in [docs/security/](docs/security/)

**...contribute to the project**
→ Read [.github/copilot-instructions.md](.github/copilot-instructions.md) and [demo-wallet/CONTRIBUTING.md](demo-wallet/CONTRIBUTING.md)

**...track current tasks**
→ Check [.github/tasks.md](.github/tasks.md)

**...understand the demo wallet**
→ See [demo-wallet/README.md](demo-wallet/README.md) and [docs/demo-wallet-verification.md](docs/demo-wallet-verification.md)

---

## 📞 Getting Help

1. **Check the FAQ**: [docs/faq.md](docs/faq.md)
2. **Search documentation**: Use your editor's search to find relevant docs
3. **Review test cases**: See [tests/](tests/) for usage examples
4. **Check issue tracker**: GitHub issues for known problems

---

## 🔄 Documentation Updates

This index is maintained as documentation evolves. Last major cleanup: October 15, 2025.

**Contributing to documentation**:
- Follow the [Copilot Working Agreement](.github/copilot-instructions.md)
- Update this index when adding new major documentation
- Keep docs/ organized by category
- Remove obsolete documentation promptly

---

**Quick Links**:
- [Main README](README.md)
- [Task Tracking](.github/tasks.md)
- [Project Status](docs/PROJECT-STATUS.md)
- [Security Guides](docs/security/)
- [API Security Complete](docs/TASK-3-COMPLETION-SUMMARY.md)
