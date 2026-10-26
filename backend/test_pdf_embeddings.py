import os 
from dotenv import load_dotenv
from google import genai
from read_pdf import extract_text_from_pdf
from chunking import chunk_pages
from pathlib import Path


#Load Gemini API key

BACKEND_DIR = Path(__file__).resolve().parent

load_dotenv(BACKEND_DIR.parent / ".env")

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=api_key)

# Extract PDF text and create chunks

pages = extract_text_from_pdf(
    BACKEND_DIR / "documents" / "business_info.pdf"
)

chunks = chunk_pages(pages)

# Genrate an embedding for each chunk

for index , chunk in enumerate( chunks , start = 1):
    result = client.models.embed_content(
        model = "gemini-embedding-2",
        contents = chunk["text"]
    )

    embedding = result.embeddings[0].values

    print(f"\n --- Chunk {index} ---")
    print("Source:" ,chunk["source"])
    print("Page:" , chunk["page"])
    print("Embeddings dimensions:", len(embedding))
    print("First 5 values:",embedding[:5])



