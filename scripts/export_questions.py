import json
from pathlib import Path

with open("data/processed/questions.jsonl", encoding="utf-8") as f:
    rows = [json.loads(line) for line in f]
bank = [{"id": r["id"], "question": r["question"], "answer": r["answer"],
         "type": r["type"], "split": r["split"]} for r in rows]

Path("static").mkdir(exist_ok=True)
Path("static/questions.json").write_text(
    json.dumps(bank, ensure_ascii=False, indent=1), encoding="utf-8")

lines = ["# Question bank (50 questions)", "",
         "Every question can be answered from the 500-paragraph sample. Source: HotpotQA (CC BY-SA 4.0).",
         "", "| # | Split | Type | Question | Expected answer |", "|---|---|---|---|---|"]
for i, b in enumerate(bank, start=1):
    q = b["question"].replace("|", "\\|")
    a = b["answer"].replace("|", "\\|")
    lines.append(f"| {i} | {b['split']} | {b['type']} | {q} | {a} |")
Path("docs").mkdir(exist_ok=True)
Path("docs/question_bank.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(len(bank), "questions exported")
