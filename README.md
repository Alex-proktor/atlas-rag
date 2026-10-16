# Atlas RAG

**Local-first, provider-neutral document retrieval. Built to be adapted, not just demonstrated.**

[![CI](https://github.com/Alex-proktor/atlas-rag/actions/workflows/ci.yml/badge.svg)](https://github.com/Alex-proktor/atlas-rag/actions/workflows/ci.yml)

Atlas RAG is an open-source Python/FastAPI service that indexes Markdown documentation in Qdrant and returns relevant passages with explicit source references. It is intended as a reusable foundation for internal knowledge assistants, documentation search and agent integrations.

**Status: early MVP.** The implementation is published, but end-to-end Docker deployment, security hardening and retrieval quality benchmarks have not yet been independently verified. It is **not production-ready**.

## Why Atlas?

- **No Llama or Ollama lock-in.** Retrieval uses local multilingual Sentence Transformers; a vendor-neutral generation adapter is planned separately.
- **Evidence-first answers.** Search results contain document paths, chunk indices, similarity scores and the original passages.
- **Local data boundary.** Documents are mounted read-only, indexed locally, and are not automatically sent to an external model.
- **Reproducible starter.** Docker Compose, automated unit tests and an openly licensed codebase.
- **Honest scope.** Authentication, enterprise permissions, evaluation, deletion sync and grounded LLM generation are roadmap items, not claimed features.

## Architecture

```text
  Markdown files (read-only)
            |
   validated document root
            |
       text chunker
            |
 local multilingual embeddings
            |
         Qdrant
            ^
            |
       FastAPI search
            |
  cited passages + scores
```

## Run locally

Requires Docker and Docker Compose. First startup downloads the embedding model and needs Internet access.

```bash
git clone https://github.com/Alex-proktor/atlas-rag.git
cd atlas-rag
docker compose up --build -d
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/index -H "Content-Type: application/json" -d '{"path":"."}'
curl -X POST http://127.0.0.1:8000/search -H "Content-Type: application/json" -d '{"query":"What does Atlas RAG index?","limit":3}'
```

Interactive API docs: http://127.0.0.1:8000/docs

API: `GET /health`, `POST /index`, `POST /search`.

For local development without Docker: `python -m pip install -e ".[dev]"` and `pytest -q`. The API needs a reachable Qdrant instance for indexing and search.

## Configuration

| Environment variable | Default | Description |
|---|---|---|
| `QDRANT_URL` | `http://qdrant:6333` | Vector database |
| `DOCS_ROOT` | `/data` | Allowed document root |
| `COLLECTION` | `atlas_documents` | Vector collection |
| `EMBEDDING_MODEL` | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Local embedding model |

Changing embedding models requires a compatible collection or reindexing. Existing index entries are currently updated by path/chunk number, but removed documents and obsolete chunks are **not** deleted automatically.

## Security boundaries

This is a **single-user development service**. API and Qdrant ports bind to localhost by default. It has no API authentication, rate limiting, role-based permissions, tenant isolation, content-size caps, malicious-file sandboxing, or production security review. Do not expose it publicly or index confidential company data without additional controls. Do not commit secrets or private documents.

## Quality and acceptance

Automated unit tests cover chunking and path validation. The next quality gate is a repeatable Docker smoke test and a small labeled retrieval evaluation set. No accuracy, latency or reliability metrics are claimed until measured.

## Roadmap

1. **Foundation:** reproducible ingestion and cited retrieval, Docker smoke test, tests and operational fixes — [Issue #1](https://github.com/Alex-proktor/atlas-rag/issues/1).
2. **Lifecycle:** incremental indexing, document update/delete sync and index migrations.
3. **Retrieval quality:** lexical + vector hybrid search, reranking, labeled benchmarks, recall@k and citation checks.
4. **Generation:** configurable OpenAI-compatible API (including self-hosted backends), grounded answers and abstention.
5. **Enterprise:** authentication, document-level permissions, observability, deployment and threat model.
6. **Integrations:** Hermes connector, polished demo, architecture and adoption guide.

## License

MIT — see [LICENSE](LICENSE). Contributions and issue reports are welcome.
