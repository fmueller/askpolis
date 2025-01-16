import os

import pymupdf4llm
import requests
from fastapi import FastAPI
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_postgres import PGVector
from langchain_text_splitters import MarkdownHeaderTextSplitter, MarkdownTextSplitter

app = FastAPI()

chat_model = ChatOllama(model="llama3.1")
prompt = ChatPromptTemplate.from_messages([
    ("system", """
    You are AskPolis, an helpful AI agent answering user questions about the political landscape backed by official documents.
    You only use the provided chunks to answer the question.
    You respond in Markdown and use paragraphs to structure your answer.
    You only provide the answer to the question without any additional fluff.
    
    Chunks:
    
    {documents}
    """),
    ("human", "Question: {question}")
])

passage_embeddings = HuggingFaceEmbeddings(model_name="jinaai/jina-embeddings-v3",
                                           model_kwargs={"trust_remote_code": True},
                                           encode_kwargs={"normalize_embeddings": True,
                                                          "task": "retrieval.passage"})
query_embeddings = HuggingFaceEmbeddings(model_name="jinaai/jina-embeddings-v3",
                                         model_kwargs={"trust_remote_code": True},
                                         encode_kwargs={"normalize_embeddings": True,
                                                        "task": "retrieval.query"})

connection = os.getenv("DATABASE_URL")
vector_store = PGVector(embeddings=passage_embeddings, collection_name="embeddings", connection=connection,
                        embedding_length=1024, create_extension=False)


@app.get("/")
def read_root():
    return {"healthy": True}


@app.get("/v0/search")
def search(query: str, limit: int = 5):
    if limit < 1:
        limit = 5
    results = vector_store.similarity_search_with_score_by_vector(embedding=query_embeddings.embed_query(query),
                                                                  k=limit)
    return {"query": query, "search_results": results}


@app.get("/v0/answers")
def get_answers(question: str):
    print("Question:", question)
    print("Querying...")
    results = vector_store.similarity_search_with_score_by_vector(embedding=query_embeddings.embed_query(question), k=5)

    if len(results) == 0:
        print("Downloading PDF")
        response = requests.get(
            "https://www.grundsatzprogramm-cdu.de/sites/www.grundsatzprogramm-cdu.de/files/downloads/240507_cdu_gsp_2024_beschluss_parteitag_final_1.pdf")

        with open("temp.pdf", "wb") as f:
            f.write(response.content)

        print("Read PDF to Markdown")
        chunks = pymupdf4llm.to_markdown("temp.pdf", show_progress=False, page_chunks=True)
        docs = [
            Document(
                page_content=chunk["text"],
                metadata=chunk["metadata"]
            ) for chunk in chunks
        ]

        headers_to_split_on = [
            ("#", "header_1"),
            ("##", "header_2"),
            ("###", "header_3"),
        ]

        header_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on, strip_headers=False)
        # TODO concatenate by respecting - word dividers and merging words that are split by the chunking
        md_chunks = header_splitter.split_text("\n\n".join([doc.page_content for doc in docs]))

        markdown_splitter = MarkdownTextSplitter(chunk_size=2000, chunk_overlap=400)
        final_chunks = markdown_splitter.split_documents(md_chunks)
        print(f"Final chunks: {len(final_chunks)}")
        vector_store.add_documents(final_chunks)
        print("Querying again...")
        results = vector_store.similarity_search_with_score_by_vector(embedding=query_embeddings.embed_query(question),
                                                                      k=5)

    context = "\n\n".join(["<chunk>\n" + r[0].page_content + "\n</chunk>" for r in results])
    chain = prompt | chat_model
    print("Invoking LLM chain...")
    answer = chain.invoke({
        "documents": context,
        "question": question
    })

    return {"question": question, "answer": answer.content, "search_results": results}
