# Stage 11 - Structured Output

import fitz
import json
import os


def build_output(job_id, grouped, exceptions, source_pdf):
    src = fitz.open(source_pdf)
    out_dir = f"output/{job_id}"
    os.makedirs(out_dir, exist_ok=True)

    manifest = {"job_id": job_id, "documents": [], "exceptions": exceptions}

    for doc_type, pages in grouped.items():
        out_pdf = fitz.open()

        for page in pages:
            out_pdf.insert_pdf(src, from_page=page["page_number"],
                                    to_page=page["page_number"])

        pdf_path = os.path.join(out_dir, f"{doc_type}.pdf")
        out_pdf.save(pdf_path)

        manifest["documents"].append({
            "type": doc_type,
            "pages": len(pages),
            "path": pdf_path,
        })

    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    return manifest
