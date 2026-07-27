# Reflection Report — Day 5: Tool Integration

## Objective
Integrate a real external API/tool (Gmail, Weather, Calendar, or MCP-
equivalent) into the existing agent from Day 4.

## What was integrated
A live weather tool (`tools/weather_tool.py`) using the Open-Meteo API:
geocoding a place name, then fetching current temperature, humidity,
barometric pressure, and wind speed. No API key or signup is required,
which matters for a "real, deployable" project — anyone cloning the repo
can run it immediately instead of first hunting down credentials.

## Why weather over Gmail/Calendar
Gmail and Calendar integrations require OAuth2 consent flows and per-user
credentials, which adds real setup friction for a grader or reviewer
cloning the repo cold. Weather was chosen because it (a) is a genuine
external network API call, not a mock, (b) needs zero credentials, and
(c) has a real, defensible reason to exist in a *medical* agent: pressure
and temperature swings are commonly self-reported triggers for migraines,
joint pain, and respiratory symptoms — so it's not a bolted-on demo, it
adds real signal to the summary the agent already produces.

## Integration approach
The new tool was added the same way as every other tool in Day 4: a
function (`get_weather`), a JSON schema entry in `TOOLS`, and one line in
`TOOL_IMPL`. The planning loop (`AgentLoop.run`) required **zero changes**
— it already treats every tool identically. That's the real validation of
the Day 4 design: if adding a new capability means touching the control
flow, the architecture wasn't actually agentic. Here it didn't.

The system prompt was updated with one new instruction: check weather only
if the report mentions a weather-sensitive symptom *and* a location is
known. This keeps the tool call conditional and relevant rather than
happening on every run regardless of usefulness — the model decides,
consistent with the planning-over-pipeline design from Day 4.

## Challenges
- **Network reliability**: unlike the local file/regex tools, an external
  API call can fail (timeout, bad location, service down). `get_weather`
  wraps the request in try/except and returns a structured `{"error": ...}`
  dict rather than raising, so a flaky network call degrades the summary
  gracefully instead of crashing the whole agent run.
- **Two-step API (geocode → forecast)**: Open-Meteo doesn't take a place
  name directly for forecasts, so the tool internally chains two HTTP
  calls behind one clean interface — the model only ever sees one tool
  call, one result. Keeping that complexity encapsulated inside the tool
  (rather than making the model orchestrate two separate tool calls) kept
  the planning loop simpler.
- **Relevance, not spam**: the naive version would call weather on every
  report regardless of content. The fix was prompt-level (only call it
  when symptoms + location both apply), not code-level — a reminder that
  not every constraint belongs in a function signature; some belong in
  the agent's instructions.

## What I'd improve with more time
- Cache repeated location lookups (geocoding rarely changes) to cut
  latency/API calls on repeated runs for the same patient.
- Add a real MCP server wrapper around `weather_tool.py` so it could be
  reused by any MCP-compatible client, not just this agent.
- Add retry-with-backoff for transient network failures instead of
  failing on the first attempt.

## Key takeaway
Good tool integration is additive: the sign of a solid agent architecture
from Day 4 was that plugging in a brand-new external API required touching
only the tool layer (one function, one schema entry, one dispatch line)
and never the planning loop itself.
