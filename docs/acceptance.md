# Acceptance evidence

## Fresh final acceptance — 2026-10-22

Starting main was independently fetched and verified as
`ce0b6d54fc0102506f8b9f99f12921ca37ee10b2`. No open issues or PRs existed at preflight;
[Issue #11](https://github.com/Alex-proktor/atlas-rag/issues/11) tracks this acceptance.
The candidate and final CI/merge state are linked in
[PR #13](https://github.com/Alex-proktor/atlas-rag/pull/13).
The existing deployment and other worktrees were preserved. Architecture and relevance
evaluation changes are outside this acceptance patch.

The README walkthrough ran in a separate checkout with a new Compose project, network
and all three volumes: Qdrant data, model cache and writer state. Only the host port
was changed to avoid the existing deployment. Docker reused dependency build layers;
this is a clean application/data/model-cache deployment, not a claim of a cache-free
image build. The demo indexed all 13 public documents, retrieved backup.md with the
30-day passage and rejected unauthenticated search with 401. No LLM was configured.

An immediate repeat of the documented up/demo sequence exposed an API startup race:
demo.py received RemoteDisconnected before Uvicorn was ready. The demo now waits up
to 60 seconds for liveness, then 300 seconds for authenticated model/database readiness
before its first write. CI runs the README sequence directly, without a separate shell
readiness loop. An immediate restart/demo repeat verifies this fix on the real service.
With Qdrant deliberately stopped, the updated demo stayed in readiness waiting and
completed successfully after Qdrant restarted; it does not retry a mutating index call.

### Real service checks

The following checks used actual HTTP requests, Qdrant 1.13.6 and the multilingual
Sentence Transformer. Temporary documents and credentials were generated only for
the isolated synthetic deployment. Sanitized observations are recorded in
[machine-readable evidence](../evaluation/acceptance-2026-10-22.json).

| Check | Observed result |
|---|---|
| Index/update/delete | Four chunks became one after editing; chunk 0 kept its ID; deleted file disappeared after scoped sync |
| Unchanged sync | indexed=0, changed=false |
| Tenant/ACL isolation | Unauthorized group saw no restricted chunks; another tenant saw only its own document; client tenant/group fields could not change credential-derived identity |
| Writer/path boundaries | ACL broadening and another group returned 403; parent-directory traversal returned 400 |
| No evidence/provider | Empty tenant returned insufficient_evidence with no sources; configured evidence with no provider returned a safe 503 |
| Qdrant outage | Search, readiness and indexing returned safe 503; liveness remained 200 |
| Qdrant recovery | Search recovered after restarting Qdrant without restarting the API |
| Persistent restart | Restarting both services preserved result IDs; subsequent sync remained unchanged |
| Reranking | Actual multilingual CrossEncoder returned numeric rerank scores; backup.md ranked first |
| Unreachable LLM | /answer returned a safe 503 while /search remained available; original provider configuration restored |

The real optional endpoint was the explicitly selected OpenRouter
liquid/lfm-2.5-2.6b:free model, listed at zero token price on the
[provider page](https://openrouter.ai/liquid/lfm-2.5-2.6b:free). It received only public
synthetic passages. The first positive /answer returned a validated 30-day quotation
and source citation. An unsupported-question request then exceeded the total provider
deadline and returned a safe 503; a repeat returned insufficient_evidence. A later
positive repeat and secret-extraction probe also returned safe 503s. No generated
content was released on those failures. One probe interrupted by an operator API
restart was excluded and repeated after restoration. Five completed requests and
that exclusion are recorded in the JSON evidence. These are individual integration
and availability observations, not a safety rate or production SLO. The current free
endpoint did not consistently complete within the configured deadline.

The rebuilt image's dependency audit checked 86 packages and found no known
vulnerabilities. It skipped the local Atlas package (no PyPI record) and the +cpu torch
wheel (local version suffix); an additional advisory query for upstream torch 2.14.1
also found no known vulnerabilities. This does not authenticate wheel contents or
replace an independent source/security review.

The installed managed Hermes 0.21.5 registry independently invoked atlas_search against
the existing synthetic deployment. It returned backup.md, chunk 0, with 30-day evidence;
reader indexing returned 403, invalid credentials returned 401, readiness returned 200.
The installed plugin and manifest exactly matched the reviewed repository. This used a
fresh process, after warming model readiness. The Telegram runtime was not tested.

### Fixes and verification

The public-data scanner missed removed sensitive filenames in history and private home
paths with forward slashes. Both omissions now have synthetic regression coverage.
The dependency audit flagged certifi 2026.10.18; requirements.lock now pins 2026.10.19.
Parallel [PR #12](https://github.com/Alex-proktor/atlas-rag/pull/12) delivered that pin
and fixed Compose forwarding of EMBEDDING_MODEL and COLLECTION. Its merged main is
included in this candidate. The merge exposed one additional scanner false positive:
GitHub's public merge-service noreply address is now allowed exactly, without allowing
other addresses at github.com.
Actual Compose config resolution passed both default and explicit model/collection
overrides; configuration output containing credentials was not published.
Deployment instructions now correctly describe document-level embedding reuse and
Hermes cold-start readiness. No runtime behavior change was needed for the exercised
Qdrant recovery or authorization paths.

The pinned Linux runtime passed **35 tests with zero skips**, plus Ruff and Bandit
(zero findings). Python was 3.11.17, qdrant-client 1.13.3, torch 2.14.1+cpu with no CUDA.
Git was supplied in an ephemeral test layer for the scanner's real-Git regressions.
The host run is secondary evidence: its client version differs and Windows skipped
the symlink case. CI independently supplies real Qdrant, models, dependency checks,
reranker evaluation and the authenticated Docker demo.

Current tracked files and reachable branch history passed the strengthened scanner.
Nine available cached PR commit snapshots passed content/filename inspection, but
legacy PR #7-9 commit metadata still exposes non-noreply email addresses. This is an
explicit privacy limitation, not a claim that public history can be fully recalled.
New commits use GitHub noreply. See [public audit](public-audit.md).

### Reproduce

1. Use a fresh clone and a unique COMPOSE_PROJECT_NAME; follow README setup. Use a
   different ATLAS_PORT and matching ATLAS_URL if port 8000 is occupied. Do not reuse
   production data or credentials. GET /health is liveness; authenticated GET /ready
   establishes embedding-model/database readiness.
2. Run the pinned CPU install and verification commands in README. Supply a disposable
   QDRANT_TEST_URL; all integration tests must run, rather than skip. The store/API
   tests recreate lifecycle, writer and tenant/ACL checks; provider tests run actual
   local HTTP servers with deterministic responses. Those servers prove protocol and
   citation validation, not language-model quality.
3. On the disposable Compose project, stop qdrant and verify /search, /ready and /index
   return 503 while /health returns 200. Start qdrant and repeat search; then restart
   api and qdrant, verify readiness and rerun scripts/demo.py. Never stop a shared service.
4. To reproduce real reranking, configure RERANKER_MODEL as documented, recreate the API
   and call /search; returned rerank_score values must be numeric. The first model
   download can exceed the Hermes request budget.
5. Real-provider acceptance is opt-in: configure an approved endpoint/model, explicitly
   consent to external processing if applicable, and use only the public fictional
   corpus. scripts/live_generation.py checks quotation/refusal against one supplied
   passage; /answer additionally exercises retrieval over HTTP. Keep live observations
   separate from deterministic provider fixtures and the historical 24-query evaluation.
6. Run the fresh installed registry smoke in docs/hermes.md with a reader identity.
   Record an unavailable runtime as untested; do not infer Telegram acceptance.

## Historical acceptance — 2026-10-19

### Verified release 0.2.2
PR #7 introduced the platform; PR #8 fixed CPU packaging; PR #9 enforces a total provider deadline and completes the final live acceptance.
Tested implementation: a560f97024a84cbacba0fb1d580de6a76b000232.
PR #8 merge: 8a2dc1da7c39829672ef33c1c106c514005be12f.

- [CI run 39234673278](https://github.com/Alex-proktor/atlas-rag/actions/runs/39234673278) passed all steps: **24 tests**, Ruff, Bandit, dependency audit, real Qdrant, actual multilingual embeddings/CrossEncoder, Docker build and authenticated HTTP demo.
- The local CPU image passed **24 tests in 8.81 seconds**, without skips. Runtime reports torch 2.14.1+cpu and cuda=None; the Dockerfile enforces that property. No GPU is required.
- Lifecycle tests cover updates/deletions, incremental vector reuse, restart, injected embedding/upload failures and model incompatibility. Security/protocol tests cover tenant/ACL filtering, authentication/roles, bounded requests/rate, citations, invalid evidence and provider failure.
- Local authenticated HTTP indexing/search completed successfully. Unauthorized search returned 401.
- Installed Hermes v0.21.5 loaded atlas-rag through its real PluginManager/ToolRegistry and returned backup.md with the 30-day evidence. A separately generated reader credential was used: writing returned 403; an invalid credential returned 401.
- The actual /answer HTTP endpoint returned a source-validated quotation about 30-day backup retention and citation [1] to backup.md, chunk 0. The opt-in live provider was a verified zero-price OpenRouter model; no proprietary content was transmitted. No provider is mandatory.
- Public live evidence: evaluation/hermes-live.json. It contains no credentials, private configuration or proprietary documents.

The final live demo provider liquid/lfm-2.5-2.6b:free also refused an unsupported question and a secret-extraction prompt. Provider generation has one 30-second deadline across headers and body, including heartbeat whitespace; a real HTTP regression verifies cancellation. Dependency audit covers the final CPU image and contains no CUDA packages.

PR #9 merge: eef03a5228e340dcb40e2734adb8e7860156ec85.

## Retrieval measurements and limits
On 24 synthetic bilingual questions (12 English, 12 Russian), BM25 Recall@3/MRR@3/nDCG@3 = 1.0000/0.9792/0.9846; dense = 0.9583/0.9375/0.9430; hybrid and reranked = 1.0000/1.0000/1.0000. Raw per-query results and current CPU CI/artifact provenance are in evaluation/results.json.

The author-created corpus is small and in-sample. Reranking did not improve this easy set. Timings include initialization and are not production latency measurements. The separate live positive/refusal/injection probe has three cases; it is not a general safety benchmark or Ragas faithfulness score.

## Installed integration
The read-only plugin was verified through the installed Hermes registry in a fresh process. An already-running agent may need a normal restart to refresh its tool list.

## Scope
Issues #1–6 have their scoped implementation and acceptance evidence. No independent production security review has taken place. This remains a bounded single-node reference platform, not a certified enterprise production system. Company rollout still requires its own identity integration, representative evaluation, retention/backup policy and security review.
