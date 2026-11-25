"""Professional search: structured filters, geography, real availability, ranking.

Proximity and availability are distinct criteria: a nearby professional is only
reported as available if the availability engine finds a real free slot.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import Text, and_, cast, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models import (
    Category,
    Professional,
    ProStatus,
    Service,
    WorkMode,
    professional_categories,
)
from app.services import availability
from app.services.geo import bounding_box, estimate_travel_minutes, haversine_km
from app.services.text import normalize

UTC = timezone.utc

STOPWORDS = set(
    """
    je tu il elle on nous vous ils elles un une des les le la de du d l a au aux en et ou pour par pas
    sur sous avec chez dans mon ma mes ton ta tes son sa ses cherche besoin trouve trouver voudrais veux
    faire faites fais moi me cherchons souhaite souhaiterais disponible dispo demain aujourd hui
    matin soir apres midi ce cette cet plus moins euros euro eur max maximum prix pas cher urgent vite rapidement
    the a an for to in at near need find looking want available
    """.split()
)

AVAILABILITY_PRESETS = ("now", "30min", "1h", "3h", "today", "tomorrow")


@dataclass
class SearchQuery:
    text: str | None = None
    category_ids: list[int] = field(default_factory=list)
    lat: float | None = None
    lon: float | None = None
    radius_km: float = 10
    max_price_cents: int | None = None
    min_rating: float | None = None
    verified_only: bool = False
    at_client: bool | None = None  # True: needs a pro who travels
    window_start: datetime | None = None
    window_end: datetime | None = None
    hour_range: tuple[float, float] | None = None
    urgent: bool = False
    sort: str = "relevance"  # relevance | distance | rating | price | soonest
    limit: int = 10
    offset: int = 0
    slots_per_result: int = 3


@dataclass
class SearchResult:
    professional: Professional
    distance_km: float | None = None
    travel_minutes: int | None = None
    reference_service: Service | None = None
    min_price_cents: int | None = None
    next_slots: list[availability.Slot] = field(default_factory=list)
    on_duty: bool = False
    sponsored: bool = False
    text_score: float = 0.0
    score: float = 0.0

    @property
    def next_slot(self):
        return self.next_slots[0] if self.next_slots else None


@dataclass
class SearchResponse:
    results: list[SearchResult]
    total: int
    query: SearchQuery


def tokens(text: str | None) -> list[str]:
    if not text:
        return []
    words = re.findall(r"[a-z0-9]+", normalize(text))
    out = []
    for w in words:
        if len(w) < 3 or w in STOPWORDS or w.isdigit():
            continue
        out.append(w[:-1] if len(w) > 4 and w.endswith("s") else w)  # naive plural stemming
    return out


def availability_window(preset: str, tz_name: str | None = None, now: datetime | None = None
                        ) -> tuple[datetime, datetime]:
    now = now or datetime.now(UTC)
    tz = ZoneInfo(tz_name or settings.default_timezone)
    local = now.astimezone(tz)
    if preset == "now":
        return now, now + timedelta(minutes=15)
    if preset == "30min":
        return now, now + timedelta(minutes=30)
    if preset == "1h":
        return now, now + timedelta(hours=1)
    if preset == "3h":
        return now, now + timedelta(hours=3)
    if preset == "today":
        end = datetime.combine(local.date() + timedelta(days=1), time(0), tz)
        return now, end.astimezone(UTC)
    if preset == "tomorrow":
        start = datetime.combine(local.date() + timedelta(days=1), time(0), tz)
        return start.astimezone(UTC), (start + timedelta(days=1)).astimezone(UTC)
    raise ValueError(f"Unknown preset {preset}")


def day_window(day: date, tz_name: str | None = None) -> tuple[datetime, datetime]:
    return availability.local_day_window(day, tz_name or settings.default_timezone)


async def expand_categories(session: AsyncSession, ids: list[int]) -> list[int]:
    """Category ids + all their descendants."""
    if not ids:
        return []
    result = set(ids)
    frontier = list(ids)
    while frontier:
        rows = (await session.execute(select(Category.id).where(Category.parent_id.in_(frontier)))).scalars().all()
        frontier = [r for r in rows if r not in result]
        result.update(frontier)
    return list(result)


def _min_notice_ok(pro: Professional) -> int:
    return pro.min_notice_min or 0


async def search(session: AsyncSession, q: SearchQuery, now: datetime | None = None) -> SearchResponse:
    now = now or datetime.now(UTC)
    stmt = (
        select(Professional)
        .where(Professional.status == ProStatus.ACTIVE)
        .options(selectinload(Professional.services), selectinload(Professional.category))
    )

    cat_ids = await expand_categories(session, q.category_ids)
    if cat_ids:
        stmt = stmt.where(
            or_(
                Professional.category_id.in_(cat_ids),
                exists().where(
                    and_(professional_categories.c.professional_id == Professional.id,
                         professional_categories.c.category_id.in_(cat_ids))
                ),
            )
        )

    toks = tokens(q.text)
    if toks and not cat_ids:
        # Without a category, free text must match something about the pro.
        conds = []
        for tok in toks:
            like = f"%{tok}%"
            conds.append(
                or_(
                    func.unaccent(func.lower(Professional.business_name)).like(like),
                    func.unaccent(func.lower(func.coalesce(Professional.description, ""))).like(like),
                    func.unaccent(func.lower(cast(Professional.specialties, Text))).like(like),
                    exists().where(and_(Service.professional_id == Professional.id, Service.is_active.is_(True),
                                        func.unaccent(func.lower(Service.name)).like(like))),
                )
            )
        stmt = stmt.where(or_(*conds))

    if q.max_price_cents is not None:
        stmt = stmt.where(
            exists().where(and_(Service.professional_id == Professional.id, Service.is_active.is_(True),
                                Service.price_cents.is_not(None), Service.price_cents <= q.max_price_cents))
        )
    if q.min_rating:
        stmt = stmt.where(Professional.rating_avg >= q.min_rating, Professional.rating_count > 0)
    if q.verified_only:
        stmt = stmt.where(Professional.is_verified.is_(True))
    if q.at_client or q.urgent:
        stmt = stmt.where(Professional.work_mode.in_([WorkMode.MOBILE, WorkMode.BOTH]))
    if q.urgent:
        stmt = stmt.where(Professional.accepts_urgent.is_(True))

    if q.lat is not None and q.lon is not None:
        # Coarse prefilter: max(user radius, 100 km for mobile pros' own radius).
        reach = max(q.radius_km, 100)
        la1, la2, lo1, lo2 = bounding_box(q.lat, q.lon, reach)
        stmt = stmt.where(Professional.lat.between(la1, la2), Professional.lon.between(lo1, lo2))

    stmt = stmt.order_by(Professional.rating_avg.desc(), Professional.id).limit(settings.search_max_candidates)
    pros = list((await session.execute(stmt)).scalars().unique())

    # ---- Python-side refinement ----------------------------------------
    results: list[SearchResult] = []
    for pro in pros:
        r = SearchResult(professional=pro)
        r.sponsored = bool(pro.sponsored_until and pro.sponsored_until > now)
        r.on_duty = bool(pro.accepts_urgent and pro.on_duty_until and pro.on_duty_until > now)
        if q.lat is not None and q.lon is not None:
            if pro.lat is None or pro.lon is None:
                continue
            d = haversine_km(q.lat, q.lon, pro.lat, pro.lon)
            r.distance_km = round(d, 1)
            within_user_radius = d <= q.radius_km
            within_pro_zone = pro.is_mobile and d <= (pro.service_radius_km or 0)
            if q.at_client or q.urgent:
                if not within_pro_zone:
                    continue
            elif not (within_user_radius or within_pro_zone):
                continue
            if pro.is_mobile and within_pro_zone:
                r.travel_minutes = estimate_travel_minutes(d)
        services = [s for s in pro.services if s.is_active]
        if q.at_client:
            services = [s for s in services if s.location.value == "at_client"] or services
        if not services:
            continue
        r.reference_service, r.text_score = _pick_service(services, toks, q.max_price_cents)
        if r.reference_service is None:
            continue
        prices = [s.price_cents for s in services if s.price_cents is not None]
        r.min_price_cents = min(prices) if prices else None
        r.text_score += _text_score(pro, toks)
        results.append(r)

    # ---- Availability ------------------------------------------------------
    if q.window_start and q.window_end:
        ctxs = await availability.load_contexts(session, [r.professional for r in results], q.window_start,
                                                q.window_end)
        kept = []
        for r in results:
            ctx = ctxs[r.professional.id]
            r.next_slots = availability.compute_slots(
                ctx, r.reference_service.duration_min, q.window_start, q.window_end, now=now,
                limit=q.slots_per_result, hour_range=q.hour_range,
            )
            if r.next_slots or (q.urgent and r.on_duty):
                kept.append(r)
        results = kept
    elif results:
        # No date constraint: show the next availabilities within 14 days as information.
        start, end = now, now + timedelta(days=14)
        ctxs = await availability.load_contexts(session, [r.professional for r in results], start, end)
        for r in results:
            r.next_slots = availability.compute_slots(
                ctxs[r.professional.id], r.reference_service.duration_min, start, end, now=now,
                limit=q.slots_per_result, hour_range=q.hour_range,
            )

    for r in results:
        r.score = _score(r, q, now)
    results.sort(key=_sort_key(q.sort, now))
    total = len(results)
    return SearchResponse(results=results[q.offset: q.offset + q.limit], total=total, query=q)


def _pick_service(services: list[Service], toks: list[str], max_price: int | None) -> tuple[Service | None, float]:
    """Most relevant service for the query (token matches, then cheapest, then shortest)."""
    candidates = []
    for s in services:
        if max_price is not None and (s.price_cents is None or s.price_cents > max_price):
            continue
        name = normalize(f"{s.name} {s.description or ''}")
        matches = float(sum(1 for tok in toks if tok in name))
        candidates.append((-matches, s.price_cents if s.price_cents is not None else 10**9, s.duration_min, s.id, s))
    if not candidates:
        return None, 0.0
    best = min(candidates, key=lambda c: c[:4])
    return best[4], -best[0]


def _text_score(pro: Professional, toks: list[str]) -> float:
    if not toks:
        return 0.0
    hay = normalize(" ".join([pro.business_name, pro.description or "", " ".join(pro.specialties or [])]))
    return sum(0.5 for tok in toks if tok in hay)


def _score(r: SearchResult, q: SearchQuery, now: datetime) -> float:
    pro = r.professional
    # Bayesian rating (prior 4.0 with weight 3) avoids 1 review = 5 stars dominating
    rating = (pro.rating_avg * pro.rating_count + 4.0 * 3) / (pro.rating_count + 3)
    score = rating * 2  # 0..10
    score += min(r.text_score, 3) * 2
    if pro.is_verified:
        score += 1
    if r.distance_km is not None:
        score += max(0.0, 3 - r.distance_km / 5)  # closer is better
    if r.next_slot:
        hours = (r.next_slot.start - now).total_seconds() / 3600
        score += max(0.0, 3 - hours / 24)  # sooner is better
    if q.urgent and r.on_duty:
        score += 4
    if r.sponsored:
        score += 1.5  # sponsored boost stays bounded: relevance first
    return score


def _sort_key(sort: str, now: datetime):
    far = now + timedelta(days=3650)
    if sort == "distance":
        return lambda r: (r.distance_km if r.distance_km is not None else 1e9, -r.score)
    if sort == "rating":
        return lambda r: (-r.professional.rating_avg, -r.professional.rating_count, -r.score)
    if sort == "price":
        return lambda r: (r.reference_service.price_cents if r.reference_service.price_cents is not None else 10**9,
                          -r.score)
    if sort == "soonest":
        return lambda r: (r.next_slot.start if r.next_slot else far, -r.score)
    return lambda r: (-r.score, r.professional.id)
