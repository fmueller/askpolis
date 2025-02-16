import pymupdf4llm
import requests
from fastapi import FastAPI
from FlagEmbedding import FlagReranker
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from pydantic import BaseModel

from askpolis.core import MarkdownSplitter
from askpolis.logging import configure_logging, get_logger

configure_logging()

logger = get_logger(__name__)
logger.info("Starting AskPolis API...")

app = FastAPI()

chat_model = ChatOllama(model="llama3.1")
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
    You are AskPolis, an helpful AI agent answering user questions about politics backed by documents.
    You only use the provided document chunks to answer the question.
    You respond in Markdown and use paragraphs to structure your answer.
    You only provide the answer to the question without any additional fluff.

    Chunks:

    {documents}
    """,
        ),
        ("human", "Question: {question}"),
    ]
)

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    model_kwargs={"trust_remote_code": True},
    encode_kwargs={"normalize_embeddings": True},
)

vector_store = InMemoryVectorStore(embeddings)

reranker = FlagReranker("BAAI/bge-reranker-v2-m3")


class HealthResponse(BaseModel):
    healthy: bool


class SearchResponse(BaseModel):
    query: str
    search_results: list[tuple[Document, float]]


class AnswerResponse(BaseModel):
    question: str
    answer: str
    search_results: list[tuple[Document, float]]


@app.get("/")
def read_root() -> HealthResponse:
    return HealthResponse(healthy=True)


@app.get("/v0/search")
def search(query: str, limit: int = 5, reranking: bool = False) -> SearchResponse:
    logger.info_with_attrs("Searching...", {"query": query, "limit": limit, "reranking": reranking})
    if limit < 1:
        limit = 5

    query_size = limit
    if reranking:
        query_size *= 2

    results = vector_store.similarity_search_with_score_by_vector(embedding=embeddings.embed_query(query), k=query_size)
    if len(results) == 0:
        logger.warning_with_attrs("No results found", {"query": query})

    if reranking and len(results) > 0:
        logger.info("Reranking...")
        reranked_scores = reranker.compute_score([(query, r[0].page_content) for r in results], normalize=True)
        ranked_docs = [doc for _, doc in sorted(zip(reranked_scores, results), reverse=True)][:limit]
        return SearchResponse(
            query=query,
            search_results=sorted(
                [(doc[0], score) for doc, score in zip(ranked_docs, reranked_scores)], key=lambda x: x[1], reverse=True
            ),
        )

    return SearchResponse(query=query, search_results=results)


@app.get("/v0/answers")
def get_answers(question: str) -> AnswerResponse:
    logger.info_with_attrs("Querying...", {"question": question})
    results = vector_store.similarity_search_with_score_by_vector(embedding=embeddings.embed_query(question), k=5)

    if len(results) == 0:
        logger.info("Downloading PDF...")
        response = requests.get(
            "https://www.grundsatzprogramm-cdu.de/sites/www.grundsatzprogramm-cdu.de/files/downloads/240507_cdu_gsp_2024_beschluss_parteitag_final_1.pdf"
        )

        with open("temp.pdf", "wb") as f:
            f.write(response.content)

        logger.info("Read PDF to Markdown...")
        parsed_markdown = pymupdf4llm.to_markdown("temp.pdf", show_progress=False, page_chunks=True)
        pages = [Document(page_content=md["text"], metadata=md["metadata"]) for md in parsed_markdown]
        final_chunks = MarkdownSplitter(chunk_size=2000, chunk_overlap=400).split(pages)
        logger.info(f"Final chunks: {len(final_chunks)}")
        vector_store.add_documents(final_chunks)
        logger.info("Querying again...")
        results = vector_store.similarity_search_with_score_by_vector(embedding=embeddings.embed_query(question), k=5)

    context = "\n\n".join(["<chunk>\n" + r[0].page_content + "\n</chunk>" for r in results])
    chain = prompt | chat_model
    logger.info("Invoking LLM chain...")
    answer = chain.invoke({"documents": context, "question": question})

    return AnswerResponse(question=question, answer=answer.pretty_repr(), search_results=results)
