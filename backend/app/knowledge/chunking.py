import re

# Split order: paragraphs, then lines, then sentences, then words.
_SPLITTERS = (
    re.compile(r"\n\s*\n"),
    re.compile(r"\n"),
    re.compile(r"(?<=[.!?])\s+"),
    re.compile(r"\s+"),
)


def _split_to_units(text, chunk_size, overlap, level=0):
    """Break text into pieces of at most chunk_size, cutting at the
    largest natural boundary available."""
    text = text.strip()
    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    if level >= len(_SPLITTERS):
        # A single "word" longer than chunk_size: hard cut as a last resort,
        # with the same overlap as normal chunks.
        pieces = []
        step = chunk_size - overlap
        start = 0
        while True:
            pieces.append(text[start:start + chunk_size])
            if start + chunk_size >= len(text):
                break
            start += step
        return pieces

    units = []
    for part in _SPLITTERS[level].split(text):
        units.extend(_split_to_units(part, chunk_size, overlap, level + 1))
    return units


def chunk_text(text, chunk_size=500, overlap=50):
    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "Overlap must be non-negative and smaller than chunk size"
        )

    units = _split_to_units(text, chunk_size, overlap)

    chunks = []
    current = []
    current_len = 0

    for unit in units:
        added = len(unit) + (1 if current else 0)

        if current and current_len + added > chunk_size:
            chunks.append("\n".join(current))

            # Carry over trailing whole units (up to `overlap` characters)
            # so the next chunk starts at a boundary, not mid-sentence.
            carried = []
            carried_len = 0
            for previous in reversed(current):
                extra = len(previous) + (1 if carried else 0)
                if carried_len + extra > overlap:
                    break
                carried.insert(0, previous)
                carried_len += extra
            current = carried
            current_len = carried_len

            # Drop carried units if they would push this chunk over the limit.
            while current and current_len + 1 + len(unit) > chunk_size:
                removed = current.pop(0)
                current_len -= len(removed) + (1 if current else 0)

            added = len(unit) + (1 if current else 0)

        current.append(unit)
        current_len += added

    if current:
        chunks.append("\n".join(current))

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