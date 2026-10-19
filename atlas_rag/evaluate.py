"""Reproducible document-level retrieval evaluation (real Qdrant/model)."""
import argparse
import json
import math
import os
import time
from pathlib import Path

from atlas_rag.main import store
from atlas_rag.retrieval import retrieve


def metrics(ranked, relevant, k):
    ranked = list(dict.fromkeys(ranked))[:k]
    relevant = set(relevant)
    hits = [int(item in relevant) for item in ranked]
    recall = sum(hits) / len(relevant) if relevant else 0.
    mrr = next((1 / i for i, hit in enumerate(hits, 1) if hit), 0.)
    dcg = sum(hit / math.log2(i + 1) for i, hit in enumerate(hits, 1))
    ideal = sum(1 / math.log2(i + 1) for i in range(1, min(len(relevant), k) + 1))
    return {"recall": recall, "mrr": mrr, "ndcg": dcg / ideal if ideal else 0.}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="evaluation/queries.json")
    parser.add_argument("--output", default="evaluation/results.json")
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--reranker", default="")
    args = parser.parse_args()
    cases = json.loads(Path(args.dataset).read_text(encoding="utf-8"))
    engine = store()
    engine.sync(tenant="default")
    report = {"dataset": args.dataset, "queries": len(cases), "k": args.k,
              "embedding_model": os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"),
              "reranker": args.reranker or None, "modes": {}}
    modes = ["bm25", "dense", "hybrid"] + (["reranked"] if args.reranker else [])
    for mode in modes:
        results = []
        started = time.monotonic()
        for case in cases:
            hits = retrieve(engine, case["query"], 20, "default", [],
                            mode="hybrid" if mode == "reranked" else mode,
                            reranker=args.reranker if mode == "reranked" else "")
            results.append({**case, **metrics([h["path"] for h in hits], case["relevant"], args.k)})
        report["modes"][mode] = {
            **{key: sum(r[key] for r in results) / len(results)
               for key in ["recall", "mrr", "ndcg"]},
            "elapsed_seconds": round(time.monotonic() - started, 3), "cases": results}
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({m: {k: v for k, v in data.items() if k != "cases"}
                      for m, data in report["modes"].items()}, indent=2))
    if report["modes"]["hybrid"]["recall"] < .8:
        raise SystemExit("Hybrid Recall@K below .8 gate")


if __name__ == "__main__":
    main()
