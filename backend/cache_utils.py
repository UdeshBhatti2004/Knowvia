
import pickle


def is_cache_valid(
    cached_data,
    pdf_hashes,
    embedding_model,
    chunk_size,
    chunk_overlap,
):
    return (
        cached_data.get("pdf_hashes") == pdf_hashes
        and cached_data.get("embedding_model") == embedding_model
        and cached_data.get("chunk_size") == chunk_size
        and cached_data.get("chunk_overlap") == chunk_overlap
        and isinstance(cached_data.get("embeddings"), list)
    )


def load_cache(cache_file):
    try:
        with open(cache_file, "rb") as file:
            cached_data = pickle.load(file)

        if not isinstance(cached_data, dict):
            return None

        return cached_data

    except (OSError, EOFError, pickle.UnpicklingError, ValueError):
        return None


def save_cache(cache_file, cache_data):
    with open(cache_file, "wb") as file:
        pickle.dump(cache_data, file)
