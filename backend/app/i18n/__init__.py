"""Minimal i18n: `t(key, lang, **kwargs)`.

French is the reference language; any missing key in another language falls
back to French. Add a language by creating `app/i18n/<code>.py` with a
`MESSAGES` dict and listing it in SUPPORTED_LANGUAGES.
"""
from __future__ import annotations

import importlib
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import settings

log = logging.getLogger(__name__)
_CATALOGS: dict[str, dict[str, str]] = {}

WEEKDAYS = {
    "fr": ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"],
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
}
WEEKDAYS_SHORT = {
    "fr": ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"],
    "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
}
MONTHS = {
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
           "novembre", "décembre"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
           "November", "December"],
}


def _catalog(lang: str) -> dict[str, str]:
    if lang not in _CATALOGS:
        try:
            _CATALOGS[lang] = importlib.import_module(f"app.i18n.{lang}").MESSAGES
        except ModuleNotFoundError:
            _CATALOGS[lang] = {}
    return _CATALOGS[lang]


def t(key: str, lang: str | None = None, **kwargs) -> str:
    lang = lang if lang in settings.supported_languages else settings.default_language
    text = _catalog(lang).get(key) or _catalog("fr").get(key)
    if text is None:
        log.warning("Missing i18n key %s", key)
        return key
    try:
        return text.format(**kwargs) if kwargs else text
    except (KeyError, IndexError):
        log.warning("Bad i18n params for %s", key)
        return text


def fmt_dt(dt: datetime, tz: str = "Europe/Paris", lang: str = "fr") -> str:
    """'vendredi 12 décembre à 14h30'."""
    d = dt.astimezone(ZoneInfo(tz))
    lang = lang if lang in WEEKDAYS else "fr"
    if lang == "fr":
        return f"{WEEKDAYS[lang][d.weekday()]} {d.day} {MONTHS[lang][d.month - 1]} à {d:%H}h{d:%M}"
    return f"{WEEKDAYS[lang][d.weekday()]} {MONTHS[lang][d.month - 1]} {d.day} at {d:%H:%M}"


def fmt_time(dt: datetime, tz: str = "Europe/Paris") -> str:
    return dt.astimezone(ZoneInfo(tz)).strftime("%H:%M")


def fmt_day(d, lang: str = "fr") -> str:
    lang = lang if lang in WEEKDAYS else "fr"
    if lang == "fr":
        return f"{WEEKDAYS_SHORT[lang][d.weekday()]} {d.day} {MONTHS[lang][d.month - 1][:4].rstrip('.')}"
    return f"{WEEKDAYS_SHORT[lang][d.weekday()]} {MONTHS[lang][d.month - 1][:3]} {d.day}"
