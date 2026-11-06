"""Google Gemini: rewords the chosen advice."""
import base64
import json
import logging

import httpx

from ..config import settings

log = logging.getLogger(__name__)

API_ROOT = "https://generativelanguage.googleapis.com/v1beta/models"

# The status of the last call, shown on the admin System panel so a missing
# or expired key is obvious during a demonstration rather than silent.
_last = {"ok": None, "error": None, "model": None}

PHRASE_PROMPT = """You are MlimiSmart, an agricultural advisory service for \
smallholder tea farmers in Thyolo and Mulanje, Malawi.

Answer the farmer's question directly, in your own words.

You are given today's weather for the farmer's area and a recommendation an agronomic rule engine has already decided. Use both to answer what was actually asked.

Rules you must follow:
- Answer the question that was asked. If the farmer asks when rain will start, answer from the weather figures; do not answer a different question.
- The recommendation is the farm action you must not contradict. If it says to delay fertilizer, never tell the farmer to apply it. If the question is not about that action, you may leave it out.
- Use only the figures given to you. Never invent a temperature, a rainfall amount or a date.
- If the figures do not answer the question, say plainly what is known and what is not.
- Write in {language_name}, in plain words a farmer with basic schooling reads \
easily. Short sentences.
- Speak directly to the farmer, respectfully. No greeting, no sign-off, no \
markdown, no bullet points, no emoji.
- At most {max_sentences} sentences.
- If writing Chichewa, use natural farming vocabulary as used in Malawi \
(kuthira fetereza, kuthyola, kutema, mphukira). Never mix in English words that \
have a common Chichewa equivalent.
"""

OPEN_PROMPT = """You are MlimiSmart, a friendly advisor for smallholder tea \
farmers in Thyolo and Mulanje districts, Malawi. The farmer is in {location}. \
It is currently {season}. {weather_line}

Answer the farmer's question using the MlimiSmart knowledge base below and \
sound, widely accepted tea growing practice for southern Malawi.

Rules:
- Write in {language_name}, in plain words a farmer with basic schooling reads \
easily. Short sentences. At most {max_sentences} sentences.
- No markdown, no bullet points, no emoji, no greeting.
- Never name a specific pesticide, brand or dose. For chemicals, tell the \
farmer to ask their extension officer (alangizi a zaulimi).
- If the question is not about farming, say politely in one sentence that \
MlimiSmart helps with tea farming, weather and farm work only.
- If you are not sure, say so and suggest the extension officer. Do not guess \
numbers.

MlimiSmart knowledge base:
{knowledge}
"""

def enabled() -> bool:
    return bool(settings.gemini_api_key)


def _language_name(language: str) -> str:
    return "Chichewa (Chinyanja)" if language == "NY" else "English"


async def _generate(system: str, parts: list[dict], *, temperature: float = 0.3,
                    max_tokens: int = 1024, schema: dict | None = None,
                    search: bool = False) -> str | None:
    """One Gemini call. Returns the text, or None on any failure.

    If the configured model has been retired (HTTP 404), the fallback model
    is tried once, so a model rename by Google does not silently switch the
    whole system to template wording.
    """
    if not enabled():
        return None

    config: dict = {"temperature": temperature, "maxOutputTokens": max_tokens}
    if schema:
        config["responseMimeType"] = "application/json"
        config["responseSchema"] = schema

    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": config,
    }
    if search:
        # Google Search grounding, for questions the knowledge base does not
        # cover. Not used for the core agronomy, where the rule engine and the
        # knowledge base stay the authority.
        body["tools"] = [{"google_search": {}}]

    models = [settings.gemini_model]
    if settings.gemini_fallback_model and settings.gemini_fallback_model not in models:
        models.append(settings.gemini_fallback_model)

    async with httpx.AsyncClient(timeout=30.0) as client:
        for model in models:
            payload = dict(body)
            if model.startswith("gemini-2.5-flash"):
                # Thinking is not needed for rewording and only adds delay.
                payload["generationConfig"] = {**config, "thinkingConfig": {"thinkingBudget": 0}}
            try:
                response = await client.post(
                    f"{API_ROOT}/{model}:generateContent",
                    json=payload,
                    headers={"x-goog-api-key": settings.gemini_api_key},
                )
            except httpx.HTTPError as exc:
                _record(False, f"network error: {exc.__class__.__name__}", model)
                return None

            if response.status_code == 404:
                _record(False, f"model {model} not found", model)
                continue
            if response.status_code != 200:
                _record(False, _error_text(response), model)
                return None

            text = _extract_text(response.json())
            if text:
                _record(True, None, model)
                return text
            _record(False, "empty or blocked response", model)
            return None
    return None


def _extract_text(data: dict) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        return ""
    parts = (candidates[0].get("content") or {}).get("parts") or []
    return "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()


def _error_text(response: httpx.Response) -> str:
    try:
        message = response.json().get("error", {}).get("message", "")
    except ValueError:
        message = response.text[:120]
    return f"HTTP {response.status_code}: {message[:160]}"


def _record(ok: bool, error: str | None, model: str) -> None:
    _last.update(ok=ok, error=error, model=model)
    if not ok:
        log.warning("Gemini call failed (%s): %s", model, error)


# ---------------------------------------------------------------------------
# 1. Phrasing a decided recommendation
# ---------------------------------------------------------------------------
async def phrase(advice_text: str, language: str, *, weather_summary: str = "",
                 question: str = "", max_sentences: int = 4,
                 weather_detail: str = "") -> tuple[str, str]:
    """Return (text, source) where source is "gemini" or "template".

    On any failure the rule engine's own wording is returned unchanged, so the
    farmer always receives the correct recommendation.
    """
    lines = []
    if question:
        lines.append(f"The farmer asked: {question}")
    if weather_detail:
        lines.append("Weather for the farmer's area:")
        lines.append(weather_detail)
    elif weather_summary:
        lines.append(f"Current weather where the farmer is: {weather_summary}")
    lines.append("The farm action the rule engine decided "
                 "(do not contradict it):")
    lines.append(advice_text)

    text = await _generate(
        PHRASE_PROMPT.format(language_name=_language_name(language),
                             max_sentences=max_sentences),
        [{"text": "\n".join(lines)}],
        temperature=0.3,
    )
    return (text, "gemini") if text else (advice_text, "template")


# ---------------------------------------------------------------------------
# 2. Open questions the rules do not cover
# ---------------------------------------------------------------------------
async def answer_open(question: str, language: str, *, location: str,
                      season: str, weather_summary: str, knowledge: str,
                      max_sentences: int = 5) -> str | None:
    """A grounded answer to a question outside the rule topics, or None."""
    weather_line = (f"Today's weather there: {weather_summary}."
                    if weather_summary else "")
    system = OPEN_PROMPT.format(
        location=location, season=season, weather_line=weather_line,
        language_name=_language_name(language), max_sentences=max_sentences,
        knowledge=knowledge[:8000],
    )
    # Search is allowed here because these are the questions the
    # knowledge base does not answer. The eight farm topics never
    # reach this path, so the rules stay the agronomic authority.
    return await _generate(system, [{"text": question}],
                           temperature=0.4, search=True)



def status() -> dict:
    """Reported on the admin dashboard so the mode in use is always visible."""
    return {
        "provider": "Google Gemini",
        "model": settings.gemini_model,
        "fallback_model": settings.gemini_fallback_model,
        "enabled": enabled(),
        "mode": "gemini" if enabled() else "template fallback",
        "last_call_ok": _last["ok"],
        "last_error": _last["error"],
    }
