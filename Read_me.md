# Medical Report Analyzer Agent — Healthcare AI Solution

## Problem statement
Patients routinely receive lab reports full of numbers (hemoglobin, glucose,
cholesterol, TSH, etc.) with no plain-English explanation of what's normal,
what isn't, or whether it's improving over time. Clinics also lack a cheap
way to give patients a first-pass, always-available explainer between visits.

## Who it's for
- **Patients** who want to understand their own report before/without a
  doctor's visit.
- **Small clinics/telehealth services** that want an automated first-pass
  triage/summary layer in front of a human clinician.

## The solution
An AI agent (not a static script) that reads a report, extracts values,
flags abnormalities against reference ranges, remembers a patient's history
across visits to show trends, and — when relevant — pulls in live weather
data because pressure/temperature swings are common self-reported triggers
for migraines, joint pain, and respiratory symptoms. It closes with a plain-
English summary and always defers diagnosis to a licensed clinician.

## Impact / what it saves
- Removes the "what do these numbers even mean" friction for patients.
- Gives clinics a free, instant first-pass summary to review/edit rather
  than write from scratch.
- Trend tracking (via memory) surfaces gradual changes a single report
  can't show on its own.

## Why this counts as an "agent" and not just a script

| Requirement | Implementation |
|---|---|
| **Tools** | 5 callable functions: `read_report`, `extract_values`, `check_ranges`, `recall_history`, `save_memory` — exposed to Claude via the Anthropic tool-use API (`agent.py`) |
| **Memory** | Persistent JSON store (`memory_store/memory.json`) keyed by patient name. Every analysis is appended, and future runs recall it to compare trends over time |
| **Planning** | A ReAct-style loop (`AgentLoop.run`) where Claude decides which tool to call next, observes the result, and iterates — it is not a fixed pipeline; the model chooses the order and whether to re-check anything, up to `max_iterations` |

## How it works

1. You give the agent a report file path + patient name.
2. The model plans: reads the file → extracts lab values → checks them
   against reference ranges → recalls that patient's past history →
   saves the new analysis to memory → writes a final summary.
3. Output: a plain-English report of what's normal, what's flagged, how it
   compares to the patient's history, and a reminder to consult a licensed
   clinician (the agent never diagnoses).

## Day 5 addition: external API tool integration

A 6th tool, `get_weather`, was added in `tools/weather_tool.py`. It calls the
live [Open-Meteo](https://open-meteo.com) API (geocoding + forecast, no API
key required) to fetch current temperature, humidity, pressure, and wind for
a location. The planning loop was **not changed** — the model simply gained
one more option to reason about, which is the point: tool integration should
be additive, not a rewrite.

Why weather, for a medical agent: barometric pressure drops and temperature
swings are commonly self-reported triggers for migraines, joint pain, and
respiratory symptoms. If a report/patient mentions those symptoms and a
location is available, the agent checks current conditions and mentions
them as context — never as a diagnosis.

```bash
python agent.py sample_data/sample_report.txt "John Doe" "Raipur, India"
```

(the location argument is optional — omit it and the agent just skips that step)

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key-here"
```

## Usage

```bash
python agent.py sample_data/sample_report.txt "John Doe"
```

Run it again with the same patient name on a newer report to see the agent
pull up history and comment on trends (e.g. improving/worsening glucose).

## Project structure

```
medical-report-analyzer/
├── agent.py              # tools + memory + planning loop
├── tools/
│   └── weather_tool.py   # Day 5: external API integration (Open-Meteo)
├── requirements.txt
├── sample_data/
│   └── sample_report.txt # example report for testing
├── memory_store/
│   └── memory.json       # created automatically on first run
├── REFLECTION.md         # Reflection: tools/memory/planning build
├── REFLECTION_DAY5.md    # Reflection: external weather API integration
├── REFLECTION_FINAL.md   # Reflection: full solution (this deliverable)
└── README.md
```

## Limitations / disclaimer

- Reference ranges are general adult defaults, not personalized clinical
  thresholds. This tool is for educational/demo purposes only — it is
  **not** a diagnostic device and does not replace a licensed clinician.
- Value extraction uses simple pattern matching on labeled `Name: Value Unit`
  lines; messy or scanned PDFs may need OCR (not included) for reliable text.
