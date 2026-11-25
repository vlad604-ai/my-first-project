"""Deterministic French/English natural-language understanding.

Always available (no API key needed) and used as a fallback when the LLM is
disabled or fails. It only extracts constraints; it never produces results.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from app.services.ai.intent import SearchIntent
from app.services.text import normalize

WEEKDAYS = {
    "lundi": 0, "mardi": 1, "mercredi": 2, "jeudi": 3, "vendredi": 4, "samedi": 5, "dimanche": 6,
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6,
}
MONTHS = {
    "janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6, "juillet": 7, "aout": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12,
}
DAY_PARTS = {
    "matin": ("08:00", "12:00"), "matinee": ("08:00", "12:00"), "morning": ("08:00", "12:00"),
    "midi": ("11:30", "14:00"), "apres midi": ("13:00", "18:00"), "aprem": ("13:00", "18:00"),
    "afternoon": ("13:00", "18:00"), "soir": ("17:30", "21:30"), "soiree": ("17:30", "21:30"),
    "evening": ("17:30", "21:30"),
}
URGENT_WORDS = ("urgent", "urgence", "tout de suite", "immediatement", "au plus vite", "des que possible",
                "maintenant", "asap", "right now", "emergency", "en urgence")
AT_CLIENT_WORDS = ("a domicile", "chez moi", "se deplace", "se deplacer", "deplacement", "at home", "domicile")
NEAR_ME_WORDS = ("pres de moi", "autour de moi", "a proximite", "proche de moi", "near me", "nearby", "a cote de moi")
QUOTE_STRONG = ("devis", "refaire", "renover", "renovation", "construire", "travaux", "amenager", "amenagement",
                "m2", "m²", "quote", "chantier", "agrandissement")
QUOTE_WEAK = ("installer", "installation", "poser", "pose de")
GREETINGS = ("bonjour", "salut", "hello", "coucou", "bonsoir", "hey", "hi")
HELP_WORDS = ("aide", "help", "comment ca marche", "comment faire")
MY_BOOKINGS_WORDS = ("mes rendez vous", "mes reservations", "mes rdv", "my bookings", "mon rendez vous")


@dataclass
class CategoryLexicon:
    slug: str
    terms: list[str]  # normalised names + keywords
    is_sub: bool
    default_mobile: bool
    names: tuple[str, ...] = ()


def _has(text: str, phrase: str) -> bool:
    return re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(s|x|es)?(?![a-z0-9])", text) is not None


def match_category(text: str, lexicon: list[CategoryLexicon]) -> tuple[CategoryLexicon | None, str | None]:
    """Best category = highest cumulated length of matched terms (sub-categories preferred)."""
    best, best_term, best_score = None, None, 0.0
    for cat in lexicon:
        matched = [term for term in cat.terms if term and _has(text, term)]
        if not matched:
            continue
        score = sum(len(term) for term in matched) + (5 if cat.is_sub else 0)
        if score > best_score:
            best, best_term, best_score = cat, max(matched, key=len), score
    return best, best_term


def _next_weekday(today: date, weekday: int) -> date:
    return today + timedelta(days=(weekday - today.weekday()) % 7)


def _hhmm(h: str, m: str | None) -> str:
    return f"{int(h):02d}:{int(m or 0):02d}"


def parse(text: str, lexicon: list[CategoryLexicon], now: datetime, city_names: dict[str, str] | None = None
          ) -> SearchIntent:
    """city_names: normalised name or alias -> canonical normalised name."""
    raw = text or ""
    t = normalize(raw).replace("-", " ")
    t = re.sub(r"(?<![0-9])[.,;!?]|[.,;!?](?![0-9])", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    today = now.date()
    intent = SearchIntent(source="rules")

    if any(_has(t, w) for w in MY_BOOKINGS_WORDS):
        intent.intent = "my_bookings"
        return intent

    cat, term = match_category(t, lexicon)
    if cat:
        intent.category_slug = cat.slug

    # ---- price -----------------------------------------------------------
    m = re.search(r"entre (\d+(?:[.,]\d+)?) ?(?:€|euros?|eur)? et (\d+(?:[.,]\d+)?) ?(?:€|euros?|eur)?", t)
    if m:
        intent.max_price_eur = float(m.group(2).replace(",", "."))
    else:
        m = re.search(
            r"(?:moins de|max(?:imum)?|jusqu'?a|pas plus de|budget(?: de| max)?|sous|under|less than|<)\s*"
            r"(\d+(?:[.,]\d+)?)\s*(?:€|euros?|eur)?", t)
        if m:
            intent.max_price_eur = float(m.group(1).replace(",", "."))

    # ---- urgency / immediacy -------------------------------------------
    if re.search(r"dans (?:l'|les? )?(?:une? )?heure|within (?:an|the) hour|dans 1 ?h", t):
        intent.availability = "1h"
    elif re.search(r"dans (?:les )?(?:30|trente) ?min", t):
        intent.availability = "30min"
    elif re.search(r"dans (?:les )?(?:3|trois) (?:prochaines )?heures", t):
        intent.availability = "3h"
    if any(_has(t, w) for w in URGENT_WORDS):
        intent.urgent = True
        intent.availability = intent.availability or "now"

    # ---- dates ---------------------------------------------------------
    if _has(t, "apres demain"):
        intent.date_from = today + timedelta(days=2)
    elif _has(t, "demain") or _has(t, "tomorrow"):
        intent.date_from = today + timedelta(days=1)
    elif _has(t, "aujourd'hui") or _has(t, "aujourd hui") or _has(t, "today") or _has(t, "ce soir") \
            or _has(t, "ce matin") or _has(t, "cet apres midi"):
        if not intent.availability:
            intent.availability = "today"
    elif re.search(r"ce (?:week ?end|we)\b|this weekend", t):
        sat = _next_weekday(today, 5)
        intent.date_from, intent.date_to = (today, sat + timedelta(days=1)) if today.weekday() == 6 else (
            sat, sat + timedelta(days=1))
    elif re.search(r"semaine prochaine|next week", t):
        monday = today + timedelta(days=7 - today.weekday())
        intent.date_from, intent.date_to = monday, monday + timedelta(days=6)
    else:
        m = re.search(r"\b(\d{1,2})[/.](\d{1,2})(?:[/.](\d{2,4}))?\b", t)
        if m:
            d, mo = int(m.group(1)), int(m.group(2))
            y = int(m.group(3)) if m.group(3) else today.year
            y = y + 2000 if y < 100 else y
            try:
                cand = date(y, mo, d)
                if not m.group(3) and cand < today:
                    cand = date(y + 1, mo, d)
                intent.date_from = cand
            except ValueError:
                pass
        if intent.date_from is None:
            m = re.search(r"\b(?:le )?(\d{1,2}) (" + "|".join(MONTHS) + r")\b", t)
            if m:
                try:
                    cand = date(today.year, MONTHS[m.group(2)], int(m.group(1)))
                    if cand < today:
                        cand = date(today.year + 1, cand.month, cand.day)
                    intent.date_from = cand
                except ValueError:
                    pass
        if intent.date_from is None:
            for name, wd in WEEKDAYS.items():
                if _has(t, name):
                    d = _next_weekday(today, wd)
                    if _has(t, f"{name} prochain") and d == today:
                        d += timedelta(days=7)
                    intent.date_from = d
                    break
    if intent.date_from and not intent.date_to:
        intent.date_to = intent.date_from

    # ---- time of day ---------------------------------------------------
    for part, (a, b) in DAY_PARTS.items():
        if _has(t, part):
            intent.time_from, intent.time_to = a, b
            break
    m = re.search(r"(?:avant|before) (\d{1,2}) ?h ?(\d{2})?", t)
    if m:
        intent.time_from, intent.time_to = intent.time_from or "06:00", _hhmm(m.group(1), m.group(2))
    m = re.search(r"(?:apres|after|a partir de) (\d{1,2}) ?h ?(\d{2})?", t)
    if m:
        intent.time_from, intent.time_to = _hhmm(m.group(1), m.group(2)), intent.time_to or "22:00"
    m = re.search(r"(?:vers|a|at|around) (\d{1,2}) ?h ?(\d{2})?\b", t)
    if m and not re.search(r"(?:avant|apres|a partir de) \d", t):
        h = int(m.group(1))
        if 0 <= h <= 23:
            mins = int(m.group(2) or 0)
            start = max(0, h * 60 + mins - 60)
            end = min(24 * 60 - 1, h * 60 + mins + 60)
            intent.time_from = f"{start // 60:02d}:{start % 60:02d}"
            intent.time_to = f"{end // 60:02d}:{end % 60:02d}"

    # ---- location ------------------------------------------------------
    location_words: set[str] = set()
    if any(_has(t, w) for w in NEAR_ME_WORDS):
        intent.use_my_location = True
    m = re.search(r"\b(\d{5})\b", t)
    if m:
        intent.location_text = m.group(1)
    elif city_names:
        padded = f" {t} "
        found = [c for c in city_names if f" {c} " in padded]
        if found:
            alias = max(found, key=len)
            intent.location_text = city_names[alias]
            location_words = set(alias.split())
    m = re.search(r"(?:dans un rayon de|rayon de|a moins de|within) (\d{1,3}) ?km", t)
    if m:
        intent.radius_km = int(m.group(1))

    if any(_has(t, w) for w in AT_CLIENT_WORDS) or (cat and cat.default_mobile):
        intent.at_client = True if any(_has(t, w) for w in AT_CLIENT_WORDS) else None

    strong_quote = any(_has(t, w) for w in QUOTE_STRONG)
    if strong_quote or any(_has(t, w) for w in QUOTE_WEAK):
        intent.quote_suggested = True

    # ---- residual service query ----------------------------------------
    stop = set(WEEKDAYS) | set(MONTHS) | {"semaine", "prochaine", "prochain", "week", "end", "heure", "heures",
                                          "minutes", "min", "rayon", "km", "domicile", "urgence", "ouvert",
                                          "ouverte", "proche", "proximite", "autour", "pres",
                                          "merci", "svp", "plait", *GREETINGS, "aide", "help"}
    if cat:  # drop the trade name itself, keep service words ("coupe homme", "fuite")
        for cname in (*cat.names, term or ""):
            stop |= set(cname.split())
    if intent.location_text:
        stop |= set(normalize(intent.location_text).replace("-", " ").split())
    stop |= location_words
    words = []
    for w in re.findall(r"[a-z']+", t):
        w = w.split("'")[-1]  # j'ai -> ai, d'eau -> eau
        if len(w) > 2 and w not in stop:
            words.append(w)
    from app.services.search import STOPWORDS  # local import avoids cycle

    words = [w for w in words if w not in STOPWORDS]
    if words:
        intent.service_query = " ".join(words)[:120]

    if not cat and not intent.service_query and not intent.location_text and not intent.availability \
            and not intent.date_from:
        if any(_has(t, g) for g in GREETINGS):
            intent.intent = "greeting"
        elif any(_has(t, h) for h in HELP_WORDS):
            intent.intent = "help"
        else:
            intent.intent = "other"
    elif strong_quote and not intent.availability and not intent.date_from:
        intent.intent = "quote"
    return intent
