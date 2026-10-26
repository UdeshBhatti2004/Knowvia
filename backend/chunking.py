# chunk_size = 500 — each chunk contains up to 500 characters.
# overlap = 50 — the next chunk starts 50 characters before the previous chunk ends.
# start += chunk_size - overlap — moves forward by 450 characters each time.
# The re module is used to egular expression module. It helps you search, match, split, and
#  replace text using patterns.

import re


def chunk_text(text, chunk_size=500, overlap=50):
    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("Overlap must be non-negative and smaller than chunk size")

    # Split text at known section headings
    sections = re.split(
        r"(?m)^(?=Refund Policy|Class Schedule|Interview Opportunities|Course Fees|Contact and Support)",
        text
    )

    chunks = []

    for section in sections:
        section = section.strip()

        if not section:
            continue

        # Keep short sections together
        if len(section) <= chunk_size:
            chunks.append(section)
            continue

        # Split longer sections into overlapping chunks
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
            overlap=overlap
        )

        for chunk in text_chunks:
            all_chunks.append({
                "text": chunk,
                "source": page["source"],
                "page": page["page"]
            })

    return all_chunks




if __name__ == "__main__":
    sample_text = (
        "Refund requests are allowed within 7 days. "
        "Classes run Monday to Friday. "
        "Students receive 3 interview opportunities. "
    ) * 10

    chunks = chunk_text(sample_text)

    print("Total Chunks", len(chunks))


    for index , chunk in enumerate( chunks , start = 1):
        print(f"\n --- Chunk {index} ---")
        print(chunk)