# Copilot Working Agreement

This repository combines a Python toolkit for biometric DID generation and a JavaScript demo wallet (`demo-wallet/`, based on Cardano Foundation's Veridian wallet). Follow these instructions whenever you contribute new code or documentation with Copilot assistance.

## 1. Planning First
- Read `docs/roadmap.md` and `docs/wallet-integration.md` before tackling a task to align with the current sprint goals.
- Confirm whether a change touches the Python toolkit, the demo wallet, or shared documentation. Note downstream impacts (tests, fixtures, docs) in your plan.
- For demo wallet work, keep upstream Veridian files intact where possible; annotate substantial divergences in comments or documentation.

## 2. Coding Conventions
- Keep files ASCII unless the file already uses Unicode and it is essential.
- Prefer small, composable functions; add brief comments only when behaviour is non-obvious.
- Python: adhere to standard formatting (PEP 8). JavaScript/TypeScript: match existing lint setup (ESLint + Prettier).
- Do not reintroduce the original Git remote inside `demo-wallet/`; the directory stays detached from the Cardano Foundation repository.

## 3. Testing & Tooling
- Python changes: run `pytest` (root `tests/`). Target individual files with `python -m pytest tests/<file>` when the suite is large.
- Demo wallet changes: run relevant npm scripts. At minimum execute `npm test` for Jest unit suites; add targeted WebDriverIO runs if UI flows change.
- When editing build tooling or configs, run a dry build (`npm run build:local` or `pip install -e .`) to ensure no regressions.
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

## 6. Review & Communication
- Summaries should state *what* changed, *why*, tests run, and outstanding follow-ups.
- Call out assumptions or open questions explicitly so reviewers can respond quickly.
- Use TODO comments sparingly; prefer GitHub issues or updates to `docs/roadmap.md` for larger gaps.

Following this agreement keeps Copilot-driven work aligned with the broader roadmap while preserving quality standards across both codebases.
