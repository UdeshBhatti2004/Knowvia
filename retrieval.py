
import os
import numpy as np
from dotenv import load_dotenv
from google import genai
from read_pdf import extract_text_from_pdf
from chunking import chunk_pages
import pickle
import hashlib
import glob

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
    result = client.models.embed_content(
        model=embedding_model,
        contents=text
    )
    return result.embeddings[0].values


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

def cosine_similarity(vector_a, vector_b):
    a = np.array(vector_a)
    b = np.array(vector_b)

    denominator = np.linalg.norm(a) * np.linalg.norm(b)


    if denominator == 0:
        return 0.0

    return float(np.dot(a, b) / denominator)


def retrieve_document(question):

    question_embedding = get_embedding(question)

    document_scores =  []


    for document, document_embedding in zip(
        knowledge_base, document_embeddings
    ):
        score = cosine_similarity(
            question_embedding,
            document_embedding
        )

        document_scores.append((document,score))

    document_scores.sort( key = lambda item : item[1] , reverse=True )

    print("\n--- All retrieval scores ---")

    for document, score in document_scores:
        print(
            f"Score: {score:.4f} | "
            f"Source: {document['source']} | "
            f"Text: {document['text'][:120]}"
        )

    print("----------------------------\n")

    threshold = 0.60

    relevant_documents = [
        ( document , score)
        for document , score in document_scores
        if score >= threshold
    ]

    if not relevant_documents:
        return None , document_scores[0][1]

    

    return relevant_documents[ : 3] , relevant_documents[0][1]



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
