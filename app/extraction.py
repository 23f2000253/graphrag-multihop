import json
import re
from typing import Literal

from anthropic import Anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from app.generation import MODEL

load_dotenv()

EntityType = Literal["PERSON", "ORGANIZATION", "LOCATION", "WORK", "EVENT", "OTHER"]
RelationType = Literal[
    "BORN_IN", "DIED_IN", "LOCATED_IN", "PART_OF", "DIRECTED_BY", "STARRED_IN",
    "CREATED_BY", "MEMBER_OF", "FOUNDED_BY", "OWNED_BY", "EMPLOYED_BY", "RELATED_TO",
]


class Entity(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: EntityType


class Relation(BaseModel):
    subject: str = Field(min_length=1, max_length=120)
    predicate: RelationType
    object: str = Field(min_length=1, max_length=120)
    evidence: str = Field(min_length=1, max_length=600)


class Extraction(BaseModel):
    entities: list[Entity] = []
    relations: list[Relation] = []


SYSTEM_PROMPT = """You extract a knowledge graph from one Wikipedia passage.
Return JSON only, in exactly this shape:
{"entities": [{"name": "...", "type": "..."}], "relations": [{"subject": "...", "predicate": "...", "object": "...", "evidence": "..."}]}

Entity types: PERSON, ORGANIZATION, LOCATION, WORK, EVENT, OTHER. (WORK = film, book, album, song, TV show, game.)
Relation types: BORN_IN, DIED_IN, LOCATED_IN, PART_OF, DIRECTED_BY, STARRED_IN, CREATED_BY, MEMBER_OF, FOUNDED_BY, OWNED_BY, EMPLOYED_BY, RELATED_TO.

Rules:
- Only extract facts the passage states explicitly. Do not use outside knowledge.
- Two things appearing in the same sentence is NOT a relation. Extract a relation only if the sentence states it.
- "evidence" must be copied word for word from the passage (one sentence or part of one).
- Use full names. Replace pronouns (he, she, it, the company) with the entity they refer to. The passage is usually about the title entity.
- Every subject and object must also appear in the entities list with exactly the same spelling.
- Use RELATED_TO only if the passage explicitly states a direct relationship that no other type fits.
- Direction examples: Film DIRECTED_BY Person; Actor STARRED_IN Film; Person BORN_IN Location; Song CREATED_BY Person; Person MEMBER_OF Organization; Company OWNED_BY Company.
- If nothing can be extracted, return empty lists."""

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = Anthropic()
    return _client


def _norm(text):
    return " ".join(text.lower().split())


def clean(extraction, passage_text):
    """Keep only relations whose evidence is in the passage and whose ends are listed entities."""
    text_n = _norm(passage_text)
    names = {_norm(e.name) for e in extraction.entities}
    kept, bad_evidence, bad_endpoint = [], 0, 0
    for r in extraction.relations:
        if _norm(r.evidence) not in text_n:
            bad_evidence += 1
        elif _norm(r.subject) not in names or _norm(r.object) not in names:
            bad_endpoint += 1
        elif _norm(r.subject) != _norm(r.object):
            kept.append(r)
    return kept, bad_evidence, bad_endpoint


def parse_tolerant(raw_json):
    """Validate entities and relations one by one; drop only the invalid items."""
    data = json.loads(raw_json)
    entities, relations, invalid = [], [], 0
    for item in data.get("entities", []):
        try:
            entities.append(Entity.model_validate(item))
        except Exception:
            invalid += 1
    for item in data.get("relations", []):
        try:
            relations.append(Relation.model_validate(item))
        except Exception:
            invalid += 1
    return Extraction(entities=entities, relations=relations), invalid


def extract_chunk(chunk):
    result = {"chunk_id": chunk["chunk_id"], "title": chunk["title"], "entities": [],
              "relations": [], "dropped_invalid": 0, "dropped_bad_evidence": 0, "dropped_bad_endpoint": 0,
              "input_tokens": 0, "output_tokens": 0, "error": None}
    try:
        response = _get_client().messages.create(
            model=MODEL,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content":
                       f"Passage title: {chunk['title']}\nPassage:\n{chunk['text']}"}],
        )
        result["input_tokens"] = response.usage.input_tokens
        result["output_tokens"] = response.usage.output_tokens
        text = "".join(b.text for b in response.content if b.type == "text")
        match = re.search(r"\{.*\}", text, re.S)
        extraction, invalid = parse_tolerant(match.group(0))
        kept, bad_ev, bad_end = clean(extraction, chunk["text"])
        result["entities"] = [e.model_dump() for e in extraction.entities]
        result["relations"] = [r.model_dump() for r in kept]
        result["dropped_bad_evidence"] = bad_ev
        result["dropped_bad_endpoint"] = bad_end
        result["dropped_invalid"] = invalid
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
    return result
