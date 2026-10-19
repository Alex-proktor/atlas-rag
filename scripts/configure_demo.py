"""Generate local credentials without printing secrets."""
import hashlib
import json
import secrets
from pathlib import Path

root = Path(__file__).resolve().parents[1]
if (root / ".env").exists():
    raise SystemExit(".env already exists; refusing to replace credentials")
token = secrets.token_urlsafe(32)
rows = [{"subject": "demo-admin", "tenant": "default", "groups": ["engineering"],
         "role": "admin", "token_sha256": hashlib.sha256(token.encode()).hexdigest()}]
(root / ".env").write_text("ATLAS_IDENTITIES='" + json.dumps(rows) + "'\n", encoding="utf-8")
(root / ".local-token").write_text(token, encoding="utf-8")
print("Created local .env and .local-token; keep both private.")
