import json
import re

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-haiku-5-5"

SYSTEM_PROMPT = """You answer questions using ONLY the numbered passages provided.
Rules:
- Give the shortest possible answer (a few words: a name, date, place, number, or yes/no). No explanations.
- If the passages do not contain enough information, the answer must be exactly: insufficient evidence
- Reply with JSON only: {"answer": "<short answer>", "citations": [<numbers of the passages you used>]}"""

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = Anthropic()
    return _client


def build_user_message(question, passages):
    lines = [f"Question: {question}", "", "Passages:"]
    for i, p in enumerate(passages, start=1):
        lines.append(f"[{i}] {p['title']}: {p['text']}")
    return "\n".join(lines)


def parse_reply(text, passages):
    match = re.search(r"\{.*\}", text, re.S)
    try:
        data = json.loads(match.group(0))
        answer = str(data.get("answer", "")).strip()
        numbers = [n for n in data.get("citations", []) if isinstance(n, int)]
    except (AttributeError, ValueError, TypeError):
        return text.strip(), []
    citations = [passages[n - 1]["chunk_id"] for n in numbers if 1 <= n <= len(passages)]
    return answer, citations


def generate_answer(question, passages):
    response = _get_client().messages.create(
        model=MODEL,
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_user_message(question, passages)}],
    )
    text = "".join(b.text for b in response.content if b.type == "text")
    answer, citations = parse_reply(text, passages)
    return {
        "answer": answer,
        "citations": citations,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "stop_reason": response.stop_reason,
    }
