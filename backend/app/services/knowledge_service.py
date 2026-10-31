from app.knowledge.retrieval import retrieve_document
from app.repositories.settings_store import DEFAULT_WORKSPACE_ID


def retrieve_knowledge(question: str, workspace_id: str = DEFAULT_WORKSPACE_ID):
    """Retrieve relevant document chunks for a question, in one workspace."""
    if workspace_id == DEFAULT_WORKSPACE_ID:
        return retrieve_document(question)
    return retrieve_document(question, workspace_id)