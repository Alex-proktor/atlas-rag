# Acceptance evidence — 2026-10-19

## Completed implementation and acceptance
PR #7 merged as 8d76b86897da96745c6d09f0c2e1d10b638f4343. The tested source head is df66867fea08409fe4c0f4cc6047e94d5f896dc2.

- GitHub CI [run 39230021766](https://github.com/Alex-proktor/atlas-rag/actions/runs/39230021766) passed every step: **23 tests**, Ruff, Bandit (no skipped rules/findings), dependency audit, real Qdrant, actual multilingual embeddings and CrossEncoder, Docker image build and authenticated HTTP demo.
- Tests cover update/delete sync, incremental reuse, restart, embedding/upload failure preservation, model mismatch, tenant/ACL filtering before dense and BM25 scoring, authentication/roles, request/rate caps, provider HTTP protocol, citations and fabricated evidence rejection.
- Live OpenRouter free model nvidia/nemotron-3.5-lightning:free passed quoted answer, unsupported-question refusal and secret-extraction refusal on public fictional content. See evaluation/live-generation.json. Three cases are not a general safety/accuracy benchmark.
- On 24 synthetic bilingual queries (12 English, 12 Russian), BM25 Recall@3/MRR@3/nDCG@3 = 1.0000/0.9792/0.9846; dense = 0.9583/0.9375/0.9430; hybrid and real CrossEncoder reranking = 1.0000/1.0000/1.0000. Raw per-query results and CI/artifact provenance are in evaluation/results.json.
- The author-created corpus is small and in-sample. Reranking did not improve this easy set. Elapsed timings include initialization and are not production latency measurements.
- Local Docker integration before the engine failure: 23 passed, no skips, 9.70 seconds. Final Windows non-service regression: 15 passed, 8 explicit skips.
- Installed Hermes v0.21.5 plugin doctor passed real discovery, manifest parsing, import and runtime registration: one tool, no hooks.
- Credential pattern scan passed. Dependency audit after upgrading pip 26.2.1/setuptools 84.0.0 found no known vulnerabilities. Public files contain fictional documents only.

## Remaining: Issue #6 live Hermes connection
Actual Hermes tool invocation against the local authenticated Atlas API is not yet accepted. The plugin is not claimed active in the live agent profile.

Docker Desktop began returning engine HTTP 500 during local acceptance. API versions 1.54 and 1.47 failed; local health endpoints were unavailable. A normal Docker Desktop restart was attempted without deleting volumes or resetting data. Local recovery must finish before installing/configuring the reader identity and proving a cited tool response plus unauthorized-access rejection. Issue #6 remains open.

No independent production security review has taken place. This is a bounded single-node reference platform, not a certified production system. See docs/security.md and docs/deployment.md.
