import io

import fitz
import pymupdf4llm
import requests
from fastapi import FastAPI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_text_splitters import MarkdownTextSplitter

app = FastAPI()


@app.get("/")
def read_root():
    return {"healthy": True}


# just some test code to test the idea locally
@app.get("/rag-test")
def rag_test():
    chat_model = ChatOllama(model="llama3.1")
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are AskPolis, an helpful AI agent answering user questions about the political landscape backed by official documents."),
        ("system", "You only use the provided chunks to answer the question."),
        ("system", "Chunks:\n\n{documents}"),
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

    question = "Wie sind die Werte der CDU?"

    response = requests.get(
        "https://www.grundsatzprogramm-cdu.de/sites/www.grundsatzprogramm-cdu.de/files/downloads/240507_cdu_gsp_2024_beschluss_parteitag_final_1.pdf")
    md_text = pymupdf4llm.to_markdown(fitz.open(stream=io.BytesIO(response.content), filetype="pdf"))

    text_splitter = MarkdownTextSplitter(chunk_size=2000, chunk_overlap=200)
    splits = text_splitter.split_text(md_text)
    vector_store = InMemoryVectorStore.from_texts(splits, passage_embeddings)

    results = vector_store.similarity_search_with_score(query=question, k=10, embeddings=query_embeddings)
    context = "\n\n".join(["<chunk>\n" + r[0].page_content + "\n</chunk>" for r in results])

    chain = prompt | chat_model
    answer = chain.invoke({
        "documents": context,
        "question": question
    })

    return {"answer": answer.content, "search_results": results}
