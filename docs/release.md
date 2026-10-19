# Release checklist

- [x] Tested implementation a560f97 passed CI, including real Qdrant, CPU-only image, models and evaluation.
- [x] Dependency audit and static security scan reviewed; no unresolved high-severity findings.
- [x] Docker demo verified from the documented configuration.
- [x] Public dataset, logs and fixtures contain only fictional content.
- [x] No .env, token files, credentials, private paths or proprietary documents tracked.
- [x] Benchmark results include corpus, query count, model and limitations.
- [x] Real provider and Hermes acceptance evidence is recorded; failures remain explicit.
- [ ] Deployment owner sets identity, external transmission, backups and physical retention policy.
- [ ] Independent security review completed before a production readiness claim.

A repository feature issue may close when its scoped criteria pass; this checklist is a separate production rollout gate.
