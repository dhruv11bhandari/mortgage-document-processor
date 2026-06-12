import re
def get_page_number(text):
    match = re.search(r"[Pp]age\s+(\d+)\s+of\s+\d+", text)
    if match:
        return int(match.group(1))
    return None


def order_document(pages):
    for page in pages:
        page["seq"] = get_page_number(page["raw_text"])

    has_seq = all(page["seq"] is not None for page in pages)

    if has_seq:
        return sorted(pages, key=lambda p: p["seq"])

    # Fallback: use original position in the PDF
    return sorted(pages, key=lambda p: p["page_number"])
