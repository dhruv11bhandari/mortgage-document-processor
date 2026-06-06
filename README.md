# Mortgage Document Package Processor

An end-to-end pipeline for processing large, unstructured mortgage loan PDF packages
(up to 2,000 pages) into clean, validated, and structured outputs ready for downstream
decisioning systems.

Designed with an **LLM-last strategy** — 10 of 11 stages run entirely on free,
open-source tools. LLM API calls are reserved only for low-confidence edge cases
in classification (~5% of pages), keeping cost to ~$0.05 per package.

---

## Pipeline Overview

| Stage | Name                    | Objective                                         | LLM? | Cost  |
|-------|-------------------------|---------------------------------------------------|------|-------|
| 1     | PDF Upload              | Validate file, extract metadata, assign Job ID   | No   | Free  |
| 2     | Page Splitter           | Burst PDF into individual page images + text      | No   | Free  |
| 3     | Scanned vs Digital      | Classify each page: text-native or image-only    | No   | Free  |
| 4     | OCR Engine              | Extract text from scanned pages via Tesseract     | No   | Free  |
| 5     | Text + Layout Extraction| Parse keywords, tables, dates, dollar amounts     | No   | Free  |
| 6     | Document Classification | Identify doc type per page (3-tier hybrid)        | ~5%  | ~$0.05/pkg |
| 7     | Page Grouping           | Cluster pages into document instances             | No   | Free  |
| 8     | Ordering Engine         | Sort pages within each doc into correct sequence  | No   | Free  |
| 9     | Validation Engine       | Check for missing pages, signatures, doc types   | No   | Free  |
| 10    | Exception Reporting     | Flag anomalies with severity levels               | No   | Free  |
| 11    | Structured Output       | Emit JSON manifest + labelled PDFs                | No   | Free  |

---

## Classification Strategy (Stage 6)

Pages are classified in three tiers, cheapest first:

- **Tier 1 — Rule-Based** `(confidence ≥ 0.85)`: keyword scoring from Stage 5. Handles ~70% of pages.
- **Tier 2 — Embedding Similarity** `(confidence 0.70–0.85)`: local `sentence-transformers` + FAISS. Handles ~25%.
- **Tier 3 — LLM Fallback** `(confidence < 0.70)`: Claude / GPT-4o-mini with a short structured prompt. Handles ~5%.

---

## Document Types Supported

`1003_form` · `bank_stmt` · `pay_stub` · `w2` · `tax_1040` · `credit_report` · `appraisal` · `title`

---

## Output

For each processed package, the system produces:

output/{job_id}/
├── manifest.json ← structured doc inventory + exceptions
├── bank_stmt.pdf
├── w2.pdf
├── pay_stub.pdf
├── tax_1040.pdf
├── credit_report.pdf
├── appraisal.pdf
├── title.pdf
└── 1003_form.pdf

**`manifest.json` structure:**
```json
{
  "job_id": "uuid-here",
  "documents": [
    { "type": "bank_stmt", "pages": 4, "path": "output/.../bank_stmt.pdf" }
  ],
  "exceptions": [
    { "type": "MISSING_SIGNATURE", "doc": "1003_form", "severity": "CRITICAL" }
  ]
}
```

---

## Exception Severity Levels

| Severity   | Meaning                                              | Example                        |
|------------|------------------------------------------------------|--------------------------------|
| `CRITICAL` | Blocks decisioning                                   | Missing final 1003, no signature |
| `WARNING`  | Needs human review                                   | Low OCR confidence, missing pages |
| `INFO`     | Informational only                                   | Duplicate page removed         |

---

## Graceful Degradation

The system is designed so partial output is always preferred over a crash:

- OCR fails → page flagged `LOW_OCR_CONFIDENCE`, pipeline continues
- Page unclassifiable → labelled `UNKNOWN`, included in exceptions
- Document group incomplete → partial output still emitted with flags
- LLM API unavailable → falls back to Tier 2 embedding only
- Corrupt page image → flagged `UNREADABLE`, rest of package processes normally
- Each stage writes results to disk — a failure in Stage 8 never loses Stages 1–7

---

## Scalability

- Target: **1,000 packages/day** (~42/hour)
- Each package: ~5–8 minutes end-to-end with 8 parallel workers
- Horizontal scaling via **Celery + Redis** task queue
- Each stage is stateless — add workers without code changes

---

## Tech Stack

**Core Processing**
- `PyMuPDF (fitz)` — PDF parsing, rendering, reassembly
- `Tesseract 5` + `pytesseract` — OCR engine
- `OpenCV (cv2)` + `Pillow` — image pre-processing, signature detection
- `sentence-transformers` + `FAISS` — embedding-based classification
- `Python re` — regex extraction
- `spaCy` *(optional)* — named entity recognition

**Infrastructure**
- `FastAPI` — REST upload endpoint
- `Celery + Redis` — async task queue
- `AWS S3` — file storage *(configurable to local disk)*
- `Claude API` / `GPT-4o-mini` — LLM fallback for Stage 6 only

---

## Installation

```bash
git clone https://github.com/your-username/mortgage-doc-processor.git
cd mortgage-doc-processor
pip install -r requirements.txt
```

Tesseract must be installed separately:
```bash
# Ubuntu
sudo apt install tesseract-ocr

# macOS
brew install tesseract
```

---

## Quick Start

```python
from pipeline.stage_01_pdf_upload import upload_package
from pipeline.stage_02_page_splitter import split_pdf
from pipeline.stage_03_scan_detection import classify_all_pages
from pipeline.stage_04_ocr_engine import ocr_scanned_pages
from pipeline.stage_05_text_extraction import extract_features
from pipeline.stage_06_classification import classify_all
from pipeline.stage_07_page_grouping import group_pages
from pipeline.stage_08_ordering import order_document
from pipeline.stage_09_validation import validate
from pipeline.stage_10_exceptions import build_report
from pipeline.stage_11_output import build_output

pdf_path = "mortgage_package.pdf"
output_dir = "tmp/pages"

job    = upload_package(pdf_path)
pages  = split_pdf(pdf_path, output_dir)
pages  = classify_all_pages(pages)
pages  = ocr_scanned_pages(pages)
pages  = [extract_features(p) for p in pages]
pages  = classify_all(pages)
grouped = group_pages(pages)

for doc_type in grouped:
    grouped[doc_type] = order_document(grouped[doc_type])

exceptions = validate(grouped)
report     = build_report(exceptions)
manifest   = build_output(job["job_id"], grouped, exceptions, pdf_path)

print(manifest)
```

---

## Cost Summary

10 of 11 stages are entirely free. LLM is only invoked for ~5% of pages in Stage 6.

| Scale              | LLM Cost         |
|--------------------|------------------|
| 1 package          | ~$0.05           |
| 100 packages/day   | ~$5/day          |
| 1,000 packages/day | ~$50/day         |

---

## Author

**Dhruv Bhandari** 
