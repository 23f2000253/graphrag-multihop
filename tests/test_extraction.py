from app.extraction import Entity, Extraction, Relation, clean, parse_tolerant
from app.generation import parse_reply


def _extraction(evidence, obj="Paris"):
    return Extraction(
        entities=[Entity(name="Alice", type="PERSON"), Entity(name="Paris", type="LOCATION")],
        relations=[Relation(subject="Alice", predicate="BORN_IN", object=obj, evidence=evidence)],
    )


def test_relation_with_unsupported_evidence_is_dropped():
    kept, bad_evidence, bad_endpoint = clean(_extraction("Alice was born in London."),
                                              "Alice was born in Paris.")
    assert kept == [] and bad_evidence == 1 and bad_endpoint == 0


def test_relation_with_supported_evidence_is_kept():
    kept, bad_evidence, _ = clean(_extraction("Alice was born in Paris."),
                                  "Alice was born in Paris. She likes tea.")
    assert len(kept) == 1 and bad_evidence == 0


def test_relation_with_unlisted_endpoint_is_dropped():
    kept, _, bad_endpoint = clean(_extraction("Alice moved to Rome.", obj="Rome"),
                                  "Alice moved to Rome.")
    assert kept == [] and bad_endpoint == 1


def test_parse_tolerant_drops_only_the_invalid_item():
    raw = ('{"entities": [{"name": "A", "type": "PERSON"}], '
           '"relations": [{"subject": "A", "predicate": "BORN_IN", "object": "B"}]}')
    extraction, invalid = parse_tolerant(raw)
    assert len(extraction.entities) == 1 and extraction.relations == [] and invalid == 1


def test_parse_reply_maps_citation_numbers_to_chunk_ids():
    passages = [{"chunk_id": "c1"}, {"chunk_id": "c2"}]
    answer, citations = parse_reply('{"answer": "X", "citations": [1, 9]}', passages)
    assert answer == "X" and citations == ["c1"]
