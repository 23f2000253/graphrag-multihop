import os
from functools import lru_cache

from dotenv import load_dotenv
from fastembed import TextEmbedding
from neo4j import GraphDatabase

load_dotenv()

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_CACHE = "data/models"
EMBED_DIM = 384
INDEX_NAME = "chunk_embeddings"


def get_driver():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    if not (uri and user and password):
        raise RuntimeError("Missing NEO4J_URI, NEO4J_USER or NEO4J_PASSWORD in .env")
    return GraphDatabase.driver(uri, auth=(user, password))


@lru_cache(maxsize=1)
def get_embedder():
    return TextEmbedding(model_name=MODEL_NAME, cache_dir=MODEL_CACHE)


def embed_texts(texts):
    return [vec.tolist() for vec in get_embedder().embed(texts)]
