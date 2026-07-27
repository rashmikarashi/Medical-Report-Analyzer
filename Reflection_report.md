# Reflection Report — Day 2: Medical Report Analyzer (LLM App)

## 1. Objective
Build a Streamlit application that uses an LLM API (OpenAI or Groq) together
with prompt templates to analyze medical reports and explain them in plain
language for a non-expert reader.

## 2. What I Built
The app accepts a medical/lab report — either uploaded as a PDF/TXT file or
pasted directly — and sends it through a structured prompt template to an LLM.
The model returns a fixed-format breakdown: summary, key findings, values
within normal range, values outside normal range with plain-language context,
suggested questions for a doctor, and a safety disclaimer. Users can also ask
free-form follow-up questions about the same report in a chat interface.

Two providers are supported (OpenAI and Groq) behind one shared function, so
switching providers is a one-line change in the sidebar rather than a code
rewrite — useful for comparing cost, speed, and quality.

## 3. Design Decisions

- **Prompt templates as a separate module (`prompts.py`)**: Keeping prompt
  text out of the UI code made it far easier to iterate on wording without
  touching app logic, and makes the prompts reusable/testable independently.
- **Fixed Markdown section headers in the analysis template**: Early tests
  without a strict template produced inconsistent formatting (sometimes a
  paragraph, sometimes bullets). Forcing exact headers made the output
  predictable enough to reliably render and let users compare reports over
  time.
- **A strong system prompt with explicit safety rules**: Because this touches
  health information, the system prompt explicitly bans diagnosis language and
  dosage recommendations and mandates a disclaimer, rather than relying on the
  model's own judgment.
- **Session-only API keys**: No `.env` file or server-side storage for user
  keys — they're typed into the sidebar each session, which is safer for a
  shareable/public demo than baking in a shared key.

## 4. Challenges Faced

- **Inconsistent LLM formatting**: Free-form prompts led to inconsistent
  section structure across different reports and providers. Solved by
  explicitly specifying exact header names and enforcing them in the prompt
  template rather than the post-processing layer.
- **PDF extraction quality**: Some real-world lab report PDFs use tables or
  scanned images that `pypdf` doesn't extract cleanly. For this version, the
  scope was limited to text-based PDFs, with OCR flagged as a future
  improvement rather than solved now.
- **Balancing helpfulness with safety**: It was tempting to let the model be
  more directly informative about "what's wrong," but that risks reading as a
  diagnosis. Iterating on the system prompt's wording (e.g., "may be
  associated with" instead of "indicates") took a few passes to get the tone
  right — informative without being prescriptive.
- **Provider parity**: OpenAI and Groq have slightly different model-name
  conventions and rate limits. Unifying them behind one `chat_completion()`
  function avoided duplicating logic, though it means new model names need to
  be added to a shared list manually when providers update their lineups.

## 5. What I'd Improve With More Time

- Add OCR (e.g. `pytesseract`) for scanned/image PDFs.
- Add structured JSON output mode so results could be rendered as UI cards
  instead of raw Markdown.
- Add basic evaluation: a small set of sample reports with expected key terms,
  to catch prompt regressions automatically.
- Add multi-report comparison (e.g., track a value like hemoglobin across
  multiple visits).

## 6. Key Takeaway
Prompt templates matter as much as the model choice — the same model produced
noticeably more reliable, structured, and safety-conscious output once the
prompt was tightened, compared to a single generic "explain this report"
instruction. Separating prompt logic from UI logic also made the whole app
easier to reason about and extend.
