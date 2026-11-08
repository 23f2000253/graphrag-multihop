import json

from app.common import get_driver
from app.resolution import entity_id, normalize_key

with open("data/processed/chunks.jsonl", encoding="utf-8") as f:
    chunks = [json.loads(line) for line in f]

rows = [
    {"chunk_id": c["chunk_id"], "title": c["title"],
     "entity_id": entity_id(normalize_key(c["title"]))}
    for c in chunks
]

with get_driver() as driver:
    driver.execute_query(
        "UNWIND $rows AS row "
        "MERGE (e:Entity {entity_id: row.entity_id}) "
        "ON CREATE SET e.name = row.title, e.type = 'OTHER', e.aliases = [row.title] "
        "WITH row, e "
        "MATCH (c:Chunk {chunk_id: row.chunk_id}) "
        "MERGE (c)-[:ABOUT]->(e)", rows=rows)
    for label, q in [
        ("ABOUT links", "MATCH ()-[a:ABOUT]->() RETURN count(a)"),
        ("Entity nodes", "MATCH (e:Entity) RETURN count(e)"),
    ]:
        records, _, _ = driver.execute_query(q)
        print(label + ":", records[0][0])
