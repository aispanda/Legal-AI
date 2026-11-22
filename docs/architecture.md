# Local RAG architecture

```text
Public Parquet or normalized JSONL → Tantivy → keyword and exact citation
Publisher Qdrant snapshots + local query models → Qdrant → semantic + BM25
Both routes → source locators → independent review → evidence packet
```

The Vaquill path downloads checksum-verified Parquet shards and resumes indexing at file boundaries. The portable path takes normalized JSONL passages and builds a fresh index in a separate directory. Both Tantivy inputs use the same keyword ranking, citation lookup, filters, and result grouping. Search results include excerpts and locators for review. The [research workflow](workflow.md) explains how to turn them into verified evidence for a drafting model.

## Build from another corpus

Download a permitted export from its publisher, court, or API. Keep the original files and record the publisher, final URL, retrieval date, release or effective date, checksum, and applicable license. See [Tools and sources](tools-and-sources.md) for source links.

Map the export to one UTF-8 JSON object per passage. For PDFs, scanned files, or HTML, extract the text with an appropriate tool first and retain page, paragraph, or section boundaries. Prefer coherent sections over fixed-size cuts. Record OCR separately and verify quoted wording against the original page.

| JSONL field | Contract |
| --- | --- |
| `document_id`, `title`, `text`, `locator` | Required strings. Reuse the same document ID for its passages. Assign different IDs to different versions. A locator can be a page, paragraph, section, or local text anchor. |
| `source_url`, `source_version`, `chunk_id` | Optional strings for provenance. Use a stable passage ID when one exists. |
| `kind`, `court`, `region`, `decision_date` | Optional filters and metadata. Kind is `judgment`, `legislation`, `regulation`, `tribunal`, or `document` by default. Use ISO dates for year filtering. |
| `citation`, `case_number`, `section_number`, `section_title` | Optional legal lookup fields. For an Act section, search exactly for the title followed by `section` and its number. |

After the README's Python setup, this synthetic example exercises the portable path without downloading a corpus.

```sh
mkdir -p research
cat > research/passages.jsonl <<'JSONL'
{"document_id":"demo-v1","title":"Example policy","text":"Keep a record of access requests.","locator":"Section 2","section_number":"2","source_version":"v1"}
JSONL
.venv/bin/python build_corpus.py research/passages.jsonl --index research/index-v1
.venv/bin/python search_index.py --index research/index-v1 search "access requests"
.venv/bin/python search_index.py --index research/index-v1 search "Example policy section 2" --exact
```

Use a new index directory when the input changes. The importer records the JSONL SHA-256 and record count in `corpus-manifest.json`. Each hit records the input filename and its one-based JSONL line. Keep the input with its index so another machine can rebuild the same corpus version. The Vaquill path preserves zero-based Parquet row offsets.

## Design decisions

An early SQLite FTS5 and Ollama prototype scanned vectors across a small document set. Tantivy took over full-corpus keyword and citation search. A custom 512-dimensional Qdrant index was considered. The Acts pilot reused Vaquill's 1,024-dimensional document vectors and generated only query vectors locally. [Publisher restore guide](https://github.com/Vaquill-AI/open-india-law/blob/main/data/QDRANT_RESTORE.md)

For semantic experiments, record the embedding model and revision, chunking rules, dimensions, and distance metric. Preserve passage IDs and source locators across indexes. Compare BM25, reranking, and hybrid search on the same questions. Measure citation accuracy, supporting-passage recall, latency, and disk use.

The [Qdrant runbook](qdrant.md) covers the Acts restore, the expected count, and a hybrid query. Both search CLIs emit JSON. Full judgment restore, comparative benchmarking, and a shared UI or MCP service remain separate work.
