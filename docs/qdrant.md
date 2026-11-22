# Qdrant pilot with Vaquill snapshots

Choose this route for search by meaning and keywords when the relevant corpus is available as a Vaquill snapshot. Start with the Acts and regulations collection. The publisher estimates an 11 GB restored footprint for Acts and about 434 GB across all three collections. Plan room for temporary restore files. The two judgment collections cover different courts, with some overlap. The publisher's guide gives the sizes, shard counts and coverage for each. [Vaquill restore and storage guide](https://github.com/Vaquill-AI/open-india-law/blob/main/data/QDRANT_RESTORE.md)

## Restore Acts locally

From the repository root, use Docker, curl, and jq in a macOS or Linux shell. The commands start a dedicated loopback container named `legal-ai-qdrant` on port 6337 with its own data directory. Choose an unused name, port, and storage directory for each new instance. If you change the port, use it in the restore block, verification command, and query helper. The restore refuses to proceed if `acts_india` already exists. Keep the current container and storage if you want to [reuse an existing restore](#verify-an-existing-restore).

```sh
(
  set -eu
  name=legal-ai-qdrant
  port=6337
  storage="$PWD/research/qdrant"
  mkdir -p research
  mkdir "$storage"
  docker run -d --name "$name" -p "127.0.0.1:$port:6333" \
    -v "$storage:/qdrant/storage" qdrant/qdrant:v1.16.3
  curl --fail --retry 10 --retry-all-errors --retry-delay 1 "http://127.0.0.1:$port/readyz"
)
```

The collection must match the source's two-shard layout and vector settings. Run the following block in one shell. It reads the snapshot names and checksums from the publisher and has Qdrant pull the files directly.

```sh
(
  set -eu
  qdrant=http://127.0.0.1:6337
  mirror=https://oss-data-in.vaquill.ai/qdrant/acts_india
  existing=$(curl -fsS "$qdrant/collections/acts_india/exists")
  if ! printf '%s\n' "$existing" | jq -e '.result.exists == false' >/dev/null; then
    printf '%s\n' 'Could not confirm that acts_india is absent. Verify the target before restoring.' >&2
    exit 1
  fi
  curl -fsS -X PUT "$qdrant/collections/acts_india" \
    -H 'Content-Type: application/json' \
    -d '{"shard_number":2,"vectors":{"dense":{"size":1024,"distance":"Cosine","on_disk":true,"quantization_config":{"scalar":{"type":"int8","quantile":0.99,"always_ram":false}}}},"sparse_vectors":{"sparse":{"modifier":"idf","index":{"on_disk":true,"full_scan_threshold":5000}}}}'
  for shard in 0 1; do
    base="$mirror/shard-$shard"
    metadata=$(curl -fsS "$base/index.json")
    snapshot=$(printf '%s' "$metadata" | jq -er '.snapshot | strings | select(length > 0)')
    checksum_file=$(curl -fsS "$base/$snapshot.checksum")
    checksum=$(printf '%s\n' "$checksum_file" | awk 'NR == 1 {print $1}')
    if ! printf '%s\n' "$checksum" | grep -Eqx '[0-9a-fA-F]{64}'; then
      printf 'Invalid SHA-256 for Acts shard %s.\n' "$shard" >&2
      exit 1
    fi
    payload=$(jq -n --arg location "$base/$snapshot" --arg checksum "$checksum" \
      '{location:$location, checksum:$checksum, priority:"snapshot"}')
    curl -fsS -X PUT "$qdrant/collections/acts_india/shards/$shard/snapshots/recover?wait=true" \
      -H 'Content-Type: application/json' -d "$payload"
  done
  curl -fsS -X POST "$qdrant/collections/acts_india/points/count" \
    -H 'Content-Type: application/json' -d '{"exact":true}' \
    | jq -e '.result.count | select(. == 1098577)'
)
```

The expected count is for the published Acts snapshot checked for this guide. If the mirror changes, confirm the expected count from the publisher. If a restore fails, inspect the failed shard and recover it again using the publisher's instructions. A matching point count verifies restore completeness for that collection. Check subject and court coverage separately.

## Verify an existing restore

Use the port of your existing Qdrant instance. If its Docker container is stopped, restart that container before running the command. This reads the collection's exact count.

```sh
port=6337
curl -fsS -X POST "http://127.0.0.1:$port/collections/acts_india/points/count" \
  -H 'Content-Type: application/json' -d '{"exact":true}' | jq -e '.result.count'
```

Compare the result with the publisher's expected count. Pass `--qdrant "http://127.0.0.1:$port"` to the query helper.

## Run a hybrid query

Install and start Ollama. Use a separate Python 3.12 environment for the helper's FastEmbed dependency. The model download and cache are local prerequisites for the first query. [Ollama](https://ollama.com/download) · [Voyage model card](https://huggingface.co/MongoDB/voyage-4-nano-GGUF)

```sh
ollama pull hf.co/MongoDB/voyage-4-nano-GGUF:Q8_0
python3.12 -m venv research/qdrant-venv
research/qdrant-venv/bin/python -m pip install 'fastembed==0.9.1'
research/qdrant-venv/bin/python scripts/query_qdrant.py "electronic records and proof"
```

Expect JSON results carrying text and available source metadata. The helper requests a 1,024-dimensional Voyage 4 query vector, uses FastEmbed's BM25 query encoder, then fuses the two rankings. For another restored collection, pass `--collection` and `--qdrant` as needed. For broad judgment coverage, restore both judgment collections using each collection's shard count and vector settings in Vaquill's guide, query both, and deduplicate by case ID. Keep Tantivy for exact citations and parts of the corpus that the vector snapshots omit.
