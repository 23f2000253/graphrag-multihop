import json
import time

from app.common import get_driver, embed_texts

with open("data/processed/chunks.jsonl", encoding="utf-8") as f:
    chunks = [json.loads(line) for line in f]

start = time.time()
vectors = embed_texts([c["text"] for c in chunks])
print(f"Embedded {len(chunks)} chunks in {time.time() - start:.1f}s")

rows = [
    {"chunk_id": c["chunk_id"], "doc_id": c["doc_id"], "title": c["title"],
     "text": c["text"], "embedding": v}
    for c, v in zip(chunks, vectors)
]

with get_driver() as driver:
    driver.execute_query(
        "CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS "
        "FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE"
    )
    driver.execute_query(
        "CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS "
        "FOR (c:Chunk) ON (c.embedding) "
        "OPTIONS {indexConfig: {`vector.dimensions`: 384, "
        "`vector.similarity_function`: 'cosine'}}"
    )
    for i in range(0, len(rows), 100):
        driver.execute_query(
            "UNWIND $rows AS row "
            "MERGE (c:Chunk {chunk_id: row.chunk_id}) "
            "SET c.doc_id = row.doc_id, c.title = row.title, "
            "c.text = row.text, c.embedding = row.embedding",
            rows=rows[i:i + 100],
        )
    records, _, _ = driver.execute_query("MATCH (c:Chunk) RETURN count(c) AS n")
    print("Chunk nodes in Neo4j:", records[0]["n"])
