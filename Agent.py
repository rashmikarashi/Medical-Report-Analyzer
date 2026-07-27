"""
Medical Report Analyzer Agent
=============================
An agentic AI system that reads a medical report (PDF or text), extracts
lab values / vitals, flags abnormal results against reference ranges,
remembers past reports per patient, and produces a plain-English summary
with recommendations.

Architecture (Day 4 - Agentic AI requirements):
  - TOOLS    : deterministic Python functions the model can call
               (read_report, extract_values, check_ranges, save_memory,
               recall_history)
  - MEMORY   : persistent JSON store (memory_store/memory.json) keyed by
               patient name, so the agent has history across sessions
  - PLANNING : a ReAct-style loop where Claude decides which tool to call
               next, observes the result, and iterates until it has enough
               information to produce a final answer (see AgentLoop.run)

Requires: ANTHROPIC_API_KEY environment variable.
"""

import os
import re
import json
import sys
from datetime import datetime

import anthropic

from tools.weather_tool import get_weather

MODEL = "claude-sonnet-4-6"
MEMORY_PATH = os.path.join(os.path.dirname(__file__), "memory_store", "memory.json")

# ---------------------------------------------------------------------------
# Reference ranges for common lab values (adult, general population).
# Not a substitute for clinical judgment — used only to flag values for
# the model to reason about.
# ---------------------------------------------------------------------------
REFERENCE_RANGES = {
    "hemoglobin": (13.0, 17.0, "g/dL"),
    "wbc": (4000, 11000, "/uL"),
    "platelets": (150000, 450000, "/uL"),
    "glucose": (70, 100, "mg/dL"),
    "creatinine": (0.6, 1.3, "mg/dL"),
    "cholesterol": (0, 200, "mg/dL"),
    "ldl": (0, 100, "mg/dL"),
    "hdl": (40, 60, "mg/dL"),
    "triglycerides": (0, 150, "mg/dL"),
    "systolic_bp": (90, 120, "mmHg"),
    "diastolic_bp": (60, 80, "mmHg"),
    "heart_rate": (60, 100, "bpm"),
    "tsh": (0.4, 4.0, "mIU/L"),
}

VALUE_PATTERN = re.compile(
    r"(?P<name>[A-Za-z][A-Za-z0-9 /_\-]{2,30}?)\s*[:\-]?\s*"
    r"(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>[A-Za-z/%µu]{0,10})",
)


# ---------------------------------------------------------------------------
# TOOLS
# ---------------------------------------------------------------------------

def read_report(file_path: str) -> str:
    """Read a medical report from a .txt or .pdf file and return raw text."""
    if not os.path.exists(file_path):
        return f"ERROR: file not found: {file_path}"
    if file_path.lower().endswith(".pdf"):
        try:
            import pypdf
        except ImportError:
            return "ERROR: pypdf not installed. pip install pypdf"
        text = []
        reader = pypdf.PdfReader(file_path)
        for page in reader.pages:
            text.append(page.extract_text() or "")
        return "\n".join(text)
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def extract_values(report_text: str) -> dict:
    """Pull out (name -> value/unit) pairs that look like lab results."""
    found = {}
    for line in report_text.splitlines():
        m = VALUE_PATTERN.search(line)
        if not m:
            continue
        key = m.group("name").strip().lower().replace(" ", "_")
        key = key.strip("_")
        try:
            val = float(m.group("value"))
        except ValueError:
            continue
        found[key] = {"value": val, "unit": m.group("unit"), "raw_line": line.strip()}
    return found


def check_ranges(values: dict) -> dict:
    """Compare extracted values against REFERENCE_RANGES; flag out-of-range ones."""
    flagged = {}
    for key, info in values.items():
        for ref_key, (low, high, unit) in REFERENCE_RANGES.items():
            if ref_key in key or key in ref_key:
                status = "normal"
                if info["value"] < low:
                    status = "low"
                elif info["value"] > high:
                    status = "high"
                flagged[ref_key] = {
                    "value": info["value"],
                    "expected_range": f"{low}-{high} {unit}",
                    "status": status,
                }
                break
    return flagged


def save_memory(patient_name: str, entry: dict) -> str:
    """Append an analysis entry to persistent memory for a given patient."""
    store = _load_memory_file()
    store.setdefault(patient_name, [])
    entry["timestamp"] = datetime.utcnow().isoformat() + "Z"
    store[patient_name].append(entry)
    os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)
    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2)
    return f"Saved analysis for {patient_name} ({len(store[patient_name])} records total)."


def recall_history(patient_name: str) -> list:
    """Return all past analysis entries for a patient."""
    store = _load_memory_file()
    return store.get(patient_name, [])


def _load_memory_file() -> dict:
    if not os.path.exists(MEMORY_PATH):
        return {}
    with open(MEMORY_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


# ---------------------------------------------------------------------------
# Tool schema exposed to the model (Anthropic tool-use format)
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "name": "read_report",
        "description": "Read a medical report file (.txt or .pdf) from disk and return its raw text.",
        "input_schema": {
            "type": "object",
            "properties": {"file_path": {"type": "string"}},
            "required": ["file_path"],
        },
    },
    {
        "name": "extract_values",
        "description": "Extract lab/vital name-value pairs from raw report text.",
        "input_schema": {
            "type": "object",
            "properties": {"report_text": {"type": "string"}},
            "required": ["report_text"],
        },
    },
    {
        "name": "check_ranges",
        "description": "Compare extracted values against clinical reference ranges and flag abnormal ones.",
        "input_schema": {
            "type": "object",
            "properties": {"values": {"type": "object"}},
            "required": ["values"],
        },
    },
    {
        "name": "recall_history",
        "description": "Retrieve past analyses previously saved for this patient, if any.",
        "input_schema": {
            "type": "object",
            "properties": {"patient_name": {"type": "string"}},
            "required": ["patient_name"],
        },
    },
    {
        "name": "save_memory",
        "description": "Persist this analysis to memory under the patient's name for future recall.",
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_name": {"type": "string"},
                "entry": {"type": "object", "description": "Summary of this analysis (flagged values, notes)."},
            },
            "required": ["patient_name", "entry"],
        },
    },
    {
        "name": "get_weather",
        "description": (
            "Get current weather (temperature, humidity, barometric pressure, wind) "
            "for a location via a live external API. Useful when the report mentions "
            "weather-sensitive symptoms such as migraines, headaches, joint pain, or "
            "respiratory issues, since pressure/temperature swings are common self-"
            "reported triggers. Only call this if a location is known or provided."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"location": {"type": "string", "description": "City name, e.g. 'Raipur' or 'Raipur, India'."}},
            "required": ["location"],
        },
    },
]

TOOL_IMPL = {
    "read_report": lambda i: read_report(i["file_path"]),
    "extract_values": lambda i: extract_values(i["report_text"]),
    "check_ranges": lambda i: check_ranges(i["values"]),
    "recall_history": lambda i: recall_history(i["patient_name"]),
    "save_memory": lambda i: save_memory(i["patient_name"], i["entry"]),
    "get_weather": lambda i: get_weather(i["location"]),
}


# ---------------------------------------------------------------------------
# PLANNING LOOP (agentic ReAct loop)
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a medical report analysis agent. Given a report \
file path and a patient name, you must plan and execute a sequence of tool \
calls to:
1. Read the report file.
2. Extract lab/vital values from it.
3. Check those values against reference ranges and flag abnormalities.
4. Recall the patient's past history from memory (if any) and note trends.
5. If the report mentions weather-sensitive symptoms (headaches, migraines, \
joint pain, respiratory issues) AND a location is available (ask for one if \
the user's request doesn't include it, or skip this step if none is given), \
call get_weather for that location and note if current pressure/temperature \
could plausibly relate to the symptoms. This is contextual, not diagnostic.
6. Save this analysis to memory.
7. Produce a final plain-English summary for a non-expert: what was found, \
what's abnormal, how it compares to past history, relevant weather context \
if checked, and general next steps \
(always recommend consulting a licensed clinician for diagnosis or treatment \
decisions — you are not a doctor and must not provide a diagnosis).

Think step by step, use tools as needed, and only give your final summary \
once you have read the report, checked ranges, and saved memory."""


class AgentLoop:
    def __init__(self, api_key: str = None, max_iterations: int = 8):
        self.client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.max_iterations = max_iterations

    def run(self, user_request: str) -> str:
        messages = [{"role": "user", "content": user_request}]

        for step in range(self.max_iterations):
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=2000,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

            if response.stop_reason != "tool_use":
                return "".join(b.text for b in response.content if b.type == "text")

            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                print(f"  [planning] step {step + 1}: calling tool '{block.name}' with {block.input}")
                try:
                    result = TOOL_IMPL[block.name](block.input)
                except Exception as e:
                    result = f"ERROR running {block.name}: {e}"
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, default=str)[:8000],
                })
            messages.append({"role": "user", "content": tool_results})

        return "Reached max planning iterations without a final answer."


def main():
    if len(sys.argv) < 3:
        print("Usage: python agent.py <report_file_path> <patient_name> [location]")
        sys.exit(1)

    file_path, patient_name = sys.argv[1], sys.argv[2]
    location = sys.argv[3] if len(sys.argv) > 3 else None
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: set the ANTHROPIC_API_KEY environment variable first.")
        sys.exit(1)

    agent = AgentLoop()
    request = (
        f"Analyze the medical report at file path '{file_path}' for patient "
        f"'{patient_name}'. Follow your full process (read, extract, check "
        f"ranges, recall history, check weather if relevant, save memory, "
        f"summarize)."
    )
    if location:
        request += f" The patient's current location is '{location}'."
    print(agent.run(request))


if __name__ == "__main__":
    main()
