from app.common import INDEX_NAME, embed_texts

VECTOR_QUERY = """
CALL db.index.vector.queryNodes($index, $k, $qvec) YIELD node, score
RETURN node.chunk_id AS chunk_id, node.doc_id AS doc_id,
       node.title AS title, node.text AS text, score
ORDER BY score DESC
"""


def vector_search(question, k, driver):
    qvec = embed_texts([question])[0]
    records, _, _ = driver.execute_query(
        VECTOR_QUERY, index=INDEX_NAME, k=k, qvec=qvec
    )
    return [r.data() for r in records]
