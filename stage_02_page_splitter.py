import fitz
import os
def split_pdf(pdf_path, output_dir):
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        mat = fitz.Matrix(150 / 72, 150 / 72)
        pix = page.get_pixmap(matrix=mat)
        img_path = os.path.join(output_dir, f"page_{i:04d}.png")
        pix.save(img_path)
        pages.append({
            "page_number": i,
            "image_path": img_path,
            "raw_text": page.get_text(),
        })

    doc.close()
    return pages
