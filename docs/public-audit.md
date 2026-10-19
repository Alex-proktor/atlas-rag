# Public repository review — 2026-10-19

## Remediation
The writer policy now requires an explicit nonempty ACL within the credential groups.
Every existing document in an authoritative sync scope must already have exactly that ACL.
Only tenant admins can relabel existing documents or publish tenant-wide content.
A rejected sync preserves the published snapshot, including when files were removed locally.

New regression coverage exercises the FastAPI route against real Qdrant, same-ACL updates,
cross-ACL overwrite/deletion rejection and administrator relabeling. The public-data guard
checks tracked files and optionally reachable history, reporting categories and object IDs
without matched values. It is a pattern scanner, not a guarantee against every secret type.

Actions and Qdrant are pinned to immutable identifiers. The CPU base image is digest-pinned.
Model revisions and package hashes still require an organization's artifact-registry policy.

## Privacy boundaries
Public samples are fictional. Reports omit local machine identifiers, home paths,
unrelated applications, credentials and personal account email addresses.
Use repository-local Git author settings with the GitHub noreply address before committing.
History cleanup replaces personal author/committer metadata and removes unrelated runtime
details. A private offline backup is retained for recovery.

A branch-history rewrite cannot recall prior downloads, forks or GitHub cached PR references.
Do not describe this as guaranteed deletion from the internet. Historical CI/evaluation
reports retain their original provenance; the source IDs precede the privacy rewrite.

## Quality boundaries
The 24-question bilingual synthetic evaluation is in-sample. Its perfect hybrid score
does not establish quality on unseen corporate documents. No RAGAS faithfulness,
production latency/SLO, independent penetration test or compliance certification is claimed.
Company adoption requires representative held-out evaluation, identity integration,
approved retention/backups, approved models and an independent security review.

## Reproduction
Run pytest with QDRANT_TEST_URL pointing at a disposable real Qdrant service.
Run python scripts/check_secrets.py --history from a complete clone.
CI also runs static analysis, a dependency audit, actual embedding/reranker evaluation
and an authenticated Docker demonstration. See acceptance.md for historical release evidence.
