"""
Medical Report Analyzer
------------------------
Parses a plain-text or PDF lab/medical report, extracts test values,
flags abnormal results against reference ranges, and produces a
plain-English summary.

Usage:
    python medical_report_analyzer.py path/to/report.txt
    python medical_report_analyzer.py path/to/report.pdf
"""

import re
import sys
import json
from dataclasses import dataclass, asdict
from typing import List, Optional

# ---------------------------------------------------------------------------
# Reference ranges for common lab tests (unit, low, high)
# Extend this dictionary to support more tests.
# ---------------------------------------------------------------------------
REFERENCE_RANGES = {
    "hemoglobin":        ("g/dL", 13.0, 17.0),
    "wbc":               ("x10^3/uL", 4.0, 11.0),
    "platelets":         ("x10^3/uL", 150, 450),
    "glucose":           ("mg/dL", 70, 99),
    "cholesterol":       ("mg/dL", 0, 200),
    "ldl":               ("mg/dL", 0, 100),
    "hdl":               ("mg/dL", 40, 60),
    "triglycerides":     ("mg/dL", 0, 150),
    "creatinine":        ("mg/dL", 0.6, 1.3),
    "alt":               ("U/L", 7, 56),
    "ast":               ("U/L", 8, 48),
    "tsh":               ("mIU/L", 0.4, 4.0),
    "sodium":            ("mmol/L", 135, 145),
    "potassium":         ("mmol/L", 3.5, 5.1),
}

# Matches lines like: "Glucose: 110 mg/dL" or "Hemoglobin - 12.1 g/dL"
LINE_PATTERN = re.compile(
    r"([A-Za-z][A-Za-z\s]{2,30})[:\-]\s*([\d.]+)\s*([A-Za-z/%^0-9]*)"
)


@dataclass
class TestResult:
    name: str
    value: float
    unit: str
    ref_low: Optional[float]
    ref_high: Optional[float]
    status: str  # "low", "normal", "high", "unknown"


def extract_text(filepath: str) -> str:
    """Read plain text, or extract text from a PDF if the extension is .pdf."""
    if filepath.lower().endswith(".pdf"):
        try:
            from pypdf import PdfReader
        except ImportError:
            sys.exit("pypdf is required for PDF input. Install with: pip install pypdf")
        reader = PdfReader(filepath)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def parse_results(text: str) -> List[TestResult]:
    results = []
    for match in LINE_PATTERN.finditer(text):
        raw_name, raw_value, raw_unit = match.groups()
        key = raw_name.strip().lower()
        # normalize a couple of common aliases
        key = key.replace("white blood cell", "wbc").replace("hb", "hemoglobin")

        if key not in REFERENCE_RANGES:
            continue  # skip lines we don't recognize as a known test

        unit, low, high = REFERENCE_RANGES[key]
        try:
            value = float(raw_value)
        except ValueError:
            continue

        if value < low:
            status = "low"
        elif value > high:
            status = "high"
        else:
            status = "normal"

        results.append(TestResult(
            name=key, value=value, unit=raw_unit or unit,
            ref_low=low, ref_high=high, status=status
        ))
    return results


def summarize(results: List[TestResult]) -> str:
    if not results:
        return "No recognized lab values were found in this report."

    abnormal = [r for r in results if r.status != "normal"]
    lines = [f"Analyzed {len(results)} recognized test value(s)."]

    if not abnormal:
        lines.append("All recognized values fall within standard reference ranges.")
    else:
        lines.append(f"{len(abnormal)} value(s) fall outside standard reference ranges:")
        for r in abnormal:
            direction = "above" if r.status == "high" else "below"
            lines.append(
                f"  - {r.name.title()}: {r.value} {r.unit} "
                f"({direction} normal range {r.ref_low}-{r.ref_high} {r.unit})"
            )
        lines.append(
            "\nNote: This is an automated screening summary, not a diagnosis. "
            "Please discuss these results with a licensed clinician."
        )
    return "\n".join(lines)


def analyze(filepath: str) -> dict:
    text = extract_text(filepath)
    results = parse_results(text)
    return {
        "results": [asdict(r) for r in results],
        "summary": summarize(results),
    }


def main():
    if len(sys.argv) != 2:
        print("Usage: python medical_report_analyzer.py <report.txt|report.pdf>")
        sys.exit(1)

    output = analyze(sys.argv[1])
    print(json.dumps(output, indent=2))
    print("\n--- Summary ---")
    print(output["summary"])


if __name__ == "__main__":
    main()
