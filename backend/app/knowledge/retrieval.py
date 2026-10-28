import glob
import hashlib
import os
import time
import threading

from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from types import MappingProxyType

import numpy as np
from google.genai import errors

from app.core.ai_client import client
from app.core.config import (
    CACHE_FILE,
    DOCUMENTS_DIR,
)
from app.knowledge.pdf_reader import extract_text_from_pdf
from app.knowledge.chunking import chunk_pages
from app.knowledge.cache_manager import get_or_create_embeddings


embedding_model = "gemini-embedding-2"
chunk_size = 500
chunk_overlap = 50


@dataclass(frozen=True)
class KnowledgeBaseState:
    knowledge_base: tuple[Mapping[str, object], ...]
    document_embeddings: tuple[tuple[float, ...], ...]
    pdf_hashes: Mapping[str, str]
    pdf_modified_time: Mapping[str, float]


knowledge_base_state = KnowledgeBaseState(
    knowledge_base=(),
    document_embeddings=(),
    pdf_hashes=MappingProxyType({}),
    pdf_modified_time=MappingProxyType({}),
)
refresh_lock = threading.Lock()


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
    global knowledge_base_state

    with refresh_lock:
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

        started = time.perf_counter()
        new_embeddings = get_or_create_embeddings(
            cache_file=CACHE_FILE,
            pdf_hashes=current_hashes,
            embedding_model=embedding_model,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            knowledge_base=new_knowledge_base,
            get_embedding=get_embedding,
            pdf_modified_times=current_modified_times,
            max_workers=4,
            requests_per_minute=90,
        )

        print(
            f"[timing] embeddings: {time.perf_counter() - started:.2f}s "
            f"for {len(new_knowledge_base)} chunks"
        )

        refreshed_state = KnowledgeBaseState(
            knowledge_base=tuple(
                MappingProxyType(document.copy())
                for document in new_knowledge_base
            ),
            document_embeddings=tuple(
                tuple(embedding) for embedding in new_embeddings
            ),
            pdf_hashes=MappingProxyType(current_hashes),
            pdf_modified_time=MappingProxyType(current_modified_times),
        )
        knowledge_base_state = refreshed_state

        print(
            f"Knowledge base refreshed: "
            f"{len(pdf_paths)} PDF(s), "
            f"{len(refreshed_state.knowledge_base)} chunk(s)."
        )


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

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
        )
    except Exception as exc:
        print(f"Query decomposition failed, using original question: {exc}")
        return [question]

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
    state = knowledge_base_state

    if not state.knowledge_base or not state.document_embeddings:
        return None, 0.0

    sub_questions = decompose_query(question)

    print("\n--- Decomposed Questions ---")
    for sub_question in sub_questions:
        print("-", sub_question)

    # Embed all sub-questions at the same time instead of one by one.
    with ThreadPoolExecutor(max_workers=len(sub_questions)) as pool:
        vectors = list(pool.map(get_embedding, sub_questions))
    embeddings = dict(zip(sub_questions, vectors))

    best_documents = {}
    threshold = 0.60

    for sub_question in sub_questions:
        question_embedding = embeddings[sub_question]
        document_scores = []

        for document, document_embedding in zip(
            state.knowledge_base,
            state.document_embeddings,
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