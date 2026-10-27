
from app.knowledge.retrieval import retrieve_document


def retrieve_knowledge(question: str):
    """
    Retrieve relevant document chunks for a user's question.

    Returns the documents and retrieval metadata produced by
    the retrieval implementation.
    """
    return retrieve_document(question)
