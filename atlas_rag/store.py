"""Immutable Qdrant snapshots; atomic alias publication, incremental embeddings."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from uuid import NAMESPACE_URL, uuid4, uuid5

from filelock import FileLock
from qdrant_client import models

from atlas_rag.core import chunks, markdown_files, safe_directory


class SnapshotStore:
    def __init__(self, client, encoder, root: Path, collection: str, model: str, state: Path):
        self.client, self.encoder, self.root = client, encoder, root
        self.alias = collection + "_live"
        self.fingerprint = hashlib.sha256((model + ":900:120:v1").encode()).hexdigest()
        state.mkdir(parents=True, exist_ok=True)
        self.lock = FileLock(str(state / (collection + ".lock")), timeout=30)

    def active(self):
        return next((a.collection_name for a in self.client.get_aliases().aliases
                     if a.alias_name == self.alias), None)

    def records(self, collection=None):
        collection = collection or self.active()
        if not collection:
            return []
        points, offset = [], None
        while True:
            batch, offset = self.client.scroll(collection, limit=128, offset=offset,
                                               with_payload=True, with_vectors=True)
            points.extend(batch)
            if offset is None:
                return points

    def sync(self, relative=".", tenant="default", acl=None, force=False):
        """All writers must share state/lock. Old snapshots retained for in-flight readers."""
        with self.lock:
            if not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", tenant):
                raise ValueError("Invalid tenant")
            base = (self.root / tenant).resolve()
            if not base.is_relative_to(self.root.resolve()):
                raise ValueError("Invalid tenant root")
            directory = safe_directory(base, relative)
            prefix = directory.relative_to(base).as_posix()
            prefix = "" if prefix == "." else prefix + "/"
            old_collection = self.active()
            old = self.records(old_collection)
            if any(p.payload.get("fingerprint") != self.fingerprint for p in old):
                raise ValueError("Embedding/chunker configuration changed; use a new COLLECTION")
            old_by_id = {str(p.id): p for p in old}
            def in_scope(payload):
                return payload["tenant"] == tenant and payload["path"].startswith(prefix)
            retained = [models.PointStruct(id=p.id, vector=p.vector, payload=p.payload)
                        for p in old if not in_scope(p.payload)]
            additions, pending, texts = [], [], []
            total_bytes = 0
            for path in markdown_files(base, relative):
                if path.stat().st_size > 1_000_000:
                    raise ValueError("Document exceeds 1 MB")
                text = path.read_text(encoding="utf-8")
                total_bytes += len(text.encode("utf-8"))
                if total_bytes > 20_000_000:
                    raise ValueError("Sync exceeds 20 MB")
                name = path.resolve().relative_to(base).as_posix()
                digest = hashlib.sha256(text.encode()).hexdigest()
                for i, passage in enumerate(chunks(text)):
                    identity = str(uuid5(NAMESPACE_URL, json.dumps([tenant, name, i])))
                    payload = dict(tenant=tenant, path=name, chunk=i, text=passage,
                                   content_hash=digest, acl=sorted(acl or []),
                                   fingerprint=self.fingerprint)
                    previous = old_by_id.get(identity)
                    if not force and previous and previous.payload == payload:
                        additions.append(models.PointStruct(id=identity, vector=previous.vector,
                                                            payload=payload))
                    else:
                        pending.append((identity, payload))
                        texts.append(passage)
            if len(retained) + len(additions) + len(pending) > 25000:
                raise ValueError("Snapshot exceeds 25000 chunks")
            if texts:
                vectors = self.encoder.encode(texts).tolist()
                if len(vectors) != len(pending):
                    raise ValueError("Embedding count mismatch")
                additions.extend(models.PointStruct(id=i, vector=v, payload=p)
                                 for (i, p), v in zip(pending, vectors, strict=True))
            points = retained + additions
            if not force and {str(p.id): p.payload for p in points} == {
                    str(p.id): p.payload for p in old}:
                return dict(indexed=0, total=len(points), changed=False)
            dimension = (len(points[0].vector) if points
                         else self.encoder.get_sentence_embedding_dimension())
            staging = self.alias + "_" + uuid4().hex
            self.client.create_collection(staging, vectors_config=models.VectorParams(
                size=dimension, distance=models.Distance.COSINE))
            published = False
            try:
                for start in range(0, len(points), 128):
                    self.client.upsert(staging, points[start:start + 128], wait=True)
                if self.client.count(staging, exact=True).count != len(points):
                    raise RuntimeError("Snapshot validation failed")
                operations = []
                if old_collection:
                    operations.append(models.DeleteAliasOperation(
                        delete_alias=models.DeleteAlias(alias_name=self.alias)))
                operations.append(models.CreateAliasOperation(create_alias=models.CreateAlias(
                    collection_name=staging, alias_name=self.alias)))
                self.client.update_collection_aliases(operations)
                published = True
            finally:
                # Do not delete an ambiguous publication: check actual alias first.
                if not published and self.active() != staging:
                    self.client.delete_collection(staging)
            return dict(indexed=len(pending), total=len(points), changed=True,
                        snapshot=staging)

    @staticmethod
    def access_filter(tenant, groups):
        return models.Filter(must=[
            models.FieldCondition(key="tenant", match=models.MatchValue(value=tenant)),
            models.Filter(should=[
                models.IsEmptyCondition(is_empty=models.PayloadField(key="acl")),
                models.FieldCondition(key="acl", match=models.MatchAny(any=groups)),
            ]),
        ])

    def search(self, query, limit=5, tenant="default", groups=None):
        collection = self.active()
        if not collection:
            return []
        hits = self.client.query_points(
            collection, query=self.encoder.encode(query).tolist(),
            query_filter=self.access_filter(tenant, groups or []),
            limit=limit, with_payload=True).points
        return [dict(id=str(h.id), score=h.score, **h.payload) for h in hits]
