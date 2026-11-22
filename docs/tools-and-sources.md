# Tools and sources

Start with the source closest to the question. Use provider search to find leads and the issuing court, legislature, or regulator to verify them. Record the release, jurisdiction, search date, and gaps.

## India

| Source | Use it for | Public links |
| --- | --- | --- |
| Vaquill Open India Law | Bulk corpus, publisher checksums, coverage, and optional Qdrant snapshots. | [GitHub](https://github.com/Vaquill-AI/open-india-law) · [Hugging Face](https://huggingface.co/datasets/vaquill/open-india-law) · [public mirror](https://oss-data-in.vaquill.ai/index.html) · [court coverage](https://github.com/Vaquill-AI/open-india-law/blob/main/COVERAGE.md) · [Qdrant restore](https://github.com/Vaquill-AI/open-india-law/blob/main/data/QDRANT_RESTORE.md) |
| Vaquill India live API | Targeted legislation and case lookups when an appropriate tool is available. Check the specific corpus and endpoint before searching. | [India API and MCP](https://www.vaquill.ai/in) |
| Official publishers | Statute text, gazettes, official orders, judgments, and case status. Verify the version applicable to the event. | [India Code](https://www.indiacode.nic.in/) · [eGazette](https://egazette.gov.in/) · [Supreme Court judgments](https://www.sci.gov.in/judgements/) · [official eCourts Services](https://services.ecourts.gov.in/ecourtindia_v6/) |
| High Courts and tribunals | Use the issuing High Court, tribunal, or regulator's site for its orders and decisions. The eCourts judgment portal is another source for court judgments. | [eCourts judgments](https://judgments.ecourts.gov.in/) |
| eCourtsIndia | An independent provider for docket, order, and case-history discovery by case number or CNR. Its terms permit automated access through its Partner API under its own terms and pricing. | [Search](https://ecourtsindia.com/) · [API documentation](https://ecourtsindia.com/api/docs) |
| Indian Kanoon and Prism | Find citations, related decisions, later mentions, and public copies. Treat AI results as leads until verified. API use requires attribution as specified in its terms. | [Search](https://indiankanoon.org/) · [API](https://api.indiankanoon.org/) · [API terms](https://api.indiankanoon.org/terms/) · [Prism access terms](https://indiankanoon.org/members/terms/) |

## United States

| Source | Use it for | Public links |
| --- | --- | --- |
| Vaquill Open US Law | Bulk statutes, regulations, and other public-law materials in the publisher's coverage. Convert selected exports to the JSONL schema for local search. | [Dataset and licensing](https://www.vaquill.ai/open-us-law) · [GitHub](https://github.com/Vaquill-AI/open-us-law) · [Hugging Face](https://huggingface.co/datasets/vaquill/open-us-law) · [mirror manifest](https://oss-data-us.vaquill.ai/index.json) |
| Vaquill US live API | Search and resolve U.S. primary-law citations with the REST API or the U.S. MCP connector. | [API setup](https://www.vaquill.ai/agents) · [U.S. MCP](https://www.vaquill.ai/mcp) |
| Official federal and state publishers | Verify statutes, legislation, regulations, and decisions in the official edition or docket. For state law use the relevant state publisher. For lower federal court dockets, use PACER, which may charge fees. | [U.S. Code](https://uscode.house.gov/) · [GovInfo](https://www.govinfo.gov/) · [eCFR](https://www.ecfr.gov/) · [Federal Register](https://www.federalregister.gov/) · [U.S. Supreme Court opinions](https://www.supremecourt.gov/opinions/opinions.aspx) · [Congress.gov](https://www.congress.gov/) · [PACER](https://pacer.uscourts.gov/) |
| CourtListener | Search opinions and citation relationships. Follow consequential results back to the issuing court. | [Search](https://www.courtlistener.com/) · [API](https://www.courtlistener.com/help/api/) |

The pinned India downloader covers the Indian release. U.S. or other exports use the [portable importer](architecture.md#build-from-another-corpus). Check the terms of each release. The Open India Law compilation is CC BY 4.0. Open US Law v2026.09.1 lists CC BY-NC 4.0 terms for its compilation.

## Retrieval and review tools

| Tool | Role | Public links |
| --- | --- | --- |
| Tantivy and PyArrow | Local keyword and exact-citation search over selected corpus shards. | [Tantivy](https://github.com/quickwit-oss/tantivy) · [PyArrow](https://arrow.apache.org/docs/python/) |
| Qdrant, Voyage 4 Nano, FastEmbed, Ollama | Optional local dense and sparse retrieval using compatible snapshots. | [Qdrant](https://qdrant.tech/documentation/) · [Voyage model](https://huggingface.co/MongoDB/voyage-4-nano-GGUF) · [BM25 model](https://huggingface.co/Qdrant/bm25) · [Ollama](https://ollama.com/download) |
| Google and Gemini | Discover sources and run a fresh independent review. The pilot used Gemini Neon for research review. Record the model and actual access used. | [Google Search](https://www.google.com/) · [Gemini](https://gemini.google.com/) · [Gemini API docs](https://ai.google.dev/gemini-api/docs) |
| TypeSafe Jev and Claude | Check whether passages support specific claims and review documentation or drafts. Verify material conclusions against primary sources. | [TypeSafe Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev) · [Claude](https://claude.ai/) |
| NotebookLM | Optional review of selected source documents. | [NotebookLM](https://notebooklm.google/) |

Use your own account for optional connected tools and keep credentials outside the repo.
