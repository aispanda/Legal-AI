# Local RAG architecture

```text
Publisher files or API export → local originals → passages with source locators
  → Tantivy index → keyword and citation search → independent source review → evidence packet
```

The Vaquill path downloads checksum-verified Parquet shards and resumes indexing at file boundaries. The portable path takes normalized JSONL passages and builds a fresh index in a separate directory. Both paths use the same keyword ranking, citation lookup, filters, and result grouping. Search results include excerpts and locators for review. The [research workflow](workflow.md) explains how to turn them into verified evidence for a drafting model.

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

## Retrieval choices and storage

| Approach | Tradeoff and result |
| --- | --- |
| SQLite FTS5 with local Ollama embeddings | Suited the early small-document prototype with a browser UI and versioned citations. Scanning embedded passages per query made it a poor fit for tens of millions of passages. |
| Tantivy and PyArrow | The implemented default. It provides exact citation and BM25 search across the selected shards with court and date filters. The full pinned Parquet release takes about 50 GiB to download. A full Tantivy build used about 80 GiB in the pilot. |
| Build custom vectors in Qdrant | The explored design used 512-dimensional local Voyage 4 Nano vectors, cosine similarity, and int8 quantization. It would require embedding the documents and benchmarking relevance, latency, and storage against the lexical baseline. |
| Restore Vaquill's Qdrant snapshots | Reuses publisher embeddings. Match the Voyage 4 query embedding space, 1,024 dimensions, and cosine distance. The published approach combines sparse BM25 and dense retrieval with reciprocal rank fusion. The local pilot restored the Acts collection and verified a hybrid query. Vaquill estimates about 434 GB for all three restored collections, plus working space for the restore. [Publisher restore guide](https://github.com/Vaquill-AI/open-india-law/blob/main/data/QDRANT_RESTORE.md#disk-requirements) |

For semantic experiments, record the embedding model and revision, chunking rules, vector dimensions, and distance metric. Keep passage IDs and source locators across indexes. On the same held-out questions, compare BM25 alone, reranking its candidates, and hybrid retrieval. Check exact citation lookup and supporting-passage recall, then measure latency and disk use. The published snapshot configuration differs from the proposed 512-dimensional custom index, so use its documented query configuration for a restore.

The implemented interfaces are CLIs that emit JSON. The full vector restore, comparative benchmark, and connection to the earlier browser UI and MCP service are separate integration work.
