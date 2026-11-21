import os

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5")

SYSTEM = (
    "You are MindMate, a patient C++ tutor for first-year college students. "
    "A student answered a question wrongly. Explain the underlying misunderstanding, not just the right answer. "
    "Rules: max 120 words; plain language; one tiny C++ example if useful; "
    "end with one short question that checks their understanding. Do not use headings."
)

def _call_llm(system: str, user: str) -> str:
    from anthropic import Anthropic
    msg = Anthropic().messages.create(
        model=MODEL, max_tokens=400, system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in msg.content if b.type == "text").strip()

def _fallback(correct_text, misconception_desc):
    why = f" Likely misunderstanding: {misconception_desc}." if misconception_desc else ""
    return f"The correct answer is: {correct_text}.{why} Re-read the code line by line and trace the values by hand."

def explain(concept, question, chosen_text, correct_text, misconception_desc, level):
    """Returns (text, source) where source is 'ai' or 'fallback'."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        return _fallback(correct_text, misconception_desc), "fallback"
    prompt = (
        f"Concept: {concept}\nStudent level: {level}\nQuestion: {question}\n"
        f"Student chose: {chosen_text}\nCorrect answer: {correct_text}\n"
        f"Diagnosed misconception: {misconception_desc or 'unknown'}"
    )
    try:
        return _call_llm(SYSTEM, prompt), "ai"
    except Exception:
        return _fallback(correct_text, misconception_desc), "fallback"
