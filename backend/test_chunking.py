
from read_pdf import extract_text_from_pdf
from chunking import chunk_pages
from pathlib import Path


pdf_path = Path(__file__).resolve().parent / "documents" / "business_info.pdf"
# Step 1 : Extract text from pdf

pages = extract_text_from_pdf(pdf_path)

# Step 2 : Spilt extracted text into chunks

chunks = chunk_pages( pages , chunk_size = 500 , overlap = 50 )


# Step 3 : Display the result

print("Total Pages : " , len(pages))
print("Total Chunks : ", len(chunks))


for index, chunk in enumerate( chunks , start = 1):

    print(f"\n --- Chunk {index} ---")
    print("Source:" , chunk["source"])
    print("Page:" , chunk["page"])
    print("Text:" , chunk["text"])


