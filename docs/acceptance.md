# Acceptance evidence — 2026-10-19

## Verified
- Baseline main: cb44fb26c2cdd318b9c4143e03a7f3440c2e2c86.
- Isolated Windows worktree and separate Docker Compose project; original checkout retained.
- Real Qdrant 1.13.6 integration in Docker: **23 passed**, no skips (9.70 seconds).
- Tests cover update/delete sync, incremental embedding reuse, restart, embedding/upload failure preservation, incompatible model refusal, tenant/ACL filtering before both search stages, bearer authorization, write roles, payload/rate limits, HTTP model contract, citations and invalid evidence rejection.
- Live OpenRouter free model nvidia/nemotron-3.5-lightning:free: positive quoted answer, unsupported question refusal and secret-extraction refusal passed. Public fictional content only. This is three acceptance cases, not a general safety/accuracy benchmark. See evaluation/live-generation.json.
- Installed Hermes v0.21.5 plugin doctor: discovery, manifest parsing, import and actual runtime registration passed (one tool, no hooks).
- Dependency audit after upgrading pip to 26.2.1 and setuptools to 84.0.0: no known vulnerabilities reported. See evaluation/dependency-audit.json.

- GitHub CI run 39229373439 passed static checks, dependency audit, real Qdrant tests and the model-backed benchmark. On 24 bilingual synthetic queries: BM25 Recall@3 1.000 / MRR@3 0.9792 / nDCG@3 0.9846; dense 0.9583 / 0.9375 / 0.9430; hybrid 1.000 / 1.000 / 1.000. Raw results and provenance: evaluation/results.json. This small authored set is not evidence of enterprise-wide accuracy.
- Final Windows non-service regression after the error-boundary change: 15 passed, 8 explicitly skipped (real Qdrant unavailable and Windows symlink permissions).
- Final Bandit scan: zero findings, no skipped rules. Tracked-file credential pattern scan passed.

## Pending acceptance
- Local model-backed smoke and benchmark were interrupted by Docker Desktop engine failures (500 Internal Server Error from dockerDesktopLinuxEngine). CI completed the benchmark instead; final Docker image smoke is still pending.
- Optional CrossEncoder implementation has not yet had a real-model acceptance run.
- Hermes end-to-end tool invocation against a running Atlas API is not yet verified.
- Final CI, source scan and final-commit regression results must be recorded before closing the corresponding issues.
- No independent production security review has taken place.

Earlier successful checks do not establish acceptance of later untested changes. Feature claims in README describe implemented interfaces; this evidence file describes what was actually verified.
