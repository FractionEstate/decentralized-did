---
applyTo: '**'
---
# Copilot Working Agreement

This repository combines a Python toolkit for biometric DID generation and a production-ready wallet (`demo-wallet/`, based on Cardano Foundation's Veridian wallet). The wallet is designed for **production use**, not just demonstration. Follow these instructions whenever you contribute new code or documentation with Copilot assistance.

**CRITICAL**: The wallet is a **production application**, not a demo or proof-of-concept. All code must be production-grade: no mock fallbacks, no placeholder implementations, no development shortcuts in production builds.

## 0. Core Constraint: Open-Source Only
**CRITICAL**: This project uses NO PAID SERVICES OR COMMERCIAL SOFTWARE.
- All code must be open-source (Apache 2.0, MIT, BSD, GPL, LGPL, or public domain)
- All tools and libraries must be free and open-source
- All external services must be self-hostable or decentralized
- Hardware must use commodity components with open drivers
- When researching solutions, explicitly exclude commercial/proprietary options
- Document open-source alternatives and their licenses in all research deliverables

**Rationale**: This is a decentralized identity system built from scratch to ensure transparency, auditability, and community ownership. Paid services introduce centralization risks and lock-in.

## 1. Planning First
- Read `docs/roadmap.md` and `docs/wallet-integration.md` before tackling a task to align with the current sprint goals.
- **Current Sprint**: Phase 4.5 - Tamper-Proof Identity Security (Week 1-2, Oct 14-25, 2025)
- **Priority Tasks**: Duplicate DID detection, transaction builder updates, documentation updates
- Confirm whether a change touches the Python toolkit, the demo wallet, or shared documentation. Note downstream impacts (tests, fixtures, docs) in your plan.
- For demo wallet work, keep upstream Veridian files intact where possible; annotate substantial divergences in comments or documentation.
- **Always write and update phases and tasks in `.github/tasks.md`** following these strict rules:
  - **Task numbering**: Each phase MUST restart at task 1 (not continuous numbering across phases)
  - **Format**: `- [ ] **task N** - Task description` where N starts at 1 for each phase
  - **Example**: Phase 0 has tasks 1-7, Phase 1 has tasks 1-6 (NOT tasks 8-13)
  - When adding or editing tasks, verify all tasks in that phase follow this pattern
  - Before committing changes, run: `python3 -c "import re; content=open('.github/tasks.md').read(); phases=re.split(r'^## Phase (\d+)', content, flags=re.MULTILINE); print('\n'.join([f'Phase {phases[i]}: tasks {min(map(int, t))}-{max(map(int, t))}' for i in range(1, len(phases), 2) if (t := re.findall(r'task (\d+)', phases[i+1]))]))"`

## 2. Coding Conventions
- Keep files ASCII unless the file already uses Unicode and it is essential.
- Prefer small, composable functions; add brief comments only when behaviour is non-obvious.
- Python: adhere to standard formatting (PEP 8). JavaScript/TypeScript: match existing lint setup (ESLint + Prettier).
- Do not reintroduce the original Git remote inside `demo-wallet/`; the directory stays detached from the Cardano Foundation repository.
- **Production Code Only**: Never use mock data, placeholder implementations, or development shortcuts in production code paths. Use feature flags or test-only modules for development/testing needs.
- **Fail Fast**: If production configuration is missing, fail with clear error messages. Do not fall back to localhost, mock APIs, or hardcoded values.

## 3. Testing & Tooling
- Python changes: run `pytest` (root `tests/`). Target individual files with `python -m pytest tests/<file>` when the suite is large.
- Demo wallet changes: run relevant npm scripts. At minimum execute `npm test` for Jest unit suites; add targeted WebDriverIO runs if UI flows change.
- When editing build tooling or configs, run a dry build (`npm run build:local` or `pip install -e .`) to ensure no regressions.
- Android deployment prep **must** include:
  - `HUSKY=0 npm install` (inside `demo-wallet/`) to guarantee local TypeScript/WDIO typings and avoid hook failures.
  - `npm run build:local` before any Capacitor sync so `build/` assets exist.
  - `npx cap sync android` after web assets change to regenerate native Gradle files.
  - `./gradlew assembleDebug` for smoke validation and `./gradlew assembleRelease` for production artifacts. Capture warnings (e.g., deprecated APIs, unstripped libs) in the summary.
- Document in your summary which commands were executed (or justify why tests were skipped).

## 4. Documentation Requirements
- Update README and the appropriate doc under `docs/` whenever behaviour, CLI flags, or workflows change.
- Keep `docs/roadmap.md` and `docs/wallet-integration.md` synchronised with implementation progress.
- If new APIs or CLI arguments are introduced, add or update module docstrings and usage examples.

## 5. Biometric Metadata Workflow
- Any change that affects metadata bundle structure must update:
  1. `src/decentralized_did/cardano/wallet_integration.py`
  2. Corresponding tests under `tests/`
  3. `docs/cardano-integration.md` and `docs/wallet-integration.md`
- Maintain compatibility with both `wallet` and `cip30` formats. Add regression tests when extending schemas.
- For demo wallet integration, ensure helper data handling remains explicit (inline vs external) and audit log updates are documented.

## 5.5. DID Generation Standards (Phase 4.5 - CRITICAL)
**ALWAYS use deterministic DID generation. Wallet-based format is DEPRECATED.**

### ✅ Correct DID Generation (DEFAULT)
```python
from src.decentralized_did.did.generator import generate_deterministic_did

# Generate DID from biometric commitment (Sybil-resistant)
did = generate_deterministic_did(commitment, network="mainnet")
# Result: did:cardano:mainnet:zQmHash...

# Build metadata with v1.1 schema
metadata = build_metadata_payload(
    wallet_address=wallet_address,
    digest=commitment,
    version="1.1",  # Always use v1.1
    controllers=[wallet_address],  # Multi-controller support
    enrollment_timestamp=datetime.now(timezone.utc).isoformat(),
    revoked=False
)
```

### ❌ Deprecated DID Generation (LEGACY)
```python
# DEPRECATED: Wallet-based format (Sybil vulnerable)
did = build_did(wallet_address, digest, deterministic=False)  # Shows warning
# Result: did:cardano:addr1...´hash´ (VULNERABLE)

# DEPRECATED: Metadata v1.0 (single controller)
metadata = build_metadata_payload(wallet_address, digest, version=1)  # Shows warning
```

### Security Principles
1. **One Person = One DID**: Deterministic generation enforces this cryptographically
2. **Privacy-Preserving**: No wallet address in DID identifier
3. **Multi-Controller Support**: One identity can be controlled by multiple wallets
4. **Revocable**: DIDs can be marked as revoked with timestamps
5. **Auditable**: Enrollment timestamps enable compliance

### When to Update Code
- **New code**: ALWAYS use `generate_deterministic_did()` and metadata v1.1
- **Existing code**: Update if touching DID generation logic
- **API servers**: Use deterministic generation (completed in Phase 4.5)
- **Tests**: Verify both deterministic (default) and legacy (with warnings) work
- **Documentation**: Show deterministic examples, note legacy format is deprecated

### Migration Path
- Legacy format still works (with deprecation warning) for backward compatibility
- All new enrollments should use deterministic format
- See `docs/MIGRATION-GUIDE.md` for detailed migration instructions
- Legacy format will be removed in v2.0

## 6. SDK Integration & Architecture
**CRITICAL**: Maintain clean separation between SDK, core API, and demo wallet.

### Architecture Pattern (Verified 2025-01-29)
```
demo-wallet/ (TypeScript/React)
    ↓ HTTP API calls
core/api/ (Python/FastAPI)
    ↓ imports from SDK
sdk/src/decentralized_did/ (Python toolkit)
```

### ✅ Correct SDK Integration
**Core API Server** (`core/api/api_server_secure.py`):
```python
# ALWAYS import from SDK - NEVER reimplement
from pathlib import Path
import sys

# Resolve SDK path
sdk_path = Path(__file__).parent.parent.parent / "sdk" / "src"
sys.path.insert(0, str(sdk_path))

# Import SDK functions
from decentralized_did.did.generator import generate_deterministic_did
from decentralized_did.cardano.koios_client import KoiosClient
from decentralized_did.cardano.cache import TTLCache
```

**Demo Wallet** (`demo-wallet/src/core/biometric/biometricDidService.ts`):
```typescript
// Call Python CLI or API - DO NOT reimplement crypto
private pythonCliPath = "python3 -m decentralized_did.cli";

// For local DID generation (non-crypto only):
// Allowed: Blake2b hashing, Base58 encoding (deterministic operations)
// Forbidden: Fuzzy extractor, commitment generation, signature verification
```

### ❌ Anti-Patterns (NEVER DO THIS)
```python
# ❌ DON'T copy SDK code into core/api/
def generate_did(commitment, network):  # WRONG - reimplements SDK
    # ... duplicated logic ...
```

```typescript
// ❌ DON'T implement biometric crypto in TypeScript
function generateCommitment(template: Buffer) {  // WRONG - should call API
    // ... reimplements fuzzy extractor ...
}
```

### SDK Version Management
1. **SDK is source of truth** for all biometric operations
2. **Current SDK version**: 0.1.0 (from `sdk/pyproject.toml`)
3. **When SDK changes**:
   - Update API server imports if function signatures change
   - Update CLI integration in demo wallet if command flags change
   - Update tests in `core/api/` and `demo-wallet/tests/`
   - Document breaking changes in `docs/MIGRATION-GUIDE.md`
4. **Version compatibility**:
   - Core API must use SDK v0.1.0+ (deterministic DID support)
   - Demo wallet must call API endpoints with v1.1 metadata schema
   - Legacy v1.0 metadata shows deprecation warnings

### Adding New SDK Features
**Step 1**: Implement in SDK (`sdk/src/decentralized_did/`)
```python
# Example: New biometric verification method
def verify_with_liveness(template: bytes, challenge: bytes) -> bool:
    """Verify template with liveness detection."""
    # Implementation here
```

**Step 2**: Add API endpoint (`core/api/api_server_secure.py`)
```python
from decentralized_did.biometric.verification import verify_with_liveness

@app.post("/api/v1/verify-liveness")
async def verify_liveness_endpoint(request: LivenessRequest):
    result = verify_with_liveness(request.template, request.challenge)
    return {"verified": result}
```

**Step 3**: Call from demo wallet (`demo-wallet/src/core/biometric/`)
```typescript
async verifyWithLiveness(template: Uint8Array, challenge: Uint8Array) {
    const response = await fetch(`${API_BASE}/verify-liveness`, {
        method: 'POST',
        body: JSON.stringify({ template, challenge })
    });
    return response.json();
}
```

**Step 4**: Test integration
```bash
# SDK unit tests
cd sdk && pytest tests/

# API integration tests
cd core/api && pytest

# Demo wallet tests
cd demo-wallet && npm test
```

### Verification Checklist
Before merging SDK-related changes:
- [ ] SDK functions properly exported in `__init__.py`
- [ ] Core API imports from SDK (no code duplication)
- [ ] Demo wallet calls API (no direct SDK imports)
- [ ] Tests pass at all three layers
- [ ] Documentation updated (`docs/cardano-integration.md`, `docs/wallet-integration.md`)
- [ ] No hardcoded biometric logic outside SDK

## 7. Review & Communication
- Summaries should state *what* changed, *why*, tests run, and outstanding follow-ups.
- Call out assumptions or open questions explicitly so reviewers can respond quickly.
- Use TODO comments sparingly; prefer GitHub issues or updates to `docs/roadmap.md` for larger gaps.

## 7.1 Android Build Environment Checklist
- Use OpenJDK 21 (`/usr/lib/jvm/java-21-openjdk-amd64`) and set `org.gradle.java.home` accordingly when modifying Gradle files.
- Ensure the Android SDK command-line tools live at `/opt/android-sdk` (or update `local.properties`) and keep `sdk.dir` out of version control.
- When tweaking ProGuard/R8 rules, run `npm run build:android:proguard` to refresh plugin overrides before invoking Gradle.
- Release artifacts live in `demo-wallet/android/app/build/outputs/apk/release/`; confirm they are regenerated after each relevant change.

## 8. Task Management in `.github/tasks.md`
**Critical Pattern**: Task numbers MUST restart at 1 for each phase.

### ✅ Correct Task Numbering
```markdown
## Phase 0 - Research
- [ ] **task 1** - First research task
- [ ] **task 2** - Second research task

## Phase 1 - Design
- [ ] **task 1** - First design task  ← Restarts at 1!
- [ ] **task 2** - Second design task
```

### ❌ Incorrect Task Numbering
```markdown
## Phase 0 - Research
- [ ] **task 1** - First research task
- [ ] **task 2** - Second research task

## Phase 1 - Design
- [ ] **task 3** - First design task  ← WRONG! Should be task 1
- [ ] **task 4** - Second design task
```

### Task Editing Checklist
1. **Adding tasks**: Insert at the correct position, renumber subsequent tasks in that phase only
2. **Removing tasks**: Delete the task, renumber subsequent tasks in that phase only
3. **Moving tasks**: Renumber both source and destination phases
4. **Verification**: After editing, verify each phase starts at task 1:
   ```bash
   grep -E "^## Phase|^\- \[ \] \*\*task [0-9]+" .github/tasks.md | less
   ```
5. **Quick count**: Verify task ranges per phase:
   ```bash
   python3 << 'EOF'
   import re
   with open('.github/tasks.md') as f:
       phases = re.split(r'^## Phase (\d+)', f.read(), flags=re.MULTILINE)
       for i in range(1, len(phases), 2):
           tasks = [int(t) for t in re.findall(r'task (\d+)', phases[i+1])]
           if tasks: print(f"Phase {phases[i]}: {len(tasks)} tasks (1-{max(tasks)})")
   EOF
   ```

### Why This Pattern?
- **Clarity**: Each phase is self-contained with clear task progression
- **Maintainability**: Adding/removing phases doesn't require renumbering all subsequent tasks
- **Navigation**: Easy to reference "Phase 3, task 2" without confusion
- **Flexibility**: Phases can be reordered without breaking task references

Following this agreement keeps Copilot-driven work aligned with the broader roadmap while preserving quality standards across both codebases.
