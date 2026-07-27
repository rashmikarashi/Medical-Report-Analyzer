"""
Streamlit web app for the Medical Report Analyzer.
Deploy free on Streamlit Community Cloud: https://share.streamlit.io

Run locally:
    streamlit run app.py
"""

import json
import streamlit as st
from medical_report_analyzer import parse_results, summarize

st.set_page_config(page_title="Medical Report Analyzer", page_icon="🩺")

st.title("🩺 Medical Report Analyzer")
st.write(
    "Upload a lab report (as text) or paste its contents below. "
    "The tool flags values outside standard reference ranges. "
    "**This is a screening aid, not a diagnosis.**"
)

uploaded_file = st.file_uploader("Upload a .txt report", type=["txt"])
pasted_text = st.text_area("...or paste report text here", height=200)

text = ""
if uploaded_file is not None:
    text = uploaded_file.read().decode("utf-8", errors="ignore")
elif pasted_text.strip():
    text = pasted_text

if st.button("Analyze") and text:
    results = parse_results(text)
    summary = summarize(results)

    st.subheader("Summary")
    st.text(summary)

    if results:
        st.subheader("Detailed Results")
        st.dataframe(
            [
                {
                    "Test": r.name.title(),
                    "Value": r.value,
                    "Unit": r.unit,
                    "Reference Range": f"{r.ref_low}-{r.ref_high}",
                    "Status": r.status.upper(),
                }
                for r in results
            ]
        )
        with st.expander("Raw JSON"):
            st.code(json.dumps([r.__dict__ for r in results], indent=2), language="json")
elif st.button("Clear"):
    st.rerun()

st.caption(
    "⚠️ Automated screening only. Always consult a licensed clinician "
    "about your actual results."
)
