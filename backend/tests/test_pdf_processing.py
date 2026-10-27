
from unittest.mock import MagicMock, patch

from app.knowledge.pdf_reader import extract_text_from_pdf
from app.knowledge.chunking import chunk_text, chunk_pages

import pytest


def test_extract_text_from_pdf():
    fake_page = MagicMock()
    fake_page.extract_text.return_value = "  Welcome to Knowvia.  "

    fake_reader = MagicMock()
    fake_reader.pages = [fake_page]

    with patch("app.knowledge.pdf_reader.PdfReader", return_value=fake_reader):
        result = extract_text_from_pdf("documents/sample.pdf")

    assert len(result) == 1
    assert result[0]["text"] == "Welcome to Knowvia."
    assert result[0]["source"] == "sample.pdf"
    assert result[0]["page"] == 1




def test_skips_empty_pages():
    empty_page = MagicMock()
    empty_page.extract_text.return_value = "   "

    blank_page = MagicMock()
    blank_page.extract_text.return_value = None

    valid_page = MagicMock()
    valid_page.extract_text.return_value = "Knowvia PDF content"

    fake_reader = MagicMock()
    fake_reader.pages = [empty_page, blank_page, valid_page]

    with patch("app.knowledge.pdf_reader.PdfReader", return_value=fake_reader):
        result = extract_text_from_pdf("documents/sample.pdf")

    assert len(result) == 1
    assert result[0]["text"] == "Knowvia PDF content"
    assert result[0]["page"] == 3



def test_extracts_multiple_pages_in_order():
    page1 = MagicMock()
    page1.extract_text.return_value = "Introduction to Knowvia"

    page2 = MagicMock()
    page2.extract_text.return_value = "Refund policy: 7 days"

    page3 = MagicMock()
    page3.extract_text.return_value = "Course duration: 3 months"

    fake_reader = MagicMock()
    fake_reader.pages = [page1, page2, page3]

    with patch("app.knowledge.pdf_reader.PdfReader", return_value=fake_reader):
        result = extract_text_from_pdf("documents/business_info.pdf")

    assert len(result) == 3
    assert [page["page"] for page in result] == [1, 2, 3]
    assert [page["source"] for page in result] == [
        "business_info.pdf",
        "business_info.pdf",
        "business_info.pdf",
    ]
    assert result[0]["text"] == "Introduction to Knowvia"
    assert result[1]["text"] == "Refund policy: 7 days"
    assert result[2]["text"] == "Course duration: 3 months"


def test_short_text_stays_in_one_chunk():
    text = "Welcome to Knowvia."

    chunks = chunk_text(text, chunk_size=100, overlap=10)

    assert len(chunks) == 1
    assert chunks[0] == text


def test_long_text_chunks_have_expected_overlap():
    text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 40  # 1040 characters

    chunks = chunk_text(text, chunk_size=500, overlap=50)

    assert len(chunks) > 1
    assert chunks[0][-50:] == chunks[1][:50]


def test_chunk_pages_preserves_source_and_page():
    pages = [
        {
            "text": "Refund requests are allowed within 7 days.",
            "source": "business_info.pdf",
            "page": 3,
        }
    ]

    chunks = chunk_pages(pages, chunk_size=100, overlap=10)

    assert len(chunks) == 1
    assert chunks[0]["text"] == "Refund requests are allowed within 7 days."
    assert chunks[0]["source"] == "business_info.pdf"
    assert chunks[0]["page"] == 3



def test_rejects_nonpositive_chunk_size():
    with pytest.raises(ValueError, match="Chunk size must be positive"):
        chunk_text("Some text", chunk_size=0)


def test_rejects_invalid_overlap():
    with pytest.raises(
        ValueError,
        match="Overlap must be non-negative and smaller than chunk size",
    ):
        chunk_text("Some text", chunk_size=100, overlap=100)



