from pathlib import Path

from askpolis.core import PdfReader


def test_pdf_to_markdown_conversion(resources_dir: Path) -> None:
    pdf_reader = PdfReader(str(resources_dir / "sample_test.pdf"))
    parsed_document = pdf_reader.to_markdown()

    assert parsed_document is not None
    assert len(parsed_document.pages) == 5


def test_text_formatting_is_preserved(resources_dir: Path) -> None:
    pdf_reader = PdfReader(str(resources_dir / "sample_test.pdf"))
    parsed_document = pdf_reader.to_markdown()

    assert parsed_document is not None
    assert len(parsed_document.pages) == 5
    assert "**This is bold red text.**" in parsed_document.pages[1].content
    assert "*This is italic green text.*" in parsed_document.pages[1].content


def test_dehyphenation(resources_dir: Path) -> None:
    pdf_reader = PdfReader(str(resources_dir / "sample_test_hyphenated.pdf"))
    parsed_document = pdf_reader.to_markdown()

    assert parsed_document is not None
    assert len(parsed_document.pages) == 5
    assert "hyphenation" in parsed_document.pages[1].content
    assert "example" in parsed_document.pages[1].content
