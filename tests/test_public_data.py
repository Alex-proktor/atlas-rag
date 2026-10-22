import importlib.util
import subprocess
from pathlib import Path

import pytest

SCANNER = Path(__file__).resolve().parents[1] / "scripts" / "check_secrets.py"
spec = importlib.util.spec_from_file_location("public_data_guard", SCANNER)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def test_guard_detects_without_exposing_values():
    token = "ghp_" + "a" * 40
    assert guard.findings(token) == ["credential"]
    assert guard.findings("person" + "@" + "mail.invalid") == ["email"]
    assert guard.findings("DESKTOP-" + "ABC123") == ["host"]
    assert guard.findings("example" + "@" + "example.com") == []
    assert guard.findings("4922872+Alex-proktor" + "@" + "users.noreply.github.com") == []
    assert guard.findings("noreply" + "@" + "github.com") == []
    assert guard.findings("person" + "@" + "github.com") == ["email"]


@pytest.mark.parametrize("home_path", [
    "C:" + "/Users/" + "PrivateFixture" + "/notes.md",
    "C:" + "\\Users\\" + "PrivateFixture" + "\\notes.md",
    "/home/" + "private-fixture" + "/notes.md",
])
def test_guard_detects_private_home_paths(home_path):
    assert guard.findings(home_path) == ["home"]


def test_guard_allows_public_and_documented_container_paths():
    assert guard.findings("C:" + "/Users/Public/notes.md") == []
    assert guard.findings("/home/atlas/.cache") == []


def test_guard_checks_history_after_worktree_is_cleaned(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    def git(*args):
        subprocess.run(["git", *args], check=True, capture_output=True)
    git("init")
    git("config", "user.name", "Test")
    git("config", "user.email", "test" + "@" + "example.com")
    token = "ghp_" + "b" * 40
    Path("sample.txt").write_text(token)
    git("add", ".")
    git("commit", "-m", "synthetic fixture")
    Path("sample.txt").write_text("safe sample")
    git("add", ".")
    git("commit", "-m", "remove fixture")
    assert guard.scan() == []
    findings = guard.scan(history=True)
    assert any("credential:historical-blob:" in item for item in findings)
    assert all(token not in item for item in findings)


@pytest.mark.parametrize("secret_name", [".local-token", "tenant/.env"])
def test_guard_checks_removed_sensitive_filenames_with_reused_blob(
        tmp_path, monkeypatch, secret_name):
    monkeypatch.chdir(tmp_path)

    def git(*args):
        subprocess.run(["git", *args], check=True, capture_output=True)

    git("init")
    git("config", "user.name", "Test")
    git("config", "user.email", "test" + "@" + "example.com")
    safe = Path("safe.txt")
    # No recognizable credential prefix: the filename must trigger the guard.
    safe.write_text("a" * 43)
    git("add", ".")
    git("commit", "-m", "synthetic public file")
    secret = Path(secret_name)
    secret.parent.mkdir(parents=True, exist_ok=True)
    safe.rename(secret)
    git("add", "-A")
    git("commit", "-m", "reuse blob at synthetic sensitive path")
    secret.unlink()
    safe.write_text("safe sample")
    git("add", "-A")
    git("commit", "-m", "remove synthetic sensitive filename")

    assert guard.scan() == []
    assert "sensitive-filename:historical-path:" + secret_name in guard.scan(history=True)
