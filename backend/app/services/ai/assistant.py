"""Conversational search assistant: text -> intent -> structured DB search."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.i18n import fmt_day, t
from app.models import Category, City, User
from app.services import search as search_service
from app.services.ai import llm, nlu
from app.services.ai.intent import SearchIntent
from app.services.geo import GeoPoint, geocode
from app.services.text import format_price

UTC = timezone.utc


ALIAS_BLACKLIST = {"saint", "le", "la", "les", "paris", "sur", "aix", "en"}


async def _lexicon(session: AsyncSession
                   ) -> tuple[list[nlu.CategoryLexicon], list[tuple[str, str]], dict[str, str]]:
    cats = (await session.execute(select(Category).where(Category.is_active.is_(True)))).scalars().all()
    lex, pairs = [], []
    for c in cats:
        cnames = {nlu.normalize(n).replace("-", " ") for n in c.names.values() if n}
        terms = set(cnames)
        terms |= {nlu.normalize(k).replace("-", " ") for k in (c.keywords or [])}
        lex.append(nlu.CategoryLexicon(c.slug, sorted(terms, key=len, reverse=True), c.parent_id is not None,
                                       c.default_work_mode.value == "mobile", tuple(cnames)))
        pairs.append((c.slug, c.name("fr")))
    names = set((await session.execute(select(City.name_norm))).scalars().all())
    names = {c for c in names if not any(ch.isdigit() for ch in c)}  # skip "paris 2e" style entries
    cities: dict[str, str] = {n: n for n in names}
    # Short aliases: "boulogne" -> "boulogne billancourt", "issy" -> "issy les moulineaux"
    first_tokens: dict[str, list[str]] = {}
    for n in names:
        if " " in n:
            first_tokens.setdefault(n.split()[0], []).append(n)
    for alias, full in first_tokens.items():
        if len(full) == 1 and len(alias) >= 4 and alias not in ALIAS_BLACKLIST and alias not in cities:
            cities[alias] = full[0]
    return lex, pairs, cities


async def understand(session: AsyncSession, text: str, previous: SearchIntent | None = None,
                     now: datetime | None = None) -> SearchIntent:
    """Parse a message. LLM first when configured, deterministic rules otherwise."""
    now = now or datetime.now(UTC)
    now_local = now.astimezone(ZoneInfo(settings.default_timezone))
    lex, pairs, cities = await _lexicon(session)
    parsed = await llm.parse_with_llm(text, pairs, now_local, previous)
    if parsed is None:
        parsed = nlu.parse(text, lex, now_local, cities)
    else:
        # Let the rules fill what the model left empty (e.g. a postal code).
        rules = nlu.parse(text, lex, now_local, cities)
        for field in ("location_text", "max_price_eur", "category_slug"):
            if getattr(parsed, field) in (None, "") and getattr(rules, field):
                setattr(parsed, field, getattr(rules, field))
    if previous is not None and parsed.intent in ("search", "quote", "other"):
        if parsed.intent == "other" and previous.is_empty:
            return parsed
        merged = previous.merged_with(parsed)
        if parsed.intent == "other":
            merged.intent = "search"
        return merged
    return parsed


@dataclass
class ResolvedQuery:
    query: search_service.SearchQuery
    location: GeoPoint | None
    category: Category | None
    location_unknown: str | None = None  # location text we could not geocode


def _parse_hhmm(value: str | None) -> float | None:
    if not value:
        return None
    try:
        h, m = value.split(":")
        return int(h) + int(m) / 60
    except ValueError:
        return None


async def intent_to_query(session: AsyncSession, intent: SearchIntent, user: User | None = None,
                          now: datetime | None = None) -> ResolvedQuery:
    now = now or datetime.now(UTC)
    tz = ZoneInfo(settings.default_timezone)
    q = search_service.SearchQuery()
    category = None
    if intent.category_slug:
        category = (await session.execute(select(Category).where(Category.slug == intent.category_slug))
                    ).scalar_one_or_none()
        if category:
            q.category_ids = [category.id]
    q.text = intent.service_query
    if intent.max_price_eur is not None:
        q.max_price_cents = int(round(intent.max_price_eur * 100))
    q.urgent = bool(intent.urgent and category is not None and category.default_work_mode.value != "on_site")
    q.at_client = intent.at_client

    location, unknown = None, None
    if intent.location_text:
        location = await geocode(session, intent.location_text)
        if location is None:
            unknown = intent.location_text
    if location is None and (intent.use_my_location or not intent.location_text) and user \
            and user.last_lat is not None:
        location = GeoPoint(user.last_lat, user.last_lon, user.last_city)
    if location:
        q.lat, q.lon = location.lat, location.lon
        q.radius_km = intent.radius_km or (user.search_radius_km if user else 10) or 10

    if intent.availability:
        q.window_start, q.window_end = search_service.availability_window(intent.availability, now=now)
    elif intent.date_from:
        start = datetime.combine(intent.date_from, time(0), tz).astimezone(UTC)
        end_day = intent.date_to or intent.date_from
        end = datetime.combine(end_day + timedelta(days=1), time(0), tz).astimezone(UTC)
        q.window_start, q.window_end = max(start, now), end
    lo, hi = _parse_hhmm(intent.time_from), _parse_hhmm(intent.time_to)
    if lo is not None and hi is not None and hi > lo:
        q.hour_range = (lo, hi)
        if not q.window_start:  # a time of day alone means "in the next days"
            q.window_start, q.window_end = now, now + timedelta(days=7)
    if q.urgent:
        q.sort = "soonest"
    return ResolvedQuery(q, location, category, unknown)


def describe(intent: SearchIntent, resolved: ResolvedQuery, lang: str = "fr") -> str:
    """Human summary of what was understood, shown before the results."""
    parts = []
    if resolved.category:
        parts.append(f"{resolved.category.icon or ''} {resolved.category.name(lang)}".strip())
    if intent.service_query:
        parts.append(f"« {intent.service_query} »")
    if resolved.location:
        parts.append(f"📍 {resolved.location.label or t('search.my_position', lang)}"
                     f" ({int(resolved.query.radius_km)} km)")
    if intent.availability:
        parts.append("⚡ " + t(f"avail.{intent.availability}", lang))
    elif intent.date_from:
        if intent.date_to and intent.date_to != intent.date_from:
            parts.append(f"📅 {fmt_day(intent.date_from, lang)} → {fmt_day(intent.date_to, lang)}")
        else:
            parts.append(f"📅 {fmt_day(intent.date_from, lang)}")
    if resolved.query.hour_range:
        parts.append(f"🕒 {intent.time_from}–{intent.time_to}")
    if resolved.query.max_price_cents is not None:
        parts.append("💶 ≤ " + format_price(resolved.query.max_price_cents))
    if intent.at_client:
        parts.append("🏠 " + t("search.at_home", lang))
    return " · ".join(parts)
