# Reproduce Legal-AI locally

1. Read the [README](README.md) and pick the smallest corpus that covers the request. Start with the Tantivy quick start for an Indian legislation demo or the synthetic JSONL example in [architecture](docs/architecture.md) for an offline index smoke test.
2. Use a fresh virtual environment. Reuse verified shards and indexes already present. Run the documented status command and verify a keyword result with its source locator. For citations, verify an exact lookup as well.
3. Use [Qdrant](docs/qdrant.md) when semantic search is requested and a compatible snapshot covers the topic. Start with the Acts pilot. Check free disk space, select an unused local port, and keep the new service separate from any existing database. Record the point count and query result. Choose large downloads only when the requested scope calls for them.
4. Consult [source and API links](docs/tools-and-sources.md) for gaps and [the validation checklist](docs/workflow.md) for research. Record source versions, coverage, citation pinpoints, and any unavailable checks. Keep generated files and matter data under ignored local directories.
5. Report the environment, installed route, files indexed, verification commands, and any steps still pending. Separate a tested quick start from optional integrations and from legal conclusions.
