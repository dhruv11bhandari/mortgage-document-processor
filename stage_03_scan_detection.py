# Stage 3 - Scanned vs Digital Detection


def detect_page_type(page):
    text = page["raw_text"].strip()

    if len(text) > 50:
        return "digital"

    return "scanned"


def classify_all_pages(pages):
    for page in pages:
        page["type"] = detect_page_type(page)

    return pages
