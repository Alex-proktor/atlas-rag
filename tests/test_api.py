import hashlib
import json

import pytest
from fastapi.testclient import TestClient

from atlas_rag.main import app
from atlas_rag.security import _buckets


@pytest.fixture
def api(monkeypatch):
    _buckets.clear()
    identities = [
        {"token_sha256": hashlib.sha256((c * 40).encode()).hexdigest(),
         "subject": c, "tenant": "default", "groups": ["engineering"], "role": role}
        for c, role in [("r", "reader"), ("w", "writer")]]
    monkeypatch.setenv("ATLAS_IDENTITIES", json.dumps(identities))
    return TestClient(app)


def test_authentication_and_roles(api):
    assert api.post("/search", json={"query": "hello"}).status_code == 401
    assert api.post("/search", headers={"Authorization": "Bearer " + "x" * 40},
                    json={"query": "hello"}).status_code == 401
    assert api.post("/index", headers={"Authorization": "Bearer " + "r" * 40},
                    json={}).status_code == 403
    assert api.post("/index", headers={"Authorization": "Bearer " + "w" * 40},
                    json={"acl": ["executives"]}).status_code == 403


def test_payload_and_rate_limits(api):
    headers = {"Authorization": "Bearer " + "r" * 40}
    assert api.post("/search", content=b"x" * 20000, headers=headers).status_code == 413
    assert api.post("/search", json={"query": "x" * 2001}, headers=headers).status_code == 422
    for _ in range(61):
        response = api.post("/index", json={}, headers=headers)
    assert response.status_code == 429


def test_no_default_credentials(api, monkeypatch):
    monkeypatch.delenv("ATLAS_IDENTITIES")
    assert api.post("/search", json={"query": "hello"}).status_code == 503


def test_public_health_does_not_load_models(api):
    assert api.get("/health").json() == {"status": "ok"}


def test_metrics():
    from atlas_rag.evaluate import metrics
    assert metrics(["a", "a", "b"], ["b"], 2) == {
        "recall": 1., "mrr": .5, "ndcg": pytest.approx(.6309297535714575)}


def test_writer_acl_boundary_through_api(api, index, monkeypatch):
    import atlas_rag.main as main

    monkeypatch.setattr(main, "store", lambda: index)
    doc = index.root / "default" / "restricted.md"
    doc.write_text("restricted evidence", encoding="utf-8")
    index.sync(acl=["executives"])
    snapshot = index.active()
    headers = {"Authorization": "Bearer " + "w" * 40}
    for acl in ([], ["engineering"]):
        response = api.post("/index", headers=headers, json={"acl": acl})
        assert response.status_code == 403
        assert index.active() == snapshot
    assert api.post("/search", headers=headers,
                    json={"query": "restricted"}).json()["results"] == []
    # An administrator can establish a writer-owned scope explicitly.
    index.sync(acl=["engineering"])
    doc.write_text("authorized update", encoding="utf-8")
    assert api.post("/index", headers=headers,
                    json={"acl": ["engineering"]}).status_code == 200
    results = api.post("/search", headers=headers,
                       json={"query": "authorized"}).json()["results"]
    assert results[0]["text"] == "authorized update"
