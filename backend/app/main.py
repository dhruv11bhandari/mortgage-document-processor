from __future__ import annotations

import json
import os
import re
import shutil
import uuid
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .processing import MAX_UPLOAD_BYTES, process_pdf

BASE = Path(__file__).resolve().parents[2]
FRONTEND = BASE / "frontend"
DATA = Path(os.getenv("MORTGAGE_DATA_DIR", str(BASE / "data")))
INCOMING = DATA / "incoming"
OUTPUT = DATA / "output"
INCOMING.mkdir(parents=True, exist_ok=True)
OUTPUT.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Mortgage Desk", version="1.0.0", description="Local-first mortgage document package processing.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv(
        "MORTGAGE_FRONTEND_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
    ).split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)
app.mount("/assets", StaticFiles(directory=FRONTEND / "assets"), name="assets")
app.mount("/static", StaticFiles(directory=FRONTEND / "assets"), name="static-compat")


def _load_jobs() -> list[dict[str, Any]]:
    jobs = []
    for path in OUTPUT.glob("*/manifest.json"):
        try:
            jobs.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return sorted(jobs, key=lambda j: j.get("created_at", ""), reverse=True)


def _run(job_id: str, path: Path) -> None:
    try:
        result = process_pdf(path, OUTPUT, job_id)
        result["created_at"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
        (OUTPUT / job_id / "manifest.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    except Exception as exc:
        job_dir = OUTPUT / job_id
        job_dir.mkdir(exist_ok=True)
        result = {"job_id": job_id, "status": "failed", "file_name": path.name, "error": str(exc)}
        (job_dir / "manifest.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    finally:
        path.unlink(missing_ok=True)


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return (FRONTEND / "index.html").read_text(encoding="utf-8")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "mortgage-desk"}


@app.get("/api/jobs")
def jobs() -> list[dict[str, Any]]:
    return _load_jobs()


@app.get("/api/jobs/{job_id}")
def job(job_id: str) -> dict[str, Any]:
    if not re.fullmatch(r"[a-f0-9-]{36}", job_id):
        raise HTTPException(404, "Job not found")
    path = OUTPUT / job_id / "manifest.json"
    if not path.is_file():
        raise HTTPException(404, "Job not found")
    return json.loads(path.read_text(encoding="utf-8"))


@app.post("/api/jobs", status_code=202)
async def create_job(background: BackgroundTasks, file: UploadFile = File(...)) -> dict[str, str]:
    if not file.filename or Path(file.filename).suffix.lower() != ".pdf":
        raise HTTPException(400, "Upload a PDF file.")
    job_id = str(uuid.uuid4())
    target = INCOMING / f"{job_id}.pdf"
    size = 0
    try:
        with target.open("wb") as out:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(413, f"File exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB upload limit.")
                out.write(chunk)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    if size == 0:
        target.unlink(missing_ok=True)
        raise HTTPException(400, "The uploaded file is empty.")
    (OUTPUT / job_id).mkdir(parents=True, exist_ok=True)
    (OUTPUT / job_id / "manifest.json").write_text(json.dumps({
        "job_id": job_id, "status": "queued", "file_name": Path(file.filename).name,
        "page_count": None, "documents": [], "exceptions": [],
    }), encoding="utf-8")
    background.add_task(_run, job_id, target)
    return {"job_id": job_id, "status": "queued"}


@app.get("/api/jobs/{job_id}/documents/{name}")
def download_document(job_id: str, name: str) -> FileResponse:
    if not re.fullmatch(r"[a-f0-9-]{36}", job_id):
        raise HTTPException(404, "Document not found")
    if Path(name).name != name or not name.endswith(".pdf"):
        raise HTTPException(400, "Invalid document name")
    path = OUTPUT / job_id / name
    if not path.is_file():
        raise HTTPException(404, "Document not found")
    return FileResponse(path, media_type="application/pdf", filename=name)
