import pymupdf as fitz
from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_and_upload_flow(tmp_path, monkeypatch):
    import backend.app.main as api
    monkeypatch.setattr(api, "OUTPUT", tmp_path / "output")
    monkeypatch.setattr(api, "INCOMING", tmp_path / "incoming")
    api.OUTPUT.mkdir()
    api.INCOMING.mkdir()
    client = TestClient(app)
    assert client.get("/api/health").json()["status"] == "ok"

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Form 1003 Uniform Residential Loan Application")
    payload = doc.tobytes()
    doc.close()
    response = client.post("/api/jobs", files={"file": ("application.pdf", payload, "application/pdf")})
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    result = client.get(f"/api/jobs/{job_id}")
    assert result.status_code == 200
    assert result.json()["status"] == "completed"
    assert client.get(f"/api/jobs/{job_id}/documents/1003_form.pdf").status_code == 200


def test_upload_rejects_non_pdf():
    client = TestClient(app)
    response = client.post("/api/jobs", files={"file": ("notes.txt", b"not a pdf", "text/plain")})
    assert response.status_code == 400
