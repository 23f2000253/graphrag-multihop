# Study map for the final review (about 2 hours)

## Say this first (one minute, in your own words)
Vector search finds paragraphs that sound like the question, so it often finds only one link
of a chain. I built a knowledge graph from the paragraphs (dots = entities, arrows = relations,
each arrow backed by an evidence sentence) and used it to find the missing links. I measured
this honestly on 35 held-out questions against a fair control, and built a web app that shows
both systems side by side.

## Study order
1. app/metrics.py: Exact Match and F1. Why answers are cleaned first, and why F1 gives partial credit.
2. app/resolution.py: safe name merging. Duplicates vs wrong merges.
3. app/common.py and scripts/build_index.py: embeddings, cosine similarity, the vector index, MERGE (no duplicates).
4. app/retrieval.py: vector_search, question_entities, graph walk (depth, hub filter, ranking by similarity), hybrid merge (5 vector + up to 3 graph), graph_neighborhood (the picture).
5. app/generation.py: prompt rules, numbered passages mapped back to real chunk IDs, "insufficient evidence".
6. app/extraction.py: allowed relation types, evidence must appear in the paragraph, tolerant parsing.
7. scripts/run_eval.py and scripts/compare.py: what is measured, dev vs test, the control.
8. app/main.py and static/index.html: the API endpoints (/query, /graph, /health, /documents), input validation, rate limits, how the page shows evidence.
9. tests/: what each test protects.

## Questions the examiners will likely ask (short answers)
- What problem does GraphRAG solve? Chain questions need paragraphs that do not sound like the question. The graph follows links to them.
- Did it work? Hybrid found all needed evidence for 28 of 35 questions, vs 26 for the control (vector, 8 paragraphs) and 21 for the baseline (5 paragraphs). F1 was 0.61 to 0.67 vs 0.58. The sample is small, so the direction is consistent but not proven.
- Why a control with 8 paragraphs? Hybrid sends up to 8 paragraphs. More text alone helps (baseline EM 0.37 to control 0.43), so the control shows what the graph adds.
- Why dev and test? Settings are chosen on dev; test is used once for final numbers. Depth 2 was chosen on dev. Depth 1 scored higher on test, but we did not switch after seeing it.
- How do you stop the model inventing graph facts? Each relation needs an evidence sentence found word for word in the paragraph, a fixed list of relation types, and both ends listed as entities. Anything else is dropped. It can still be wrong or incomplete.
- Why merge names so carefully? A wrong merge creates false facts; a missed merge only loses some links. 2570 raw names became 2556 entities.
- When does the graph hurt? It can add unrelated paragraphs (the Raffaella Reggi vs Lucie Hradecka question), and when it adds nothing hybrid has 5 paragraphs vs 8 for the control. Depth 2 lowered scores on the 6 comparison questions.
- How are citations validated? The model cites passage numbers; the code maps them to real chunk IDs and drops invalid numbers.
- What did it cost? Extraction about 0.21 USD once for 500 paragraphs (3 failed). Query cost stayed under one cent per 35 questions.
- Why Neo4j? One database holds the graph, the text, and the vector index.
- How do you protect the public demo and your API credits? Input length limit, 10 requests per 10 minutes per visitor, 200 per day overall, keys only in environment variables.
- What would you do next? Fill empty graph slots with extra vector results, test on more questions, add reranking, scale beyond 500 paragraphs.

## Limitations (say them before they ask)
Small test set (35), small corpus (500 paragraphs), LLM extraction can be wrong, many candidate
relations were dropped for missing evidence, conservative merging leaves duplicates,
the free hosting sleeps when idle.

## Glossary
- Embedding: a list of numbers that captures meaning.
- Cosine similarity: how close two embeddings point (1 = same direction).
- Entity: a thing (person, place, work). Relation: an arrow between two entities.
- Triple: subject, relation, object.
- Hop: one step along an arrow.
- Evidence recall: share of the needed paragraphs that were retrieved.
- EM (Exact Match): answer equals the gold answer after cleaning.
- F1: partial credit for word overlap.
