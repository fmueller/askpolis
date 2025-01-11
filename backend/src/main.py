import pymupdf4llm
import requests
from fastapi import FastAPI
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_text_splitters import MarkdownHeaderTextSplitter, MarkdownTextSplitter

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

    question = "Was sind die Werte der CDU?"

    response = requests.get(
        "https://www.grundsatzprogramm-cdu.de/sites/www.grundsatzprogramm-cdu.de/files/downloads/240507_cdu_gsp_2024_beschluss_parteitag_final_1.pdf")

    with open("temp.pdf", "wb") as f:
        f.write(response.content)

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
    md_chunks = header_splitter.split_text("\n\n".join([doc.page_content for doc in docs]))

    markdown_splitter = MarkdownTextSplitter(chunk_size=2000, chunk_overlap=400)
    final_chunks = markdown_splitter.split_documents(md_chunks)
    print(f"Final chunks: {len(final_chunks)}")
    vector_store = InMemoryVectorStore.from_documents(final_chunks, passage_embeddings)

    results = vector_store.similarity_search_with_score(query=question, k=5, embeddings=query_embeddings)
    context = "\n\n".join(["<chunk>\n" + r[0].page_content + "\n</chunk>" for r in results])

    chain = prompt | chat_model
    answer = chain.invoke({
        "documents": context,
        "question": question
    })

    return {"answer": answer.content, "search_results": results}
