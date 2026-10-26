
from cache_utils import is_cache_valid, load_cache, save_cache


def get_or_create_embeddings(
    cache_file,
    pdf_hashes,
    embedding_model,
    chunk_size,
    chunk_overlap,
    knowledge_base,
    get_embedding,
    pdf_modified_times=None,
):
    cached_data = load_cache(cache_file)

    if is_cache_valid(
        cached_data or {},
        pdf_hashes,
        embedding_model,
        chunk_size,
        chunk_overlap,
    ):
        return cached_data["embeddings"]

    embeddings = [
        get_embedding(document["text"])
        for document in knowledge_base
    ]

    save_cache(
        cache_file,
        {
            "embeddings": embeddings,
            "pdf_modified_times": pdf_modified_times or {},
            "pdf_hashes": pdf_hashes,
            "embedding_model": embedding_model,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        },
    )

    return embeddings
