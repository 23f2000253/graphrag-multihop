from app.resolution import entity_id, normalize_key


def test_company_suffix_and_case_are_ignored():
    assert normalize_key("VIVA Media AG") == normalize_key("viva media")


def test_leading_the_and_accents_removed():
    assert normalize_key("The Beatles") == "beatles"
    assert normalize_key("Café") == "cafe"


def test_similar_but_different_names_are_not_merged():
    assert normalize_key("Viva") != normalize_key("VIVA Media")


def test_single_token_suffix_is_kept():
    assert normalize_key("AG") == "ag"


def test_entity_id_is_stable():
    assert entity_id("viva media") == entity_id("viva media")
    assert entity_id("viva media") != entity_id("viva")
