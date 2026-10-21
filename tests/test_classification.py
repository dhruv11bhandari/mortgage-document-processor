from backend.app.classification import classify_text, score_text


def test_classifies_common_mortgage_documents():
    assert classify_text("Uniform Residential Loan Application Form 1003")[0] == "1003_form"
    assert classify_text("Bank Statement Beginning Balance Ending Balance")[0] == "bank_stmt"
    assert classify_text("Employee W-2 Wage and Tax Statement")[0] == "w2"


def test_unknown_text_is_not_forced_into_a_category():
    assert classify_text("A page with unrelated correspondence")[0] == "unknown"


def test_scores_cover_all_supported_types():
    assert set(score_text("FICO credit score report")) == {
        "1003_form", "bank_stmt", "pay_stub", "w2", "tax_1040", "credit_report", "appraisal", "title"
    }
