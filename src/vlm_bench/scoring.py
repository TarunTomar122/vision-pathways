import re
import string
from typing import Iterable


_WHITESPACE = re.compile(r"\s+")


def normalize_answer(value: object) -> str:
    """Normalize short benchmark answers without changing their semantic content."""
    text = str(value).strip().lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return _WHITESPACE.sub(" ", text).strip()


def first_binary_token(value: object) -> str:
    normalized = normalize_answer(value)
    tokens = normalized.split()
    if not tokens:
        return ""
    if tokens[0] in {"yes", "true"}:
        return "yes"
    if tokens[0] in {"no", "false"}:
        return "no"
    return normalized


def first_integer(value: object) -> str:
    normalized = normalize_answer(value)
    match = re.search(r"(?<!\w)-?\d+(?!\w)", normalized)
    return match.group(0) if match else normalized


def score_prediction(prediction: object, answers: Iterable[object], answer_format: str) -> dict:
    normalized_answers = [normalize_answer(answer) for answer in answers]
    normalized_prediction = normalize_answer(prediction)

    if answer_format == "binary":
        normalized_prediction = first_binary_token(prediction)
        normalized_answers = [first_binary_token(answer) for answer in answers]
    elif answer_format == "integer":
        normalized_prediction = first_integer(prediction)
        normalized_answers = [first_integer(answer) for answer in answers]

    exact = normalized_prediction in normalized_answers
    contains = any(
        answer and re.search(rf"(?<!\w){re.escape(answer)}(?!\w)", normalized_prediction)
        for answer in normalized_answers
    )
    correct = contains if answer_format == "short_text" else exact
    return {
        "normalized_prediction": normalized_prediction,
        "normalized_answers": normalized_answers,
        "exact_match": exact,
        "contains_match": contains,
        "correct": bool(correct),
    }
