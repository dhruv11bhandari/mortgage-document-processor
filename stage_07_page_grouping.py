# Stage 7 - Page Grouping

import hashlib
from collections import defaultdict


def get_hash(text):
    return hashlib.md5(text.encode()).hexdigest()


def group_pages(pages):
    buckets = defaultdict(list)

    for page in pages:
        buckets[page["doc_type"]].append(page)

    grouped = {}

    for doc_type, doc_pages in buckets.items():
        seen = {}
        unique = []

        for page in doc_pages:
            h = get_hash(page["raw_text"])

            if h in seen:
                page["is_duplicate"] = True
            else:
                seen[h] = page["page_number"]
                page["is_duplicate"] = False
                unique.append(page)

        grouped[doc_type] = unique

    return grouped
