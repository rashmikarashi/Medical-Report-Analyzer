# Medical Report Analyzer

A lightweight Python tool that reads a lab/medical report (TXT or PDF),
extracts recognized test values, compares them against standard clinical
reference ranges, and generates a plain-English summary flagging
abnormal results.

## Features
- Accepts `.txt` or `.pdf` input
- Recognizes 14 common lab tests (hemoglobin, glucose, cholesterol, LDL,
  HDL, triglycerides, creatinine, ALT, AST, TSH, sodium, potassium, WBC,
  platelets)
- Flags each value as `low`, `normal`, or `high`
- Outputs structured JSON + a human-readable summary
- No external API keys or paid services required

## Project Structure
```
medical_report_analyzer.py   # Core script (parsing + analysis logic)
app.py                       # Streamlit web app (deployment entry point)
sample_report.txt            # Example input for testing
requirements.txt             # Python dependencies
README.md                    # This file
REFLECTION_REPORT.md         # Project reflection
```

## Setup
```bash
pip install -r requirements.txt
```

## Usage — Command Line
```bash
python medical_report_analyzer.py sample_report.txt
python medical_report_analyzer.py path/to/report.pdf
```

## Usage — Web App (local)
```bash
streamlit run app.py
```
Opens a browser UI to upload or paste a report and view flagged results.

## Deployment (Streamlit Community Cloud — free)
1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with
   GitHub.
3. Click **New app**, select this repo/branch, and set the main file to
   `app.py`.
4. Click **Deploy** — the app builds from `requirements.txt` automatically
   and gives you a public URL.

Any host that runs Python (Render, Railway, Hugging Face Spaces) also
works: install `requirements.txt` and run `streamlit run app.py`
(or `python medical_report_analyzer.py` for CLI-only use).

## Example Output
```
--- Summary ---
Analyzed 13 recognized test value(s).
5 value(s) fall outside standard reference ranges:
  - Glucose: 118.0 mg/dL (above normal range 70-99 mg/dL)
  - Cholesterol: 215.0 mg/dL (above normal range 0-200 mg/dL)
  ...
Note: This is an automated screening summary, not a diagnosis.
Please discuss these results with a licensed clinician.
```

## How It Works
1. **Text extraction** — reads the file directly, or pulls text from PDF
   pages using `pypdf`.
2. **Parsing** — a regex scans each line for a `<test name>: <value> <unit>`
   pattern and matches it against a dictionary of known tests.
3. **Range check** — each matched value is compared to its reference range
   and labeled low/normal/high.
4. **Summary** — a plain-English report is generated, listing all abnormal
   findings with a clinical-disclaimer note.

## Extending
Add new tests by adding an entry to `REFERENCE_RANGES` in
`medical_report_analyzer.py`:
```python
"vitamin_d": ("ng/mL", 30, 100),
```

## Limitations
- Rule-based text parsing; unusual report formats or handwritten/scanned
  (non-OCR) PDFs may not parse correctly.
- Reference ranges are general adult defaults and do not account for age,
  sex, or lab-specific variation.
- Not a substitute for professional medical review — for educational/
  screening purposes only.

## License
MIT
