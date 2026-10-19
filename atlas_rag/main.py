"""Authenticated knowledge API; tenant and groups come only from credentials."""
import logging
import os
from functools import lru_cache
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from filelock import Timeout
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient

from atlas_rag.generation import ProviderUnavailable, grounded_answer
from atlas_rag.retrieval import retrieve
from atlas_rag.security import BodyLimit, Identity, audit, authenticate, writer
from atlas_rag.store import SnapshotStore

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Atlas RAG", version="0.2.2")
app.add_middleware(BodyLimit)
app.middleware("http")(audit)


@lru_cache
def store():
    from sentence_transformers import SentenceTransformer
    model = os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    return SnapshotStore(QdrantClient(url=os.getenv("QDRANT_URL", "http://qdrant:6333"), timeout=30),
                         SentenceTransformer(model), Path(os.getenv("DOCS_ROOT", "/data")),
                         os.getenv("COLLECTION", "atlas_documents"), model,
                         Path(os.getenv("STATE_ROOT", str(Path.home() / ".local" / "state" / "atlas-rag"))))


class IndexRequest(BaseModel):
    path: str = Field(default=".", max_length=512)
    force: bool = False
    acl: list[str] = Field(default_factory=list, max_length=32)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=5, ge=1, le=20)


@app.middleware("http")
async def safe_error(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        # Catch before ServerErrorMiddleware: never re-raise secret-bearing errors to Uvicorn.
        logging.getLogger("atlas.audit").error("request_failed type=%s", type(exc).__name__)
        return JSONResponse(status_code=503, content={"detail": "Service temporarily unavailable"})


@app.get("/health")
def health():
    # Liveness only: do not download models or reveal infrastructure.
    return {"status": "ok"}


@app.get("/ready")
def ready(identity: Identity = Depends(authenticate)):
    store().client.get_collections()
    return {"status": "ready"}


@app.post("/index")
def index(request: IndexRequest, identity: Identity = Depends(authenticate)):
    writer(identity)
    if identity.role != "admin" and not set(request.acl).issubset(identity.groups):
        raise HTTPException(403, "ACL groups exceed writer permissions")
    try:
        return store().sync(request.path, identity.tenant, request.acl, request.force)
    except (ValueError, UnicodeError) as exc:
        raise HTTPException(400, "Invalid document scope, configuration or limits") from exc
    except Timeout as exc:
        raise HTTPException(409, "Index update already running") from exc


def find(request, identity):
    return retrieve(store(), request.query, request.limit, identity.tenant, list(identity.groups),
                    reranker=os.getenv("RERANKER_MODEL", ""))


@app.post("/search")
def search(request: SearchRequest, identity: Identity = Depends(authenticate)):
    return {"results": find(request, identity)}


@app.post("/answer")
def answer(request: SearchRequest, identity: Identity = Depends(authenticate)):
    try:
        return grounded_answer(request.query, find(request, identity))
    except ProviderUnavailable as exc:
        raise HTTPException(503, "Generation provider unavailable or invalid evidence") from exc
