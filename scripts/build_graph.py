import json
from collections import Counter

from app.common import get_driver
from app.resolution import entity_id, normalize_key

with open("data/processed/extractions.jsonl", encoding="utf-8") as f:
    extractions = [json.loads(line) for line in f]

entities = {}
mentions = set()
relations = {}
raw_names = set()
for ex in extractions:
    cid = ex["chunk_id"]
    for e in ex["entities"]:
        raw_names.add(e["name"])
        eid = entity_id(normalize_key(e["name"]))
        ent = entities.setdefault(eid, {"names": Counter(), "types": Counter()})
        ent["names"][e["name"]] += 1
        ent["types"][e["type"]] += 1
        mentions.add((cid, eid))
    for r in ex["relations"]:
        s = entity_id(normalize_key(r["subject"]))
        o = entity_id(normalize_key(r["object"]))
        if s in entities and o in entities and s != o:
            relations[(s, r["predicate"], o, cid)] = r["evidence"]

entity_rows = []
for eid, ent in entities.items():
    types = [t for t, _ in ent["types"].most_common() if t != "OTHER"]
    entity_rows.append({
        "entity_id": eid,
        "name": ent["names"].most_common(1)[0][0],
        "type": types[0] if types else "OTHER",
        "aliases": sorted(ent["names"]),
    })
mention_rows = [{"chunk_id": c, "entity_id": e} for c, e in mentions]
relation_rows = [
    {"s": s, "predicate": p, "o": o, "chunk_id": c, "evidence": ev}
    for (s, p, o, c), ev in relations.items()
]
print(f"Raw entity names: {len(raw_names)} -> resolved entities: {len(entity_rows)}")
print(f"Mentions: {len(mention_rows)}, relations: {len(relation_rows)}")


def batches(rows, size=500):
    for i in range(0, len(rows), size):
        yield rows[i:i + size]


with get_driver() as driver:
    driver.execute_query(
        "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS "
        "FOR (e:Entity) REQUIRE e.entity_id IS UNIQUE"
    )
    for b in batches(entity_rows):
        driver.execute_query(
            "UNWIND $rows AS row MERGE (e:Entity {entity_id: row.entity_id}) "
            "SET e.name = row.name, e.type = row.type, e.aliases = row.aliases", rows=b)
    for b in batches(mention_rows):
        driver.execute_query(
            "UNWIND $rows AS row "
            "MATCH (c:Chunk {chunk_id: row.chunk_id}) "
            "MATCH (e:Entity {entity_id: row.entity_id}) "
            "MERGE (c)-[:MENTIONS]->(e)", rows=b)
    for b in batches(relation_rows):
        driver.execute_query(
            "UNWIND $rows AS row "
            "MATCH (s:Entity {entity_id: row.s}) MATCH (o:Entity {entity_id: row.o}) "
            "MERGE (s)-[r:RELATION {predicate: row.predicate, chunk_id: row.chunk_id}]->(o) "
            "SET r.evidence = row.evidence", rows=b)

    def one(query):
        records, _, _ = driver.execute_query(query)
        return records[0][0]

    print("\n--- Graph statistics ---")
    print("Chunk nodes:", one("MATCH (c:Chunk) RETURN count(c)"))
    print("Entity nodes:", one("MATCH (e:Entity) RETURN count(e)"))
    print("MENTIONS:", one("MATCH ()-[m:MENTIONS]->() RETURN count(m)"))
    print("RELATION arrows:", one("MATCH ()-[r:RELATION]->() RETURN count(r)"))
    print("Entities mentioned in 2+ paragraphs:", one(
        "MATCH (e:Entity)<-[:MENTIONS]-(c:Chunk) "
        "WITH e, count(DISTINCT c) AS n WHERE n > 1 RETURN count(e)"))
    print("2-step paths whose two arrows come from DIFFERENT paragraphs:", one(
        "MATCH (a:Entity)-[r1:RELATION]->(b:Entity)-[r2:RELATION]->(c:Entity) "
        "WHERE r1.chunk_id <> r2.chunk_id AND a <> c RETURN count(*)"))
    print("\nExample cross-paragraph paths:")
    records, _, _ = driver.execute_query(
        "MATCH (a:Entity)-[r1:RELATION]->(b:Entity)-[r2:RELATION]->(c:Entity) "
        "WHERE r1.chunk_id <> r2.chunk_id AND a <> c "
        "RETURN a.name AS a, r1.predicate AS p1, b.name AS b, "
        "r2.predicate AS p2, c.name AS c LIMIT 5")
    for r in records:
        print(f"  {r['a']} -[{r['p1']}]-> {r['b']} -[{r['p2']}]-> {r['c']}")
