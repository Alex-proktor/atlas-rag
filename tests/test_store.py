import pytest

from atlas_rag.store import SnapshotStore


def test_incremental_update_delete_and_restart(index, tmp_path):
    doc = index.root / "default" / "one.md"
    doc.write_text("a" * 2000, encoding="utf-8")
    first = index.sync()
    assert first["total"] == 3
    calls = index.encoder.calls
    assert index.sync()["changed"] is False
    assert index.encoder.calls == calls
    doc.write_text("replacement", encoding="utf-8")
    assert index.sync()["total"] == 1
    assert index.search("query")[0]["text"] == "replacement"
    restarted = SnapshotStore(index.client, index.encoder, index.root,
                              index.alias.removesuffix("_live"), "test", tmp_path / "state")
    assert restarted.active() == index.active()
    doc.unlink()
    assert index.sync()["total"] == 0
    assert index.search("query") == []


def test_failed_embedding_preserves_published_snapshot(index, monkeypatch):
    doc = index.root / "default" / "one.md"
    doc.write_text("published", encoding="utf-8")
    index.sync()
    snapshot = index.active()
    doc.write_text("changed", encoding="utf-8")
    def fail(_):
        raise RuntimeError("injected failure")
    monkeypatch.setattr(index.encoder, "encode", fail)
    with pytest.raises(RuntimeError):
        index.sync()
    assert index.active() == snapshot
    assert index.records()[0].payload["text"] == "published"


def test_failed_upload_preserves_snapshot(index, monkeypatch):
    doc = index.root / "default" / "one.md"
    doc.write_text("published", encoding="utf-8")
    index.sync()
    snapshot = index.active()
    doc.write_text("changed", encoding="utf-8")
    def fail(*args, **kwargs):
        raise RuntimeError("injected upload failure")
    monkeypatch.setattr(index.client, "upsert", fail)
    with pytest.raises(RuntimeError):
        index.sync()
    assert index.active() == snapshot
    assert index.records()[0].payload["text"] == "published"


def test_tenant_acl_and_scoped_sync(index):
    (index.root / "a" / "one.md").write_text("private", encoding="utf-8")
    (index.root / "b" / "one.md").write_text("public", encoding="utf-8")
    index.sync(tenant="a", acl=["engineering"])
    index.sync(tenant="b")
    assert index.search("query", tenant="a") == []
    assert len(index.search("query", tenant="a", groups=["engineering"])) == 1
    assert len(index.search("query", tenant="b")) == 1
    index.sync(tenant="a", acl=["new"])
    assert index.search("query", tenant="a", groups=["engineering"]) == []
    assert len(index.search("query", tenant="b")) == 1


def test_model_mismatch_fails_closed(index):
    (index.root / "default" / "one.md").write_text("text", encoding="utf-8")
    index.sync()
    index.fingerprint = "different-model"
    with pytest.raises(ValueError, match="configuration changed"):
        index.sync()


def test_writer_cannot_declassify_or_overwrite_other_acl(index):
    doc = index.root / "default" / "restricted.md"
    doc.write_text("restricted evidence", encoding="utf-8")
    index.sync(acl=["executives"])
    snapshot = index.active()
    doc.write_text("replacement", encoding="utf-8")
    for acl in ([], ["engineering"], ["engineering", "executives"]):
        with pytest.raises(PermissionError):
            index.sync(acl=acl, writer_groups=["engineering"])
        assert index.active() == snapshot
    assert index.records()[0].payload["text"] == "restricted evidence"
    with pytest.raises(PermissionError):
        index.sync(acl=["engineering"], writer_groups=["engineering", "executives"])


def test_writer_same_acl_update_delete_and_admin_relabel(index):
    doc = index.root / "default" / "one.md"
    doc.write_text("original", encoding="utf-8")
    index.sync(acl=["engineering"], writer_groups=["engineering"])
    doc.write_text("updated", encoding="utf-8")
    index.sync(acl=["engineering"], writer_groups=["engineering"])
    assert index.search("q", groups=["engineering"])[0]["text"] == "updated"
    index.sync(acl=[])
    assert index.search("q")[0]["text"] == "updated"
    snapshot = index.active()
    doc.unlink()
    with pytest.raises(PermissionError):
        index.sync(acl=["engineering"], writer_groups=["engineering"])
    assert index.active() == snapshot
    index.sync(acl=[])
    assert index.search("q") == []
