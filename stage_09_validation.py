RULES = {
    "1003_form":     {"min_pages": 4, "needs_signature": True},
    "bank_stmt":     {"min_pages": 3, "needs_signature": False},
    "w2":            {"min_pages": 1, "needs_signature": False},
    "pay_stub":      {"min_pages": 1, "needs_signature": False},
    "tax_1040":      {"min_pages": 2, "needs_signature": True},
    "credit_report": {"min_pages": 5, "needs_signature": False},
    "appraisal":     {"min_pages": 8, "needs_signature": True},
    "title":         {"min_pages": 2, "needs_signature": True},
}
def has_signature(pages):
    for page in pages:

        text = page["raw_text"].lower()

        if "signature" in text:
            return True

    return False

def validate(grouped):
    exceptions = []

    for doc_type, rules in RULES.items():
        if doc_type not in grouped:
            exceptions.append({"type": "MISSING_DOCUMENT", "doc": doc_type})
            continue

        pages = grouped[doc_type]

        if len(pages) < rules["min_pages"]:
            exceptions.append({
                "type": "MISSING_PAGES",
                "doc": doc_type,
                "found": len(pages),
                "expected": rules["min_pages"],
            })

        if rules["needs_signature"] and not has_signature(pages):
            exceptions.append({"type": "MISSING_SIGNATURE", "doc": doc_type})

    return exceptions
