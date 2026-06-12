import re
KEYWORDS = {
    "1003_form":     ["Uniform Residential Loan Application", "1003"],
    "bank_stmt":     ["Beginning Balance", "Ending Balance", "Statement Period"],
    "pay_stub":      ["Pay Period", "Year to Date", "Net Pay"],
    "w2":            ["W-2 Wage and Tax Statement"],
    "tax_1040":      ["Form 1040", "U.S. Individual Income Tax"],
    "credit_report": ["FICO", "Credit Score", "Tradeline"],
    "appraisal":     ["Appraised Value", "Subject Property"],
    "title":         ["Title Insurance", "Deed of Trust"],
}
def extract_features(page):
    text = page["raw_text"]

    scores = {}
    for doc_type, keywords in KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw.lower() in text.lower())
        scores[doc_type] = hits / len(keywords)

    page["keyword_scores"] = scores
    return page
