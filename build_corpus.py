"""Build a fresh local index from normalized UTF-8 JSON Lines passages."""

import argparse
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import tantivy as tv

from search_index import KINDS, document, schema

PROVENANCE = ("locator", "source_version")
REQUIRED = ("document_id", "title", "text", "locator")


def parse_passage(line, line_number):
    try:
        row = json.loads(line)
    except json.JSONDecodeError as error:
        raise ValueError(f"Line {line_number}: {error.msg}") from error
    if not isinstance(row, dict):
        raise ValueError(f"Line {line_number}: expected a JSON object")
    for field in REQUIRED:
        if not isinstance(row.get(field), str) or not row[field].strip():
            raise ValueError(f"Line {line_number}: {field} must be a non-empty string")
    kind = row.get("kind", "document")
    if kind not in (*KINDS.values(), "document"):
        raise ValueError(f"Line {line_number}: unknown kind {kind!r}")
    for field in ("section_number", "citation", "case_number", "court", "region",
                  "source_url", "source_version", "section_title", "decision_date", "chunk_id"):
        if field in row and not isinstance(row[field], str):
            raise ValueError(f"Line {line_number}: {field} must be a string")
    # Map the portable ID and text to the existing search engine's fields.
    row["case_id"] = row["document_id"]
    row["text_original"] = row["text"]
    return row, kind


def build_corpus(source, destination):
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"{destination} already exists. Choose a new index directory.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    count = 0
    with TemporaryDirectory(prefix=".build-", dir=destination.parent) as temporary:
        staging = Path(temporary)
        index = tv.Index(schema(PROVENANCE), path=str(staging))
        writer = index.writer(heap_size=64_000_000, num_threads=1)
        try:
            with source.open("rb") as stream:
                for line_number, line in enumerate(stream, 1):
                    digest.update(line)
                    if not line.strip():
                        continue
                    row, kind = parse_passage(line.decode("utf-8"), line_number)
                    writer.add_document(document(
                        row, source, kind, row.get("region", ""), line_number, PROVENANCE
                    ))
                    count += 1
            if not count:
                raise ValueError("The corpus has no passages.")
            writer.commit()
        except BaseException:
            writer.rollback()
            raise
        finally:
            writer.wait_merging_threads()
        manifest = {
            "source_file": source.name,
            "source_sha256": digest.hexdigest(),
            "records_indexed": count,
        }
        (staging / "corpus-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        staging.rename(destination)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="UTF-8 JSONL file containing the passages")
    parser.add_argument("--index", type=Path, required=True, help="new index directory")
    args = parser.parse_args()
    try:
        print(json.dumps(build_corpus(args.source, args.index), indent=2))
    except (ValueError, OSError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
