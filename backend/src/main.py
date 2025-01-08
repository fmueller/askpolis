from fastapi import FastAPI
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter

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

    loader = PyPDFLoader("C:/Users/felix/Downloads/240507_CDU_GSP_2024_Beschluss_Parteitag_FINAL.pdf")
    pages = loader.load()
    pages = "\n".join([page.page_content for page in pages])
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    splits = text_splitter.split_documents([Document(page_content=pages)])
    vector_store = InMemoryVectorStore.from_documents(splits, passage_embeddings)
    results = vector_store.similarity_search_with_score(query=question, k=10, embeddings=query_embeddings)
    context = "\n\n".join(["<chunk>\n" + r[0].page_content + "\n</chunk>" for r in results])
    print(context)

    chain = prompt | chat_model
    answer = chain.invoke({
        "documents": context,
        "question": question
    })

    return {"answer": answer.content, "search_results": results}
