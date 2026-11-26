import os
import httpx

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM = (
    "You are MindMate, a patient C++ tutor for first-year college students. "
    "A student answered a question wrongly. Explain the underlying misunderstanding, not just the right answer. "
    "Rules: max 120 words; plain language; one tiny C++ example if useful; "
    "end with one short question that checks their understanding. Do not use headings."
)

def _provider():
    """Which AI service to use, based on which key is set. None means use the built-in fallback."""
    if os.getenv("GROQ_API_KEY"):
        return "groq"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    return None

def _call_groq(system: str, user: str) -> str:
    r = httpx.post(
        GROQ_URL,
        headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}", "User-Agent": "MindMate/1.0"},
        json={
            "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "max_tokens": 400,
            "temperature": 0.4,
        },
        timeout=20,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()

def _call_anthropic(system: str, user: str) -> str:
    from anthropic import Anthropic
    msg = Anthropic().messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5"), max_tokens=400, system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in msg.content if b.type == "text").strip()

def _call_llm(system: str, user: str) -> str:
    return (_call_groq if _provider() == "groq" else _call_anthropic)(system, user)

def _fallback(correct_text, misconception_desc):
    why = f" Likely misunderstanding: {misconception_desc}." if misconception_desc else ""
    return f"The correct answer is: {correct_text}.{why} Re-read the code line by line and trace the values by hand."

def explain(concept, question, chosen_text, correct_text, misconception_desc, level):
    """Returns (text, source) where source is 'ai' or 'fallback'."""
    if not _provider():
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
