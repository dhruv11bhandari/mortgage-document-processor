from mortgage_processor.processing import _page_sequence


def test_page_sequence_recognizes_common_labels():
    assert _page_sequence("Page 2 of 8") == 2
    assert _page_sequence("PAGE 3/9") == 3
    assert _page_sequence("Page one") is None


def test_process_pdf_creates_grouped_pdf_and_manifest(tmp_path):
    import pymupdf as fitz
    import json
    from mortgage_processor.processing import process_pdf

    source = tmp_path / "sample.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Bank Statement Beginning Balance Ending Balance Statement Period")
    doc.save(source)
    doc.close()

    result = process_pdf(source, tmp_path / "output", "12345678-1234-1234-1234-123456789abc")
    out = tmp_path / "output" / result["job_id"]
    assert result["status"] == "completed"
    assert result["documents"][0]["type"] == "bank_stmt"
    assert (out / "bank_stmt.pdf").is_file()
    assert json.loads((out / "manifest.json").read_text())["page_count"] == 1
