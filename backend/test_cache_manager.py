
from cache_manager import get_or_create_embeddings


def test_valid_cache_reuses_embeddings(tmp_path):
    cache_file = tmp_path / "cache.pkl"
    pdf_hashes = {"sample.pdf": "hash123"}
    expected_embeddings = [[0.1, 0.2, 0.3]]

    # Create an existing valid cache.
    from cache_utils import save_cache

    save_cache(
        cache_file,
        {
            "embeddings": expected_embeddings,
            "pdf_hashes": pdf_hashes,
            "embedding_model": "gemini-embedding-2",
            "chunk_size": 500,
            "chunk_overlap": 50,
        },
    )

    def should_not_run(text):
        raise AssertionError("Embeddings should be reused from cache")

    result = get_or_create_embeddings(
        str(cache_file),
        pdf_hashes,
        "gemini-embedding-2",
        500,
        50,
        [{"text": "Sample document"}],
        should_not_run,
    )

    assert result == expected_embeddings


def test_missing_cache_generates_and_saves_embeddings(tmp_path):
    cache_file = tmp_path / "cache.pkl"
    generated_embeddings = [[0.4, 0.5, 0.6]]
    calls = []

    def fake_embedding(text):
        calls.append(text)
        return generated_embeddings[0]

    result = get_or_create_embeddings(
        str(cache_file),
        {"sample.pdf": "hash123"},
        "gemini-embedding-2",
        500,
        50,
        [{"text": "Sample document"}],
        fake_embedding,
    )

    assert result == generated_embeddings
    assert calls == ["Sample document"]
    assert cache_file.exists()


def test_changed_pdf_hash_regenerates_embeddings(tmp_path):
    cache_file = tmp_path / "cache.pkl"

    from cache_utils import save_cache

    save_cache(
        cache_file,
        {
            "embeddings": [[0.1, 0.2, 0.3]],
            "pdf_hashes": {"sample.pdf": "old_hash"},
            "embedding_model": "gemini-embedding-2",
            "chunk_size": 500,
            "chunk_overlap": 50,
        },
    )

    generated_embeddings = [[0.7, 0.8, 0.9]]
    calls = []

    def fake_embedding(text):
        calls.append(text)
        return generated_embeddings[0]

    result = get_or_create_embeddings(
        str(cache_file),
        {"sample.pdf": "new_hash"},
        "gemini-embedding-2",
        500,
        50,
        [{"text": "Updated document"}],
        fake_embedding,
    )

    assert result == generated_embeddings
    assert calls == ["Updated document"]
