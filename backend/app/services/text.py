"""Text helpers: normalisation, slugs, money formatting."""
from __future__ import annotations

import re
import secrets
import unicodedata

_REF_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no ambiguous chars


def normalize(text: str) -> str:
    """Lowercase, strip accents, collapse whitespace and punctuation."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    text = text.replace("’", "'")
    text = re.sub(r"[^a-z0-9€'\s:/.,h-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def slugify(text: str) -> str:
    s = normalize(text)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:150] or "pro"


def booking_reference() -> str:
    return "UB-" + "".join(secrets.choice(_REF_ALPHABET) for _ in range(7))


def format_price(cents: int | None, price_type: str | None = None) -> str:
    if cents is None:
        return "Sur devis"
    euros = cents / 100
    amount = f"{euros:.0f} €" if euros == int(euros) else f"{euros:.2f} €".replace(".", ",")
    if price_type == "from":
        return f"dès {amount}"
    if price_type == "quote":
        return "Sur devis"
    return amount


def stars(avg: float, count: int) -> str:
    if not count:
        return "Nouveau"
    return f"⭐ {avg:.1f}/5 ({count} avis)"


def truncate(text: str | None, length: int) -> str:
    if not text:
        return ""
    return text if len(text) <= length else text[: length - 1].rstrip() + "…"


def escape_html(text: str | None) -> str:
    if not text:
        return ""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
