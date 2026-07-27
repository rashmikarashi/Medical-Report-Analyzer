"""
app.py
------
PDF Chatbot — upload one or more PDFs and chat with them using a
LangChain Retrieval-Augmented Generation (RAG) pipeline backed by ChromaDB.

Run with:
    streamlit run app.py
"""

import streamlit as st

from rag_pipeline import (
    load_and_split_pdfs,
    get_embeddings,
    build_vectorstore,
    clear_vectorstore,
    build_qa_chain,
    save_uploaded_pdfs,
)

st.set_page_config(page_title="PDF Chatbot (LangChain + ChromaDB)", page_icon="📚", layout="centered")

st.title("📚 PDF Chatbot")
st.caption("LangChain + Embeddings + ChromaDB — ask questions about your own PDFs.")

# ----------------------------- Session state -----------------------------
for key, default in {
    "vectordb": None,
    "qa_chain": None,
    "chat_history": [],
    "processed_files": [],
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ----------------------------- Sidebar: config -----------------------------
with st.sidebar:
    st.header("⚙️ Settings")

    llm_provider = st.selectbox("LLM Provider", ["OpenAI", "Groq"], index=0)
    llm_model = st.text_input(
        "LLM model name",
        value="gpt-4o-mini" if llm_provider == "OpenAI" else "llama-3.3-70b-versatile",
    )
    llm_api_key = st.text_input(f"{llm_provider} API Key", type="password")

    st.divider()

    embedding_provider = st.selectbox(
        "Embeddings",
        ["HuggingFace (local, free)", "OpenAI"],
        index=0,
        help="HuggingFace embeddings run locally and don't need an API key. "
             "OpenAI embeddings are higher quality but require an OpenAI key.",
    )
    embedding_provider_key = "OpenAI" if embedding_provider == "OpenAI" else "HuggingFace"

    openai_embed_key = ""
    if embedding_provider_key == "OpenAI":
        openai_embed_key = st.text_input("OpenAI API Key (for embeddings)", type="password")

    top_k = st.slider("Chunks to retrieve per question (k)", 1, 10, 4)

    st.divider()
    if st.button("🗑️ Reset knowledge base", use_container_width=True):
        clear_vectorstore()
        st.session_state.vectordb = None
        st.session_state.qa_chain = None
        st.session_state.chat_history = []
        st.session_state.processed_files = []
        st.success("Cleared. Upload a new PDF to start fresh.")


# ----------------------------- Upload & index -----------------------------
st.subheader("1. Upload your PDF(s)")

uploaded_files = st.file_uploader(
    "Choose one or more PDF files", type=["pdf"], accept_multiple_files=True
)

col1, col2 = st.columns(2)
with col1:
    chunk_size = st.number_input("Chunk size", min_value=200, max_value=3000, value=1000, step=100)
with col2:
    chunk_overlap = st.number_input("Chunk overlap", min_value=0, max_value=500, value=150, step=50)

process_clicked = st.button("⚡ Process & Index PDFs", type="primary", use_container_width=True)

if process_clicked:
    if not uploaded_files:
        st.error("Please upload at least one PDF.")
    elif embedding_provider_key == "OpenAI" and not openai_embed_key:
        st.error("Please provide an OpenAI API key for embeddings, or switch to local HuggingFace embeddings.")
    else:
        with st.spinner("Reading, chunking, and embedding your PDF(s)... this may take a moment."):
            try:
                paths = save_uploaded_pdfs(uploaded_files)
                chunks = load_and_split_pdfs(paths, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
                embeddings = get_embeddings(embedding_provider_key, openai_api_key=openai_embed_key)
                vectordb = build_vectorstore(chunks, embeddings)

                st.session_state.vectordb = vectordb
                st.session_state.processed_files = [f.name for f in uploaded_files]
                st.session_state.chat_history = []
                st.session_state.qa_chain = None  # rebuilt lazily once LLM key is available

                st.success(f"Indexed {len(chunks)} chunks from {len(uploaded_files)} file(s).")
            except Exception as e:
                st.error(f"Failed to process PDFs: {e}")

if st.session_state.processed_files:
    st.info("📁 Indexed: " + ", ".join(st.session_state.processed_files))


# ----------------------------- Chat -----------------------------
st.subheader("2. Chat with your document(s)")

if st.session_state.vectordb is None:
    st.caption("Upload and process a PDF above to start chatting.")
else:
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("Sources"):
                    for s in msg["sources"]:
                        st.markdown(f"- Page {s}")

    question = st.chat_input("Ask a question about your PDF(s)...")
    if question:
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        if not llm_api_key:
            answer, sources = f"⚠️ Please enter your {llm_provider} API key in the sidebar.", []
        else:
            try:
                if st.session_state.qa_chain is None:
                    st.session_state.qa_chain = build_qa_chain(
                        st.session_state.vectordb,
                        llm_provider=llm_provider,
                        api_key=llm_api_key,
                        model=llm_model,
                        k=top_k,
                    )

                with st.spinner("Thinking..."):
                    result = st.session_state.qa_chain.invoke({"question": question})
                    answer = result["answer"]
                    sources = sorted(
                        {
                            (doc.metadata.get("page", "?") + 1)
                            if isinstance(doc.metadata.get("page"), int)
                            else doc.metadata.get("page", "?")
                            for doc in result.get("source_documents", [])
                        }
                    )
            except Exception as e:
                answer, sources = f"Something went wrong: {e}", []

        st.session_state.chat_history.append(
            {"role": "assistant", "content": answer, "sources": sources}
        )
        with st.chat_message("assistant"):
            st.markdown(answer)
            if sources:
                with st.expander("Sources"):
                    for s in sources:
                        st.markdown(f"- Page {s}")

st.divider()
st.caption(
    "Built with LangChain, ChromaDB, and Streamlit. Answers are grounded strictly "
    "in the uploaded document(s) via retrieval — the model is instructed not to use outside knowledge."
)
