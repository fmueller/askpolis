import tempfile
from typing import Any, Optional, Union

import pymupdf4llm
from langchain_core.documents import Document as LangchainDocument
from pydantic import BaseModel

from askpolis.logging import get_logger

logger = get_logger(__name__)


class PdfPage(BaseModel):
    page_number: int
    content: str
    metadata: dict[str, Any]


class PdfDocument(BaseModel):
    pages: list[PdfPage]
    path: str

    def to_langchain_documents(self) -> list[LangchainDocument]:
        return [LangchainDocument(page_content=page.content, metadata=page.metadata) for page in self.pages]


class PdfReader:
    def __init__(self, pdf_source: Union[str, bytes]):
        self.pdf_source = pdf_source
        self.temp_file: Any = None

    def _get_pdf_path(self) -> str:
        if isinstance(self.pdf_source, bytes):
            if self.temp_file is None:
                self.temp_file = tempfile.NamedTemporaryFile(delete=True, suffix=".pdf")  # noqa: SIM115
                self.temp_file.write(self.pdf_source)
                self.temp_file.flush()
            assert self.temp_file is not None
            return str(self.temp_file.name)
        return self.pdf_source

    def to_markdown(self) -> Optional[PdfDocument]:
        try:
            return self._to_markdown_with_merging_concatenated_words()
        except Exception as e:
            logger.warning_with_attrs(
                "Failed to parse PDF with merging concatenated words. Trying without it.",
                attrs={"error": e, "pdf_path": self._get_pdf_path()},
            )
            try:
                parsed_markdown = pymupdf4llm.to_markdown(
                    self._get_pdf_path(), show_progress=False, page_chunks=True, extract_words=False
                )
                return PdfDocument(
                    path=self._get_pdf_path(),
                    pages=[
                        PdfPage(
                            content=str(parsed_page["text"]),
                            page_number=int(parsed_page["metadata"]["page"]),
                            metadata=dict[str, Any](parsed_page["metadata"]),
                        )
                        for parsed_page in parsed_markdown
                    ],
                )
            except Exception as e:
                logger.error_with_attrs(
                    "Failed to parse PDF without merging concatenated words.",
                    attrs={"error": e, "pdf_path": self._get_pdf_path()},
                )
                return None
        finally:
            if self.temp_file is not None:
                self.temp_file.close()

    def _to_markdown_with_merging_concatenated_words(self) -> Optional[PdfDocument]:
        # issue: https://github.com/pymupdf/RAG/issues/214
        # from the issue: "TEXT_DEHYPHENATE - this is and will need to be kept off, because otherwise word particles
        # will be included in boundary boxes of lines and spans - making the compilation into markdown impossible.
        # Exposure to the API cannot be granted."
        parsed_markdown = pymupdf4llm.to_markdown(
            self._get_pdf_path(), show_progress=False, page_chunks=True, extract_words=True
        )
        for page in parsed_markdown:
            cleaned_words = []
            words = page["words"]
            i = 0
            for word in page["text"].split(" "):
                if i >= len(words):
                    cleaned_words.append(word)
                    continue

                current_word = words[i][4]
                current_row = int(words[i][5])
                end_of_row = i < len(words) - 1 and int(words[i + 1][5]) == current_row + 1 and words[i + 1][7] == 0
                if end_of_row:
                    if current_word.endswith("-"):
                        cleaned_words.append(
                            word.replace("\n", "").replace("-**", "").replace("-~~", "").replace("-__", "")
                        )
                        i += 1
                    else:
                        cleaned_words.append(word)
                        count_newlines = word.count("\n\n")
                        if (
                            count_newlines > 0
                            and i + count_newlines < len(words)
                            and word.endswith(words[i + count_newlines][4])
                        ):
                            i += count_newlines
                else:
                    cleaned_words.append(word)
                i += 1
            page["text"] = " ".join(cleaned_words)

        return PdfDocument(
            path=self._get_pdf_path(),
            pages=[
                PdfPage(
                    content=str(parsed_page["text"]),
                    page_number=int(parsed_page["metadata"]["page"]),
                    metadata=dict[str, Any](parsed_page["metadata"]),
                )
                for parsed_page in parsed_markdown
            ],
        )
