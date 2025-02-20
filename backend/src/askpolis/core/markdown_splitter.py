import enum
import json
import re

from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from askpolis.core.pdf_reader import PdfReader
from askpolis.logging import get_logger

logger = get_logger(__name__)


class HeaderLevel(str, enum.Enum):
    H1 = "#"
    H2 = "##"
    H3 = "###"
    H4 = "####"
    H5 = "#####"
    H6 = "######"


PAGE_MARKER_REGEX = r"<!-- ASKPOLIS_PAGE_MARKER: (.*?) -->"


class MarkdownSplitter:
    def __init__(self, chunk_size: int, chunk_overlap: int):
        self._header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[(header.value, header.name) for header in HeaderLevel], strip_headers=False
        )
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap, separators=["\n\n", "\n", ".", "?", "!", " ", ""]
        )

    def split(self, markdown_documents: list[Document]) -> list[Document]:
        # Join pages with a marker that encodes each page's metadata
        joined_lines = []
        chunk_id = 0
        for i, page in enumerate(markdown_documents):
            next_page = None
            if i < len(markdown_documents) - 1:
                next_page = markdown_documents[i + 1]

            page.page_content = MarkdownSplitter._replace_horizontal_rule_with_newline(page.page_content)
            ends_with_md = MarkdownSplitter._ends_with_hyphen(page.page_content)
            if next_page and ends_with_md:
                page.page_content = MarkdownSplitter._merge_hyphenated_texts(page.page_content, next_page.page_content)
                next_page.page_content = MarkdownSplitter._replace_horizontal_rule_with_newline(next_page.page_content)
                next_page.page_content = MarkdownSplitter._remove_first_word(next_page.page_content)

            if re.search(PAGE_MARKER_REGEX, page.page_content):
                logger.warning("Existing page marker found in document content. Document may be malformed.")
                page.page_content = re.sub(PAGE_MARKER_REGEX, "", page.page_content)

            joined_lines.append(f"<!-- ASKPOLIS_PAGE_MARKER: {json.dumps(page.metadata)} -->")
            cleaned_page = MarkdownSplitter._clean_hyphenated_words_with_markdown_formatting(page.page_content)
            cleaned_page = MarkdownSplitter._remove_whitespaces_surrounding_each_line(cleaned_page)
            if len(cleaned_page) > 0:
                joined_lines.append(cleaned_page)

        joined_text = "\n".join(joined_lines)

        all_page_markers = re.findall(PAGE_MARKER_REGEX, joined_text)
        if not all_page_markers:
            raise ValueError("No page markers found in the document.")

        chunked_documents = []

        last_page_marker = json.loads(all_page_markers[0])
        header_chunks = self._header_splitter.split_text(joined_text)

        for header_chunk in header_chunks:
            markers = list(re.finditer(PAGE_MARKER_REGEX, header_chunk.page_content))
            cleaned_chunk = re.sub(PAGE_MARKER_REGEX, "", header_chunk.page_content)
            cleaned_chunk = re.sub(r"\n+", "\n", cleaned_chunk)
            # the header splitter may have added whitespaces at the start or end of the chunk
            cleaned_chunk = MarkdownSplitter._remove_whitespaces_surrounding_each_line(cleaned_chunk)

            for sub_chunk in self._splitter.split_text(cleaned_chunk):
                # Find the closest page marker prior to the sub_chunk within the header_chunk
                current_page_marker = last_page_marker
                sub_chunk_start_index = header_chunk.page_content.find(sub_chunk)
                markers_before_sub_chunk = [m for m in markers if m.start() <= sub_chunk_start_index]
                if markers_before_sub_chunk:
                    try:
                        current_page_marker = json.loads(markers_before_sub_chunk[-1].group(1))
                    except Exception as e:
                        logger.warning_with_attrs(
                            "Failed to parse page marker:",
                            attrs={"marker": markers_before_sub_chunk[-1].group(1), "error": e},
                        )
                        current_page_marker = last_page_marker

                if "chunk_id" in current_page_marker or "headers" in current_page_marker:
                    logger.warning_with_attrs(
                        "Page marker contains chunk_id or headers. These will be overwritten.",
                        attrs={"page_marker": current_page_marker},
                    )

                chunked_documents.append(
                    Document(
                        page_content=sub_chunk,
                        metadata={
                            "chunk_id": chunk_id,
                            "headers": header_chunk.metadata,
                            **current_page_marker,
                        },
                    )
                )
                chunk_id += 1

            if markers:
                try:
                    last_page_marker = json.loads(markers[-1].group(1))
                except Exception as e:
                    logger.error_with_attrs(
                        "Failed to parse page marker:", attrs={"marker": markers[-1].group(1), "error": e}
                    )

        return chunked_documents

    @staticmethod
    def _ends_with_hyphen(text: str) -> bool:
        end_of_non_md_text = len(text)
        position_md_formatting_at_end = MarkdownSplitter._position_markdown_formatting_end(text)
        if position_md_formatting_at_end != -1:
            end_of_non_md_text = position_md_formatting_at_end

        cleaned_end = text[:end_of_non_md_text].rstrip()
        if len(cleaned_end) < 2:
            return False

        ends_with_hyphen = cleaned_end.endswith("-")
        return cleaned_end[-2].isalnum() and ends_with_hyphen

    @staticmethod
    def _merge_hyphenated_texts(text_1: str, text_2: str) -> str:
        end_of_non_md_text = len(text_1)
        position_md_formatting_at_end = MarkdownSplitter._position_markdown_formatting_end(text_1)
        if position_md_formatting_at_end != -1:
            end_of_non_md_text = position_md_formatting_at_end

        markdown_formatting = text_1[end_of_non_md_text:]
        merged_text_1 = (
            text_1[:end_of_non_md_text].rstrip(" \t\r\n-") + MarkdownSplitter._first_word(text_2) + markdown_formatting
        )
        return merged_text_1

    @staticmethod
    def _position_markdown_formatting_end(text: str) -> int:
        stripped = text.rstrip()
        if len(stripped) < 2:
            return -1

        if stripped.endswith("**") or stripped.endswith("__") or stripped.endswith("~~"):
            return len(stripped) - 2

        return -1

    @staticmethod
    def _first_word(text: str) -> str:
        # TODO use same logic as in _remove_first_word
        return text.lstrip().split()[0]

    @staticmethod
    def _remove_first_word(text: str) -> str:
        stripped = text.lstrip()
        first_whitespace = stripped.find(" ")
        if first_whitespace == -1:
            first_whitespace = stripped.find("\t")
        if first_whitespace == -1:
            return ""
        if first_whitespace == len(stripped) - 1:
            return stripped[:first_whitespace]
        return stripped[first_whitespace + 1 :]

    @staticmethod
    def _replace_horizontal_rule_with_newline(text: str) -> str:
        cleaned_text = re.sub(r"\n\s*---+\s*\n", "\n", text)
        cleaned_text = re.sub(r"\n\s*\*\*\*+\s*\n", "\n", cleaned_text)
        cleaned_text = re.sub(r"\n\s*___+\s*\n", "\n", cleaned_text)
        return cleaned_text

    @staticmethod
    def _clean_hyphenated_words_with_markdown_formatting(text: str) -> str:
        text = re.sub(r"(\w+)-\s*\*\*\s*\n\s*(\w+)", r"\1\2**\n", text)
        text = re.sub(r"(\w+)-\s*~~\s*\n\s*(\w+)", r"\1\2~~\n", text)
        text = re.sub(r"(\w+)-\s*__\s*\n\s*(\w+)", r"\1\2__\n", text)
        text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2\n", text)
        text = re.sub(r"[ ]+", " ", text)
        return text.strip()

    @staticmethod
    def _remove_whitespaces_surrounding_each_line(text: str) -> str:
        lines = text.split("\n")
        lines = [line.strip() for line in lines]
        return "\n".join(lines)


if __name__ == "__main__":
    # For testing purposes
    markdown_doc = PdfReader("temp.pdf").to_markdown()
    assert markdown_doc is not None
    print(markdown_doc.pages[71].content)
    print("-----")
    print(markdown_doc.pages[72].content)
    print("SPLITTING")
    print("-----")
    splitter = MarkdownSplitter(chunk_size=2000, chunk_overlap=400)
    result = splitter.split(markdown_doc.to_langchain_documents())
    for r in result:
        if r.metadata["page"] == 71 or r.metadata["page"] == 72:
            print(r.page_content)
            print("-----")
    print(len(result))
