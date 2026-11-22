"""Resume and verify the public Open India Law release."""

import argparse
import concurrent.futures
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).parent / "corpus" / "v2026.08.1"
MANIFEST = json.loads((Path(__file__).parent / "release.json").read_text())


def fetch(entry):
    name = entry["file"]
    target = ROOT / name
    partial = ROOT / (name + ".part")
    receipt = ROOT / (name + ".verified.json")
    expected = entry["sha256"]
    if receipt.exists() and target.exists():
        previous = json.loads(receipt.read_text())
        if previous["etag"] == entry["etag"] and target.stat().st_size == entry["bytes"]:
            if previous.get("publisher_sha256_verified") and previous.get("sha256") == expected:
                return previous

    if not target.exists():
        if not partial.exists() or partial.stat().st_size < entry["bytes"]:
            subprocess.run(
                [
                    "curl", "--fail", "--silent", "--show-error", "--location",
                    "--retry", "4", "--retry-delay", "2", "--connect-timeout", "20",
                    "--speed-limit", "65536", "--speed-time", "90", "--continue-at", "-",
                    "--header", f'If-Match: "{entry["etag"]}"',
                    "--output", str(partial), entry["url"],
                ],
                check=True,
            )
        candidate = partial
    else:
        candidate = target
    if candidate.stat().st_size != entry["bytes"]:
        raise ValueError(f"{name}: file size differs from the release manifest")
    with candidate.open("rb") as data:
        sha256 = hashlib.file_digest(data, "sha256").hexdigest()
        if name.endswith(".parquet"):
            data.seek(0)
            header = data.read(4)
            data.seek(-4, 2)
            if header != b"PAR1" or data.read() != b"PAR1":
                raise ValueError(f"{name}: invalid Parquet envelope")
    if sha256 != expected:
        raise ValueError(f"{name}: SHA-256 differs from the release checksum")
    if candidate == partial:
        partial.replace(target)
    result = {"file": name, "bytes": entry["bytes"], "etag": entry["etag"],
              "sha256": sha256, "publisher_sha256_verified": True}
    receipt.write_text(json.dumps(result) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--file", action="append", choices=[entry["file"] for entry in MANIFEST["files"]])
    selection.add_argument("--all", action="store_true", help="download every shard in the pinned release")
    selection.add_argument("--list", action="store_true", help="show shard names and sizes in bytes")
    args = parser.parse_args()

    if args.list:
        for entry in MANIFEST["files"]:
            print(f'{entry["file"]}\t{entry["bytes"]}')
        return

    names = set(args.file or ["in_central_legislation.parquet"])
    files = [entry for entry in MANIFEST["files"] if args.all or entry["file"] in names]
    files.sort(key=lambda entry: entry["bytes"], reverse=True)
    ROOT.mkdir(parents=True, exist_ok=True)
    failures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        jobs = {pool.submit(fetch, entry): entry["file"] for entry in files}
        for job in concurrent.futures.as_completed(jobs):
            try:
                result = job.result()
                print(f'{result["file"]} {result["bytes"]:,} verified', flush=True)
            except (OSError, ValueError, subprocess.CalledProcessError) as error:
                failures.append(jobs[job])
                print(f"{jobs[job]}: {error}", flush=True)
    if failures:
        raise SystemExit(f"{len(failures)} downloads need attention")


if __name__ == "__main__":
    main()
