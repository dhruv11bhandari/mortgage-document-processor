"""Transparent, deterministic page classification for common mortgage documents."""
from __future__ import annotations

KEYWORDS = {
    "1003_form": ("uniform residential loan application", "form 1003", "loan application"),
    "bank_stmt": ("bank statement", "beginning balance", "ending balance", "statement period", "checking account"),
    "pay_stub": ("pay stub", "pay period", "year to date", "net pay", "gross pay"),
    "w2": ("w-2 wage and tax statement", "wage and tax statement", "form w-2"),
    "tax_1040": ("form 1040", "u.s. individual income tax return", "1040-sr"),
    "credit_report": ("credit report", "fico score", "credit score", "tradeline"),
    "appraisal": ("appraisal report", "appraised value", "subject property"),
    "title": ("title insurance", "commitment for title", "deed of trust"),
}


def score_text(text: str) -> dict[str, float]:
    normalized = (text or "").casefold()
    return {kind: sum(term in normalized for term in terms) / len(terms) for kind, terms in KEYWORDS.items()}


def classify_text(text: str, minimum_confidence: float = 0.30) -> tuple[str, float]:
    """Return the strongest keyword match, or unknown when evidence is weak."""
    scores = score_text(text)
    kind, score = max(scores.items(), key=lambda item: item[1])
    if score < minimum_confidence or score == 0:
        return "unknown", score
    return kind, score
