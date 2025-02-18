import random
import string

from faker import Faker
from langchain_core.documents import Document

from askpolis.core.markdown_splitter import MarkdownSplitter

faker = Faker()

splitter = MarkdownSplitter(2000, 400)


def random_string(length: int) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def test_empty_string_is_not_split() -> None:
    result = splitter.split([Document("")])

    assert len(result) == 0


def test_one_text_line_is_not_split() -> None:
    result = splitter.split([Document("Hello World!")])

    assert len(result) == 1
    assert result[0].page_content == "Hello World!"
    assert result[0].metadata == {"headers_metadata": {}, "markdown_metadata": {}}


def test_split_by_header() -> None:
    headers = [faker.name() for _ in range(3)]

    result = splitter.split([Document(f"# {headers[0]}\nabc\n\n## {headers[1]}\ndef\n\n### {headers[2]}\nghi")])

    assert len(result) == 3
    assert result[0].page_content == f"# {headers[0]}\nabc"
    assert result[1].page_content == f"## {headers[1]}\ndef"
    assert result[2].page_content == f"### {headers[2]}\nghi"


def test_split_by_header_with_paragraph() -> None:
    headers = [faker.name() for _ in range(3)]
    paragraphs = [faker.paragraph() for _ in range(3)]
    headers_with_paragraph = [f"{'#' * (i + 1)} {header}\n{paragraphs[i]}" for i, header in enumerate(headers)]

    result = splitter.split([Document("\n\n".join(headers_with_paragraph))])

    assert len(result) == 3
    assert result[0].page_content == f"# {headers[0]}\n{paragraphs[0]}"
    assert result[1].page_content == f"## {headers[1]}\n{paragraphs[1]}"
    assert result[2].page_content == f"### {headers[2]}\n{paragraphs[2]}"


def test_split_by_header_with_long_paragraphs() -> None:
    headers = [random_string(5) for _ in range(6)]
    paragraph = " ".join([f"word {i}" for i in range(10)])
    paragraphs = [paragraph for _ in range(6)]
    headers_with_paragraph = [f"{'#' * (i + 1)} {header}\n{paragraphs[i]}" for i, header in enumerate(headers)]

    result = MarkdownSplitter(20, 0).split([Document("\n\n".join(headers_with_paragraph))])

    expected_chunks_pattern = [
        "word 0 word 1 word",
        "2 word 3 word 4",
        "word 5 word 6 word",
        "7 word 8 word 9",
    ]

    assert len(result) == 30
    chunks_count = 0
    header_count = 0
    for chunk in result:
        if chunk.page_content.startswith("#"):
            assert chunk.page_content == f"{'#' * (header_count + 1)} {headers[header_count]}"
            header_count += 1
        else:
            assert chunk.page_content == f"{expected_chunks_pattern[chunks_count % 4]}"
            chunks_count += 1


def test_header_level_metadata() -> None:
    result = splitter.split([Document("# First\nabc\n\n## Second\nabc\n\n### Third\nabc")])

    assert len(result) == 3
    assert len(result[0].metadata["headers_metadata"]) == 1
    assert len(result[1].metadata["headers_metadata"]) == 2
    assert len(result[2].metadata["headers_metadata"]) == 3


def test_joins_metadata_across_pages() -> None:
    pages = [
        Document(page_content="# First\nabc", metadata={"page": 1}),
        Document(page_content="## Second\nabc", metadata={"page": 2}),
        Document(page_content="\nabc", metadata={"page": 3}),
    ]

    result = splitter.split(pages)

    assert len(result) == 2
    assert result[0].metadata["markdown_metadata"]["page"] == 1
    assert result[1].metadata["markdown_metadata"]["page"] == 2


def test_joins_metadata_across_pages_when_content_does_not_start_with_header() -> None:
    pages = [
        Document(page_content="abc", metadata={"page": 1}),
        Document(page_content="# First\nabc", metadata={"page": 2}),
        Document(page_content="\nabc", metadata={"page": 3}),
    ]

    result = splitter.split(pages)

    assert len(result) == 2
    assert result[0].metadata["markdown_metadata"]["page"] == 1
    assert result[1].metadata["markdown_metadata"]["page"] == 2


def test_joining_metadata_with_headers_on_same_page() -> None:
    pages = [
        Document(page_content="# First\nabc\n\n## Second\nabc", metadata={"page": 1}),
        Document(page_content="# Third\nabc", metadata={"page": 2}),
    ]

    result = splitter.split(pages)

    assert len(result) == 3
    assert result[0].metadata["markdown_metadata"]["page"] == 1
    assert result[1].metadata["markdown_metadata"]["page"] == 1
    assert result[2].metadata["markdown_metadata"]["page"] == 2


def test_with_page_marker_in_document() -> None:
    pages = [
        Document(page_content='<!-- ASKPOLIS_PAGE_MARKER: {"page": 23} -->\n# First\nabc', metadata={"page": 1}),
        Document(page_content="# Second\nabc", metadata={"page": 2}),
        Document(page_content="# Third\nabc", metadata={"page": 3}),
    ]

    result = splitter.split(pages)

    assert len(result) == 3
    assert result[0].metadata["markdown_metadata"]["page"] == 1
    assert result[1].metadata["markdown_metadata"]["page"] == 2
    assert result[2].metadata["markdown_metadata"]["page"] == 3


def test_with_page_break_in_a_paragraph() -> None:
    pages = [
        Document(page_content=f"# Header 1\n{random_string(10)}", metadata={"page": 1}),
        Document(page_content=f"#### Header 2\n{random_string(5)}", metadata={"page": 2}),
        Document(page_content=f"##### Header 3\n{random_string(10)}", metadata={"page": 3}),
        Document(page_content=f"## Header 4\n{random_string(10)}", metadata={"page": 4}),
    ]

    result = MarkdownSplitter(chunk_size=20, chunk_overlap=0).split(pages)

    assert len(result) == 7
    assert result[0].metadata["markdown_metadata"]["page"] == 1
    assert result[1].metadata["markdown_metadata"]["page"] == 1
    assert result[2].metadata["markdown_metadata"]["page"] == 2
    assert result[3].metadata["markdown_metadata"]["page"] == 3
    assert result[4].metadata["markdown_metadata"]["page"] == 3
    assert result[5].metadata["markdown_metadata"]["page"] == 4
    assert result[6].metadata["markdown_metadata"]["page"] == 4


def test_merging_words_split_by_hyphens() -> None:
    pages = [
        Document(page_content="abc- \ndef and thi-\n s i-\ns and n\n  -ot", metadata={"page": 1}),
        Document(page_content="Generati-**\nonen", metadata={"page": 2}),
        Document(page_content="Hou-~~\n   se", metadata={"page": 3}),
        Document(page_content="You-__\n   th", metadata={"page": 4}),
    ]

    result = splitter.split(pages)

    assert len(result) == 1
    assert result[0].page_content == "abcdef\nand this\nis\nand n\n-ot\nGenerationen**\nHouse~~\nYouth__"


def test_merging_words_split_by_hyphens_and_newlines() -> None:
    pages = [
        Document(page_content="abc-", metadata={"page": 1}),
        Document(page_content="def and thi-\n", metadata={"page": 2}),
        Document(page_content="\ns i-", metadata={"page": 3}),
        Document(page_content="\ns", metadata={"page": 4}),
    ]

    result = splitter.split(pages)

    assert len(result) == 1
    assert result[0].page_content == "abcdef\nand this\nis"


def test_merging_words_split_by_hyphens_and_newlines_and_markdown_formatting() -> None:
    pages = [
        Document(page_content="** abc-", metadata={"page": 1}),
        Document(page_content="\n def** and thi-  **\n", metadata={"page": 2}),
        Document(page_content="\n s\n", metadata={"page": 3}),
        Document(page_content="* i-  \n ", metadata={"page": 4}),
        Document(page_content="\n s", metadata={"page": 5}),
    ]

    result = splitter.split(pages)

    assert len(result) == 1
    assert result[0].page_content == "** abcdef**\nand this**\n* is"


def test_merging_across_multiple_pages() -> None:
    pages = [
        Document(page_content="# First\nabc-", metadata={"page": 1}),
        Document(page_content="\n   def and thi-\n", metadata={"page": 2}),
        Document(page_content="\ns i-", metadata={"page": 3}),
        Document(page_content="s", metadata={"page": 4}),
        Document(page_content="# Second\nabc-", metadata={"page": 5}),
        Document(page_content="def and thi-**     \n", metadata={"page": 6}),
        Document(page_content="s i-", metadata={"page": 7}),
        Document(page_content="  \ns", metadata={"page": 8}),
    ]

    result = splitter.split(pages)

    assert len(result) == 2
    assert result[0].page_content == "# First\nabcdef\nand this\nis"
    assert result[1].page_content == "# Second\nabcdef\nand this**\nis"


def test_not_merging_words_due_to_markdown_divider_lines() -> None:
    pages = [
        Document(page_content="abc\n---\n", metadata={"page": 1}),
        Document(page_content="def", metadata={"page": 2}),
    ]

    result = splitter.split(pages)

    assert len(result) == 1
    assert result[0].page_content == "abc\ndef"


def test_merging_across_markdown_divider_lines() -> None:
    pages = [
        Document(page_content="abc-\n---\n", metadata={"page": 1}),
        Document(page_content="def", metadata={"page": 2}),
    ]

    result = splitter.split(pages)

    assert len(result) == 1
    assert result[0].page_content == "abcdef"


def test_merging_across_markdown_dividers_at_end_of_page() -> None:
    pages = [
        Document(page_content="abc-----", metadata={"page": 1}),
        Document(page_content="###### Headline\nabc", metadata={"page": 2}),
    ]

    result = splitter.split(pages)

    assert len(result) == 2
    assert result[0].page_content == "abc-----"
    assert result[1].page_content == "###### Headline\nabc"
