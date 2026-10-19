"""Real Qdrant contract tests. Set QDRANT_TEST_URL to enable."""
import os
from uuid import uuid4

import numpy as np
import pytest
from qdrant_client import QdrantClient

from atlas_rag.store import SnapshotStore


class Encoder:
    calls = 0

    def encode(self, texts):
        self.calls += 1
        if isinstance(texts, str):
            return np.array([1., 0., 0.])
        return np.array([[1., 0., 0.] for _ in texts])

    def get_sentence_embedding_dimension(self):
        return 3


@pytest.fixture
def index(tmp_path):
    url = os.getenv("QDRANT_TEST_URL")
    if not url:
        pytest.skip("QDRANT_TEST_URL required for real Qdrant integration")
    client = QdrantClient(url=url)
    name = "test_" + uuid4().hex
    root = tmp_path / "docs"
    root.mkdir()
    (root / "default").mkdir()
    (root / "a").mkdir()
    (root / "b").mkdir()
    instance = SnapshotStore(client, Encoder(), root, name, "test", tmp_path / "state")
    yield instance
    aliases = [a for a in client.get_aliases().aliases if a.alias_name == instance.alias]
    if aliases:
        from qdrant_client import models
        client.update_collection_aliases([models.DeleteAliasOperation(
            delete_alias=models.DeleteAlias(alias_name=instance.alias))])
    for c in client.get_collections().collections:
        if c.name.startswith(name):
            client.delete_collection(c.name)
