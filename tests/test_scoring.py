from vlm_bench.scoring import normalize_answer, score_prediction


def test_normalize_answer() -> None:
    assert normalize_answer("  The Red-Car! ") == "the redcar"


def test_binary_uses_first_token() -> None:
    result = score_prediction("Yes, because it is visible.", ["yes"], "binary")
    assert result["correct"] is True


def test_integer_extracts_first_number() -> None:
    result = score_prediction("There are 12 objects.", ["12"], "integer")
    assert result["correct"] is True


def test_short_text_allows_bounded_containment() -> None:
    result = score_prediction("The sign says OPEN now", ["open"], "short_text")
    assert result["correct"] is True
