import unittest.mock
from unittest.mock import patch

from askpolis.core.models import Document
from askpolis.core.pdf_reader import PdfReader

pdf_reader = PdfReader("dummy_path.pdf")


@patch("askpolis.core.pdf_reader.pymupdf4llm.to_markdown")
def test_to_markdown_with_merging_words(mock_to_markdown: unittest.mock.Mock) -> None:
    mock_to_markdown.return_value = [
        {
            "text": "This is a test\ndocument.",
            "words": [
                ["This", 0, 0, 0, "This", 0, 0, 0],
                ["is", 0, 0, 0, "is", 0, 0, 0],
                ["a", 0, 0, 0, "a", 0, 0, 0],
                ["test", 0, 0, 0, "test-", 0, 0, 0],
                ["document.", 0, 0, 0, "document.", 1, 0, 0],
            ],
            "metadata": {"page": 1},
        }
    ]

    result = pdf_reader.to_markdown()

    assert isinstance(result, Document)
    assert result.path == "dummy_path.pdf"
    assert len(result.pages) == 1
    assert result.pages[0].content == "This is a testdocument."
    assert result.pages[0].page_number == 1


@patch("askpolis.core.pdf_reader.pymupdf4llm.to_markdown")
def test_to_markdown_with_default_fallback(mock_to_markdown: unittest.mock.Mock) -> None:
    mock_to_markdown.side_effect = [
        Exception("Test exception"),
        [{"text": "This is a test document without dehyphenation.", "metadata": {"page": 1}}],
    ]

    result = pdf_reader.to_markdown()

    assert isinstance(result, Document)
    assert result.path == "dummy_path.pdf"
    assert len(result.pages) == 1
    assert result.pages[0].content == "This is a test document without dehyphenation."
    assert result.pages[0].page_number == 1


@patch("askpolis.core.pdf_reader.pymupdf4llm.to_markdown")
def test_pdf_reader_to_markdown_and_all_markdown_transforms_fail(mock_to_markdown: unittest.mock.Mock) -> None:
    mock_to_markdown.side_effect = [Exception("First exception"), Exception("Second exception")]

    result = pdf_reader.to_markdown()

    assert result is None
