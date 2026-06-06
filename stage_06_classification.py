def embedding_classify(text):
    text = text.lower()
    if "bank statement" in text:
        return {
            "doc_type": "bank_stmt",
            "confidence": 0.82
        }
    elif "w-2" in text or "tax statement" in text:
        return {
            "doc_type": "w2",
            "confidence": 0.78
        }
    elif "pay period" in text or "net pay" in text:
        return {
            "doc_type": "pay_stub",
            "confidence": 0.76
        }
    elif "credit score" in text or "fico" in text:
        return {
            "doc_type": "credit_report",
            "confidence": 0.80
        }
    else:
        return {
            "doc_type": "unknown",
            "confidence": 0.50
        }
def llm_classify(text):
    # Replace later with OpenAI/Claude API
    return {
        "doc_type": "unknown"
    }
def classify_page(page):
    scores = page["keyword_scores"]
    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]
    if best_score >= 0.85:
        return best_type, "rule"
    result = embedding_classify(page["raw_text"])
    if result["confidence"] >= 0.70:
        return result["doc_type"], "embedding"
    result = llm_classify(page["raw_text"])
    return result["doc_type"], "llm"
def classify_all(pages):
    for page in pages:
        doc_type, method = classify_page(page)
        page["doc_type"] = doc_type
        page["classified_by"] = method
    return pages
pages = [
    {
        "raw_text": "This is a Bank Statement for January 2025",
        "keyword_scores": {
            "bank_stmt": 0.90,
            "w2": 0.20,
            "pay_stub": 0.10
        }
    },
    {
        "raw_text": "Employee W-2 Wage and Tax Statement",
        "keyword_scores": {
            "bank_stmt": 0.30,
            "w2": 0.60,
            "pay_stub": 0.20
        }
    },
    {
        "raw_text": "FICO credit score report document",
        "keyword_scores": {
            "bank_stmt": 0.10,
            "w2": 0.20,
            "credit_report": 0.50
        }
    }

]
classified_pages = classify_all(pages)
for page in classified_pages:
    print("TEXT:", page["raw_text"])
    print("DOCUMENT TYPE:", page["doc_type"])
    print("CLASSIFIED BY:", page["classified_by"])
    print("-" * 50)

    