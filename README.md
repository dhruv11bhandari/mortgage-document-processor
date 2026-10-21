# Mortgage Desk

Mortgage Desk turns mortgage PDF packages into organized, review-ready document groups. It combines a local web workspace with a FastAPI service and a transparent, keyword-based classifier. The app runs on your machine; uploaded documents are written under `data/` and are not sent to a hosted service.

> **Review required:** classification and page grouping are assistive. They are not underwriting, compliance, or lending decisions. Confirm every result and exception with a qualified reviewer.

## What it does

- Accepts PDF packages up to 50 MB and 2,000 pages by default.
- Extracts text from digital PDFs and attempts OCR for scanned pages when Tesseract is installed.
- Identifies 1003 applications, bank statements, pay stubs, W-2s, 1040s, credit reports, appraisals, and title documents using explainable keyword evidence.
- Groups identified pages into downloadable PDFs, preserving original page order unless page numbering is detected.
- Produces a JSON manifest with source pages, classification confidence, and review flags for unknown pages or unavailable OCR.
- Provides a responsive browser workspace for uploading, reviewing, and downloading results.

The classifier intentionally does not call an LLM or use a trained embedding model. Its scores are keyword-match rates, not calibrated probabilities. Review the manifest and source PDFs before relying on a classification.

## Run locally

Requires Python 3.10 or later.

```bash
./start.sh
```

The launcher creates `.venv` and installs the runtime dependencies on the first run, then starts the app. Stop it with `Ctrl+C`. Optional settings: `HOST` (default `127.0.0.1`) and `PORT` (default `8000`).

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). On macOS, install Tesseract with `brew install tesseract`; on Ubuntu/Debian, use `sudo apt install tesseract-ocr`. Without Tesseract, digital PDFs still work and scanned pages are marked for review.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `MORTGAGE_DATA_DIR` | `./data` | Local input and output storage |
| `MORTGAGE_MAX_UPLOAD_BYTES` | `52428800` | Upload size limit in bytes |
| `MORTGAGE_MAX_PAGES` | `2000` | Maximum pages per PDF |

The API exposes `GET /api/health`, `GET /api/jobs`, `GET /api/jobs/{job_id}`, and `POST /api/jobs` (multipart form field `file`). Documents are available through `/api/jobs/{job_id}/documents/{filename}`. Interactive API documentation is at `/docs`.

## Processing flow

1. Validate upload extension and size.
2. Extract text per page and try local OCR when text is absent.
3. Score supported document types against keyword evidence; low-evidence pages remain `unknown`.
4. Create one PDF per detected type and a `manifest.json` for review.

Output folders are isolated by job ID. Failed jobs return an error in their manifest. OCR failures are reported per page and do not stop digital-page processing.

## Tests

```bash
python -m pip install -e '.[dev]'
python -m pytest
```

## Project layout

- `backend/app/main.py` — FastAPI app and upload/job/download routes
- `backend/app/processing.py` — PDF extraction, optional OCR, grouping, and output
- `backend/app/classification.py` — deterministic classifier and supported keyword sets
- `frontend/` — responsive browser workspace and its assets
- `tests/` — focused classifier and page-ordering checks

## Privacy and operational notes

This is a local development application, not a hardened multi-user service. Keep `data/` access restricted, use trusted input PDFs, and place it behind suitable authentication and storage controls before exposing it on a network. The default local instance does not implement user accounts, retention policies, encryption-at-rest, or a durable distributed queue.
