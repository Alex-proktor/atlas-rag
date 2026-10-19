
import pytest

from atlas_rag.core import chunks, markdown_files, safe_directory


def test_chunking():
    assert chunks("abcdefghij", size=6, overlap=2) == ["abcdef", "efghij"]


def test_empty():
    assert chunks("  ") == []


def test_invalid():
    with pytest.raises(ValueError):
        chunks("abc", size=3, overlap=3)


def test_traversal(tmp_path):
    with pytest.raises(ValueError):
        safe_directory(tmp_path, "../")


def test_symlink_exclusion(tmp_path):
    (tmp_path / "valid.md").write_text("public")
    outside = tmp_path.parent / "outside-atlas-test.md"
    outside.write_text("private")
    try:
        (tmp_path / "link.md").symlink_to(outside)
    except OSError:
        pytest.skip("Creating symlinks requires elevated Windows privileges")
    try:
        assert markdown_files(tmp_path, ".") == [tmp_path / "valid.md"]
    finally:
        outside.unlink()
