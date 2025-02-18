from typing import Optional

import pymupdf4llm

from askpolis.core.models import Document, Page


class PdfReader:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    def to_markdown(self) -> Optional[Document]:
        # issue: https://github.com/pymupdf/RAG/issues/214
        parsed_markdown = pymupdf4llm.to_markdown(
            self.pdf_path, show_progress=False, page_chunks=True, extract_words=True
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
                # if word != current_word:
                #     print(f"word: {word}, current_word: {current_word}")
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

        return Document(
            path=self.pdf_path,
            pages=[
                Page(
                    content=str(parsed_page["text"]),
                    page_number=int(parsed_page["metadata"]["page"]),
                    metadata=parsed_page["metadata"],
                )
                for parsed_page in parsed_markdown
            ],
        )
