"""
app.py
------
Medical Report Analyzer — a Streamlit app that uses an LLM (OpenAI or Groq)
to explain medical/lab reports in plain language via structured prompt templates.

Run with:
    streamlit run app.py

IMPORTANT: This tool is for educational purposes only. It does not provide
medical diagnoses and is not a substitute for professional medical advice.
"""

import io
import streamlit as st
from pypdf import PdfReader

from prompts import SYSTEM_PROMPT, build_analysis_prompt, build_followup_prompt
from llm_client import chat_completion, OPENAI_MODELS, GROQ_MODELS


# ----------------------------- Page setup -----------------------------
st.set_page_config(
    page_title="Medical Report Analyzer",
    page_icon="🩺",
    layout="centered",
)

st.title("🩺 Medical Report Analyzer")
st.caption("Upload or paste a medical/lab report and get a plain-language explanation.")

st.warning(
    "⚠️ This app is an educational tool only. It does **not** diagnose conditions "
    "or replace advice from a licensed healthcare professional. Always consult "
    "your doctor about your results.",
    icon="⚠️",
)

# ----------------------------- Session state -----------------------------
if "report_text" not in st.session_state:
    st.session_state.report_text = ""
if "analysis" not in st.session_state:
    st.session_state.analysis = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ----------------------------- Sidebar: API config -----------------------------
with st.sidebar:
    st.header("⚙️ Settings")

    provider = st.selectbox("LLM Provider", ["OpenAI", "Groq"], index=0)

    api_key = st.text_input(
        f"{provider} API Key",
        type="password",
        help="Your key is used only for this session and is never stored or logged.",
    )

    if provider == "OpenAI":
        model = st.selectbox("Model", OPENAI_MODELS, index=0)
    else:
        model = st.selectbox("Model", GROQ_MODELS, index=0)

    language = st.selectbox(
        "Explanation language",
        ["English", "Hindi", "Hinglish", "Spanish", "French"],
        index=0,
    )

    temperature = st.slider("Creativity (temperature)", 0.0, 1.0, 0.3, 0.1)

    st.divider()
    st.caption(
        "Get a free API key:\n\n"
        "- OpenAI: platform.openai.com/api-keys\n"
        "- Groq: console.groq.com/keys"
    )


# ----------------------------- Input section -----------------------------
st.subheader("1. Provide your report")

tab_upload, tab_paste = st.tabs(["📄 Upload file", "✏️ Paste text"])

with tab_upload:
    uploaded_file = st.file_uploader(
        "Upload a PDF or TXT file", type=["pdf", "txt"], accept_multiple_files=False
    )
    if uploaded_file is not None:
        if uploaded_file.type == "application/pdf":
            try:
                reader = PdfReader(io.BytesIO(uploaded_file.read()))
                extracted = "\n".join(
                    (page.extract_text() or "") for page in reader.pages
                )
                st.session_state.report_text = extracted
                st.success(f"Extracted {len(extracted)} characters from PDF.")
            except Exception as e:
                st.error(f"Could not read PDF: {e}")
        else:
            st.session_state.report_text = uploaded_file.read().decode("utf-8", errors="ignore")
            st.success("Text file loaded.")

with tab_paste:
    pasted = st.text_area(
        "Paste report text here",
        value=st.session_state.report_text,
        height=250,
        placeholder="e.g. Complete Blood Count (CBC): Hemoglobin 10.2 g/dL (Low)...",
    )
    if pasted != st.session_state.report_text:
        st.session_state.report_text = pasted

with st.expander("Preview report text"):
    st.text(st.session_state.report_text[:3000] or "No report text provided yet.")


# ----------------------------- Analysis section -----------------------------
st.subheader("2. Run analysis")

analyze_clicked = st.button("🔍 Analyze Report", type="primary", use_container_width=True)

if analyze_clicked:
    if not api_key:
        st.error(f"Please enter your {provider} API key in the sidebar.")
    elif not st.session_state.report_text.strip():
        st.error("Please upload or paste a report first.")
    else:
        with st.spinner("Analyzing report with the LLM..."):
            try:
                user_prompt = build_analysis_prompt(
                    st.session_state.report_text, language=language
                )
                result = chat_completion(
                    provider=provider,
                    api_key=api_key,
                    model=model,
                    system_prompt=SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    temperature=temperature,
                )
                st.session_state.analysis = result
                st.session_state.chat_history = []  # reset follow-up chat for new report
            except Exception as e:
                st.error(f"Something went wrong calling the {provider} API: {e}")

if st.session_state.analysis:
    st.divider()
    st.subheader("📋 Analysis Result")
    st.markdown(st.session_state.analysis)

    st.download_button(
        "⬇️ Download analysis (Markdown)",
        data=st.session_state.analysis,
        file_name="medical_report_analysis.md",
        mime="text/markdown",
    )

    # ----------------------------- Follow-up Q&A -----------------------------
    st.divider()
    st.subheader("3. Ask a follow-up question")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    followup_q = st.chat_input("Ask something about this report...")
    if followup_q:
        st.session_state.chat_history.append({"role": "user", "content": followup_q})
        with st.chat_message("user"):
            st.markdown(followup_q)

        if not api_key:
            answer = f"⚠️ Please enter your {provider} API key in the sidebar first."
        else:
            try:
                fu_prompt = build_followup_prompt(
                    st.session_state.report_text, followup_q
                )
                answer = chat_completion(
                    provider=provider,
                    api_key=api_key,
                    model=model,
                    system_prompt=SYSTEM_PROMPT,
                    user_prompt=fu_prompt,
                    temperature=temperature,
                )
            except Exception as e:
                answer = f"Something went wrong calling the {provider} API: {e}"

        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)

st.divider()
st.caption(
    "Made for educational purposes. Not affiliated with any medical institution. "
    "No report data is stored server-side; everything lives only in your browser session."
)
