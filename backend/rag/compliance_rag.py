import os
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DOC_PATH = os.path.join(BASE_DIR, "compliance_docs", "investment_guidelines.txt")

PERSIST_DIR = os.path.join(BASE_DIR, "rag", "vectorstore", "chroma_compliance_db")


def build_compliance_rag():

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # Fix — if the vectorstore already exists on disk, load it directly.
    # This avoids re-embedding the entire document on every server start
    # (previously took 5–20 s on each startup).
    if os.path.exists(PERSIST_DIR):
        return Chroma(
            persist_directory=PERSIST_DIR,
            embedding_function=embeddings
        )

    # First-time setup: load, split, embed and persist
    loader    = TextLoader(DOC_PATH)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    docs = splitter.split_documents(documents)

    vectordb = Chroma.from_documents(
        docs,
        embeddings,
        persist_directory=PERSIST_DIR
    )

    return vectordb