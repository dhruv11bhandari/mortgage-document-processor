# Stage 1 - PDF Upload

import fitz
import uuid
import os


def upload_package(pdf_path):
    job_id = str(uuid.uuid4())

    doc = fitz.open(pdf_path)
    page_count = doc.page_count
    doc.close()

    return {
        "job_id": job_id,
        "page_count": page_count,
        "file_size": os.path.getsize(pdf_path),
    }
