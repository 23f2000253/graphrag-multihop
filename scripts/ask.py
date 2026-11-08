import argparse

from app.common import get_driver
from app.generation import generate_answer
from app.retrieval import graph_search, hybrid_search, vector_search

parser = argparse.ArgumentParser()
parser.add_argument("question")
parser.add_argument("--strategy", default="hybrid", choices=["vector", "graph", "hybrid"])
parser.add_argument("--k", type=int, default=5)
parser.add_argument("--depth", type=int, default=2)
args = parser.parse_args()

with get_driver() as driver:
    if args.strategy == "vector":
        hits = vector_search(args.question, args.k, driver)
    elif args.strategy == "graph":
        hits = graph_search(args.question, args.k, driver, depth=args.depth)
    else:
        hits = hybrid_search(args.question, args.k, driver, depth=args.depth)

result = generate_answer(args.question, hits)
cited = set(result["citations"])

print(f"\nSTRATEGY: {args.strategy}")
print(f"ANSWER:   {result['answer']}")
print("CITED:    " + (", ".join(h["title"] for h in hits if h["chunk_id"] in cited) or "none"))
print("\nEVIDENCE SENT TO THE MODEL:")
for i, h in enumerate(hits, start=1):
    mark = "*" if h["chunk_id"] in cited else " "
    print(f" {mark}[{i}] ({h['via']}, score {h['score']:.2f}) {h['title']}: {h['text'][:110]}...")
