
import os
import numpy as np
from dotenv import load_dotenv
from google import genai
from read_pdf import extract_text_from_pdf
from chunking import chunk_pages
import pickle
import hashlib
import glob
import time
from google.genai import errors

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

cache_file = "documents_embedding.pkl"
embedding_model = "gemini-embedding-2"
chunk_size = 500
chunk_overlap = 50
pdf_paths = glob.glob("documents/*.pdf")
pdf_modified_time = {
    path: os.path.getmtime(path)
    for path in pdf_paths
}

pdf_hashes = {}

for path in pdf_paths:
    with open(path, "rb") as file:
        pdf_hashes[path] = hashlib.sha256(file.read()).hexdigest()

pages = []

for path in pdf_paths:
    pages.extend(extract_text_from_pdf(path))


knowledge_base = chunk_pages(
    pages,
    chunk_size=chunk_size,
    overlap=chunk_overlap
 )

def get_embedding(text):

    max_attempts = 3

    for attempt in range(max_attempts):
        try:
            result = client.models.embed_content(
                    model=embedding_model,
                    contents=text
                )
            return result.embeddings[0].values

        except errors.APIError as e :

            print(
                f" Gemini Embedding Failed",
                f"(attempt {attempt + 1}): {e}"
                )

            if e.code not in ( 429 , 500 , 502 , 503 , 504 ):
                raise

            if attempt == max_attempts - 1:
                raise

            time.sleep( 2 ** attempt)  


if os.path.exists(cache_file):
    with open(cache_file, "rb") as file:
        cached_data = pickle.load(file)
        

    if (
    cached_data.get("pdf_hashes") == pdf_hashes
    and cached_data.get("embedding_model") == embedding_model
    and cached_data.get("chunk_size") == chunk_size
    and cached_data.get("chunk_overlap") == chunk_overlap
    ):
        print("Embedding Cache Found")
        document_embeddings = cached_data["embeddings"]
    else:
        print("Cache invalid or configuration changed. Regenerating embeddings...")
        document_embeddings = None
else:
    print("Embedding Cache not Found")
    document_embeddings = None

if document_embeddings is None:
    document_embeddings = [
        get_embedding(document["text"])
        for document in knowledge_base
    ]

    with open(cache_file, "wb") as file:
        pickle.dump({
            "embeddings": document_embeddings,
            "pdf_modified_times": pdf_modified_time,
            "pdf_hashes":pdf_hashes,
            "embedding_model": embedding_model,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        }, file)

    print("Embedding cache saved.")




def decompose_query(question):

    question_lower = question.lower().strip()

    # Common indicators of multiple information needs
    multi_part_indicators = [
        " and ",
        "also ",
        " as well as ",
        " in addition to ",
        "but "
    ]

    # Skip Gemini decomposition for likely single-part questions
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
        contents=prompt
    )

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
            knowledge_base, document_embeddings
        ):
            score = cosine_similarity(
                question_embedding,
                document_embedding
            )

            document_scores.append((document, score))

        document_scores.sort(
            key=lambda item: item[1],
            reverse=True
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
                document["text"]
            )

            if (
                key not in best_documents
                or score > best_documents[key][1]
            ):
                best_documents[key] = (document, score)


    relevant_documents = sorted(
        best_documents.values(),
        key=lambda item: item[1],
        reverse=True
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

    question = "What is the Python course duration, and what is the refund deadline?"

    document, score = retrieve_document(question)

    print("Question:", question)

    if document is None:
        print("No relevant document found.")
    else:
       for doc, score in document:
         print("Matching document:", doc["text"])
         print("Similarity score:", round(score, 4))
         print()


    sub_questions = decompose_query(question)

    print("\nDecomposed questions:")
    for sub_question in sub_questions:
        print("-", sub_question)