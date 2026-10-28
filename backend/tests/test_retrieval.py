from types import MappingProxyType

import pytest

from app.knowledge import retrieval

# Tiny fake "embedding space": one axis per topic.
REFUND = (1.0, 0.0, 0.0)
PYTHON = (0.0, 1.0, 0.0)
NOTHING = (0.0, 0.0, 1.0)


def fake_embedding(text):
    text = text.lower()
    if "refund" in text:
        return REFUND
    if "python" in text or "duration" in text:
        return PYTHON
    return NOTHING


@pytest.fixture(autouse=True)
def fake_knowledge_base(monkeypatch):
    chunks = (
        MappingProxyType({
            "text": "Refund Policy: full refund within 7 days of enrolment.",
            "source": "business_info.pdf",
            "page": 1,
        }),
        MappingProxyType({
            "text": "Python course duration is 3 months.",
            "source": "courses.pdf",
            "page": 1,
        }),
    )
    state = retrieval.KnowledgeBaseState(
        knowledge_base=chunks,
        document_embeddings=(REFUND, PYTHON),
        pdf_hashes=MappingProxyType({}),
        pdf_modified_time=MappingProxyType({}),
    )
    monkeypatch.setattr(retrieval, "knowledge_base_state", state)
    monkeypatch.setattr(retrieval, "get_embedding", fake_embedding)
    # No Gemini call: split questions with a simple fake.
    monkeypatch.setattr(
        retrieval,
        "decompose_query",
        lambda question: (
            ["What is the Python course duration?", "What is the refund policy?"]
            if " and " in question.lower()
            else [question]
        ),
    )


def test_retrieve_refund_policy():
    documents, highest_score = retrieval.retrieve_document(
        "Can I get a refund within 5 days"
    )

    assert documents is not None
    sources = [document["source"] for document, score in documents]
    assert "business_info.pdf" in sources
    assert highest_score >= 0.60


def test_unrelated_question():
    documents, highest_score = retrieval.retrieve_document(
        "What is the capital of France"
    )

    assert documents is None
    assert highest_score == 0.0


def test_multi_part_question():
    documents, highest_score = retrieval.retrieve_document(
        "What is the Python course duration and refund policy?"
    )

    assert documents is not None
    combined_text = " ".join(
        document["text"] for document, score in documents
    ).lower()

    assert "3 months" in combined_text
    assert "7 days" in combined_text


def test_empty_knowledge_base_returns_nothing(monkeypatch):
    empty = retrieval.KnowledgeBaseState(
        knowledge_base=(),
        document_embeddings=(),
        pdf_hashes=MappingProxyType({}),
        pdf_modified_time=MappingProxyType({}),
    )
    monkeypatch.setattr(retrieval, "knowledge_base_state", empty)

    assert retrieval.retrieve_document("anything") == (None, 0.0)