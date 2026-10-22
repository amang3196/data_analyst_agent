"""The one place that knows which LLM we use.

To switch provider (OpenAI, Azure, Groq...), change only this file.
"""

from functools import lru_cache

from langchain_core.exceptions import ModelAPIError, ModelNotFoundError, ModelRateLimitError
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from app.config import settings
from app.progress import report_progress

# Errors where trying another model makes sense (not e.g. a wrong API key)
FALLBACK_ERRORS = {
    ModelAPIError: "server busy",
    ModelRateLimitError: "rate limit hit",
    ModelNotFoundError: "model not found",
}


@lru_cache
def _gemini(model: str) -> ChatGoogleGenerativeAI:
    """Create a Gemini chat model once and reuse it. temperature=0 keeps SQL stable."""
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=settings.google_api_key,
        temperature=0,
        max_retries=1,
    )


def ask_llm(schema: type[BaseModel], prompt: str) -> BaseModel:
    """Ask the LLM and get back an object shaped like `schema` (structured output).

    If the main model fails (the free tier sometimes answers 503 "high demand"),
    tell the user and retry once with the backup model.
    """
    main, backup = settings.gemini_model, settings.gemini_fallback_model
    try:
        return _gemini(main).with_structured_output(schema).invoke(prompt)
    except tuple(FALLBACK_ERRORS) as e:
        reason = next(text for error, text in FALLBACK_ERRORS.items() if isinstance(e, error))
        report_progress(f"{main} failed ({reason}), retrying with {backup}")
        return _gemini(backup).with_structured_output(schema).invoke(prompt)
