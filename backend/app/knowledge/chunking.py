
import re


def chunk_text(text, chunk_size=500, overlap=50):
    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "Overlap must be non-negative and smaller than chunk size"
        )

    sections = re.split(
        r"(?m)^(?=Refund Policy|Class Schedule|Interview Opportunities|Course Fees|Contact and Support)",
        text,
    )

    chunks = []

    for section in sections:
        section = section.strip()

        if not section:
            continue

        if len(section) <= chunk_size:
            chunks.append(section)
            continue

        start = 0

        while start < len(section):
            end = start + chunk_size
            chunk = section[start:end].strip()

            if chunk:
                chunks.append(chunk)

            start += chunk_size - overlap

    return chunks


def chunk_pages(pages, chunk_size=500, overlap=50):
    all_chunks = []

    for page in pages:
        text_chunks = chunk_text(
            page["text"],
            chunk_size=chunk_size,
            overlap=overlap,
        )

        for chunk in text_chunks:
            all_chunks.append({
                "text": chunk,
                "source": page["source"],
                "page": page["page"],
            })

    return all_chunks
