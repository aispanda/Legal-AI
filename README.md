# Legal-AI

Legal-AI helps you build and verify a local legal search index. Use the pinned Open India Law data or bring another corpus as JSONL. The [research checklist](docs/workflow.md) turns search results into an evidence packet with citations and pinpoints.

## Choose a search route

| Route | Advantages | Tradeoffs |
| --- | --- | --- |
| **Tantivy** | Exact citations and keyword search. Runs locally without a model or API account. Start with a 25 MiB download, choose individual shards, or use your own corpus. | Wording matters for keyword queries. The full India download is about 50 GiB and a full index used about 80 GiB in the pilot. |
| **Qdrant** | Restores Vaquill's prebuilt embeddings for search by meaning plus BM25. Skips local document embedding. | Requires Docker, compatible query models, and more disk. The publisher estimates 11 GB for Acts and 434 GB for all three restored collections. Check court coverage and leave room for restore files. |

**Recommendation:** Start with Tantivy and the smallest relevant corpus. Add the [Qdrant Acts pilot](docs/qdrant.md) if your questions rely on paraphrases or vocabulary differences. Compare both on the same questions before restoring judgment collections. [Vaquill disk requirements](https://github.com/Vaquill-AI/open-india-law/blob/main/data/QDRANT_RESTORE.md#disk-requirements)

For agents, [AGENTS.md](AGENTS.md) gives the setup sequence and checks. The [architecture guide](docs/architecture.md) explains how both routes connect to the research workflow.

## Tantivy quick start

Clone this repository from GitHub or download and unzip it. From its root, use Python 3.14 and curl. The commands below use a macOS or Linux shell. The starter download is about 25 MiB and contains central legislation. The search returns source filenames and row positions alongside the matching text and available source metadata.

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python download_corpus.py
.venv/bin/python search_index.py build
.venv/bin/python search_index.py status
.venv/bin/python search_index.py search "electronic record" --kind legislation --limit 3
```

Run `.venv/bin/python -m unittest -v` to check indexing and search with synthetic fixtures. These tests run without corpus downloads.

## Add judgments and regional sources

List the shards and their sizes before downloading. Choose the courts, statutes, regulations, or tribunals that match the research question. The example below adds Supreme Court judgments, a download of about 3.5 GiB. Building again adds the newly downloaded shards to the index.

```sh
.venv/bin/python download_corpus.py --list
.venv/bin/python download_corpus.py --file in_supreme-court_judgments.parquet
.venv/bin/python search_index.py build
.venv/bin/python search_index.py search "procedural fairness" --kind judgment --limit 5
.venv/bin/python search_index.py search "CITATION" --kind judgment --exact --limit 3
```

Replace `CITATION` with a verified citation or case number. Repeat `--file` in one command to select several shards. The optional `--all` flag downloads about 50 GiB. Allow additional disk space for the local index and build files. The downloader checks publisher SHA-256 values before accepting new downloads. Keep one download or build process active per checkout. For an invalid checksum after an interrupted transfer, delete the affected `corpus/v2026.08.1/<shard>.part` and retry. To rehash an existing downloaded file, remove its `corpus/v2026.08.1/<shard>.verified.json` receipt and rerun the downloader.

The release metadata is pinned to **Open India Law v2026.08.1**. Court and date coverage vary by source. Review coverage and use current official sources for material developments, including amendments and later treatment. Corpus attribution and source options are listed in [Tools and sources](docs/tools-and-sources.md).

## Use another corpus

Export passages from your source as UTF-8 JSON Lines. Build a separate local index with `build_corpus.py` and query it with the existing search command. The [architecture and corpus guide](docs/architecture.md) gives the schema, setup commands, and provenance rules.

## Run a research assignment

1. Copy the [research brief and prompts](templates/research-brief.md) into your local research notes and fill in one concrete question.
2. Follow the [research and validation checklist](docs/workflow.md). Start with local search and fill specific gaps using the [tools and sources](docs/tools-and-sources.md).
3. Record findings using the [evidence packet](templates/evidence-packet.md). Give the packet to the drafting model after the independent review and source checks.

The repository contains the search tooling, release metadata, and reusable instructions and templates. Keep downloaded data in `corpus/`, shard indexes in `tantivy-*/`, and custom indexes and matter files in `research/`. These paths and local `.env*` files are ignored by Git.
