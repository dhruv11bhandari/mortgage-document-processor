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
