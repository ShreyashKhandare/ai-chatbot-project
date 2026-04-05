import os
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

load_dotenv()

VECTOR_DB_PATH = "vectorstore/faiss_index"

embeddings = OpenAIEmbeddings()
vector_store = None


def load_pdf(path):
    global vector_store

    loader = PyPDFLoader(path)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = splitter.split_documents(docs)

    vector_store = FAISS.from_documents(chunks, embeddings)
    vector_store.save_local(VECTOR_DB_PATH)


def load_vectorstore():
    global vector_store

    if os.path.exists(VECTOR_DB_PATH):
        vector_store = FAISS.load_local(
            VECTOR_DB_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )


def search_docs(query):
    global vector_store

    if vector_store is None:
        return ""

    results = vector_store.similarity_search(query, k=3)
    return "\n\n".join([doc.page_content for doc in results])