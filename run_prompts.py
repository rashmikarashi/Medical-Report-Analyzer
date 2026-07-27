"""
run_prompts.py
Runs all 20 prompts (Zero-shot, Few-shot, Chain-of-Thought, Role) from
PROMPTS_AND_OUTPUTS.md against the Claude API and saves the live outputs
to outputs.json. Requires ANTHROPIC_API_KEY to be set as an environment
variable.

Usage:
export ANTHROPIC_API_KEY="your-key-here"
python run_prompts.py
"""

import os
import json
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"

LAB_REPORT = """Patient Lab Results:

Hemoglobin: 10.2 g/dL (Reference: 12.0-15.5) - Low

WBC Count: 11,500 /uL (Reference: 4,000-11,000) - High

Fasting Glucose: 118 mg/dL (Reference: 70-99) - Borderline High

TSH: 2.1 mIU/L (Reference: 0.4-4.0) - Normal

Vitamin D: 18 ng/mL (Reference: 30-100) - Deficient"""


Each entry: (id, technique, label, prompt_template)

"{report}" is substituted with LAB_REPORT where relevant.

PROMPTS = [
(1, "Zero-shot", "Basic explanation - after",
"You are analyzing a lab report for a patient with no medical background. "
"For each abnormal value, state what it measures, why it's flagged, and one "
"plain-language reason it might be off. Do not suggest a diagnosis. End with "
"a note to consult a doctor.\n\n{report}"),
(2, "Zero-shot", "Flag abnormal values - after",
"List every value that falls outside its reference range. For each, state the "
"direction (high/low) and the exact reference range it deviated from. Output "
"as a table.\n\n{report}"),
(3, "Zero-shot", "Patient-friendly rewrite - after",
"Rewrite this report as if explaining it to a worried patient with no medical "
"training, using everyday analogies. Keep it under 150 words. Avoid alarming "
"language.\n\n{report}"),
(4, "Zero-shot", "Structured extraction - after",
"Extract all lab values into valid JSON with keys: test_name, value, unit, "
"reference_range, flag. Return only JSON, no other text.\n\n{report}"),
(5, "Zero-shot", "Urgency triage - after",
"Classify overall urgency as Low / Moderate / High based only on the values "
"given, and justify in one sentence per flagged value. If any value could "
"indicate an emergency, say so explicitly; otherwise state that none of these "
"values alone indicate an emergency.\n\n{report}"),

(6, "Few-shot", "Consistent explanation format - after",  
 "Example:\nValue: Sodium 148 mEq/L (High, ref 135-145)\nExplanation: Sodium "  
 "helps balance fluids in your body. A high reading can relate to dehydration "  
 "or high salt intake. Worth mentioning to your doctor.\n\n"  
 "Now do the same for: Hemoglobin 10.2 g/dL (Low, ref 12.0-15.5)"),  
(7, "Few-shot", "Tone calibration - after",  
 "Example (target tone):\nGlucose 105 mg/dL (Borderline High) -> \"Your blood "  
 "sugar is running a little higher than the ideal range - not alarming, but a "  
 "good thing to watch with diet and your next check-up.\"\n\n"  
 "Now write the WBC result in this same tone: WBC 11,500/uL (High, ref 4,000-11,000)"),  
(8, "Few-shot", "Terminology simplification - after",  
 "Example:\n\"TSH 2.1 mIU/L, normal, reference 0.4-4.0\" -> \"Your thyroid "  
 "hormone level is right in the healthy range - no concerns here.\"\n\n"  
 "Now simplify: \"Fasting Glucose 118 mg/dL, borderline high, reference 70-99\""),  
(9, "Few-shot", "Comparative reporting - after",  
 "Example:\nPrevious WBC: 9,000 -> Current WBC: 11,500\n\"Your white blood cell "  
 "count has risen by about 28% since your last test, moving from within-range "  
 "to above the upper limit.\"\n\n"  
 "Now compare Previous Hemoglobin: 13.1 -> Current Hemoglobin: 10.2"),  
(10, "Few-shot", "Multi-value summary paragraph - after",  
 "Example summary style for a different 3-value report:\n"  
 "\"Overall, this report is reassuring. Your cholesterol is slightly elevated "  
 "but manageable with diet, and your liver enzymes and kidney function both "  
 "look normal. A follow-up in six months is reasonable.\"\n\n"  
 "Now write a summary paragraph in this same style for the following report:\n{report}"),  

(11, "Chain-of-Thought", "Root-cause brainstorming - after",  
 "Think step by step: first, what does hemoglobin measure? Second, what are "  
 "the 3 most common categories of causes for it being low? Third, given the "  
 "other values in this report (elevated WBC, low vitamin D), does anything "  
 "support or rule out any category? Then give a final summary sentence.\n\n{report}"),  
(12, "Chain-of-Thought", "Urgency reasoning - after",  
 "Reason through each value one at a time: state the value, state whether it "  
 "individually is a red-flag emergency threshold, and explain why or why not. "  
 "After going through all five, give a final overall urgency verdict.\n\n{report}"),  
(13, "Chain-of-Thought", "Follow-up question list - after",  
 "First, identify which values are abnormal. Second, for each abnormal value, "  
 "think about what a doctor would need to know to interpret it (diet, "  
 "symptoms, medication, family history). Third, turn each of those into a "  
 "specific question the patient could ask. List the final questions only.\n\n{report}"),  
(14, "Chain-of-Thought", "Explaining a contradiction - after",  
 "Reason through this step by step: (1) what does each value measure "  
 "biologically, (2) are they part of the same body system or different ones, "  
 "(3) does one being off and the other normal tell us anything useful? Explain "  
 "your reasoning, then conclude. Values: WBC 11,500 (High), TSH 2.1 (Normal)."),  
(15, "Chain-of-Thought", "Prioritization - after",  
 "Think through this step by step: consider severity of deviation from range, "  
 "reversibility/ease of treatment, and downstream risk if left unaddressed for "  
 "each abnormal value. Rank all four abnormal values from highest to lowest "  
 "priority, explaining each ranking decision.\n\n{report}"),  

(16, "Role", "Physician persona - after",  
 "You are a board-certified internal medicine physician explaining lab "  
 "results to a patient during a follow-up appointment. Use a calm, "  
 "reassuring, professional tone. Avoid jargon where possible, but you may "  
 "use precise terms if you immediately explain them.\n\n{report}"),  
(17, "Role", "Anxious-patient nurse persona - after",  
 "You are a compassionate nurse who specializes in calming anxious patients "  
 "before they see their doctor. You never dismiss a patient's worry, but you "  
 "always ground reassurance in specifics from their real results.\n\n{report}"),  
(18, "Role", "Study-buddy persona - after",  
 "You are a friendly senior medical student helping a junior student study "  
 "for an exam using this specific report as a case example. Use teaching "  
 "language like \"notice that...\" and \"this is a classic example of...\".\n\n{report}"),  
(19, "Role", "Insurance reviewer persona - after",  
 "You are a clinical documentation reviewer preparing a formal summary for "  
 "an insurance claims file. Use precise, neutral, third-person clinical "  
 "language. Structure as: Findings, Clinical Significance, Recommendation.\n\n{report}"),  
(20, "Role", "Skeptical second-opinion persona - after",  
 "You are a meticulous physician giving a second opinion, whose job is to "  
 "question assumptions and check for anything that might have been "  
 "overlooked in a first read. Actively look for inconsistencies, missing "  
 "context, or values that deserve more scrutiny than they'd normally get.\n\n{report}"),

]

def run():
results = []
for pid, technique, label, template in PROMPTS:
prompt = template.format(report=LAB_REPORT)
print(f"[{pid:02d}] {technique} - {label} ...")
response = client.messages.create(
model=MODEL,
max_tokens=500,
messages=[{"role": "user", "content": prompt}],
)
output_text = "".join(
block.text for block in response.content if block.type == "text"
)
results.append({
"id": pid,
"technique": technique,
"label": label,
"prompt": prompt,
"output": output_text,
})

with open("outputs.json", "w") as f:  
    json.dump(results, f, indent=2)  
print(f"\nSaved {len(results)} results to outputs.json")

if name == "main":
run()

Where to put this run prompt
