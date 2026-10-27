
from pathlib import Path

from pypdf import PdfReader


def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        if text.strip():
            pages.append({
                "text": text.strip(),
                "source": Path(pdf_path).name,
                "page": page_number,
            })

    return pages
