import csv
import json
from pathlib import Path

DIR = Path("evaluation_results")
RUNS = [
    ("Vector k=5 (baseline)", "vector_test_k5"),
    ("Vector k=8 (control)", "vector_test_k8"),
    ("Graph only (depth 2)", "graph_test_k5_d2_g3"),
    ("Hybrid depth 1", "hybrid_test_k5_d1_g3"),
    ("Hybrid depth 2", "hybrid_test_k5_d2_g3"),
]


def load_summary(stem):
    path = DIR / f"{stem}_summary.json"
    if not path.exists():
        print("MISSING:", path)
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_rows(stem):
    with open(DIR / f"{stem}.jsonl", encoding="utf-8") as f:
        return {r["id"]: r for r in map(json.loads, f)}


def md(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


main_header = ["System", "EM", "F1", "Evidence recall", "All evidence found",
               "Avg latency (s)", "Est. cost (USD)", "Failures"]
type_header = ["System", "Bridge EM", "Bridge F1", "Comparison EM", "Comparison F1"]
main_rows, type_rows = [], []
for label, stem in RUNS:
    s = load_summary(stem)
    if s is None:
        continue
    main_rows.append([
        label, f"{s['exact_match']:.3f}", f"{s['f1']:.3f}",
        f"{s['evidence_recall']:.3f}", f"{s['all_evidence_rate']:.3f}",
        f"{s['avg_total_s']:.2f}", f"{s['estimated_cost_usd']:.4f}", str(s["failures"])])
    b = s["by_type"].get("bridge", {})
    c = s["by_type"].get("comparison", {})
    type_rows.append([
        label, f"{b.get('em', 0):.3f}", f"{b.get('f1', 0):.3f}",
        f"{c.get('em', 0):.3f}", f"{c.get('f1', 0):.3f}"])

report = ["# Test-set comparison (35 questions)", "", md(main_header, main_rows), "",
          "## By question type", "", md(type_header, type_rows), ""]

try:
    ctrl = load_rows("vector_test_k8")
    hyb = load_rows("hybrid_test_k5_d2_g3")
except FileNotFoundError:
    ctrl, hyb = {}, {}


def describe(i):
    h, c = hyb[i], ctrl[i]
    added = [t for t, v in zip(h["retrieved_titles"], h["via"]) if v == "graph"]
    return (f"- Q: {h['question'][:110]}\n"
            f"  gold: {h['gold_answer']} | vector k=8: {c['prediction']!r} (F1 {c['f1']:.2f})"
            f" | hybrid: {h['prediction']!r} (F1 {h['f1']:.2f})\n"
            f"  graph-added paragraphs: {added}")


helped = [i for i in hyb if i in ctrl and hyb[i]["all_evidence"] and not ctrl[i]["all_evidence"]]
hurt = [i for i in hyb if i in ctrl and ctrl[i]["all_evidence"] and not hyb[i]["all_evidence"]]
worse = [i for i in hyb if i in ctrl and hyb[i]["f1"] <= ctrl[i]["f1"] - 0.5]
better = [i for i in hyb if i in ctrl and hyb[i]["f1"] >= ctrl[i]["f1"] + 0.5]

report += [
    "## Hybrid depth 2 vs vector k=8 (per question)", "",
    f"Hybrid found all evidence where vector k=8 did not: {len(helped)}",
    f"Vector k=8 found all evidence where hybrid did not: {len(hurt)}",
    f"Hybrid answer F1 better by 0.5 or more: {len(better)}",
    f"Hybrid answer F1 worse by 0.5 or more: {len(worse)}", "",
]
for title, ids in [("Graph helped (evidence)", helped), ("Graph hurt (evidence)", hurt),
                   ("Hybrid answer much better", better), ("Hybrid answer much worse", worse)]:
    report += [f"### {title}", ""] + [describe(i) for i in ids[:8]] + [""]

text = "\n".join(report)
print(text)
(DIR / "comparison.md").write_text(text, encoding="utf-8")
with open(DIR / "comparison.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(main_header)
    writer.writerows(main_rows)
