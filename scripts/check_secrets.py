"""Check public files and optionally reachable Git history; never print matched values."""
import argparse
import re
import subprocess
from pathlib import Path

PATTERNS = {
    "credential": re.compile(
        r"gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|"
        r"sk-(?:or-v1-)?[A-Za-z0-9_-]{32,}|"
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|"
        r"xox[baprs]-[A-Za-z0-9-]{20,}|"
        r"AKIA[A-Z0-9]{16}|\b[0-9]{8,12}:[A-Za-z0-9_-]{30,}"),
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "host": re.compile(r"\bDESKTOP-[A-Z0-9]{4,}\b"),
    "home": re.compile(
        r"(?i)\b[A-Z]:[\\/]Users[\\/](?!Public[\\/])[A-Za-z0-9_. -]+[\\/]|"
        r"/home/(?!atlas/)[A-Za-z0-9_.-]+/"),
}
ALLOWED_DOMAINS = {"example.com", "example.org", "example.net", "users.noreply.github.com"}


def git(*args):
    return subprocess.check_output(["git", *args])


def findings(text):
    result = []
    for category, pattern in PATTERNS.items():
        matches = pattern.findall(text)
        if category == "email":
            matches = [m for m in matches if m.rsplit("@", 1)[1].lower() not in ALLOWED_DOMAINS]
        if matches:
            result.append(category)
    return result


def sensitive_filename(name):
    path = Path(name)
    return ((path.name.startswith(".env") and path.name != ".env.example") or
            path.name == ".local-token" or path.suffix in {".pem", ".key", ".p12", ".pfx"})


def scan(history=False):
    failures = set()
    paths = git("ls-files", "-z").decode().split("\0")
    for name in filter(None, paths):
        path = Path(name)
        if sensitive_filename(name):
            failures.add("sensitive-filename:" + name)
        if path.is_file():
            for category in findings(path.read_text(encoding="utf-8", errors="replace")):
                failures.add(category + ":" + name)
    if history:
        # Diff names cover every historical path, including renames, root commits
        # and merge-only changes. rev-list --objects can show only one name for a
        # blob reused at several paths, so its names are insufficient for this check.
        historical_paths = git("log", "--all", "--root", "-m", "--format=",
                               "--name-only", "-z", "--no-renames").decode().split("\0")
        for name in filter(None, historical_paths):
            if sensitive_filename(name):
                failures.add("sensitive-filename:historical-path:" + name)
        objects = git("rev-list", "--objects", "--all").decode().splitlines()
        for line in objects:
            oid = line.split(" ", 1)[0]
            if git("cat-file", "-t", oid).strip() == b"blob":
                for category in findings(git("cat-file", "blob", oid).decode("utf-8", errors="replace")):
                    failures.add(category + ":historical-blob:" + oid)
        for oid in git("rev-list", "--all").decode().splitlines():
            metadata = git("show", "-s", "--format=%ae%n%ce%n%B", oid).decode()
            for category in findings(metadata):
                failures.add(category + ":commit:" + oid)
    return sorted(failures)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", action="store_true")
    args = parser.parse_args()
    failures = scan(args.history)
    if failures:
        raise SystemExit("Public-data scan failed (values redacted):\n" + "\n".join(failures))
    print("Public-data pattern scan passed" + (" including reachable history." if args.history else "."))
