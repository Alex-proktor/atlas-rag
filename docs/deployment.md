# Deployment and adoption

## Local demonstration
Run `python scripts/configure_demo.py`, then `docker compose up --build -d`. Never commit `.env` or `.local-token`. The generated identity is an admin for the synthetic default tenant. To authorize Swagger requests, enter `Bearer <token>` in the Authorization header; curl and scripts also work.

For a different host port set ATLAS_PORT in .env. Only loopback is published. Qdrant is not externally published.

## Corporate customization
1. Replace the examples mount with read-only `/approved-documents:/data:ro`.
2. Create one folder per tenant (letters, digits, hyphen or underscore), containing only approved Markdown.
3. Supply identities from your secret/configuration system. Each row has subject, tenant, groups, role and token_sha256. Never embed plaintext tokens in images.
4. Start with reader identities. Give writers explicit group scope; admin means full ACL authoring within its own tenant, not cross-tenant access.
5. Configure an approved embedding model and optionally a multilingual reranker. Keep model artifacts/revisions in your model registry.
6. For generation set LLM_BASE_URL ending in /v1, LLM_MODEL and LLM_API_KEY. External endpoints additionally need LLM_ALLOW_EXTERNAL=true. Authorized passages are sent to that endpoint.
7. Validate against your own corpus and access matrix before adding an SSO gateway, TLS, monitoring, encrypted storage and backup policy.

## Lifecycle and consistency
POST /index accepts path (relative directory), force (re-embed scope), and acl (group list). It is an authoritative sync of Markdown files in that scope: removed documents and stale chunks disappear in the newly published snapshot. All files in that scope receive the supplied ACL; split directories by access policy when needed.

The store compares full content hashes and reuses vectors for unchanged chunks. It copies the complete live index into a new Qdrant collection, validates point count, then atomically updates a live alias. Queries pin one immutable collection for both retrieval stages. Failed embedding/upload/validation leaves the old alias untouched. Emptying a scope publishes an empty replacement when appropriate.

This provides atomic visibility, not low-cost delta storage: embedding work is incremental; snapshot storage/upload is O(total index). Intended maximum is 25,000 chunks. BM25 scans authorized chunks per query. Use Qdrant sparse vectors/inverted indexes before scaling beyond this bounded reference design.

All writers must use the same STATE_ROOT lock volume; supported topology is one API instance. Do not deploy independent writers with separate locks. Initial migration uses a new _live alias and does not touch legacy MVP collections.

## Model migration
Embedding model/chunker fingerprint mismatch rejects a sync. Set a new COLLECTION, reindex fully, validate, then route readers to it. Keep the old collection for rollback. Changing upstream model files without changing the model identifier is unsupported: pin model revisions in an artifact registry for controlled releases.

## Backup, rollback and physical deletion
Back up Qdrant storage and deployment configuration with your approved tools; protect token digests and credentials. Snapshot collections have names ending in random UUIDs. Previous snapshots are intentionally retained for in-flight readers and operator rollback; no automatic garbage collector is shipped.

To remove obsolete snapshots: stop the API, record the active alias target, back up if policy permits, delete only nonactive snapshot collections through the private Qdrant administration channel, then restart and verify search. Also remove backups according to policy for legal erasure. Never delete an active collection or mutate a published snapshot. Retention is an explicit operator responsibility.

## Health
GET /health is unauthenticated liveness only. GET /ready requires credentials and loads the model/checks Qdrant. Monitor latency, error codes and resource use. Model downloads can make first readiness slow. Resource/request caps are bounded-demo defaults; tune from measured traffic, not guesses.
