
from pathlib import Path
from pypdf import PdfReader

def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)

    pages=[]

    for page_number , page in enumerate( reader.pages , start = 1):

        text = page.extract_text() or ""

        if text.strip():
            pages.append({
                "text":text.strip(),
                "source":Path(pdf_path).name,
                "page":page_number
            })
    return pages

if __name__ == "__main__":
    pdf_path = "documents/business_info.pdf"

    extracted_pages = extract_text_from_pdf(pdf_path)

    print("Total pages extracted:", len(extracted_pages))
    print("Source:", extracted_pages[0]["source"])
    print("Page number:", extracted_pages[0]["page"])
    print("Text preview:")
    print(extracted_pages[0]["text"][:200])

    

