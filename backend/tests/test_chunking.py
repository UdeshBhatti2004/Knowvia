import textwrap

import pytest

from app.knowledge.chunking import chunk_pages, chunk_text


def test_short_text_is_one_chunk():
    assert chunk_text("Hello world.") == ["Hello world."]


def test_empty_text_gives_no_chunks():
    assert chunk_text("   \n\n ") == []


def test_chunks_never_exceed_size():
    text = " ".join(f"Sentence number {i} is here." for i in range(200))
    for chunk in chunk_text(text, chunk_size=200, overlap=30):
        assert len(chunk) <= 200


def test_chunks_start_and_end_on_sentence_boundaries():
    sentences = [f"This is sentence number {i}." for i in range(60)]
    text = " ".join(sentences)
    chunks = chunk_text(text, chunk_size=150, overlap=40)
    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.startswith("This is sentence")
        assert chunk.endswith(".")


def test_all_content_is_kept():
    sentences = [f"Fact {i} is true." for i in range(80)]
    chunks = chunk_text(" ".join(sentences), chunk_size=120, overlap=30)
    joined = "\n".join(chunks)
    for sentence in sentences:
        assert sentence in joined


def test_overlap_repeats_trailing_sentence():
    text = "Alpha one. Beta two. Gamma three. Delta four."
    chunks = chunk_text(text, chunk_size=25, overlap=12)
    assert len(chunks) > 1
    shared = set(chunks[0].split("\n")) & set(chunks[1].split("\n"))
    assert shared


def test_prefers_paragraph_breaks():
    text = ("A" * 40 + ".") + "\n\n" + ("B" * 40 + ".")
    assert chunk_text(text, chunk_size=50, overlap=0) == [
        "A" * 40 + ".",
        "B" * 40 + ".",
    ]


def test_very_long_word_is_hard_cut():
    text = "".join(chr(97 + i % 26) for i in range(250))
    chunks = chunk_text(text, chunk_size=100, overlap=10)
    assert all(len(c) <= 100 for c in chunks)
    assert chunks[0][-10:] == chunks[1][:10]
    assert chunks[0][:10] == text[:10]
    assert chunks[-1][-10:] == text[-10:]


def test_long_text_without_boundaries_has_exact_overlap():
    text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 40
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert len(chunks) > 1
    assert chunks[0][-50:] == chunks[1][:50]


def test_lines_wrapped_by_a_pdf_do_not_start_chunks_mid_sentence():
    adjectives = ["red", "quiet", "bright", "heavy", "gentle", "rapid", "narrow", "warm"]
    nouns = ["river", "engine", "garden", "bridge", "market", "forest", "harbor", "tunnel"]
    sentences = [
        f"This is the {a} story about the {n} near the old town."
        for a in adjectives
        for n in nouns
    ]
    wrapped = textwrap.fill(" ".join(sentences), width=70)
    assert "\n" in wrapped

    chunks = chunk_text(wrapped, chunk_size=200, overlap=60)

    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.startswith("This is the")
        assert chunk.endswith(".")


def test_unwrapping_keeps_questions_answers_and_short_lines_apart():
    text = (
        "Q: What is a task role?\n"
        "A: A role assumed temporarily by a service with no permanent credentials, safer\n"
        "for automation.\n"
        "Q: Why use it?\n"
        "Course Name: Python\n"
        "Duration: 3 months"
    )

    result = chunk_text(text, chunk_size=1000, overlap=0)[0]

    assert "safer for automation." in result
    assert "\nQ: Why use it?" in result
    assert "Course Name: Python\nDuration: 3 months" in result


def test_invalid_settings_raise():
    with pytest.raises(ValueError):
        chunk_text("text", chunk_size=0)
    with pytest.raises(ValueError):
        chunk_text("text", chunk_size=100, overlap=100)
    with pytest.raises(ValueError):
        chunk_text("text", chunk_size=100, overlap=-1)


def test_chunk_pages_keeps_source_and_page():
    pages = [{"text": "One.", "source": "a.pdf", "page": 3}]
    assert chunk_pages(pages) == [
        {"text": "One.", "source": "a.pdf", "page": 3}
    ]




def test_question_and_answer_stay_in_the_same_chunk():
    pairs = [
        f"Q: What is thing number {i}?\n"
        f"A: Thing number {i} is a small part of the system that does one job."
        for i in range(30)
    ]

    chunks = chunk_text("\n".join(pairs), chunk_size=200, overlap=40)

    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.startswith("Q:")
        assert chunk.count("Q:") == chunk.count("A:")


def test_sentence_split_by_a_page_break_is_rejoined():
    pages = [
        {
            "text": "Intro line.\nA service keeps tasks running, handles",
            "source": "a.pdf",
            "page": 1,
        },
        {
            "text": "restarts, and integrates with a load balancer. A cluster groups tasks.",
            "source": "a.pdf",
            "page": 2,
        },
    ]

    chunks = chunk_pages(pages)

    assert "handles restarts, and integrates with a load balancer." in chunks[0]["text"]
    assert chunks[1]["text"] == "A cluster groups tasks."
    # The input pages are not modified.
    assert pages[1]["text"].startswith("restarts,")


def test_page_breaks_are_left_alone_when_the_sentence_is_complete():
    pages = [
        {"text": "First page ends here.", "source": "a.pdf", "page": 1},
        {"text": "second page starts lowercase.", "source": "a.pdf", "page": 2},
        {"text": "Another file", "source": "b.pdf", "page": 1},
        {"text": "continues here.", "source": "c.pdf", "page": 1},
    ]

    chunks = chunk_pages(pages)

    assert [c["text"] for c in chunks] == [
        "First page ends here.",
        "second page starts lowercase.",
        "Another file",
        "continues here.",
    ]