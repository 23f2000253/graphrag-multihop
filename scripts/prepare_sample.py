import hashlib
import json
from pathlib import Path

import pandas as pd

SRC = "data/raw/distractor/validation-00000-of-00001.parquet"
OUT = Path("data/processed")
N_QUESTIONS, N_DEV, SEED = 50, 15, 42


def make_doc_id(title: str) -> str:
    return "doc_" + hashlib.sha1(title.encode("utf-8")).hexdigest()[:10]


df = pd.read_parquet(SRC)
picked = df.sample(n=N_QUESTIONS, random_state=SEED).reset_index(drop=True)

chunks = {}
questions = []
for i, row in picked.iterrows():
    ctx = row["context"]
    for title, sents in zip(ctx["title"], ctx["sentences"]):
        sents = [str(s).strip() for s in sents]
        text = " ".join(sents).strip()
        if not text:
            continue
        doc_id = make_doc_id(title)
        chunk_id = doc_id + "_c0"
        chunks.setdefault(
            chunk_id,
            {"chunk_id": chunk_id, "doc_id": doc_id, "title": title,
             "text": text, "sentences": sents},
        )

    facts = row["supporting_facts"]
    questions.append({
        "id": row["id"],
        "question": row["question"],
        "answer": row["answer"],
        "type": row["type"],
        "level": row["level"],
        "split": "dev" if i < N_DEV else "test",
        "supporting_doc_ids": sorted({make_doc_id(t) for t in facts["title"]}),
        "supporting_facts": [
            {"title": t, "sent_id": int(s)}
            for t, s in zip(facts["title"], facts["sent_id"])
        ],
    })

missing = sum(
    1 for q in questions for d in q["supporting_doc_ids"] if d + "_c0" not in chunks
)

OUT.mkdir(parents=True, exist_ok=True)
with open(OUT / "questions.jsonl", "w", encoding="utf-8") as f:
    for q in questions:
        f.write(json.dumps(q, ensure_ascii=False) + "\n")
with open(OUT / "chunks.jsonl", "w", encoding="utf-8") as f:
    for c in chunks.values():
        f.write(json.dumps(c, ensure_ascii=False) + "\n")

print("questions:", len(questions))
print("dev / test:", sum(q["split"] == "dev" for q in questions),
      "/", sum(q["split"] == "test" for q in questions))
print("chunks:", len(chunks))
print("evidence paragraphs missing from chunks:", missing)
