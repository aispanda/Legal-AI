"""Search a restored Vaquill collection with local Ollama and FastEmbed."""

import argparse
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

from fastembed import SparseTextEmbedding


def post(url, body):
    request = Request(
        url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    with urlopen(request, timeout=120) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question")
    parser.add_argument("--collection", default="acts_india")
    parser.add_argument("--qdrant", default="http://127.0.0.1:6337")
    parser.add_argument("--ollama", default="http://127.0.0.1:11434")
    args = parser.parse_args()

    embedding = post(args.ollama.rstrip("/") + "/api/embed", {
        "model": "hf.co/MongoDB/voyage-4-nano-GGUF:Q8_0",
        "input": "Represent the query for retrieving supporting documents: " + args.question,
        "dimensions": 1024,
    })["embeddings"][0]
    if len(embedding) != 1024:
        parser.error("The restored snapshots require 1,024-dimensional Voyage 4 query vectors.")

    cache_dir = Path(__file__).resolve().parents[1] / "research" / "fastembed-cache"
    model = SparseTextEmbedding("Qdrant/bm25", cache_dir=str(cache_dir))
    sparse = next(model.query_embed(args.question))
    collection = quote(args.collection, safe="")
    endpoint = f"{args.qdrant.rstrip('/')}/collections/{collection}/points/query"
    response = post(endpoint, {
        "prefetch": [
            {"using": "dense", "query": embedding, "limit": 50},
            {"using": "sparse", "query": {
                "indices": sparse.indices.tolist(), "values": sparse.values.tolist(),
            }, "limit": 50},
        ],
        "query": {"fusion": "rrf"},
        "limit": 5,
        "with_payload": True,
    })
    print(json.dumps(response["result"]["points"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
