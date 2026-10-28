from types import SimpleNamespace

import pytest

from app.knowledge import cache_manager
from app.knowledge.cache_utils import load_cache


def make_chunks(count):
    return [{"text": f"chunk {i}"} for i in range(count)]


def call_it(cache_file, chunks, get_embedding, **extra):
    return cache_manager.get_or_create_embeddings(
        str(cache_file),
        {"a.pdf": "hash"},
        "gemini-embedding-2",
        500,
        50,
        chunks,
        get_embedding,
        **extra,
    )


@pytest.fixture
def waits(monkeypatch):
    recorded = []
    fake_time = SimpleNamespace(
        sleep=lambda seconds: recorded.append(seconds),
        monotonic=lambda: 0.0,
    )
    monkeypatch.setattr(cache_manager, "time", fake_time)
    return recorded


def test_embeds_in_batches_and_pauses_between_them(tmp_path, waits):
    calls = []

    def fake_embedding(text):
        calls.append(text)
        return [float(len(text))]

    result = call_it(
        tmp_path / "c.pkl", make_chunks(5), fake_embedding,
        requests_per_minute=2,
    )

    assert calls == [f"chunk {i}" for i in range(5)]
    assert result == [[7.0]] * 5
    assert waits == [60, 60]  # 3 batches -> 2 pauses


def test_no_pause_when_everything_fits_in_one_batch(tmp_path, waits):
    call_it(
        tmp_path / "c.pkl", make_chunks(3), lambda text: [1.0],
        requests_per_minute=10,
    )
    assert waits == []


def test_failure_keeps_finished_batches(tmp_path, waits):
    cache_file = tmp_path / "c.pkl"

    def failing_embedding(text):
        if text == "chunk 3":
            raise RuntimeError("429")
        return [1.0]

    with pytest.raises(RuntimeError):
        call_it(
            cache_file, make_chunks(5), failing_embedding,
            requests_per_minute=2,
        )

    # Batch 1 (chunks 0-1) finished and was saved before the failure.
    assert len(load_cache(str(cache_file))["chunk_embeddings"]) == 2

    retried = []

    def working_embedding(text):
        retried.append(text)
        return [1.0]

    call_it(
        cache_file, make_chunks(5), working_embedding,
        requests_per_minute=2,
    )

    # The retry only embeds what is still missing.
    assert retried == ["chunk 2", "chunk 3", "chunk 4"]