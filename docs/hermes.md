# Hermes integration

The standalone plugin in integrations/hermes registers the read-only atlas_search tool. It uses POST /search and returns untrusted_evidence with paths, chunks and original passages. It never invokes /index or changes the agent's model/provider. Its token determines permissions; use a reader credential in a corporate installation.

Install the folder as atlas-rag under your Hermes profile plugins directory using the supported plugin workflow. Set ATLAS_URL (loopback HTTP or approved HTTPS) and ATLAS_TOKEN_FILE (private credential file) in the Hermes environment. Validate the plugin against the installed Hermes version and start a new agent session to load it. Do not restart unrelated runtimes.

The caller must treat evidence as data, cite source paths/chunks and refuse unsupported claims. A prompt inside a retrieved passage must never become an agent command. This plugin does not give Atlas authority to execute tools.

Acceptance must distinguish: import/registration tests, HTTP integration and actual installed Hermes registry invocation. See docs/acceptance.md for the level actually verified.
