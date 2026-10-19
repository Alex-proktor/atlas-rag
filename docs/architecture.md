# Architecture decisions

## Chosen boundaries
- Pure ingestion helpers, snapshot store, retrieval, generation and security are separate modules.
- Qdrant alias switching gives atomic visibility. Unchanged content reuses embeddings; a failed sync never partially replaces live passages.
- Local multilingual embeddings plus Unicode BM25 and RRF balance semantic matches with identifiers/keywords. An optional cross-encoder reranks a bounded candidate pool.
- Dense and lexical candidates use identical server-side authorization before scoring and generation.
- An OpenAI-compatible HTTP contract supports local or corporate-hosted backends without provider SDK lock-in.
- Exact quotations are a deliberately restricted answer format. They are mechanically verifiable but still need semantic relevance evaluation.
- Hermes consumes a read-only search contract, not implementation internals. Its model-routing decisions do not become Atlas configuration.

## Reuse from hermes-ai-lab
Reviewed main architecture and the Boss Controller plugin interface on 2026-10-19. Reused the separation of logical capabilities from provider/model IDs, isolated worktrees, minimal evidence contracts and explicit external-data boundaries. Did not copy Telegram, shell execution, model fleet or worker orchestration into a document service. The integration uses Hermes register_tool and a standard-library HTTP client.

## Sources consulted
- [Qdrant hybrid and multi-stage queries](https://qdrant.tech/documentation/search/hybrid-queries/): candidate fusion and RRF.
- [Qdrant aliases](https://qdrant.tech/documentation/concepts/collections/#collection-aliases): atomic collection switching.
- [Ragas metrics](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/): separate retrieval coverage, answer relevance and faithfulness.
- [OWASP prompt injection prevention](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html): untrusted context, least privilege and layered controls.
- [Sentence Transformers rerankers](https://www.sbert.net/examples/cross_encoder/applications/README.html): cross-encoder candidate scoring.

These sources inform design; they do not certify this implementation. Server-side BM25 is intentionally a simple auditable bounded-corpus baseline; it is not advertised as Qdrant-native sparse search.
