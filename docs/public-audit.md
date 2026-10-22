# Public repository review вЂ” 2026-10-19

## Remediation
The writer policy now requires an explicit nonempty ACL within the credential groups.
Every existing document in an authoritative sync scope must already have exactly that ACL.
Only tenant admins can relabel existing documents or publish tenant-wide content.
A rejected sync preserves the published snapshot, including when files were removed locally.

Regression coverage exercises the FastAPI route against real Qdrant, same-ACL updates,
cross-ACL overwrite/deletion rejection and administrator relabeling. The public-data guard
checks tracked files and optionally reachable history, reporting categories and object IDs
without matched values. It is a pattern scanner, not a guarantee against every secret type.

The 2026-10-22 acceptance fixed two scanner omissions: deleted sensitive filenames
were not checked in history, and private home paths using forward slashes were missed.
History now checks changed filenames as well as blob content, including a blob reused
under different names. Regression fixtures contain only synthetic values.

Actions and Qdrant are pinned to immutable identifiers. The CPU base image is digest-pinned.
Model revisions and package hashes still require an organization's artifact-registry policy.

## Privacy boundaries
Public samples are fictional. Reports omit local machine identifiers, home paths,
unrelated applications, credentials and personal account email addresses.
Use repository-local Git author settings with the GitHub noreply address before committing.
History cleanup replaces personal author/committer metadata and removes unrelated runtime
details. A private local backup is retained for recovery.

A branch-history rewrite cannot recall prior downloads, forks or GitHub cached PR references.
Do not describe this as guaranteed deletion from the internet. Historical CI/evaluation
reports retain their original provenance; the source IDs precede the privacy rewrite.

The fresh audit found no matches in current files or the 32 reachable branch-history
commits at the starting main. Their author/committer emails use GitHub noreply. All nine
available commit snapshots from PRs #7-10 also passed the content/filename check.
Legacy cached commit metadata in PRs #7-9 still contains non-noreply email addresses;
PR #10 metadata is clean. Those records are an explicit unresolved privacy limit.

The dependency audit flagged certifi 2026.10.18 under PYSEC-2026-4320. The lock now
uses 2026.10.19, the fixed version recorded by the audit database; the image must be
rebuilt to use it. See the [advisory](https://osv.dev/vulnerability/PYSEC-2026-4320).

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

CI checks the authored candidate head. GitHub-generated PR merge metadata is outside
the project's author control; the merge gate is a fast-forward of that verified head.
