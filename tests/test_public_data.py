import importlib.util
import subprocess
from pathlib import Path

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
