"""Pure document ingestion helpers."""
from pathlib import Path


def safe_directory(root: Path, relative: str) -> Path:
    base = root.resolve()
    candidate = (base / relative).resolve()
    if not candidate.is_relative_to(base) or not candidate.is_dir():
        raise ValueError("Directory must exist inside DOCS_ROOT")
    return candidate


def markdown_files(root: Path, relative: str) -> list[Path]:
    base = root.resolve()
    directory = safe_directory(base, relative)
    return [p for p in sorted(directory.rglob("*.md")) if p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(base)]


def chunks(text: str, size: int = 900, overlap: int = 120) -> list[str]:
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("Invalid chunk parameters")
    text = text.strip()
    if not text:
        return []
    output = []
    start = 0
    while start < len(text):
        part = text[start:start + size]
        if part.strip():
            output.append(part)
        if start + size >= len(text):
            break
        start += size - overlap
    return output
