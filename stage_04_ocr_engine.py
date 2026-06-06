# Stage 4 - OCR Engine

import pytesseract
import cv2
from PIL import Image


def run_ocr(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_OTSU)

    pil_img = Image.fromarray(thresh)
    text = pytesseract.image_to_string(pil_img)

    return text.strip()


def ocr_scanned_pages(pages):
    for page in pages:
        if page["type"] == "scanned":
            page["raw_text"] = run_ocr(page["image_path"])

    return pages
