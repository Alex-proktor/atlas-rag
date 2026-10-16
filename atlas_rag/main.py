"""HTTP retrieval API. Answer generation is deliberately out of MVP scope."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

from atlas_rag.core import chunks, markdown_files

app = FastAPI(title="Atlas RAG", version="0.1.0")
ROOT = Path(os.getenv("DOCS_ROOT", "/data"))
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
COLLECTION = os.getenv("COLLECTION", "atlas_documents")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
_model = None
_client = None


def encoder():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def database():
    global _client
    if _client is None:
        _client = QdrantClient(url=QDRANT_URL, timeout=20)
    return _client


class IndexRequest(BaseModel):
    path: str = Field(default=".", max_length=512)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=5, ge=1, le=20)


@app.get("/health")
def health():
    try:
        database().get_collections()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Vector store unavailable") from exc
    return {"status": "ok", "vector_store": "reachable"}


@app.post("/index")
def index(request: IndexRequest):
    try:
        paths = markdown_files(ROOT, request.path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    passages = []
    for file in paths:
        relative = file.resolve().relative_to(ROOT.resolve()).as_posix()
        for number, passage in enumerate(chunks(file.read_text(encoding="utf-8"))):
            passages.append((relative, number, passage))
    if not passages:
        return {"indexed": 0}
    vectors = encoder().encode([p[2] for p in passages]).tolist()
    client = database()
    dimension = len(vectors[0])
    if not client.collection_exists(COLLECTION):
        client.create_collection(COLLECTION, vectors_config=models.VectorParams(size=dimension, distance=models.Distance.COSINE))
    points = []
    for (path, number, passage), vector in zip(passages, vectors):
        identity = UUID(bytes=hashlib.sha256(f"{path}:{number}".encode()).digest()[:16], version=4)
        points.append(models.PointStruct(id=str(identity), vector=vector, payload={"path": path, "chunk": number, "text": passage}))
    client.upsert(collection_name=COLLECTION, points=points, wait=True)
    return {"indexed": len(points)}


@app.post("/search")
def search(request: SearchRequest):
    client = database()
    if not client.collection_exists(COLLECTION):
        return {"results": []}
    vector = encoder().encode(request.query).tolist()
    matches = client.query_points(collection_name=COLLECTION, query=vector, limit=request.limit, with_payload=True)
    return {"results": [{"score": hit.score, **(hit.payload or {})} for hit in matches.points]}
