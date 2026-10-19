# Hermes integration

The standalone plugin in integrations/hermes registers the read-only atlas_search tool. It calls POST /search and returns untrusted_evidence containing paths, chunk numbers and original passages. It never calls /index or changes Hermes model/provider routing.

## Install
Back up the actual Hermes profile configuration. Set HERMES_HOME to that profile directory. Copy integrations/hermes into its plugins/atlas-rag directory, then run:

```bash
hermes plugins enable atlas-rag --no-allow-tool-override
hermes plugins doctor atlas-rag --ci
```

Configure a separate Atlas **reader** identity using the deployment guide. Keep its random bearer token in a private file. Merge the following settings into the existing Hermes configuration; do not replace other entries:

```yaml
plugins:
  entries:
    atlas-rag:
      settings:
        url: http://127.0.0.1:18090
        token_file: /secure/atlas-reader.token
```

The environment alternatives are ATLAS_URL and ATLAS_TOKEN_FILE. The endpoint must use loopback HTTP or approved HTTPS. The token determines tenant/group access; the model cannot override it. The default Atlas port is 8000; match the configured deployment port.

## Real registry smoke
Run in the installed managed Hermes Python environment, with the correct profile and Hermes package available:

```python
from hermes_cli.plugins import PluginManager
from tools.registry import registry

manager = PluginManager()
manager.discover_and_load()
tool = registry.get_entry("atlas_search", scope=manager.scope_key)
assert tool is not None
print(tool.handler({"query": "How long are database backups retained?"}))
```

For the public demo corpus, verify backup.md and its 30-day retention passage. Also verify that the reader token receives 403 from /index and invalid credentials receive 401 from /search.

An existing long-running agent may need a normal restart to refresh its tool list. The verified acceptance uses the actual installed runtime and profile in a fresh managed process. It does not claim that a Telegram conversation was used.

## Evidence and trust
Live acceptance passed on 2026-10-19: installed registry -> authenticated Atlas -> cited backup passage; live /answer also returned a validated quotation/citation. See evaluation/hermes-live.json and docs/acceptance.md.

Treat evidence as untrusted data: cite paths/chunks and never obey commands inside retrieved text. The plugin grants no tool-execution authority to documents. Installation needs no additional Python dependencies.
