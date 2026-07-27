# Reflection Report — Medical Report Analyzer Agent

## Objective
Build an AI agent that demonstrates three core agentic capabilities — tool
use, memory, and planning — applied to a real, useful problem: analyzing
medical lab reports.

## Design decisions

**Tools over one giant prompt.** Rather than asking the model to "read and
summarize" in one shot, the task is broken into five discrete tools
(`read_report`, `extract_values`, `check_ranges`, `recall_history`,
`save_memory`). This mirrors how a human would work through the problem and
lets the model verify intermediate results (e.g. confirm what was extracted)
before committing to a final answer, rather than hallucinating values.

**Memory as a first-class tool, not a hidden feature.** Memory is exposed to
the model as two tools (`recall_history`, `save_memory`) instead of being
silently injected into the prompt. This lets the agent *decide* when to check
history (e.g. skip it for a first-time patient) — a small but real planning
choice, and it keeps the memory implementation swappable (JSON file now,
could be a database later) without changing the agent's reasoning.

**Planning as a loop, not a pipeline.** The `AgentLoop.run` method does not
hardcode "call tool A, then B, then C." It sends the system prompt describing
the goal and lets Claude choose the next tool call each iteration, stopping
when the model decides it has enough information. This is what makes it an
agent rather than a script — the control flow is decided at run time by the
model, based on what it observes.

## Challenges

- **Extraction reliability**: real-world lab reports are inconsistent in
  formatting. A regex-based extractor is fast and dependency-light but will
  miss unusual layouts (e.g. multi-column PDFs, values without units). A
  production version would benefit from a dedicated extraction tool call
  where the model itself parses text it has already read, rather than
  relying purely on regex.
- **Reference ranges are not personalized**: general adult ranges will
  misflag values for edge cases (children, pregnancy, athletes). This is
  called out explicitly in the README as a limitation rather than something
  the agent silently gets wrong.
- **Bounding the planning loop**: without a `max_iterations` cap, a
  misbehaving tool call or ambiguous instruction could loop indefinitely.
  Capping at 8 iterations was a practical tradeoff between giving the model
  room to plan and preventing runaway token usage.

## What I'd improve with more time
- Add an OCR fallback tool for scanned/image-based PDF reports.
- Add a `flag_drug_interactions` tool for patients on multiple medications.
- Move memory from a flat JSON file to SQLite for concurrent access and
  querying by date range.
- Add unit tests for the extraction and range-checking logic specifically,
  since those are the parts most likely to silently produce wrong output.

## Key takeaway
The difference between a "chatbot that talks about medical reports" and an
"agent" is that the agent's control flow — which tool to call, whether to
check memory, when to stop — is decided by the model at runtime based on
what it observes, not hardcoded by the developer. Building the memory and
planning pieces as explicit, inspectable tools (rather than folding them into
one big prompt) made this behavior visible and debuggable.
