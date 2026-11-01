from app.knowledge import retrieval


def empty_state():
    return retrieval.KnowledgeBaseState(
        knowledge_base=(),
        document_embeddings=(),
        pdf_hashes={},
        pdf_modified_time={},
    )


def test_oldest_workspace_is_evicted(monkeypatch):
    monkeypatch.setattr(retrieval, "_states", {})
    monkeypatch.setattr(retrieval, "MAX_LOADED_WORKSPACES", 2)

    for ws in ("a", "b", "c"):
        retrieval._store_state(ws, empty_state())

    assert not retrieval.is_loaded("a")
    assert retrieval.is_loaded("b")
    assert retrieval.is_loaded("c")


def test_using_a_workspace_keeps_it_loaded(monkeypatch):
    monkeypatch.setattr(retrieval, "_states", {})
    monkeypatch.setattr(retrieval, "MAX_LOADED_WORKSPACES", 2)

    retrieval._store_state("a", empty_state())
    retrieval._store_state("b", empty_state())
    assert retrieval.get_state("a") is not None  # a is now most recent
    retrieval._store_state("c", empty_state())

    assert retrieval.is_loaded("a")
    assert not retrieval.is_loaded("b")


def test_default_workspace_is_never_evicted(monkeypatch):
    monkeypatch.setattr(retrieval, "_states", {})
    monkeypatch.setattr(retrieval, "MAX_LOADED_WORKSPACES", 1)

    retrieval._store_state("a", empty_state())
    retrieval._store_state("b", empty_state())

    assert retrieval.is_loaded("default")