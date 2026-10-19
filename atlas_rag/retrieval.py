"""ACL-filtered BM25 + dense reciprocal-rank fusion and optional cross-encoder."""
import math
import re
from collections import Counter
from functools import lru_cache


def tokens(text):
    return re.findall(r"[^\W_]+", text.casefold(), flags=re.UNICODE)


def bm25(query, records):
    documents = [tokens(p.payload["text"]) for p in records]
    counts = [Counter(d) for d in documents]
    if not documents:
        return []
    average = sum(map(len, documents)) / len(documents) or 1
    scores = [0.] * len(documents)
    for term in set(tokens(query)):
        df = sum(term in c for c in counts)
        idf = math.log(1 + (len(documents) - df + .5) / (df + .5))
        for i, count in enumerate(counts):
            tf = count[term]
            scores[i] += idf * tf * 2.5 / (tf + 1.5 * (.25 + .75 * len(documents[i]) / average))
    return sorted([(p, score) for p, score in zip(records, scores) if score > 0],
                  key=lambda x: (-x[1], str(x[0].id)))


@lru_cache(maxsize=1)
def cross_encoder(name):
    from sentence_transformers import CrossEncoder
    return CrossEncoder(name, max_length=512)


def retrieve(store, query, limit, tenant, groups, mode="hybrid", reranker=""):
    collection = store.active()
    if not collection:
        return []
    access = store.access_filter(tenant, groups)
    depth = max(20, limit * 4)
    # Pin the immutable collection: lexical and dense stages see the same snapshot.
    dense = []
    if mode != "bm25":
        dense = store.client.query_points(
            collection, query=store.encoder.encode(query).tolist(), query_filter=access,
            limit=depth, with_payload=True).points
    lexical = []
    if mode != "dense":
        records, offset = [], None
        while True:
            batch, offset = store.client.scroll(collection, scroll_filter=access,
                                                limit=256, offset=offset, with_payload=True)
            records.extend(batch)
            if offset is None:
                break
        lexical = [p for p, _ in bm25(query, records)[:depth]]
    scores, candidates = {}, {}
    for ranking in [dense, lexical]:
        for rank, point in enumerate(ranking, 1):
            identity = str(point.id)
            scores[identity] = scores.get(identity, 0.) + 1 / (60 + rank)
            candidates[identity] = point
    ordered = sorted(candidates, key=lambda i: (-scores[i], i))[:depth]
    rerank_scores = {}
    if reranker and ordered:
        predictions = cross_encoder(reranker).predict(
            [(query, candidates[i].payload["text"]) for i in ordered])
        rerank_scores = dict(zip(ordered, map(float, predictions), strict=True))
        ordered.sort(key=lambda i: (-rerank_scores[i], i))
    return [dict(id=i, score=scores[i], rerank_score=rerank_scores.get(i),
                 **candidates[i].payload) for i in ordered[:limit]]
