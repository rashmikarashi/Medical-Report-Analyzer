"""
rag_pipeline.py
----------------
Core Retrieval-Augmented Generation (RAG) logic for the PDF Chatbot.

Pipeline:
  1. Load PDF(s) with LangChain's PyPDFLoader
  2. Split into overlapping chunks with RecursiveCharacterTextSplitter
  3. Embed chunks (OpenAI embeddings or local HuggingFace embeddings)
  4. Store/persist vectors in a ChromaDB collection
  5. Build a conversational retrieval chain (retriever + LLM) for Q&A

Kept separate from app.py so the retrieval/embedding logic can be tested,
reused, or swapped out independently of the Streamlit UI.
"""

import os
import shutil
import tempfile
from typing import List

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate


CHROMA_PERSIST_DIR = "chroma_db"

QA_PROMPT_TEMPLATE = """You are a helpful assistant answering questions about a specific PDF document.
Use ONLY the following retrieved context to answer the question. If the answer
is not contained in the context, say "I couldn't find that in the document"
instead of guessing or using outside knowledge.

Always mention which part of the document (page number, if available) supports
your answer when possible.

Context:
{context}

Chat History:
{chat_history}

Question: {question}

Answer (clear, concise, grounded strictly in the context above):"""

QA_PROMPT = PromptTemplate(
    template=QA_PROMPT_TEMPLATE,
    input_variables=["context", "chat_history", "question"],
)


def load_and_split_pdfs(pdf_paths: List[str], chunk_size: int = 1000, chunk_overlap: int = 150):
    """Load one or more PDFs and split them into overlapping text chunks."""
    all_docs = []
    for path in pdf_paths:
        loader = PyPDFLoader(path)
        docs = loader.load()
        all_docs.extend(docs)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(all_docs)


def get_embeddings(embedding_provider: str, openai_api_key: str = None):
    """Return an embeddings object: OpenAI (needs API key) or local HuggingFace (free, no key)."""
    if embedding_provider == "OpenAI":
        return OpenAIEmbeddings(api_key=openai_api_key, model="text-embedding-3-small")
    else:
        # Runs locally, no API key required — good default for demos/free tiers
        return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


def build_vectorstore(chunks, embeddings, collection_name: str = "pdf_chatbot", persist: bool = True):
    """Embed chunks and store them in a (optionally persisted) ChromaDB collection."""
    persist_directory = CHROMA_PERSIST_DIR if persist else None
    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory=persist_directory,
    )
    return vectordb


def load_existing_vectorstore(embeddings, collection_name: str = "pdf_chatbot"):
    """Reload a previously persisted ChromaDB collection from disk."""
    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
    )


def clear_vectorstore():
    """Delete the persisted ChromaDB directory (used when starting fresh with a new PDF)."""
    if os.path.exists(CHROMA_PERSIST_DIR):
        shutil.rmtree(CHROMA_PERSIST_DIR)


def build_qa_chain(vectordb, llm_provider: str, api_key: str, model: str, k: int = 4):
    """Build a ConversationalRetrievalChain backed by the given vector store and LLM."""
    if llm_provider == "OpenAI":
        llm = ChatOpenAI(api_key=api_key, model=model, temperature=0.2)
    elif llm_provider == "Groq":
        from langchain_groq import ChatGroq
        llm = ChatGroq(api_key=api_key, model=model, temperature=0.2)
    else:
        raise ValueError(f"Unknown LLM provider: {llm_provider}")

    retriever = vectordb.as_retriever(search_kwargs={"k": k})

    memory = ConversationBufferMemory(
        memory_key="chat_history", return_messages=True, output_key="answer"
    )

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": QA_PROMPT},
        return_source_documents=True,
    )
    return chain


def save_uploaded_pdfs(uploaded_files) -> List[str]:
    """Write Streamlit UploadedFile objects to a temp dir and return their paths."""
    paths = []
    tmp_dir = tempfile.mkdtemp()
    for f in uploaded_files:
        path = os.path.join(tmp_dir, f.name)
        with open(path, "wb") as out:
            out.write(f.read())
        paths.append(path)
    return paths
