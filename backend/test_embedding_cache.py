
import pickle
import pytest

from cache_utils import is_cache_valid, load_cache, save_cache


@pytest.fixture
def valid_cache_data():
    return {
        "embeddings": [[0.1, 0.2, 0.3]],
        "pdf_hashes": {"documents/sample.pdf": "abc123"},
        "embedding_model": "gemini-embedding-2",
        "chunk_size": 500,
        "chunk_overlap": 50,
    }


def test_cache_metadata_matches_expected_configuration(tmp_path, valid_cache_data):
    cache_file = tmp_path / "documents_embedding.pkl"

    save_cache(cache_file, valid_cache_data)
    loaded_data = load_cache(cache_file)

    assert loaded_data == valid_cache_data


def test_changed_pdf_hash_is_detected(valid_cache_data):
    assert is_cache_valid(
        valid_cache_data,
        {"documents/sample.pdf": "new_hash"},
        "gemini-embedding-2",
        500,
        50,
    ) is False


def test_cache_is_valid_when_configuration_matches(valid_cache_data):
    assert is_cache_valid(
        valid_cache_data,
        {"documents/sample.pdf": "abc123"},
        "gemini-embedding-2",
        500,
        50,
    ) is True


@pytest.mark.parametrize(
    ("pdf_hashes", "model", "chunk_size", "chunk_overlap"),
    [
        ({"documents/sample.pdf": "changed_hash"}, "gemini-embedding-2", 500, 50),
        ({"documents/sample.pdf": "abc123"}, "different-model", 500, 50),
        ({"documents/sample.pdf": "abc123"}, "gemini-embedding-2", 600, 50),
        ({"documents/sample.pdf": "abc123"}, "gemini-embedding-2", 500, 25),
    ],
)
def test_cache_is_invalid_when_configuration_changes(
    valid_cache_data, pdf_hashes, model, chunk_size, chunk_overlap
):
    assert is_cache_valid(
        valid_cache_data,
        pdf_hashes,
        model,
        chunk_size,
        chunk_overlap,
    ) is False


def test_missing_cache_returns_none(tmp_path):
    assert load_cache(tmp_path / "missing.pkl") is None


def test_corrupted_cache_returns_none(tmp_path):
    cache_file = tmp_path / "corrupted.pkl"
    cache_file.write_bytes(b"not a valid pickle")

    assert load_cache(cache_file) is None


def test_cache_without_embeddings_is_invalid(valid_cache_data):
    valid_cache_data.pop("embeddings")

    assert is_cache_valid(
        valid_cache_data,
        {"documents/sample.pdf": "abc123"},
        "gemini-embedding-2",
        500,
        50,
    ) is False
