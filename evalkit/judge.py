"""Optional LLM-as-judge faithfulness scorer (Gemini). Skips cleanly with no key."""
from __future__ import annotations

from .config import settings

_PROMPT = (
    "You are a strict grader. Given CONTEXT and an ANSWER, reply with a single number "
    "from 0.0 to 1.0 for how well the answer is supported by the context "
    "(1.0 = fully grounded, 0.0 = unsupported/hallucinated). Reply with only the number.\n\n"
    "CONTEXT:\n{context}\n\nANSWER:\n{answer}\n"
)


def is_available() -> bool:
    return settings.gemini_ready


def faithfulness(answer: str, context: str) -> float | None:
    """Return a 0..1 faithfulness score, or None if no LLM is configured."""
    if not is_available():
        return None
    from langchain_google_genai import ChatGoogleGenerativeAI

    llm = ChatGoogleGenerativeAI(
        model=settings.model_name, google_api_key=settings.google_api_key, temperature=0
    )
    raw = str(llm.invoke(_PROMPT.format(context=context, answer=answer)).content).strip()
    try:
        return max(0.0, min(1.0, float(raw.split()[0])))
    except (ValueError, IndexError):
        return None
