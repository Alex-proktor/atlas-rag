"""Public synthetic corpus HTTP smoke; standard-library only."""
import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

base = os.getenv("ATLAS_URL", "http://127.0.0.1:8000")
token = (Path(__file__).resolve().parents[1] / ".local-token").read_text().strip()


def call(path, payload):
    request = Request(base + path, data=json.dumps(payload).encode(),
                      headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
    with urlopen(request, timeout=300) as response:
        return json.load(response)


indexed = call("/index", {})
result = call("/search", {"query": "How long are database backups retained?", "limit": 3})
assert any(s["path"] == "backup.md" and "30 days" in s["text"] for s in result["results"])
try:
    urlopen(Request(base + "/search", data=b'{"query":"backup"}',
                    headers={"Content-Type": "application/json"}), timeout=10)
except HTTPError as exc:
    assert exc.code == 401
else:
    raise AssertionError("Unauthenticated search was allowed")
print(json.dumps({"index": indexed, "search": result, "unauthenticated_status": 401}, indent=2, ensure_ascii=False))
