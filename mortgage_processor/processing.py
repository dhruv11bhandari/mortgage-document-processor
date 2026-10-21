"""Local PDF processing primitives. OCR is optional and failures are recorded per page."""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import uuid
from pathlib import Path
from typing import Any

import pymupdf as fitz

from .classification import classify_text

MAX_PAGES = int(os.getenv("MORTGAGE_MAX_PAGES", "2000"))
MAX_UPLOAD_BYTES = int(os.getenv("MORTGAGE_MAX_UPLOAD_BYTES", str(50 * 1024 * 1024)))


def process_pdf(source: Path, output_root: Path, job_id: str | None = None) -> dict[str, Any]:
    job_id = job_id or str(uuid.uuid4())
    job_dir = output_root / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    docs: dict[str, list[dict[str, Any]]] = {}
    exceptions: list[dict[str, Any]] = []
    pages: list[dict[str, Any]] = []
    try:
        with fitz.open(source) as pdf:
            if pdf.is_encrypted:
                raise ValueError("Password-protected PDFs are not supported.")
            if pdf.page_count == 0:
                raise ValueError("The PDF has no pages.")
            if pdf.page_count > MAX_PAGES:
                raise ValueError(f"PDF exceeds the {MAX_PAGES:,} page limit.")
            for index, page in enumerate(pdf):
                text = page.get_text("text").strip()
                scanned = len(text) < 40
                ocr_status = "not_needed"
                if scanned:
                    try:
                        import pytesseract
                        from PIL import Image
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                        text = pytesseract.image_to_string(Image.frombytes("RGB", [pix.width, pix.height], pix.samples)).strip()
                        ocr_status = "completed" if text else "no_text_found"
                    except Exception as exc:  # optional system OCR may be missing or fail on a page
                        ocr_status = "unavailable"
                        exceptions.append({"type": "OCR_UNAVAILABLE", "page": index + 1, "severity": "WARNING", "detail": str(exc)[:180]})
                doc_type, confidence = classify_text(text)
                if doc_type == "unknown":
                    exceptions.append({"type": "UNCLASSIFIED_PAGE", "page": index + 1, "severity": "WARNING"})
                pages.append({"page_number": index, "text": text, "type": doc_type, "confidence": round(confidence, 2), "scanned": scanned, "ocr_status": ocr_status})

            for item in pages:
                docs.setdefault(item["type"], []).append(item)
            manifest_docs = []
            for kind, items in docs.items():
                out = fitz.open()
                for item in sorted(items, key=lambda p: (_page_sequence(p["text"]) is None,
                                                         _page_sequence(p["text"]) or p["page_number"],
                                                         p["page_number"])):
                    out.insert_pdf(pdf, from_page=item["page_number"], to_page=item["page_number"])
                filename = f"{kind}.pdf"
                out.save(job_dir / filename, garbage=4, deflate=True)
                out.close()
                manifest_docs.append({"type": kind, "pages": len(items), "path": filename,
                                      "source_pages": [i["page_number"] + 1 for i in items],
                                      "average_confidence": round(sum(i["confidence"] for i in items) / len(items), 2)})
        manifest = {"job_id": job_id, "status": "completed", "file_name": source.name,
                    "page_count": len(pages), "documents": manifest_docs, "exceptions": exceptions,
                    "pages": [{k: v for k, v in p.items() if k != "text"} for p in pages]}
        import json
        (job_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return manifest
    except Exception:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise


def _page_sequence(text: str) -> int | None:
    match = re.search(r"\bpage\s+(\d+)\s*(?:of\s+|/\s*)\d+", text, re.I)
    return int(match.group(1)) if match else None
