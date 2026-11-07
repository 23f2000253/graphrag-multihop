import argparse
import json
import time
from collections import defaultdict
from pathlib import Path

from app.common import get_driver
from app.generation import MODEL, generate_answer
from app.metrics import exact_match, f1_score
from app.retrieval import vector_search

PRICE_IN, PRICE_OUT = 0.10, 0.50  # USD per million tokens (list price, prompts <= 100K tokens)
STRATEGIES = {"vector": vector_search}

parser = argparse.ArgumentParser()
parser.add_argument("--strategy", default="vector", choices=STRATEGIES)
parser.add_argument("--split", default="dev", choices=["dev", "test", "all"])
parser.add_argument("--k", type=int, default=5)
parser.add_argument("--limit", type=int, default=None)
args = parser.parse_args()

with open("data/processed/questions.jsonl", encoding="utf-8") as f:
    questions = [json.loads(line) for line in f]
if args.split != "all":
    questions = [q for q in questions if q["split"] == args.split]
if args.limit:
    questions = questions[: args.limit]

search = STRATEGIES[args.strategy]
results = []
with get_driver() as driver:
    for q in questions:
        t0 = time.perf_counter()
        hits = search(q["question"], args.k, driver)
        t1 = time.perf_counter()
        error = None
        try:
            gen = generate_answer(q["question"], hits)
        except Exception as exc:
            gen = {"answer": "", "citations": [], "input_tokens": 0, "output_tokens": 0}
            error = str(exc)[:200]
        t2 = time.perf_counter()

        gold_docs = set(q["supporting_doc_ids"])
        found = len(gold_docs & {h["doc_id"] for h in hits})
        row = {
            "id": q["id"], "type": q["type"], "question": q["question"],
            "gold_answer": q["answer"], "prediction": gen["answer"],
            "em": exact_match(gen["answer"], q["answer"]),
            "f1": f1_score(gen["answer"], q["answer"]),
            "evidence_recall": found / len(gold_docs),
            "all_evidence": found == len(gold_docs),
            "retrieved_chunk_ids": [h["chunk_id"] for h in hits],
            "retrieved_titles": [h["title"] for h in hits],
            "scores": [round(h["score"], 4) for h in hits],
            "citations": gen["citations"],
            "retrieval_s": t1 - t0, "generation_s": t2 - t1, "total_s": t2 - t0,
            "input_tokens": gen["input_tokens"], "output_tokens": gen["output_tokens"],
            "error": error,
        }
        results.append(row)
        print(f"{len(results)}/{len(questions)} EM={row['em']:.0f} F1={row['f1']:.2f} "
              f"pred={row['prediction']!r} gold={row['gold_answer']!r}")


def mean(key, rows):
    return sum(r[key] for r in rows) / len(rows) if rows else 0.0


tokens_in = sum(r["input_tokens"] for r in results)
tokens_out = sum(r["output_tokens"] for r in results)
summary = {
    "strategy": args.strategy, "split": args.split, "k": args.k, "model": MODEL,
    "questions": len(results), "failures": sum(1 for r in results if r["error"]),
    "exact_match": mean("em", results), "f1": mean("f1", results),
    "evidence_recall": mean("evidence_recall", results),
    "all_evidence_rate": mean("all_evidence", results),
    "avg_retrieval_s": mean("retrieval_s", results),
    "avg_generation_s": mean("generation_s", results),
    "avg_total_s": mean("total_s", results),
    "input_tokens": tokens_in, "output_tokens": tokens_out,
    "estimated_cost_usd": tokens_in / 1e6 * PRICE_IN + tokens_out / 1e6 * PRICE_OUT,
}
by_type = defaultdict(list)
for r in results:
    by_type[r["type"]].append(r)
summary["by_type"] = {
    t: {"n": len(rows), "em": mean("em", rows), "f1": mean("f1", rows),
        "evidence_recall": mean("evidence_recall", rows)}
    for t, rows in by_type.items()
}

out = Path("evaluation_results")
out.mkdir(exist_ok=True)
stem = f"{args.strategy}_{args.split}_k{args.k}"
with open(out / f"{stem}.jsonl", "w", encoding="utf-8") as f:
    for r in results:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
with open(out / f"{stem}_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)
print()
print(json.dumps(summary, indent=2))
