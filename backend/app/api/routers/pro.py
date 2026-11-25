"""Professional space API (web/mobile pro dashboards use the same services as the bot)."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_pro, current_user
from app.api.routers.public import pro_detail
from app.db import get_session
from app.models import BookingLocation, PriceType, Professional, User, WorkMode
from app.schemas.common import (
    BookingOut,
    HoursIn,
    ProDetail,
    QuoteIn,
    QuoteOut,
    QuoteRequestOut,
    ServiceIn,
    ServiceOut,
    TimeOffIn,
)
from app.services import booking as booking_service
from app.services import professionals as pro_service
from app.services import quotes as quote_service

router = APIRouter(prefix="/pro", tags=["pro"])
UTC = timezone.utc


class ProCreateIn(BaseModel):
    business_name: str
    category_id: int
    work_mode: str = "on_site"
    address: str | None = None
    lat: float | None = None
    lon: float | None = None
    service_radius_km: int = 0
    description: str | None = None
    phone: str | None = None


class ProUpdateIn(BaseModel):
    business_name: str | None = None
    description: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    address: str | None = None
    service_radius_km: int | None = None
    travel_buffer_min: int | None = None
    auto_confirm: bool | None = None
    accepts_quotes: bool | None = None
    accepts_urgent: bool | None = None
    slot_step_min: int | None = None
    min_notice_min: int | None = None
    max_advance_days: int | None = None
    closed_on_holidays: bool | None = None
    specialties: list[str] | None = None
    quote_keywords: list[str] | None = None
    logo_url: str | None = None


def _err(exc: Exception) -> HTTPException:
    return HTTPException(422, str(exc))


@router.post("", response_model=ProDetail, status_code=201)
async def create(body: ProCreateIn, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)):
    try:
        pro = await pro_service.create_professional(
            session, user, body.business_name, body.category_id, WorkMode(body.work_mode), body.address,
            body.lat, body.lon, body.service_radius_km, body.description, body.phone)
    except (pro_service.ProError, ValueError) as exc:
        raise _err(exc) from exc
    return pro_detail(await pro_service.get_public_pro(session, pro.id))


@router.get("/me", response_model=ProDetail)
async def me(pro: Professional = Depends(current_pro), session: AsyncSession = Depends(get_session)):
    return pro_detail(await pro_service.get_public_pro(session, pro.id))


@router.patch("/me", response_model=ProDetail)
async def update(body: ProUpdateIn, pro: Professional = Depends(current_pro),
                 session: AsyncSession = Depends(get_session)):
    try:
        await pro_service.update_profile(session, pro, **body.model_dump(exclude_none=True))
    except pro_service.ProError as exc:
        raise _err(exc) from exc
    return pro_detail(await pro_service.get_public_pro(session, pro.id))


@router.post("/services", response_model=ServiceOut, status_code=201)
async def add_service(body: ServiceIn, pro: Professional = Depends(current_pro),
                      session: AsyncSession = Depends(get_session)):
    try:
        return await pro_service.add_service(session, pro, body.name, body.duration_min, body.price_cents,
                                             PriceType(body.price_type),
                                             BookingLocation(body.location) if body.location else None,
                                             body.description)
    except (pro_service.ProError, ValueError) as exc:
        raise _err(exc) from exc


@router.put("/services/{service_id}", response_model=ServiceOut)
async def update_service(service_id: int, body: ServiceIn, pro: Professional = Depends(current_pro),
                         session: AsyncSession = Depends(get_session)):
    data = body.model_dump()
    data["price_type"] = PriceType(data["price_type"])
    data["location"] = BookingLocation(data["location"]) if data.get("location") else None
    if data["location"] is None:
        data.pop("location")
    try:
        return await pro_service.update_service(session, pro, service_id, **data)
    except (pro_service.ProError, ValueError) as exc:
        raise _err(exc) from exc


@router.delete("/services/{service_id}", status_code=204)
async def delete_service(service_id: int, pro: Professional = Depends(current_pro),
                         session: AsyncSession = Depends(get_session)):
    try:
        await pro_service.delete_service(session, pro, service_id)
    except pro_service.ProError as exc:
        raise _err(exc) from exc


@router.put("/hours")
async def set_hours(body: HoursIn, pro: Professional = Depends(current_pro), session: AsyncSession = Depends(get_session)):
    try:
        weekly = {int(d): pro_service.parse_day_ranges(", ".join(r)) if r else [] for d, r in body.weekly.items()}
    except pro_service.ProError as exc:
        raise _err(exc) from exc
    if any(d not in range(7) for d in weekly):
        raise HTTPException(422, "weekday must be 0..6")
    await pro_service.set_weekly_hours(session, pro, weekly)
    return {"ok": True}


@router.post("/time-off", status_code=201)
async def add_time_off(body: TimeOffIn, pro: Professional = Depends(current_pro),
                       session: AsyncSession = Depends(get_session)):
    try:
        off, conflicts = await pro_service.add_time_off(session, pro, body.start_at, body.end_at, body.reason)
    except pro_service.ProError as exc:
        raise _err(exc) from exc
    return {"id": off.id, "conflicting_bookings": conflicts}


@router.delete("/time-off/{off_id}", status_code=204)
async def delete_time_off(off_id: int, pro: Professional = Depends(current_pro),
                          session: AsyncSession = Depends(get_session)):
    try:
        await pro_service.delete_time_off(session, pro, off_id)
    except pro_service.ProError as exc:
        raise _err(exc) from exc


@router.get("/bookings", response_model=list[BookingOut])
async def bookings(days: int = 14, pro: Professional = Depends(current_pro), session: AsyncSession = Depends(get_session)):
    now = datetime.now(UTC)
    return await booking_service.list_pro_bookings(session, pro, now - timedelta(days=1), now + timedelta(days=days))


async def _pro_booking(session: AsyncSession, pro: Professional, booking_id: uuid.UUID):
    b = await booking_service.load_booking(session, booking_id)
    if b is None or b.professional_id != pro.id:
        raise HTTPException(404, "Booking not found")
    return b


@router.post("/bookings/{booking_id}/{action}", response_model=BookingOut)
async def booking_action(booking_id: uuid.UUID, action: str, reason: str | None = None,
                         user: User = Depends(current_user), pro: Professional = Depends(current_pro),
                         session: AsyncSession = Depends(get_session)):
    b = await _pro_booking(session, pro, booking_id)
    try:
        if action == "confirm":
            return await booking_service.confirm_booking(session, b, user)
        if action == "refuse":
            return await booking_service.refuse_booking(session, b, user, reason)
        if action == "cancel":
            return await booking_service.cancel_booking(session, b, user, reason)
        if action == "complete":
            return await booking_service.complete_booking(session, b, user)
    except booking_service.BookingError as exc:
        raise HTTPException(409, {"code": exc.code, "message": str(exc)}) from exc
    raise HTTPException(404, "Unknown action")


@router.get("/stats")
async def stats(days: int = 30, pro: Professional = Depends(current_pro), session: AsyncSession = Depends(get_session)):
    return await pro_service.pro_stats(session, pro, days)


@router.post("/duty")
async def duty(hours: int | None = None, pro: Professional = Depends(current_pro),
               session: AsyncSession = Depends(get_session)):
    try:
        await pro_service.set_on_duty(session, pro, hours)
    except pro_service.ProError as exc:
        raise _err(exc) from exc
    return {"on_duty_until": pro.on_duty_until}


@router.get("/quote-requests", response_model=list[QuoteRequestOut])
async def quote_inbox(pro: Professional = Depends(current_pro), session: AsyncSession = Depends(get_session)):
    return [await quote_service.get_request(session, r.id) for r in await quote_service.pro_inbox(session, pro)]


@router.post("/quote-requests/{request_id}/quote", response_model=QuoteOut, status_code=201)
async def submit_quote(request_id: int, body: QuoteIn, pro: Professional = Depends(current_pro),
                       session: AsyncSession = Depends(get_session)):
    try:
        return await quote_service.submit_quote(session, pro, request_id, body.amount_cents, body.message,
                                                body.estimated_days)
    except quote_service.QuoteError as exc:
        raise _err(exc) from exc
