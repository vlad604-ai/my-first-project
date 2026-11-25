"""LLM-based understanding with Claude (structured outputs).

The model only *extracts constraints* into a validated schema. It never sees
nor produces professionals, prices or availabilities: those always come from
the database through the search engine.
"""
from __future__ import annotations

import logging
from datetime import datetime

from app.config import settings
from app.services.ai.intent import SearchIntent

log = logging.getLogger(__name__)
_client = None

SYSTEM_PROMPT = """You turn a user's message, sent to a French booking marketplace bot on Telegram, \
into search constraints. Users look for any kind of professional (health, building trades, beauty, \
car repair, lawyers, teachers...).

Rules:
- Only fill a field if the message (or the previous constraints given as context) supports it. Never guess.
- category_slug must be one of the allowed slugs listed below, or null if none fits. Prefer the most specific \
sub-category.
- Dates: resolve relative expressions ("demain", "vendredi", "ce week-end") against the current local date \
given below and output ISO dates. date_to is the last day of the range (same as date_from for a single day).
- availability: "now" for immediate/urgent needs, "30min", "1h", "3h", "today", "tomorrow" when the user \
says so explicitly; otherwise null.
- time_from/time_to: local HH:MM bounds ("matin" = 08:00-12:00, "après-midi" = 13:00-18:00, \
"soir" = 17:30-21:30).
- max_price_eur: only when a budget or maximum price is stated.
- at_client: true when the professional must come to the user's place (plumber, electrician, home service...).
- location_text: the city / postal code / address exactly as written; use_my_location when they say \
"près de moi", "autour de moi".
- quote_suggested: true for projects whose price cannot be fixed in advance (renovation, installation, \
construction, large jobs) or when they ask for a quote ("devis").
- intent: "search" to find a professional, "quote" for a project needing quotes, "my_bookings" when they \
ask about their appointments, "greeting"/"help"/"other" otherwise.
- service_query: the specific service in a few words (e.g. "coupe homme", "fuite d'eau", "3 prises").
"""


def _get_client():
    global _client
    if _client is None:
        import anthropic

        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key or None,
                                           timeout=settings.ai_timeout_seconds, max_retries=1)
    return _client


def llm_available() -> bool:
    return bool(settings.ai_enabled and settings.anthropic_api_key)


async def parse_with_llm(text: str, categories: list[tuple[str, str]], now_local: datetime,
                         previous: SearchIntent | None = None) -> SearchIntent | None:
    if not llm_available():
        return None
    import anthropic

    allowed = "\n".join(f"- {slug}: {name}" for slug, name in categories)
    context = ""
    if previous and not previous.is_empty:
        context = (
            "\nPrevious constraints of this conversation (the new message may refine them; "
            f"only output what the new message implies plus what still applies):\n{previous.model_dump_json()}\n"
        )
    user_content = (
        f"Current local date and time: {now_local:%A %Y-%m-%d %H:%M} (Europe/Paris).\n"
        f"Allowed category slugs:\n{allowed}\n{context}\nUser message:\n{text[:1500]}"
    )
    try:
        response = await _get_client().beta.messages.parse(
            model=settings.ai_model,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
            output_format=SearchIntent,
            output_config={"effort": settings.ai_effort},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
    except anthropic.APIConnectionError as exc:
        log.warning("LLM connection error, falling back to rules: %s", exc)
        return None
    except anthropic.RateLimitError:
        log.warning("LLM rate limited, falling back to rules")
        return None
    except anthropic.APIStatusError as exc:
        log.warning("LLM API error %s, falling back to rules", exc.status_code)
        return None
    except Exception:  # parsing/validation problems must never break the bot
        log.exception("LLM parsing failed, falling back to rules")
        return None
    if response.stop_reason == "refusal" or response.parsed_output is None:
        return None
    intent: SearchIntent = response.parsed_output
    intent.source = "llm"
    valid = {slug for slug, _ in categories}
    if intent.category_slug not in valid:
        intent.category_slug = None
    return intent
