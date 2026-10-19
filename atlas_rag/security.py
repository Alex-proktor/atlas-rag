"""Fail-closed bearer identities, bounded requests and metadata-only audit."""
import hashlib
import hmac
import json
import logging
import os
import time
from dataclasses import dataclass
from threading import Lock

from fastapi import Header, HTTPException, Request


@dataclass(frozen=True)
class Identity:
    subject: str
    tenant: str
    groups: tuple[str, ...]
    role: str


def identities():
    try:
        rows = json.loads(os.getenv("ATLAS_IDENTITIES", "[]"))
        if not isinstance(rows, list) or not rows:
            raise ValueError()
        for row in rows:
            if (len(row["token_sha256"]) != 64 or not row["tenant"] or
                    row["role"] not in {"reader", "writer", "admin"}):
                raise ValueError()
        return rows
    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(503, "Identity configuration unavailable") from exc


_buckets = {}
_lock = Lock()


def authenticate(authorization: str = Header(default="")):
    rows = identities()
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or len(token) < 32 or len(token) > 256:
        raise HTTPException(401, "Valid bearer token required",
                            headers={"WWW-Authenticate": "Bearer"})
    digest = hashlib.sha256(token.encode()).hexdigest()
    match = None
    for row in rows:
        if hmac.compare_digest(digest, row["token_sha256"]):
            match = row
    if match is None:
        raise HTTPException(401, "Valid bearer token required")
    minute = int(time.monotonic() // 60)
    with _lock:
        if len(_buckets) > 1000:
            _buckets.clear()
        bucket = _buckets.get(digest, (minute, 0))
        count = bucket[1] + 1 if bucket[0] == minute else 1
        _buckets[digest] = (minute, count)
    if count > 60:
        raise HTTPException(429, "Request rate exceeded", headers={"Retry-After": "60"})
    return Identity(match["subject"], match["tenant"], tuple(match.get("groups", [])), match["role"])


def writer(identity):
    if identity.role not in {"writer", "admin"}:
        raise HTTPException(403, "Writer role required")


class BodyLimit:
    """ASGI streaming cap; does not trust Content-Length."""
    def __init__(self, app, maximum=16384):
        self.app, self.maximum = app, maximum

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        size, messages = 0, []
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > self.maximum:
                await send({"type": "http.response.start", "status": 413,
                            "headers": [(b"content-type", b"application/json")]})
                await send({"type": "http.response.body", "body": b'{"detail":"Request too large"}'})
                return
            messages.append(message)
            if not message.get("more_body", False):
                break
        async def replay():
            return messages.pop(0) if messages else await receive()
        await self.app(scope, replay, send)


async def audit(request: Request, call_next):
    started = time.monotonic()
    response = await call_next(request)
    route = request.scope.get("route")
    logging.getLogger("atlas.audit").info(
        "method=%s route=%s status=%s duration_ms=%d",
        request.method, getattr(route, "path", "unmatched"),
        response.status_code, int((time.monotonic() - started) * 1000))
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    return response
