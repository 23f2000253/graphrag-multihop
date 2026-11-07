import hashlib
import re
import unicodedata

COMPANY_SUFFIXES = {
    "ag", "inc", "ltd", "llc", "gmbh", "co", "corp", "corporation",
    "plc", "sa", "company", "limited",
}


def normalize_key(name):
    """Safe normalization: same key means 'treat as the same entity'."""
    text = unicodedata.normalize("NFKD", name)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    tokens = text.split()
    if tokens and tokens[0] == "the":
        tokens = tokens[1:]
    while len(tokens) > 1 and tokens[-1] in COMPANY_SUFFIXES:
        tokens = tokens[:-1]
    key = " ".join(tokens)
    return key or name.strip().lower()


def entity_id(key):
    return "ent_" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
