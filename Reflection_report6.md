# Reflection Report — Medical Report Analyzer

## Domain & Problem
Healthcare. Patients and even busy clinicians often receive lab reports
full of unfamiliar abbreviations and numeric values with no context on
what's normal. This tool automates the first-pass screening step:
extracting values and flagging anything outside standard reference
ranges, so a person can quickly see what to ask their doctor about.

## Approach
I chose a **rule-based, deterministic** design over an LLM-based one for
this core version:
- **Transparency**: every flag traces back to an explicit reference
  range, which matters a lot in a medical context — no hallucinated
  numbers.
- **No cost/dependency on an external API key**, making it runnable
  anywhere instantly.
- **Simplicity**: a regex-based parser plus a lookup table is easy to
  audit, test, and extend.

The trade-off is reduced flexibility: the parser only recognizes lines
matching a `name: value unit` shape and a fixed vocabulary of test
names. A generative-AI layer (e.g., an LLM call to summarize findings
in natural language, or to normalize messier formats) would be a
natural next iteration, but was intentionally left out of the initial
version to keep the tool deterministic, dependency-light, and free to
run.

## What Worked Well
- The regex + dictionary approach correctly parsed and classified all
  13 values in the sample report on the first test run.
- Separating extraction, parsing, and summarization into distinct
  functions made the code easy to test and reason about.

## Challenges & Limitations
- **Naming variance**: real-world reports use many aliases for the same
  test (e.g., "Hb", "Hgb", "Hemoglobin"). The current alias map is
  minimal and would need to grow significantly for production use.
- **Scanned PDFs**: the tool relies on extractable text; scanned image
  PDFs would need OCR (e.g., `pytesseract`), which was left out to keep
  dependencies minimal.
- **Reference range generalization**: ranges don't adjust for age, sex,
  or pregnancy status, which can matter clinically.

## Future Improvements
1. Expand the alias/vocabulary table or replace the regex parser with
   an LLM-based extraction step for messier, non-standard report layouts.
2. Add OCR support for scanned reports.
3. Support age/sex-adjusted reference ranges.
4. Add a simple web UI (Streamlit/Flask) for non-technical users.

## Day 7 — Deployment & Capstone Wrap-Up
For the capstone, I added a **Streamlit web app** (`app.py`) on top of the
existing core logic, so the tool is usable by non-technical people, not
just from the command line. The app reuses the same `parse_results` and
`summarize` functions from `medical_report_analyzer.py` — no logic was
duplicated, which kept the deployed version consistent with the
already-tested CLI version and reduced risk of divergent bugs.

**Deployment choice**: Streamlit Community Cloud, because it's free,
deploys directly from a GitHub repo with zero server management, and is
well-suited to small data/ML tools like this one.

**What I'd do differently with more time**: add automated tests (e.g.,
`pytest`) run via GitHub Actions on every push, and containerize with
Docker for portability across hosting providers beyond Streamlit Cloud.

## Ethical Considerations
The tool explicitly labels its output as a **screening aid, not a
diagnosis**, and includes a disclaimer recommending clinician review.
This is a hard requirement for any healthcare-adjacent tool to avoid
misleading users into self-diagnosis or delaying real medical care.
