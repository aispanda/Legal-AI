"""Local BM25 and citation lookup for legal corpora."""

import argparse
import json
import re
import unicodedata
from pathlib import Path

import pyarrow.parquet as pq
import tantivy as tv

ROOT = Path(__file__).parent
CORPUS = ROOT / "corpus" / "v2026.08.1"
INDEX = ROOT / "tantivy-v2026.08.1"
KINDS = {"judgments": "judgment", "legislation": "legislation",
         "regulations": "regulation", "matters": "tribunal"}
TEXT = ("title", "heading", "body")
KEYWORDS = ("kind", "court", "region", "source_file", "group", "exact", "checkpoint")
STORED = ("citation", "case_number", "section", "source_url", "mirror_url", "decision_date", "chunk_id")
COLUMNS = {
    "title", "section_title", "text", "text_original", "citation", "case_number", "court",
    "court_code", "state", "jurisdiction", "year", "decision_date", "section_number", "source_url",
    "mirror_url", "page_start", "page_end", "chunk_id", "case_id", "act_id", "tribunal",
}


def schema(additional_fields=()):
    builder = tv.SchemaBuilder()
    for key in TEXT:
        builder.add_text_field(key, stored=True)
    for key in KEYWORDS + STORED + additional_fields:
        builder.add_text_field(key, stored=key != "exact", tokenizer_name="raw", index_option="basic")
    for key in ("year", "row", "page_start", "page_end"):
        builder.add_unsigned_field(key, stored=True, indexed=key == "year", fast=key == "year")
    return builder.build()


def key(value, *, distinguish_numeric_parts=False):
    normalized = unicodedata.normalize("NFKC", str(value)).casefold().strip()
    if distinguish_numeric_parts:
        return re.sub(r"((?<=\d)[\W_]+(?=\d))|[\W_]+",
                      lambda match: " " if match[1] else "", normalized)
    return re.sub(r"[\W_]+", "", normalized)


def citation_values(title, section, citation, case_number):
    source_title = re.sub(r"^the\s+", "", title.strip(), flags=re.I)
    act_section = source_title + " section " + section if section else ""
    return citation, case_number, act_section


def document(row, path, kind, region, position, additional_fields=()):
    title = row.get("title") or ""
    section = row.get("section_number") or ""
    case_number = row.get("case_number") or ""
    citation = row.get("citation") or ""
    identity = row.get("case_id") or row.get("act_id") or f"{path.name}:{position}"
    values = {
        "kind": kind, "region": row.get("state") or region,
        "court": row.get("court_code") or row.get("court") or row.get("tribunal") or "",
        "source_file": path.name, "group": f"{kind}:{identity}",
        "title": title, "heading": row.get("section_title") or "",
        "body": row.get("text_original") or row.get("text") or "",
        "citation": citation, "case_number": case_number, "section": section,
        "source_url": row.get("source_url") or "", "mirror_url": row.get("mirror_url") or "",
        "decision_date": row.get("decision_date") or "", "chunk_id": row.get("chunk_id") or "",
    }
    values.update({field: row.get(field) for field in additional_fields})
    doc = tv.Document()
    for field, value in values.items():
        if value:
            text = str(value).lower() if field in {"court", "region"} else str(value)
            doc.add_text(field, text)
    for value in {key(val) for val in citation_values(title, section, citation, case_number)} - {""}:
        doc.add_text("exact", value)
    doc.add_unsigned("row", position)
    for field in ("year", "page_start", "page_end"):
        value = row.get(field)
        if field == "year" and not value:
            date = re.match(r"^([0-9]{4})-", str(values["decision_date"]))
            value = int(date.group(1)) if date else None
        if isinstance(value, (int, float)) and 0 < value < 1000000:
            doc.add_unsigned(field, int(value))
    return doc


def open_index(destination=INDEX):
    return tv.Index.open(str(destination))


def term(index, field, value):
    return tv.Query.term_query(index.schema, field, value, index_option="basic")


def build(sources, destination=INDEX, threads=5):
    destination.mkdir(parents=True, exist_ok=True)
    index = tv.Index(schema(), path=str(destination))
    writer = index.writer(heap_size=640_000_000, num_threads=threads)
    total = 0
    try:
        for path in sources:
            if index.searcher().search(term(index, "checkpoint", path.name), limit=1).count:
                continue
            stem = path.stem.removeprefix("in_")
            region, suffix = stem.rsplit("_", 1)
            region = region.removesuffix("_tribunal")
            kind = KINDS[suffix]
            parquet = pq.ParquetFile(path)
            columns = sorted(COLUMNS.intersection(parquet.schema_arrow.names))
            position = 0
            for batch in parquet.iter_batches(batch_size=4096, columns=columns):
                for row in batch.to_pylist():
                    writer.add_document(document(row, path, kind, region, position))
                    position += 1
            if position != parquet.metadata.num_rows:
                raise RuntimeError(f"{path.name}: imported {position} of {parquet.metadata.num_rows} rows")
            marker = tv.Document()
            marker.add_text("checkpoint", path.name)
            marker.add_unsigned("row", position)
            writer.add_document(marker)
            writer.commit()
            index.reload()
            total += position
            print(f"{path.name}: {position:,} records committed", flush=True)
    except BaseException:
        writer.rollback()
        raise
    finally:
        writer.wait_merging_threads()
    return total


def search(index, query, *, exact=False, court=None, region=None, kind=None,
           from_year=None, to_year=None, limit=10):
    if not query.strip():
        raise ValueError("Enter a citation or search terms.")
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("Search limit must be an integer between 1 and 100.")
    if exact:
        query = re.sub(r"^the\s+", "", query.strip(), flags=re.I)
        match = term(index, "exact", key(query))
    else:
        match = index.parse_query(query, list(TEXT), field_boosts={"title": 3.0, "heading": 2.0})
    filters = [
        (tv.Occur.Must, match),
        (tv.Occur.MustNot, tv.Query.regex_query(index.schema, "checkpoint", ".+")),
    ]
    for field, value in (("court", court), ("region", region), ("kind", kind)):
        if value:
            filters.append((tv.Occur.Must, term(index, field, value.casefold())))
    if from_year is not None or to_year is not None:
        year_range = tv.Query.range_query(
            index.schema, "year", tv.FieldType.Unsigned, from_year, to_year, use_inverted_index=True
        )
        filters.append((tv.Occur.Must, year_range))
    searcher = index.searcher()
    ranked = tv.Query.boolean_query(filters)
    batch_size = max(limit * 10, 100)
    exact_key = key(query, distinguish_numeric_parts=True) if exact else None
    results = {}
    offset = 0
    while True:
        batch_query = ranked
        if not exact and results:
            seen = tv.Query.term_set_query(index.schema, "group", list(results))
            batch_query = tv.Query.boolean_query([(tv.Occur.Must, ranked), (tv.Occur.MustNot, seen)])
        raw = searcher.search(batch_query, limit=batch_size, offset=offset, count=False)
        for _, address in raw.hits:
            evidence = searcher.doc(address).to_dict()
            if exact:
                values = citation_values(*(evidence.get(field, [""])[0]
                                           for field in ("title", "section", "citation", "case_number")))
                if not any(key(value, distinguish_numeric_parts=True) == exact_key for value in values if value):
                    continue
            results.setdefault(evidence["group"][0], evidence)
            if len(results) == limit:
                return list(results.values())
        if len(raw.hits) < batch_size:
            return list(results.values())
        if exact:
            offset += batch_size


def release_files():
    manifest = json.loads((ROOT / "release.json").read_text())
    paths = []
    for item in manifest["files"]:
        name = item["file"]
        path = CORPUS / name
        if not path.exists():
            continue
        receipt_path = CORPUS / (name + ".verified.json")
        if not receipt_path.exists():
            raise RuntimeError(f"{name}: run download_corpus.py --file {name} to verify this file")
        receipt = json.loads(receipt_path.read_text())
        if (path.stat().st_size != item["bytes"]
                or receipt.get("sha256") != item["sha256"]
                or not receipt.get("publisher_sha256_verified")):
            raise RuntimeError(f"{name}: verified input required")
        paths.append(path)
    if not paths:
        raise RuntimeError("Download at least one corpus shard with download_corpus.py before indexing.")
    return sorted(paths, key=lambda path: path.stat().st_size)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, help="path to a custom index for search")
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("build")
    status = actions.add_parser("status")
    status.set_defaults(action="status")
    query = actions.add_parser("search")
    query.add_argument("query")
    query.add_argument("--exact", action="store_true")
    query.add_argument("--court")
    query.add_argument("--region")
    query.add_argument("--kind", choices=(*KINDS.values(), "document"))
    query.add_argument("--from-year", type=int)
    query.add_argument("--to-year", type=int)
    query.add_argument("--limit", type=int, default=10, choices=range(1, 101))
    args = vars(parser.parse_args())
    action = args.pop("action")
    destination = args.pop("index")
    if destination is not None and action != "search":
        parser.error("--index is available for search")
    if action == "build":
        build(release_files())
    elif action == "status":
        index = open_index()
        searcher = index.searcher()
        files = release_files()
        done = sum(searcher.search(term(index, "checkpoint", f.name), limit=1).count for f in files)
        print(json.dumps({"files_indexed": done, "downloaded_files": len(files),
                          "records_indexed": searcher.num_docs - done}))
    else:
        print(json.dumps(search(open_index(destination or INDEX), **args), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
