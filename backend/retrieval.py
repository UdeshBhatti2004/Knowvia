
import os
import glob
import time
import hashlib
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import errors

from read_pdf import extract_text_from_pdf
from chunking import chunk_pages
from cache_manager import get_or_create_embeddings


BACKEND_DIR = Path(__file__).resolve().parent
DOCUMENTS_DIR = BACKEND_DIR / "documents"
CACHE_FILE = str(BACKEND_DIR / "documents_embedding.pkl")

load_dotenv(BACKEND_DIR.parent / ".env")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

embedding_model = "gemini-embedding-2"
chunk_size = 500
chunk_overlap = 50

knowledge_base = []
document_embeddings = []
pdf_hashes = {}
pdf_modified_time = {}


def get_embedding(text):
    max_attempts = 3

    for attempt in range(max_attempts):
        try:
            result = client.models.embed_content(
                model=embedding_model,
                contents=text,
            )
            return result.embeddings[0].values

        except errors.APIError as e:
            print(
                f"Gemini Embedding Failed "
                f"(attempt {attempt + 1}): {e}"
            )

            if e.code not in (429, 500, 502, 503, 504):
                raise

            if attempt == max_attempts - 1:
                raise

            time.sleep(2 ** attempt)


def refresh_knowledge_base():
    global knowledge_base
    global document_embeddings
    global pdf_hashes
    global pdf_modified_time

    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

    pdf_paths = sorted(
        glob.glob(str(DOCUMENTS_DIR / "*.pdf"))
    )

    current_hashes = {}
    current_modified_times = {}

    for path in pdf_paths:
        with open(path, "rb") as file:
            current_hashes[path] = hashlib.sha256(
                file.read()
            ).hexdigest()

        current_modified_times[path] = os.path.getmtime(path)

    pages = []

    for path in pdf_paths:
        pages.extend(extract_text_from_pdf(path))

    new_knowledge_base = chunk_pages(
        pages,
        chunk_size=chunk_size,
        overlap=chunk_overlap,
    )

    new_embeddings = get_or_create_embeddings(
        cache_file=CACHE_FILE,
        pdf_hashes=current_hashes,
        embedding_model=embedding_model,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        knowledge_base=new_knowledge_base,
        get_embedding=get_embedding,
        pdf_modified_times=current_modified_times,
    )

    knowledge_base = new_knowledge_base
    document_embeddings = new_embeddings
    pdf_hashes = current_hashes
    pdf_modified_time = current_modified_times

    print(
        f"Knowledge base refreshed: "
        f"{len(pdf_paths)} PDF(s), "
        f"{len(knowledge_base)} chunk(s)."
    )


refresh_knowledge_base()


def decompose_query(question):
    question_lower = question.lower().strip()

    multi_part_indicators = [
        " and ",
        "also ",
        " as well as ",
        " in addition to ",
        "but ",
    ]

    if not any(
        indicator in question_lower
        for indicator in multi_part_indicators
    ):
        return [question]

    prompt = f"""
    Break the user's question into independent, simple questions
    that can be answered separately using a business knowledge base.

    Rules:
    - Return one question per line.
    - Do not split a question if it asks for only one thing.
    - Do not answer the questions.
    - Do not add numbering or explanations.

    User question: {question}
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    if not response.text:
        return [question]

    sub_questions = [
        line.strip().lstrip("0123456789.-) ")
        for line in response.text.splitlines()
        if line.strip()
    ]

    return sub_questions or [question]


def cosine_similarity(vector_a, vector_b):
    a = np.array(vector_a)
    b = np.array(vector_b)

    denominator = np.linalg.norm(a) * np.linalg.norm(b)

    if denominator == 0:
        return 0.0

    return float(np.dot(a, b) / denominator)


def retrieve_document(question):
    # Detect newly uploaded, changed, or deleted PDFs.
    current_paths = sorted(
        glob.glob(str(DOCUMENTS_DIR / "*.pdf"))
    )

    current_hashes = {}

    for path in current_paths:
        with open(path, "rb") as file:
            current_hashes[path] = hashlib.sha256(
                file.read()
            ).hexdigest()

    if current_hashes != pdf_hashes:
        print("PDF collection changed. Refreshing knowledge base...")
        refresh_knowledge_base()

    if not knowledge_base or not document_embeddings:
        return None, 0.0

    sub_questions = decompose_query(question)

    print("\n--- Decomposed Questions ---")
    for sub_question in sub_questions:
        print("-", sub_question)

    best_documents = {}
    threshold = 0.60

    for sub_question in sub_questions:
        question_embedding = get_embedding(sub_question)
        document_scores = []

        for document, document_embedding in zip(
            knowledge_base,
            document_embeddings,
        ):
            score = cosine_similarity(
                question_embedding,
                document_embedding,
            )
            document_scores.append((document, score))

        document_scores.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        print(f"\n--- Retrieval scores for: {sub_question} ---")

        for document, score in document_scores:
            print(
                f"Score: {score:.4f} | "
                f"Source: {document['source']} | "
                f"Text: {document['text'][:120]}"
            )

        selected_documents = [
            (document, score)
            for document, score in document_scores
            if score >= threshold
        ][:2]

        for document, score in selected_documents:
            key = (
                document["source"],
                document["page"],
                document["text"],
            )

            if (
                key not in best_documents
                or score > best_documents[key][1]
            ):
                best_documents[key] = (document, score)

    relevant_documents = sorted(
        best_documents.values(),
        key=lambda item: item[1],
        reverse=True,
    )

    print("\n--- Combined Retrieval Results ---")

    for document, score in relevant_documents:
        print(
            f"Score: {score:.4f} | "
            f"Source: {document['source']} | "
            f"Text: {document['text'][:120]}"
        )

    print("----------------------------------\n")

    if not relevant_documents:
        return None, 0.0

    return relevant_documents[:3], relevant_documents[0][1]


if __name__ == "__main__":
    question = (
        "What is the Python course duration, "
        "and what is the refund deadline?"
    )

    documents, score = retrieve_document(question)

    print("Question:", question)

    if documents is None:
        print("No relevant document found.")
    else:
        for doc, doc_score in documents:
            print("Matching document:", doc["text"])
            print("Source:", doc["source"])
            print("Similarity score:", round(doc_score, 4))
            print()
