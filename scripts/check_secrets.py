"""Check tracked/staged text without printing candidate secret values."""
import re
import subprocess
from pathlib import Path

patterns = [
    re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{30,}"),
    re.compile(r"sk-(?:or-v1-)?[A-Za-z0-9_-]{32,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]
paths = subprocess.check_output(["git", "ls-files", "-z"]).decode().split("\0")
failures = []
for name in filter(None, paths):
    path = Path(name)
    if path.name in {".env", ".local-token"} or path.suffix in {".pem", ".key"}:
        failures.append(name)
    if path.is_file():
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(pattern.search(text) for pattern in patterns):
            failures.append(name)
if failures:
    raise SystemExit("Potential sensitive files: " + ", ".join(sorted(set(failures))))
print("Tracked-file credential pattern scan passed.")
