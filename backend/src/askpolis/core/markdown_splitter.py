import enum
import json
import re

from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

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
        self._splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    # TODO concatenate by respecting '-' word dividers and merging words that are split by the chunking
    def split(self, markdown_documents: list[Document]) -> list[Document]:
        # Join pages with a marker that encodes each page's metadata
        joined_lines = []
        for doc in markdown_documents:
            if re.search(PAGE_MARKER_REGEX, doc.page_content):
                logger.warning("Existing page marker found in document content. Document may be malformed.")
                doc.page_content = re.sub(PAGE_MARKER_REGEX, "", doc.page_content)

            joined_lines.append(f"<!-- ASKPOLIS_PAGE_MARKER: {json.dumps(doc.metadata)} -->")
            joined_lines.append(doc.page_content)

        joined_text = "\n".join(joined_lines)

        all_page_markers = re.findall(PAGE_MARKER_REGEX, joined_text)
        if not all_page_markers:
            raise ValueError("No page markers found in the document.")

        chunked_documents = []

        last_page_marker = json.loads(all_page_markers[0])
        header_chunks = self._header_splitter.split_text(joined_text)

        for header_chunk in header_chunks:
            markers = list(re.finditer(PAGE_MARKER_REGEX, header_chunk.page_content))
            cleaned_chunk = re.sub(PAGE_MARKER_REGEX, "", header_chunk.page_content).strip()

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
                chunked_documents.append(
                    Document(
                        page_content=sub_chunk,
                        metadata={"headers_metadata": header_chunk.metadata, "markdown_metadata": current_page_marker},
                    )
                )

            if markers:
                try:
                    last_page_marker = json.loads(markers[-1].group(1))
                except Exception as e:
                    logger.error_with_attrs(
                        "Failed to parse page marker:", attrs={"marker": markers[-1].group(1), "error": e}
                    )

        return chunked_documents
