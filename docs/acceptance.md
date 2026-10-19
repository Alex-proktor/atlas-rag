# Acceptance evidence — 2026-10-19

## Verified release 0.2.1
PR #7 introduced the platform; PR #8 fixed CPU packaging and completed live Hermes acceptance.
Tested implementation: 039bb89edd3e40510d657c69469e3fd4e8e15628.
PR #8 merge: 8a2dc1da7c39829672ef33c1c106c514005be12f.

- [CI run 39233062458](https://github.com/Alex-proktor/atlas-rag/actions/runs/39233062458) passed all steps: **23 tests**, Ruff, Bandit, dependency audit, real Qdrant, actual multilingual embeddings/CrossEncoder, Docker build and authenticated HTTP demo.
- The local CPU image passed **23 tests in 10.51 seconds**, without skips. Runtime reports torch 2.14.1+cpu and cuda=None; the Dockerfile enforces that property. No GPU is required.
- Lifecycle tests cover updates/deletions, incremental vector reuse, restart, injected embedding/upload failures and model incompatibility. Security/protocol tests cover tenant/ACL filtering, authentication/roles, bounded requests/rate, citations, invalid evidence and provider failure.
- Local authenticated HTTP indexing/search completed successfully. Unauthorized search returned 401.
- Installed Hermes v0.21.5 loaded atlas-rag through its real PluginManager/ToolRegistry and returned backup.md with the 30-day evidence. A separately generated reader credential was used: writing returned 403; an invalid credential returned 401.
- The actual /answer HTTP endpoint returned a source-validated quotation about 30-day backup retention and citation [1] to backup.md, chunk 0. The opt-in live provider was a verified zero-price OpenRouter model; no proprietary content was transmitted. No provider is mandatory.
- Managed Python 3.14.7 imports, STT/TTS imports, worker health, fresh Gateway heartbeat and Telegram polling health evidence passed after plugin configuration. No voice transcription or Telegram-message acceptance is claimed.
- Public live evidence: evaluation/hermes-live.json. It contains no credentials, private configuration or proprietary documents.

## Retrieval measurements and limits
On 24 synthetic bilingual questions (12 English, 12 Russian), BM25 Recall@3/MRR@3/nDCG@3 = 1.0000/0.9792/0.9846; dense = 0.9583/0.9375/0.9430; hybrid and reranked = 1.0000/1.0000/1.0000. Raw per-query results and current CPU CI/artifact provenance are in evaluation/results.json.

The author-created corpus is small and in-sample. Reranking did not improve this easy set. Timings include initialization and are not production latency measurements. The separate live positive/refusal/injection probe has three cases; it is not a general safety benchmark or Ragas faithfulness score.

## Operational recovery
Docker Desktop launch from a remote automation process failed when the Windows ProgramData environment variable was missing. Restoring it from the Windows CommonApplicationData folder allowed normal startup. Volumes were preserved; no data reset or Windows reboot was used. DGT and the existing proxy resumed alongside Atlas.

The plugin is installed/enabled in the actual Hermes profile with a configuration backup and reader-only token. Acceptance invoked the installed registry in a fresh managed process; an already-running agent may need a normal restart to refresh its tool list.

## Scope
Issues #1–6 have their scoped implementation and acceptance evidence. No independent production security review has taken place. This remains a bounded single-node reference platform, not a certified enterprise production system. Company rollout still requires its own identity integration, representative evaluation, retention/backup policy and security review.
