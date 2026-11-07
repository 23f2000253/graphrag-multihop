import re
import string
from collections import Counter


def normalize_answer(text):
    text = text.lower()
    text = "".join(ch for ch in text if ch not in set(string.punctuation))
    text = re.sub(r"\b(a|an|the)\b", " ", text)
    return " ".join(text.split())


def exact_match(prediction, gold):
    return float(normalize_answer(prediction) == normalize_answer(gold))


def f1_score(prediction, gold):
    pred = normalize_answer(prediction)
    true = normalize_answer(gold)
    special = {"yes", "no", "noanswer"}
    if (pred in special or true in special) and pred != true:
        return 0.0
    pred_tokens, true_tokens = pred.split(), true.split()
    overlap = sum((Counter(pred_tokens) & Counter(true_tokens)).values())
    if overlap == 0:
        return 0.0
    precision = overlap / len(pred_tokens)
    recall = overlap / len(true_tokens)
    return 2 * precision * recall / (precision + recall)
