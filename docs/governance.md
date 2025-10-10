# Governance & Community Process

## Objectives
- Maintain decentralized stewardship over biometric algorithms, parameters, and metadata schemas.
- Ensure upgrades are transparent, well-reviewed, and backwards compatible when possible.
- Build community trust through open RFCs, testing requirements, and public audits.

## Roles
- **Maintainers**: Curate repository, merge changes, coordinate releases.
- **Researchers**: Propose biometric or cryptographic improvements; shepherd RFCs.
- **Wallet Partners**: Integrate metadata schema and surface enrollment UX feedback.
- **Community Reviewers**: Validate implementations, run reproducibility tests, and raise security concerns.

## Decision Flow
1. Submit proposal as RFC (Markdown template in `docs/templates/rfc.md` when available).
2. Discuss asynchronously (GitHub issues, Cardano forum, Discord) for minimum seven days.
3. Run reference implementation + tests; publish results.
4. Maintainers issue a merge decision; contentious proposals can trigger off-chain vote assisted by a Catalyst-style ballot.
5. Tag release with semantic version; notify integrators via mailing list and metadata registry.

## Parameters Under Governance
- Quantization grid size and angle bins.
- Hash algorithm and personalization tags.
- Helper data length, salt entropy, and validation thresholds.
- Metadata schema versioning and optional fields.

## Transparency Practices
- Publish change logs with human-readable summaries and migration guides.
- Maintain public dashboard tracking adoption metrics (wallet support, number of enrollments, audit status).
- Host quarterly community calls to review roadmap progress and surface new risks.

## Dispute Resolution
- Encourage mediation in working groups; if unresolved, escalate to time-boxed vote with clear acceptance thresholds.
- Emergency security fixes can bypass normal timelines but require retroactive disclosure and review.
