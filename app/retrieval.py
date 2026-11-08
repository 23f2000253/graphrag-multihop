import re
import unicodedata

from app.common import INDEX_NAME, embed_texts
from app.resolution import normalize_key

VECTOR_QUERY = """
CALL db.index.vector.queryNodes($index, $k, $qvec) YIELD node, score
RETURN node.chunk_id AS chunk_id, node.doc_id AS doc_id,
       node.title AS title, node.text AS text, score
ORDER BY score DESC
"""

_ENTITY_INDEX = None


def vector_search(question, k, driver):
    qvec = embed_texts([question])[0]
    records, _, _ = driver.execute_query(
        VECTOR_QUERY, index=INDEX_NAME, k=k, qvec=qvec
    )
    rows = [r.data() for r in records]
    for row in rows:
        row["via"] = "vector"
    return rows


def _plain(text):
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().replace("&", " and ")
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", text).split())


def _entity_index(driver):
    """Map normalized entity name -> entity ids (built once, from all aliases)."""
    global _ENTITY_INDEX
    if _ENTITY_INDEX is None:
        records, _, _ = driver.execute_query(
            "MATCH (e:Entity) UNWIND e.aliases AS alias "
            "RETURN e.entity_id AS id, alias")
        index = {}
        for r in records:
            key = normalize_key(r["alias"])
            if len(key) >= 4:
                index.setdefault(key, set()).add(r["id"])
        _ENTITY_INDEX = index
    return _ENTITY_INDEX


def question_entities(question, driver, limit=6):
    """Entities whose name appears in the question (longest names win)."""
    padded = f" {_plain(question)} "
    index = _entity_index(driver)
    matched = sorted((key for key in index if f" {key} " in padded), key=len, reverse=True)
    chosen = []
    for key in matched:
        if not any(key in longer for longer in chosen):
            chosen.append(key)
    ids = []
    for key in chosen[:limit]:
        ids.extend(index[key])
    return ids


def _graph_candidates(seed_ids, qvec, exclude_ids, depth, limit, driver, max_degree=12):
    if not seed_ids:
        return []
    depth = max(1, min(int(depth), 3))
    query = f"""
    MATCH (seed:Entity) WHERE seed.entity_id IN $seed_ids
    MATCH p = (seed)-[:RELATION*0..{depth}]-(n:Entity)
    WHERE all(x IN nodes(p)[1..] WHERE COUNT {{ (x)-[:RELATION]-() }} <= $max_degree)
    WITH DISTINCT n
    MATCH (c:Chunk)-[:ABOUT]->(n)
    WHERE NOT c.chunk_id IN $exclude
    RETURN DISTINCT c.chunk_id AS chunk_id, c.doc_id AS doc_id, c.title AS title,
           c.text AS text, vector.similarity.cosine(c.embedding, $qvec) AS score
    ORDER BY score DESC LIMIT $limit
    """
    records, _, _ = driver.execute_query(
        query, seed_ids=list(seed_ids), qvec=qvec, exclude=list(exclude_ids),
        limit=limit, max_degree=max_degree)
    rows = [r.data() for r in records]
    for row in rows:
        row["via"] = "graph"
    return rows


def graph_search(question, k, driver, depth=2, max_graph=None):
    """Graph only: paragraphs about entities in the question and their neighbours."""
    qvec = embed_texts([question])[0]
    seeds = set(question_entities(question, driver))
    return _graph_candidates(seeds, qvec, set(), depth, k, driver)


def hybrid_search(question, k, driver, depth=2, max_graph=3):
    """Vector top-k first, then up to max_graph extra paragraphs found through the graph."""
    hits = vector_search(question, k, driver)
    qvec = embed_texts([question])[0]
    seeds = set(question_entities(question, driver))
    top_ids = [h["chunk_id"] for h in hits[:2]]
    records, _, _ = driver.execute_query(
        "MATCH (c:Chunk)-[:ABOUT]->(e:Entity) WHERE c.chunk_id IN $ids "
        "RETURN e.entity_id AS id", ids=top_ids)
    seeds.update(r["id"] for r in records)
    extra = _graph_candidates(seeds, qvec, {h["chunk_id"] for h in hits},
                              depth, max_graph, driver)
    return hits + extra
