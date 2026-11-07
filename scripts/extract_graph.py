import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from app.extraction import extract_chunk

PRICE_IN, PRICE_OUT = 0.10, 0.50  # USD per million tokens (list price, prompts <= 100K tokens)
OUT = Path("data/processed/extractions.jsonl")

parser = argparse.ArgumentParser()
parser.add_argument("--limit", type=int, default=None)
parser.add_argument("--workers", type=int, default=4)
parser.add_argument("--show", action="store_true")
args = parser.parse_args()

with open("data/processed/chunks.jsonl", encoding="utf-8") as f:
    chunks = [json.loads(line) for line in f]

done = set()
if OUT.exists():
    with open(OUT, encoding="utf-8") as f:
        done = {json.loads(line)["chunk_id"] for line in f}
todo = [c for c in chunks if c["chunk_id"] not in done]
if args.limit:
    todo = todo[: args.limit]
print(f"{len(done)} already done, {len(todo)} to process")

stats = {"ok": 0, "errors": 0, "entities": 0, "relations": 0,
         "dropped_invalid": 0, "dropped_evidence": 0, "dropped_endpoint": 0, "in": 0, "out": 0}
first_error = None
with ThreadPoolExecutor(max_workers=args.workers) as pool, open(OUT, "a", encoding="utf-8") as f:
    futures = [pool.submit(extract_chunk, c) for c in todo]
    for n, fut in enumerate(as_completed(futures), start=1):
        res = fut.result()
        stats["in"] += res["input_tokens"]
        stats["out"] += res["output_tokens"]
        if res["error"]:
            stats["errors"] += 1
            first_error = first_error or res["error"]
            continue
        f.write(json.dumps(res, ensure_ascii=False) + "\n")
        f.flush()
        stats["ok"] += 1
        stats["entities"] += len(res["entities"])
        stats["relations"] += len(res["relations"])
        stats["dropped_evidence"] += res["dropped_bad_evidence"]
        stats["dropped_endpoint"] += res["dropped_bad_endpoint"]
        stats["dropped_invalid"] += res["dropped_invalid"]
        if args.show:
            print(f"\n[{res['title']}] {len(res['entities'])} entities")
            for r in res["relations"]:
                print(f"   {r['subject']} -[{r['predicate']}]-> {r['object']}")
        elif n % 50 == 0:
            print(f"  {n}/{len(todo)} done")

cost = stats["in"] / 1e6 * PRICE_IN + stats["out"] / 1e6 * PRICE_OUT
print("\nThis run:", json.dumps(stats))
print(f"Estimated cost of this run: ${cost:.4f}")
if first_error:
    print("First error:", first_error)
