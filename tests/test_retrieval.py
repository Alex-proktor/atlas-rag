from atlas_rag.retrieval import bm25, retrieve, tokens


def test_unicode_tokens():
    assert tokens("Срок API-42") == ["срок", "api", "42"]


def test_hybrid_acl_before_bm25_and_dense(index):
    (index.root / "a" / "one.md").write_text("secret payroll password", encoding="utf-8")
    (index.root / "b" / "one.md").write_text("public backup", encoding="utf-8")
    index.sync(tenant="a", acl=["finance"])
    index.sync(tenant="b")
    assert retrieve(index, "secret payroll", 5, "a", []) == []
    assert len(retrieve(index, "secret payroll", 5, "a", ["finance"])) == 1
    results = retrieve(index, "secret payroll", 5, "b", [])
    assert all("secret" not in h["text"] for h in results)


def test_bm25_exact_keyword(index):
    (index.root / "default" / "a.md").write_text("backup backup database", encoding="utf-8")
    (index.root / "default" / "b.md").write_text("employee vacation manager", encoding="utf-8")
    index.sync()
    assert bm25("backup", index.records())[0][0].payload["path"] == "a.md"
    assert bm25("unseen", index.records()) == []
