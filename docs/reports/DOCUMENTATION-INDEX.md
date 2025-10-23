# Documentation Index

Quick reference guide for navigating the Decentralized DID project documentation.

**Last Updated**: October 15, 2025

---

## 🚀 Quick Start

- **New to the project?** Start with [README.md](../../README.md)
- **API security complete?** See [TASK-3-COMPLETION-SUMMARY.md](../TASK-3-COMPLETION-SUMMARY.md)
- **Current status?** Check [PROJECT-STATUS.md](../PROJECT-STATUS.md)
- **Task tracking?** View [.github/tasks.md](../../.github/tasks.md)

---

## 📋 Core Documentation

### Project Overview
- [README.md](../../README.md) - Main project documentation
- [docs/PROJECT-STATUS.md](../PROJECT-STATUS.md) - Current project status
- [docs/roadmap.md](../roadmap.md) - Development roadmap
- [docs/PHASE-4.6-EXECUTIVE-SUMMARY.md](../PHASE-4.6-EXECUTIVE-SUMMARY.md) - Executive overview
- [docs/PHASE-4.6-PLAN.md](../PHASE-4.6-PLAN.md) - Phase 4.6 detailed plan

### Task Completion Summaries
- [docs/TASK-3-COMPLETION-SUMMARY.md](../TASK-3-COMPLETION-SUMMARY.md) - API Server Security Hardening (100% complete)
- [.github/tasks.md](../../.github/tasks.md) - Active task tracking and progress

---

## 🏗️ Architecture & Design

### System Architecture
- [docs/architecture.md](../architecture.md) - Overall system architecture
- [docs/requirements.md](../requirements.md) - Functional and non-functional requirements
- [docs/design/](../design/) - Detailed design documents
- [docs/research/](../research/) - Research and analysis documentation

### Security & Privacy
- [docs/privacy-security.md](../privacy-security.md) - Privacy and security policies
- [docs/sybil-resistance-design.md](../sybil-resistance-design.md) - Sybil resistance architecture
- [docs/tamper-proof-identity-security.md](../tamper-proof-identity-security.md) - Tamper-proof design

---

## 🔐 Security Documentation

**Location**: [docs/security/](../security/)

### Security Testing Guides
- [docs/security/owasp-zap-guide.md](../security/owasp-zap-guide.md) - OWASP ZAP security scanning
- [docs/security/load-testing-guide.md](../security/load-testing-guide.md) - Load testing (1000+ concurrent users)
- [docs/security/performance-benchmarking.md](../security/performance-benchmarking.md) - Performance optimization
- [docs/security/security-testing-checklist.md](../security/security-testing-checklist.md) - OWASP API Top 10 checklist

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
- [docs/SDK.md](../SDK.md) - Python SDK documentation and API reference
- [docs/cardano-integration.md](../cardano-integration.md) - Cardano blockchain integration
- [docs/wallet-integration.md](../wallet-integration.md) - Wallet integration guide

### Biometric Integration
- [docs/biometric-did-integration.md](../biometric-did-integration.md) - DID generation from biometrics
- [docs/fingerprint-sensor-integration.md](../fingerprint-sensor-integration.md) - Hardware sensor integration
- [docs/webauthn-integration.md](../webauthn-integration.md) - WebAuthn integration
- [docs/biometric-lockpage-integration.md](../biometric-lockpage-integration.md) - Lock page integration
- [docs/biometric-transaction-signing.md](../biometric-transaction-signing.md) - Transaction signing

### Demo Wallet
- [docs/demo-wallet-verification.md](../demo-wallet-verification.md) - Demo wallet verification guide
- [docs/mobile-enrollment-architecture.md](../mobile-enrollment-architecture.md) - Mobile enrollment architecture
- [demo-wallet/README.md](../../demo-wallet/README.md) - Demo wallet documentation

---

## 🛠️ Technical Implementation

### Development Guides
- [docs/cli-execution-implementation.md](../cli-execution-implementation.md) - CLI implementation
- [docs/testnet-deployment-guide.md](../testnet-deployment-guide.md) - Testnet deployment
- [docs/DEPLOYMENT-QUICKSTART.md](../DEPLOYMENT-QUICKSTART.md) - Quick deployment guide

### Testing
- [docs/testing/](../testing/) - Testing documentation
- [tests/](../../tests/) - Test suite (307 tests, 100% passing)
- Run tests: `pytest tests/ -v`

---

## 📊 Governance & Business

### Project Governance
- [docs/governance.md](../governance.md) - Project governance model
- [docs/proposal.md](../proposal.md) - Original project proposal
- [docs/faq.md](../faq.md) - Frequently asked questions

### Business & Outreach
- [docs/pitch-outline.md](../pitch-outline.md) - Pitch deck outline
- [docs/hackathon-playbook.md](../hackathon-playbook.md) - Hackathon participation guide

---

## 📁 Directory Structure

```
decentralized-did/
├── README.md                    # Main project documentation
├── .github/
│   ├── tasks.md                 # Task tracking
│   └── instructions/            # Copilot working agreement
├── docs/
│   ├── reports/                 # Deployment and audit reports
│   │   ├── DOCUMENTATION-INDEX.md      # This file
│   │   ├── DEPLOYMENT_ACHIEVEMENT.md
│   │   ├── DEPLOYMENT_READINESS.md
│   │   ├── FINAL_VALIDATION_REPORT.md
│   │   └── POST_DEPLOYMENT_ACTIONS.md
│   ├── TASK-3-COMPLETION-SUMMARY.md
│   ├── PROJECT-STATUS.md
│   ├── roadmap.md
│   ├── architecture.md
│   ├── requirements.md
│   ├── SDK.md
│   ├── security/
│   ├── design/
│   ├── research/
│   ├── testing/
│   └── deployment/
├── src/
│   └── decentralized_did/
├── tests/
├── demo-wallet/
└── examples/
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
→ Start with [docs/architecture.md](../architecture.md)

**...integrate biometric authentication**
→ See [docs/biometric-did-integration.md](../biometric-did-integration.md)

**...use the Python SDK**
→ Read [docs/SDK.md](../SDK.md)

**...integrate with Cardano**
→ Check [docs/cardano-integration.md](../cardano-integration.md)

**...deploy to production**
→ Follow [docs/testnet-deployment-guide.md](../testnet-deployment-guide.md) and [docs/DEPLOYMENT-QUICKSTART.md](../DEPLOYMENT-QUICKSTART.md)

**...run security tests**
→ Use guides in [docs/security/](../security/)

**...contribute to the project**
→ Read [.github/copilot-instructions.md](../../.github/copilot-instructions.md) and [demo-wallet/CONTRIBUTING.md](../../demo-wallet/CONTRIBUTING.md)

**...track current tasks**
→ Check [.github/tasks.md](../../.github/tasks.md)

**...understand the demo wallet**
→ See [demo-wallet/README.md](../../demo-wallet/README.md) and [docs/demo-wallet-verification.md](../demo-wallet-verification.md)

---

## 📞 Getting Help

1. **Check the FAQ**: [docs/faq.md](../faq.md)
2. **Search documentation**: Use your editor's search to find relevant docs
3. **Review test cases**: See [tests/](../../tests/) for usage examples
4. **Check issue tracker**: GitHub issues for known problems

---

## 🔄 Documentation Updates

This index is maintained as documentation evolves. Last major cleanup: October 15, 2025.

**Contributing to documentation**:
- Follow the [Copilot Working Agreement](../../.github/copilot-instructions.md)
- Update this index when adding new major documentation
- Keep docs/ organized by category
- Remove obsolete documentation promptly

---

**Quick Links**:
- [Main README](../../README.md)
- [Task Tracking](../../.github/tasks.md)
- [Project Status](../PROJECT-STATUS.md)
- [Security Guides](../security/)
- [API Security Complete](../TASK-3-COMPLETION-SUMMARY.md)
