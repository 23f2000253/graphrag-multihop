import logging
import os
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.common import embed_texts, get_driver
from app.generation import generate_answer
from app.retrieval import graph_neighborhood, hybrid_search, vector_search

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("graphrag")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
PER_IP_LIMIT = int(os.getenv("PER_IP_LIMIT", "10"))
WINDOW_SECONDS = int(os.getenv("WINDOW_SECONDS", "600"))
DAILY_LIMIT = int(os.getenv("DAILY_LIMIT", "200"))

_recent = defaultdict(deque)
_daily = {"day": None, "count": 0}


def client_ip(request):
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_rate_limit(ip):
    now = time.time()
    today = time.strftime("%Y-%m-%d")
    if _daily["day"] != today:
        _daily["day"], _daily["count"] = today, 0
    if _daily["count"] >= DAILY_LIMIT:
        raise HTTPException(429, "The daily demo limit has been reached. Please try again tomorrow.")
    recent = _recent[ip]
    while recent and now - recent[0] > WINDOW_SECONDS:
        recent.popleft()
    if len(recent) >= PER_IP_LIMIT:
        raise HTTPException(429, "Too many requests. Please wait a few minutes and try again.")
    recent.append(now)
    _daily["count"] += 1


class QueryRequest(BaseModel):
    question: str = Field(min_length=5, max_length=300)
    strategy: Literal["vector", "hybrid"] = "hybrid"


class Evidence(BaseModel):
    chunk_id: str
    title: str
    text: str
    score: float
    via: str
    cited: bool


class QueryResponse(BaseModel):
    strategy: str
    answer: str
    evidence: list[Evidence]
    retrieval_ms: int
    generation_ms: int
    input_tokens: int
    output_tokens: int


@asynccontextmanager
async def lifespan(app):
    app.state.driver = get_driver()
    try:
        app.state.driver.verify_connectivity()
    except Exception:
        logger.exception("Neo4j is not reachable at startup")
    embed_texts(["warm up"])
    yield
    app.state.driver.close()


app = FastAPI(title="GraphRAG demo", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    try:
        app.state.driver.verify_connectivity()
    except Exception:
        raise HTTPException(503, "Database unavailable")
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query(body: QueryRequest, request: Request):
    check_rate_limit(client_ip(request))
    driver = app.state.driver
    try:
        t0 = time.perf_counter()
        if body.strategy == "vector":
            hits = vector_search(body.question, 8, driver)
        else:
            hits = hybrid_search(body.question, 5, driver, depth=2, max_graph=3)
        t1 = time.perf_counter()
        gen = generate_answer(body.question, hits)
        t2 = time.perf_counter()
    except Exception:
        logger.exception("query failed")
        raise HTTPException(502, "Something went wrong while answering. Please try again.")
    cited = set(gen["citations"])
    return QueryResponse(
        strategy=body.strategy,
        answer=gen["answer"],
        evidence=[Evidence(chunk_id=h["chunk_id"], title=h["title"], text=h["text"],
                           score=round(h["score"], 4), via=h["via"],
                           cited=h["chunk_id"] in cited) for h in hits],
        retrieval_ms=int((t1 - t0) * 1000),
        generation_ms=int((t2 - t1) * 1000),
        input_tokens=gen["input_tokens"],
        output_tokens=gen["output_tokens"],
    )


@app.get("/documents/{chunk_id}")
def get_document(chunk_id: str):
    records, _, _ = app.state.driver.execute_query(
        "MATCH (c:Chunk {chunk_id: $id}) "
        "RETURN c.chunk_id AS chunk_id, c.doc_id AS doc_id, c.title AS title, c.text AS text",
        id=chunk_id)
    if not records:
        raise HTTPException(404, "Document not found")
    return records[0].data()


class GraphNode(BaseModel):
    id: str
    name: str
    ring: int


class GraphEdge(BaseModel):
    source: str
    target: str
    predicate: str
    evidence: str | None = None


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


@app.post("/graph", response_model=GraphResponse)
def graph(body: QueryRequest):
    try:
        data = graph_neighborhood(body.question, app.state.driver)
    except Exception:
        logger.exception("graph view failed")
        raise HTTPException(502, "Could not build the graph view.")
    return GraphResponse(nodes=data["nodes"], edges=data["edges"])
