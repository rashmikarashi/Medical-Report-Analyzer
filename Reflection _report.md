# Reflection Report — PDF Chatbot (LangChain + Embeddings + ChromaDB)

## 1. Objective
Build a chatbot that can answer questions about the contents of a user-supplied
PDF, using a proper Retrieval-Augmented Generation (RAG) pipeline: LangChain
for orchestration, an embeddings model to turn text into vectors, and ChromaDB
as the vector store.

## 2. What I Built
Users upload one or more PDFs, which are loaded page-by-page, split into
overlapping chunks, embedded, and stored in a persisted ChromaDB collection.
A `ConversationalRetrievalChain` then retrieves the top-k most relevant chunks
per question and passes them to an LLM (OpenAI or Groq) along with a prompt
that restricts answers strictly to the retrieved context and cites source
page numbers. Chat memory allows natural follow-up questions ("what about the
second point?") without re-stating context.

## 3. Design Decisions

- **Separating `rag_pipeline.py` from `app.py`**: All LangChain/ChromaDB logic
  lives outside the Streamlit file, so the retrieval pipeline can be reused or
  swapped (e.g., new vector store) without touching UI code.
- **Offering local HuggingFace embeddings alongside OpenAI**: This was a
  deliberate choice to make the app fully runnable at zero API cost for the
  embedding step, since embeddings are the part of RAG that's called most
  frequently (once per chunk at index time) and can add up in cost on paid
  APIs. The chat LLM call happens once per question, which is cheaper to gate
  behind an API key.
- **Strict "context-only" prompt template**: Early testing without this
  constraint caused the LLM to sometimes blend general knowledge with document
  content, making it unclear whether an answer was actually grounded in the
  PDF. Explicitly instructing the model to say "I couldn't find that in the
  document" when retrieval doesn't surface relevant chunks made behavior much
  more trustworthy and testable.
- **Persisting ChromaDB to disk (`chroma_db/`)**: Avoids needing to re-embed
  the same PDF on every app restart, which matters more as PDF size grows.
- **Source citations (page numbers) in the UI**: Makes it possible to actually
  verify the model's answer against the source document, which is important
  for any retrieval-based tool where hallucination risk exists.

## 4. Challenges Faced

- **Chunking trade-offs**: Too small a chunk size lost surrounding context
  (e.g., splitting a table row from its header); too large diluted retrieval
  precision. Settled on a default of 1000 characters with 150 overlap as a
  reasonable general-purpose starting point, exposed as adjustable sliders
  rather than hardcoding one "correct" value.
- **Keeping citations accurate**: LangChain's PDF loader stores 0-indexed page
  numbers in metadata; had to explicitly offset by 1 when displaying so page
  numbers matched what a user sees when opening the PDF.
- **Provider parity between OpenAI and Groq for the LLM step**: Handled by
  branching only inside `build_qa_chain()`, so the rest of the retrieval
  pipeline stays provider-agnostic.
- **Balancing free vs. paid options**: Wanted the app usable without any paid
  API key at all for indexing, which pushed toward defaulting to local
  HuggingFace embeddings even though OpenAI embeddings are generally higher
  quality — a deliberate trade-off favoring accessibility.

## 5. What I'd Improve With More Time

- Add OCR fallback (e.g. `pytesseract`) for scanned PDFs with no extractable text.
- Support hybrid search (keyword + vector) for queries where exact terms
  matter (IDs, codes, names).
- Add a lightweight eval set (sample PDF + expected answers) to catch
  regressions when prompt or chunking parameters change.
- Allow deleting/replacing individual documents from the ChromaDB collection
  instead of only a full reset.
- Stream LLM responses token-by-token instead of waiting for the full answer.

## 6. Key Takeaway
The quality of a RAG chatbot depends less on the LLM itself and more on the
retrieval pipeline around it — chunk size, embedding choice, and a prompt that
forces grounding in retrieved context all had a bigger visible impact on
answer trustworthiness than swapping the underlying chat model.
