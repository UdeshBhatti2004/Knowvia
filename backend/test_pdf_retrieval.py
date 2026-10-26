import os 
import numpy as np 
from dotenv import load_dotenv
from google import genai
from pathlib import Path
from read_pdf import extract_text_from_pdf
from chunking import chunk_pages

# Load API key
# 
BACKEND_DIR = Path(__file__).resolve().parent 

load_dotenv(BACKEND_DIR.parent / ".env")

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

client = genai.Client( api_key=api_key)

def get_embedding(text):
    result = client.models.embed_content(
        model ="gemini-embedding-2",
        contents=text
    )

    return result.embeddings[0].values


def cosine_similarity( vector_a , vector_b):
    a = np.array(vector_a)
    b = np.array(vector_b)

    denominator = np.linalg.norm(a) * np.linalg.norm(b)

    if denominator == 0:
        return 0.0

    return float( np.dot( a, b) / denominator)

# Read the Pdf and create chunks 

pages = extract_text_from_pdf(
    BACKEND_DIR / "documents" / "business_info.pdf"
)

chunks = chunk_pages(pages , chunk_size=250 , overlap=40)

# Genrate and store eachc chunk's embeddings

for chunk in chunks:
    chunk["embedding"] = get_embedding(chunk["text"])


def reterive_chunk(questions):
    question_embedding = get_embedding(questions)

    best_chunk = None
    best_score = -1.0

    for chunk in chunks:
        scorce = cosine_similarity(
            question_embedding,
            chunk["embedding"]
        )

        if scorce > best_score:
            best_score = scorce
            best_chunk = chunk

    return best_chunk , best_score


if __name__ == "__main__":
    question = "Can I get my money back after five days?"

    chunk , score = reterive_chunk(question)

    print("Question:", question)
    print("Best matching chunk:", chunk["text"])
    print("Source:", chunk["source"])
    print("Page:", chunk["page"])
    print("Similarity:", round(score, 4))