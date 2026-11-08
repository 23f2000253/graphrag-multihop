from app.metrics import exact_match, f1_score, normalize_answer


def test_normalize_removes_case_punctuation_articles():
    assert normalize_answer("The Quick, Brown Fox!") == "quick brown fox"


def test_exact_match_ignores_case_and_articles():
    assert exact_match("The Beatles", "beatles") == 1.0


def test_exact_match_different_answers():
    assert exact_match("Paris", "London") == 0.0


def test_f1_partial_overlap():
    score = f1_score("mit beschränkter Haftung", "Gesellschaft mit beschränkter Haftung")
    assert abs(score - 6 / 7) < 1e-9


def test_f1_yes_no_mismatch_is_zero():
    assert f1_score("yes", "no") == 0.0


def test_f1_no_overlap_is_zero():
    assert f1_score("apple", "orange") == 0.0
