# Evaluation protocol

## Retrieval
The versioned dataset contains 24 hand-labeled queries: 12 English and 12 Russian, against a fictional bilingual corporate handbook. Each query has a document-level relevance label. Scores deduplicate document paths before computing Recall@3, MRR@3 and binary nDCG@3. Dense, BM25 and RRF use the same corpus and labels.

Run `python -m atlas_rag.evaluate` with DOCS_ROOT, QDRANT_URL, STATE_ROOT and a disposable COLLECTION. This performs real indexing and retrieval. Optional `--reranker cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` adds a measured reranking variant. The hybrid recall gate is 0.8; it is a smoke regression gate, not a business acceptance threshold.

The corpus and questions were authored together. There is no held-out enterprise set, statistical significance or out-of-domain generalization claim. Bilingual passages make cross-language coverage easier. Report per-language/domain results on an independently labeled customer corpus before deployment. Do not call these numbers a universal accuracy score.

## Generation
Unit/protocol tests use a real HTTP server with controlled JSON responses. They verify the OpenAI-compatible contract, citations, invalid-source rejection, refusal and failures; they do not evaluate a real model.

An optional live provider probe records separate evidence in evaluation/live-generation.json. Unavailable providers and invalid evidence remain failures. Generated quotations are validated exactly; this is not a semantic faithfulness score.

## Ragas
Ragas was reviewed as an optional second-stage evaluator. Its LLM-judged faithfulness, response relevance and context recall must use an approved judge and a recorded model/version. No Ragas scores are claimed without a completed judge run. Export questions, reference answers, retrieved contexts and responses, then run Ragas in the evaluation environment with approved credentials. Treat judge results as estimates and inspect disagreement cases.

Avoid sending confidential test data to a public judge. Deterministic retrieval metrics run independently of any paid LLM.
