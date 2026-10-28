import hashlib
import time
from concurrent.futures import ThreadPoolExecutor

from app.knowledge.cache_utils import (
    is_cache_valid,
    load_cache,
    save_cache,
)


def _chunk_key(embedding_model, text):
    """Stable key for one chunk: same model + same text = same embedding."""
    return hashlib.sha256(
        f"{embedding_model}\n{text}".encode("utf-8")
    ).hexdigest()


def get_or_create_embeddings(
    cache_file,
    pdf_hashes,
    embedding_model,
    chunk_size,
    chunk_overlap,
    knowledge_base,
    get_embedding,
    pdf_modified_times=None,
    max_workers=1,
    requests_per_minute=None,
):
    cached_data = load_cache(cache_file)

    # Fast path: nothing changed at all.
    if (
        is_cache_valid(
            cached_data or {},
            pdf_hashes,
            embedding_model,
            chunk_size,
            chunk_overlap,
        )
        and len(cached_data["embeddings"]) == len(knowledge_base)
    ):
        return cached_data["embeddings"]

    # Something changed: reuse the embedding of every chunk whose text we
    # have already embedded, and only call the API for the new chunks.
    chunk_cache = (cached_data or {}).get("chunk_embeddings") or {}

    keys = [
        _chunk_key(embedding_model, document["text"])
        for document in knowledge_base
    ]

    missing = {}  # key -> text, in first-seen order, no duplicates
    for key, document in zip(keys, knowledge_base):
        if key not in chunk_cache and key not in missing:
            missing[key] = document["text"]

    if missing:
        missing_keys = list(missing.keys())
        texts = list(missing.values())

        # Embed in batches that stay under the API's per-minute limit.
        batch_size = requests_per_minute or len(texts)

        for start in range(0, len(texts), batch_size):
            batch_started = time.monotonic()
            batch_texts = texts[start:start + batch_size]
            batch_keys = missing_keys[start:start + batch_size]

            if max_workers > 1 and len(batch_texts) > 1:
                with ThreadPoolExecutor(max_workers=max_workers) as pool:
                    batch_vectors = list(pool.map(get_embedding, batch_texts))
            else:
                batch_vectors = [get_embedding(text) for text in batch_texts]

            for key, vector in zip(batch_keys, batch_vectors):
                chunk_cache[key] = vector

            if start + batch_size < len(texts):
                # Save progress so a later failure doesn't lose this work.
                # "embeddings" is empty and the hashes don't match, so this
                # partial file can never be mistaken for a complete cache.
                save_cache(
                    cache_file,
                    {
                        "embeddings": [],
                        "chunk_embeddings": dict(chunk_cache),
                        "pdf_modified_times": {},
                        "pdf_hashes": {},
                        "embedding_model": embedding_model,
                        "chunk_size": chunk_size,
                        "chunk_overlap": chunk_overlap,
                    },
                )

                wait = 60 - (time.monotonic() - batch_started)
                if wait > 0:
                    print(
                        f"Embedding rate limit: pausing {wait:.0f}s "
                        f"({start + batch_size}/{len(texts)} new chunks done)."
                    )
                    time.sleep(wait)

    embeddings = [chunk_cache[key] for key in keys]

    save_cache(
        cache_file,
        {
            "embeddings": embeddings,
            # Keep only chunks that still exist, so the cache doesn't grow forever.
            "chunk_embeddings": {key: chunk_cache[key] for key in keys},
            "pdf_modified_times": pdf_modified_times or {},
            "pdf_hashes": pdf_hashes,
            "embedding_model": embedding_model,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        },
    )

    return embeddings