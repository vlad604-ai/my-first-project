"""Public endpoints: catalog, search, profiles, availability."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import optional_user
from app.db import get_session
from app.models import Category, City, ProStatus, Service, User
from app.schemas.common import (
    CategoryOut,
    NaturalSearchIn,
    ProDetail,
    ProSummary,
    ReviewOut,
    SearchOut,
    SearchResultOut,
    ServiceOut,
    SlotOut,
)
from app.services import availability
from app.services import professionals as pro_service
from app.services import search as search_service
from app.services.ai import assistant
from app.services.ai.intent import SearchIntent
from app.services.geo import geocode

router = APIRouter(tags=["public"])
UTC = timezone.utc


def _tree(categories: list[Category]) -> list[CategoryOut]:
    by_parent: dict[int | None, list[Category]] = {}
    for c in categories:
        by_parent.setdefault(c.parent_id, []).append(c)

    def build(c: Category) -> CategoryOut:
        out = CategoryOut.model_validate({**{k: getattr(c, k) for k in CategoryOut.model_fields if k != "children"},
                                          "children": []})
        out.children = [build(ch) for ch in sorted(by_parent.get(c.id, []), key=lambda x: x.sort_order)]
        return out

    return [build(c) for c in sorted(by_parent.get(None, []), key=lambda x: x.sort_order)]


@router.get("/categories", response_model=list[CategoryOut])
async def categories(session: AsyncSession = Depends(get_session)):
    cats = (await session.execute(select(Category).where(Category.is_active.is_(True)))).scalars().all()
    return _tree(list(cats))


@router.get("/cities")
async def cities(q: str = Query(min_length=2), session: AsyncSession = Depends(get_session)):
    from app.services.text import normalize

    norm = normalize(q).replace("-", " ")
    rows = (await session.execute(
        select(City).where((City.name_norm.like(f"{norm}%")) | (City.postal_code.like(f"{q}%")))
        .order_by(City.population.desc()).limit(10))).scalars().all()
    return [{"name": c.name, "postal_code": c.postal_code, "lat": c.lat, "lon": c.lon} for c in rows]


def _result_out(r: search_service.SearchResult) -> SearchResultOut:
    return SearchResultOut(
        professional=ProSummary.model_validate(r.professional),
        distance_km=r.distance_km, travel_minutes=r.travel_minutes,
        reference_service=ServiceOut.model_validate(r.reference_service) if r.reference_service else None,
        min_price_cents=r.min_price_cents,
        next_slots=[SlotOut(start=s.start, end=s.end, freed=s.freed) for s in r.next_slots],
        on_duty=r.on_duty, sponsored=r.sponsored, score=round(r.score, 3),
    )


@router.get("/search", response_model=SearchOut)
async def search(
    session: AsyncSession = Depends(get_session),
    q: str | None = None,
    category: str | None = Query(None, description="category slug"),
    lat: float | None = None,
    lon: float | None = None,
    location: str | None = Query(None, description="city, postal code or address"),
    radius_km: float = Query(10, ge=1, le=100),
    max_price_cents: int | None = None,
    min_rating: float | None = None,
    verified_only: bool = False,
    at_client: bool | None = None,
    available: str | None = Query(None, pattern="^(now|30min|1h|3h|today|tomorrow)$"),
    day: date | None = None,
    urgent: bool = False,
    sort: str = Query("relevance", pattern="^(relevance|distance|rating|price|soonest)$"),
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
):
    query = search_service.SearchQuery(text=q, radius_km=radius_km, max_price_cents=max_price_cents,
                                       min_rating=min_rating, verified_only=verified_only, at_client=at_client,
                                       urgent=urgent, sort=sort, limit=limit, offset=offset)
    if category:
        cat = (await session.execute(select(Category).where(Category.slug == category))).scalar_one_or_none()
        if cat is None:
            raise HTTPException(404, "Unknown category")
        query.category_ids = [cat.id]
    if lat is not None and lon is not None:
        query.lat, query.lon = lat, lon
    elif location:
        point = await geocode(session, location)
        if point is None:
            raise HTTPException(422, "Unknown location")
        query.lat, query.lon = point.lat, point.lon
    if available:
        query.window_start, query.window_end = search_service.availability_window(available)
    elif day:
        query.window_start, query.window_end = search_service.day_window(day)
        query.window_start = max(query.window_start, datetime.now(UTC))
    resp = await search_service.search(session, query)
    return SearchOut(total=resp.total, results=[_result_out(r) for r in resp.results])


@router.post("/search/natural", response_model=SearchOut)
async def natural_search(body: NaturalSearchIn, session: AsyncSession = Depends(get_session),
                         user: User | None = Depends(optional_user)):
    previous = SearchIntent(**body.previous) if body.previous else None
    intent = await assistant.understand(session, body.text, previous)
    if body.lat is not None and body.lon is not None and user is None:
        user = User(last_lat=body.lat, last_lon=body.lon, search_radius_km=10)  # transient, not persisted
    elif body.lat is not None and body.lon is not None:
        user.last_lat, user.last_lon = body.lat, body.lon
    resolved = await assistant.intent_to_query(session, intent, user)
    resp = await search_service.search(session, resolved.query)
    return SearchOut(total=resp.total, results=[_result_out(r) for r in resp.results],
                     understood=intent.model_dump(mode="json"), summary=assistant.describe(intent, resolved))


async def _public_pro(session: AsyncSession, pro_id: int):
    pro = await pro_service.get_public_pro(session, pro_id)
    if pro is None or pro.status != ProStatus.ACTIVE:
        raise HTTPException(404, "Professional not found")
    return pro


def pro_detail(pro) -> ProDetail:
    hours: dict[int, list[str]] = {d: [] for d in range(7)}
    for wh in sorted(pro.working_hours, key=lambda w: (w.weekday, w.start_time)):
        hours[wh.weekday].append(f"{wh.start_time:%H:%M}-{wh.end_time:%H:%M}")
    data = ProSummary.model_validate(pro).model_dump()
    return ProDetail(**data, address=pro.address, phone=pro.phone, website=pro.website,
                     specialties=pro.specialties or [], timezone=pro.timezone, status=pro.status.value,
                     services=[ServiceOut.model_validate(s) for s in pro.services if s.is_active], hours=hours,
                     photos=[{"id": p.id, "url": p.url, "file_id": p.file_id, "caption": p.caption}
                             for p in pro.photos])


@router.get("/professionals/{pro_id}", response_model=ProDetail)
async def professional(pro_id: int, session: AsyncSession = Depends(get_session)):
    return pro_detail(await _public_pro(session, pro_id))


@router.get("/professionals/{pro_id}/reviews", response_model=list[ReviewOut])
async def professional_reviews(pro_id: int, limit: int = Query(20, le=100), session: AsyncSession = Depends(get_session)):
    return await pro_service.published_reviews(session, pro_id, limit)


@router.get("/professionals/{pro_id}/availability", response_model=list[SlotOut])
async def professional_availability(
    pro_id: int, service_id: int, start: date | None = None, days: int = Query(7, ge=1, le=31),
    session: AsyncSession = Depends(get_session),
):
    pro = await _public_pro(session, pro_id)
    svc = await session.get(Service, service_id)
    if svc is None or svc.professional_id != pro.id or not svc.is_active:
        raise HTTPException(404, "Unknown service")
    now = datetime.now(UTC)
    if start:
        window_start, _ = availability.local_day_window(start, pro.timezone)
    else:
        window_start = now
    window_start = max(window_start, now)
    slots = await availability.get_slots(session, pro, svc.duration_min, window_start,
                                         window_start + timedelta(days=days))
    return [SlotOut(start=s.start, end=s.end, freed=s.freed) for s in slots]
