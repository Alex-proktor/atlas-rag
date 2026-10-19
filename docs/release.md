# Release checklist

- [ ] CI passes at the release commit, including real Qdrant tests and evaluation.
- [ ] Dependency audit and static security scan reviewed; no unresolved high-severity findings.
- [ ] Docker demo verified from the documented configuration.
- [ ] Public dataset, logs and fixtures contain only fictional content.
- [ ] No .env, token files, credentials, private paths or proprietary documents tracked.
- [ ] Benchmark results include corpus, query count, model and limitations.
- [ ] Real provider and Hermes acceptance evidence is recorded; failures remain explicit.
- [ ] Deployment owner sets identity, external transmission, backups and physical retention policy.
- [ ] Independent security review completed before a production readiness claim.

A repository feature issue may close when its scoped criteria pass; this checklist is a separate production rollout gate.
