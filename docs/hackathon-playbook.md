# Hackathon Playbook

## Goals
- Deliver a working biometric DID prototype with live CLI demo and supporting documentation.
- Collect user feedback from judges and peers to inform post-hackathon roadmap.
- Produce a compelling narrative for privacy-preserving identity on Cardano.

## Team Roles
- **Lead Engineer**: owns biometric pipeline, CLI, and test harness.
- **Blockchain Specialist**: prepares Cardano metadata submission scripts and wallet demos.
- **UX & Demo Advocate**: curates enrollment walkthrough, slide deck, and live storytelling.
- **Research & Governance Lead**: fields privacy/governance questions, manages RFC backlog.

## Timeline
### Week -2 to -1 (Preparation)
- Validate fingerprint capture hardware compatibility; secure SDK licenses if needed.
- Rehearse CLI flow with synthetic data; capture screen recordings for backup demo.
- Draft slide deck covering problem, architecture, and impact.
- Align on success metrics (digest stability, verification latency, user control messaging).

### Week -1 (Polish)
- Conduct internal security review checklist using `docs/privacy-security.md` as guide.
- Finalize branding, visuals, and key talking points for pitch.
- Prepare FAQ sheet addressing privacy, false positives, governance, and Cardano integration.
- Run full test suite on clean environment; document setup in README.

### Event Day 1
- Morning: Kickoff meeting, confirm roles, sync on judging criteria.
- Midday: Integrate live hardware capture into CLI (optional if hardware available).
- Afternoon: Produce short video (≤90s) showing enrollment + verification pipeline.
- Evening: Dry-run presentation with mentors; log action items for improvements.

### Event Day 2
- Morning: Polish demo artifacts, ensure metadata submission to Cardano testnet works.
- Midday: Finalize pitch narrative, rehearse transitions between speakers.
- Afternoon: Deliver official submission package (code, docs, video, README quickstart).
- Evening: Present to judges; capture questions and follow-up topics.

## Deliverables Checklist
- ✅ Code repository with tests (`pytest` green).
- ✅ Documentation suite (proposal, architecture, privacy, governance, roadmap, playbook).
- ☐ Demo video or live capture fallback.
- ☐ Slide deck (Problem → Solution → Architecture → Demo → Impact → Roadmap).
- ☐ Optional: Cardano transaction metadata file produced live.

## Risk Mitigation
- **Hardware failure**: keep prerecorded footage and synthetic dataset as backup.
- **Time overrun**: enforce 30-minute limit per work session, re-evaluate priorities twice daily.
- **Questions overload**: designate Q&A owner; share FAQ to team via shared doc.

## Post-Hackathon
- Publish recap blog with lessons learned and judge feedback.
- Prioritize feature requests gathered during event; open issues tagged `post-hackathon`.
- Reach out to wallet partners and identity researchers for collaboration.
