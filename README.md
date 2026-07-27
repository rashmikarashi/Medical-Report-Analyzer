Medical Report Analyzer — Day 1: Prompt Engineering
Objective
Explore four core prompting strategies — Zero-shot, Few-shot, Chain-of-Thought (CoT), and Role prompting — by applying each to the problem of turning a raw medical lab report into a patient-friendly explanation. For every technique, a naive ("before") prompt is compared against an engineered ("after") prompt, showing how prompt design changes output quality.
Why Medical Report Analysis?
Lab reports are dense, jargon-heavy, and easy to misread. An LLM-powered explainer needs to:
Correctly flag abnormal values without inventing a diagnosis
Translate clinical terms into plain language
Stay cautious and recommend professional follow-up rather than giving medical advice
Structure output consistently so it can be rendered in a UI
This makes it a good testbed for prompting technique comparison — the failure modes (hallucinated diagnoses, inconsistent structure, missed values) are easy to see and easy to fix with better prompting.
Repo Structure
Code
Sample Input Used Across All Prompts
To keep comparisons fair, every prompt in this exercise is tested against the same synthetic lab report:
Code
This is fictional data, not a real patient record.
Setup
Bash
This will run all 20 prompts against the Claude API and save outputs to outputs.json.
Screenshots
Since these prompts are meant to be run interactively (e.g., in the Claude or ChatGPT web UI, or via the script above) for the assignment's screenshot deliverable, see screenshots/SCREENSHOT_GUIDE.md for exactly which 6 interactions to capture and save as images once you run this yourself — a screenshot has to come from an actual live session, so this guide tells you precisely what to screenshot rather than faking one.
Deliverables Checklist
[x] GitHub Repository structure
[x] README
[x] requirements.txt
[x] PROMPTS_AND_OUTPUTS.md (20 prompts, before/after)
[x] REFLECTION_REPORT.md
[ ] Screenshots (capture per SCREENSHOT_GUIDE.md when you run it)
