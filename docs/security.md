# Security model

## Trust boundaries
The API authenticates a bearer credential against a configured SHA-256 digest using constant-time comparison. Configuration supplies subject, tenant, groups and reader/writer/admin role. Clients cannot choose a tenant in requests. Tokens must have at least 32 characters; generate random tokens, never human passwords. Rotate by replacing the configured digest and restarting the API.

The filesystem has a separate read-only directory per tenant. Writers may synchronize only their tenant root. Dense retrieval applies tenant/ACL filters inside Qdrant. BM25 receives only the same authorized records, so unauthorized text does not affect lexical scores. Generation receives only the resulting evidence. Empty document ACL means tenant-wide access; ACL groups have OR semantics.

Qdrant is on a private Compose network with no published port. Its administrator can read every snapshot; database administrators, host administrators and the credential configuration are trusted. Network isolation is not database-level encryption or an identity provider. Before multi-host operation, add database authentication, TLS and network policy.

## Enforced controls
- Reader credentials cannot mutate the index. Writers must provide a nonempty ACL within their configured groups. Every existing document in the synchronized scope must already have exactly that ACL. Only an admin can relabel existing documents or publish tenant-wide content; a broader directory sync fails before publication if it includes another ACL.
- Path traversal, files outside tenant roots and symbolic-link files are excluded.
- 16 KiB HTTP bodies, 2,000-character questions, at most 20 results.
- 1 MB/document, 20 MB per sync, 25,000 chunks per global snapshot.
- 60 authenticated requests/minute/credential/process. One Uvicorn worker and bounded concurrency.
- Non-root API, dropped capabilities, CPU/memory/PID caps, no automatic external LLM fallback.
- No query strings, document content, bearer tokens, provider errors or credentials in application audit records.
- Remote generation needs explicit external-transmission opt-in and HTTPS. HTTP is allowed only for loopback.
- Provider redirects and environment HTTP proxies are disabled. Model responses have a byte cap and timeout.

## Prompt injection and answer limits
Retrieved text and questions are untrusted. The model has no execution tools. Answers contain only exact source substrings and server-created citations. Malformed output, invented quotes, invalid source IDs and provider failures are rejected.

This proves textual provenance, not semantic correctness or complete prompt-injection resistance. A malicious source may itself contain a misleading quotation. Review corpus provenance, measure relevance/faithfulness and maintain human review for consequential decisions. No regex or system prompt is presented as a complete defense.

## Explicit deployment limits
This is a single-node reference implementation, without SSO/OIDC, distributed quotas, encryption at rest, a hardened document parser sandbox, automated key rotation, formal compliance or independent penetration testing. Use a TLS/authentication gateway for company deployment. Do not claim production readiness without independent security review.

Immutable previous snapshots retain deleted/revoked data physically until an administrator removes them. Current retrieval never searches old snapshots. Apply an approved retention policy; see deployment guide. SHA-256 token digests are not substitutes for a vault.
