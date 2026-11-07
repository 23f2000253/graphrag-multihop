import json

from app.common import get_driver
from app.retrieval import vector_search

K = 5

with open("data/processed/questions.jsonl", encoding="utf-8") as f:
    questions = [json.loads(line) for line in f]
dev = [q for q in questions if q["split"] == "dev"]

recalls, full = [], []
with get_driver() as driver:
    for q in dev:
        hits = vector_search(q["question"], K, driver)
        got = {h["doc_id"] for h in hits}
        gold = set(q["supporting_doc_ids"])
        found = len(gold & got)
        recalls.append(found / len(gold))
        full.append(found == len(gold))

print(f"Dev questions: {len(dev)}, top-{K}")
print(f"Average evidence recall@{K}: {sum(recalls) / len(recalls):.2f}")
print(f"Questions with ALL evidence found: {sum(full)}/{len(full)}")
