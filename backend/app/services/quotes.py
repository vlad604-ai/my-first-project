"""Quote requests (devis): publish, dispatch to matching pros, answer, compare, accept."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models import (
    Professional,
    ProStatus,
    Quote,
    QuoteRecipient,
    QuoteRequest,
    QuoteRequestStatus,
    QuoteStatus,
    RecipientStatus,
    Urgency,
    User,
    professional_categories,
)
from app.services import notifications
from app.services.audit import audit
from app.services.geo import bounding_box, haversine_km
from app.services.search import expand_categories
from app.services.text import normalize

UTC = timezone.utc


class QuoteError(Exception):
    pass


async def create_request(session: AsyncSession, client: User, category_id: int, description: str,
                         city: str | None = None, postal_code: str | None = None, lat: float | None = None,
                         lon: float | None = None, budget_cents: int | None = None,
                         urgency: Urgency = Urgency.FLEXIBLE, target_pro_id: int | None = None
                         ) -> tuple[QuoteRequest, int]:
    if len(description.strip()) < 10:
        raise QuoteError("description_too_short")
    open_count = len((await session.execute(select(QuoteRequest.id).where(
        QuoteRequest.client_id == client.id, QuoteRequest.status == QuoteRequestStatus.OPEN))).all())
    if open_count >= 10:
        raise QuoteError("too_many_open_requests")  # anti-abuse
    req = QuoteRequest(client_id=client.id, category_id=category_id, description=description.strip()[:4000],
                       city=city, postal_code=postal_code, lat=lat, lon=lon, budget_cents=budget_cents,
                       urgency=urgency, expires_at=datetime.now(UTC) + timedelta(days=settings.quote_request_ttl_days))
    session.add(req)
    await session.flush()
    pros = await matching_professionals(session, req)
    if target_pro_id and all(p.id != target_pro_id for p in pros):
        target = (await session.execute(select(Professional).where(
            Professional.id == target_pro_id, Professional.status == ProStatus.ACTIVE,
            Professional.accepts_quotes.is_(True)).options(selectinload(Professional.user)))).scalar_one_or_none()
        if target and target.user_id != client.id:
            pros.insert(0, target)
    for pro in pros:
        session.add(QuoteRecipient(request_id=req.id, professional_id=pro.id))
    audit(session, "quote_request.create", "quote_request", req.id, client.id, recipients=len(pros))
    await session.commit()
    for pro in pros:
        await notifications.quote_request_received(pro, req)
    return req, len(pros)


async def matching_professionals(session: AsyncSession, req: QuoteRequest) -> list[Professional]:
    cat_ids = await expand_categories(session, [req.category_id])
    stmt = (
        select(Professional)
        .where(Professional.status == ProStatus.ACTIVE, Professional.accepts_quotes.is_(True),
               Professional.user_id != req.client_id,
               or_(Professional.category_id.in_(cat_ids),
                   exists().where(and_(professional_categories.c.professional_id == Professional.id,
                                       professional_categories.c.category_id.in_(cat_ids)))))
        .options(selectinload(Professional.user))
    )
    if req.lat is not None and req.lon is not None:
        la1, la2, lo1, lo2 = bounding_box(req.lat, req.lon, 100)
        stmt = stmt.where(Professional.lat.between(la1, la2), Professional.lon.between(lo1, lo2))
    pros = list((await session.execute(stmt)).scalars())
    desc = normalize(req.description)
    scored = []
    for pro in pros:
        if req.budget_cents and pro.quote_min_budget_cents and req.budget_cents < pro.quote_min_budget_cents:
            continue
        dist = None
        if req.lat is not None and pro.lat is not None:
            dist = haversine_km(req.lat, req.lon, pro.lat, pro.lon)
            reach = pro.service_radius_km if pro.is_mobile else 30
            if dist > max(reach, 5):
                continue
        # Pros may restrict the kind of jobs they want (quote_keywords)
        keywords = [normalize(k) for k in (pro.quote_keywords or []) if k]
        if keywords and not any(k in desc for k in keywords):
            continue
        scored.append(((dist if dist is not None else 50) - pro.rating_avg * 2 - (5 if pro.is_verified else 0), pro))
    scored.sort(key=lambda x: x[0])
    return [p for _, p in scored[: settings.quote_request_max_recipients]]


async def get_request(session: AsyncSession, request_id: int) -> QuoteRequest | None:
    return (await session.execute(
        select(QuoteRequest).where(QuoteRequest.id == request_id)
        .options(selectinload(QuoteRequest.quotes).selectinload(Quote.professional),
                 selectinload(QuoteRequest.category), selectinload(QuoteRequest.client),
                 selectinload(QuoteRequest.recipients))
        .execution_options(populate_existing=True)
    )).scalar_one_or_none()


async def list_client_requests(session: AsyncSession, client: User) -> list[QuoteRequest]:
    rows = await session.execute(
        select(QuoteRequest).where(QuoteRequest.client_id == client.id)
        .options(selectinload(QuoteRequest.quotes), selectinload(QuoteRequest.category))
        .order_by(QuoteRequest.created_at.desc()).limit(20))
    return list(rows.scalars())


async def pro_inbox(session: AsyncSession, pro: Professional) -> list[QuoteRequest]:
    rows = await session.execute(
        select(QuoteRequest).join(QuoteRecipient, QuoteRecipient.request_id == QuoteRequest.id)
        .where(QuoteRecipient.professional_id == pro.id, QuoteRecipient.status == RecipientStatus.SENT,
               QuoteRequest.status == QuoteRequestStatus.OPEN)
        .options(selectinload(QuoteRequest.category)).order_by(QuoteRequest.created_at.desc()).limit(20))
    return list(rows.scalars())


async def _recipient(session: AsyncSession, req_id: int, pro_id: int) -> QuoteRecipient:
    rec = (await session.execute(select(QuoteRecipient).where(QuoteRecipient.request_id == req_id,
                                                              QuoteRecipient.professional_id == pro_id))
           ).scalar_one_or_none()
    if rec is None:
        raise QuoteError("not_a_recipient")
    return rec


async def submit_quote(session: AsyncSession, pro: Professional, request_id: int, amount_cents: int,
                       message: str | None = None, estimated_days: int | None = None) -> Quote:
    req = await get_request(session, request_id)
    if req is None or req.status != QuoteRequestStatus.OPEN:
        raise QuoteError("request_closed")
    rec = await _recipient(session, request_id, pro.id)
    if amount_cents <= 0:
        raise QuoteError("invalid_amount")
    if any(q.professional_id == pro.id for q in req.quotes):
        raise QuoteError("already_quoted")
    quote = Quote(request_id=req.id, professional_id=pro.id, amount_cents=amount_cents,
                  message=(message or None) and message[:2000], estimated_days=estimated_days,
                  valid_until=(datetime.now(UTC) + timedelta(days=30)).date())
    session.add(quote)
    rec.status = RecipientStatus.RESPONDED
    await session.commit()
    await notifications.quote_received(req.client, quote, pro)
    return quote


async def decline_request(session: AsyncSession, pro: Professional, request_id: int) -> None:
    rec = await _recipient(session, request_id, pro.id)
    rec.status = RecipientStatus.DECLINED
    await session.commit()


async def accept_quote(session: AsyncSession, client: User, quote_id: int) -> Quote:
    quote = (await session.execute(select(Quote).where(Quote.id == quote_id)
                                   .options(selectinload(Quote.professional).selectinload(Professional.user),
                                            selectinload(Quote.request)))).scalar_one_or_none()
    if quote is None or quote.request.client_id != client.id:
        raise QuoteError("unknown_quote")
    if quote.request.status != QuoteRequestStatus.OPEN or quote.status != QuoteStatus.SENT:
        raise QuoteError("request_closed")
    quote.status = QuoteStatus.ACCEPTED
    quote.request.status = QuoteRequestStatus.AWARDED
    others = (await session.execute(select(Quote).where(Quote.request_id == quote.request_id, Quote.id != quote.id))
              ).scalars()
    for other in others:
        if other.status == QuoteStatus.SENT:
            other.status = QuoteStatus.REJECTED
    audit(session, "quote.accept", "quote", quote.id, client.id)
    await session.commit()
    await notifications.quote_accepted(quote.professional, quote, client)
    return quote


async def cancel_request(session: AsyncSession, client: User, request_id: int) -> None:
    req = await session.get(QuoteRequest, request_id)
    if req is None or req.client_id != client.id:
        raise QuoteError("unknown_request")
    if req.status == QuoteRequestStatus.OPEN:
        req.status = QuoteRequestStatus.CANCELLED
        await session.commit()
