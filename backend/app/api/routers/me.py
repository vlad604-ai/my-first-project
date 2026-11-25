"""Authenticated client endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user
from app.db import get_session
from app.models import Urgency, User
from app.schemas.common import (
    BookingIn,
    BookingOut,
    CancelIn,
    MessageIn,
    ProSummary,
    QuoteOut,
    QuoteRequestIn,
    QuoteRequestOut,
    RescheduleIn,
    ReviewIn,
    ReviewOut,
    UserOut,
)
from app.services import booking as booking_service
from app.services import messaging
from app.services import quotes as quote_service
from app.services import reviews as review_service
from app.services import users as user_service

router = APIRouter(prefix="/me", tags=["me"])


def _booking_error(exc: booking_service.BookingError) -> HTTPException:
    code = {"slot_unavailable": 409, "not_allowed": 403, "self_booking": 403, "pro_unavailable": 404,
            "unknown_service": 404, "invalid_state": 409}.get(exc.code, 422)
    return HTTPException(code, {"code": exc.code, "message": str(exc)})


@router.get("", response_model=UserOut)
async def me(user: User = Depends(current_user)):
    return user


@router.get("/bookings", response_model=list[BookingOut])
async def my_bookings(upcoming: bool = True, user: User = Depends(current_user),
                      session: AsyncSession = Depends(get_session)):
    return await booking_service.list_client_bookings(session, user, upcoming=upcoming, limit=50)


@router.post("/bookings", response_model=BookingOut, status_code=201)
async def create_booking(body: BookingIn, user: User = Depends(current_user),
                         session: AsyncSession = Depends(get_session)):
    try:
        return await booking_service.create_booking(
            session, user, body.professional_id, body.service_id, body.start_at, address=body.address,
            lat=body.lat, lon=body.lon, client_note=body.client_note, is_urgent=body.is_urgent, source="api")
    except booking_service.BookingError as exc:
        raise _booking_error(exc) from exc


async def _own_booking(session: AsyncSession, booking_id: uuid.UUID, user: User):
    b = await booking_service.load_booking(session, booking_id)
    if b is None or b.client_id != user.id:
        raise HTTPException(404, "Booking not found")
    return b


@router.get("/bookings/{booking_id}", response_model=BookingOut)
async def get_booking(booking_id: uuid.UUID, user: User = Depends(current_user),
                      session: AsyncSession = Depends(get_session)):
    return await _own_booking(session, booking_id, user)


@router.post("/bookings/{booking_id}/cancel", response_model=BookingOut)
async def cancel_booking(booking_id: uuid.UUID, body: CancelIn, user: User = Depends(current_user),
                         session: AsyncSession = Depends(get_session)):
    b = await _own_booking(session, booking_id, user)
    try:
        return await booking_service.cancel_booking(session, b, user, body.reason)
    except booking_service.BookingError as exc:
        raise _booking_error(exc) from exc


@router.post("/bookings/{booking_id}/reschedule", response_model=BookingOut)
async def reschedule_booking(booking_id: uuid.UUID, body: RescheduleIn, user: User = Depends(current_user),
                             session: AsyncSession = Depends(get_session)):
    b = await _own_booking(session, booking_id, user)
    try:
        return await booking_service.reschedule_booking(session, b, user, body.start_at)
    except booking_service.BookingError as exc:
        raise _booking_error(exc) from exc


@router.post("/bookings/{booking_id}/review", response_model=ReviewOut, status_code=201)
async def review_booking(booking_id: uuid.UUID, body: ReviewIn, user: User = Depends(current_user),
                         session: AsyncSession = Depends(get_session)):
    try:
        return await review_service.create_review(session, user, booking_id, body.rating, body.comment)
    except review_service.ReviewError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/favorites", response_model=list[ProSummary])
async def favorites(user: User = Depends(current_user), session: AsyncSession = Depends(get_session)):
    return await user_service.list_favorites(session, user)


@router.post("/favorites/{pro_id}")
async def toggle_favorite(pro_id: int, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)):
    return {"favorite": await user_service.toggle_favorite(session, user, pro_id)}


@router.post("/quote-requests", response_model=QuoteRequestOut, status_code=201)
async def create_quote_request(body: QuoteRequestIn, user: User = Depends(current_user),
                               session: AsyncSession = Depends(get_session)):
    try:
        req, _ = await quote_service.create_request(
            session, user, body.category_id, body.description, city=body.city, postal_code=body.postal_code,
            lat=body.lat, lon=body.lon, budget_cents=body.budget_cents, urgency=Urgency(body.urgency),
            target_pro_id=body.target_pro_id)
    except (quote_service.QuoteError, ValueError) as exc:
        raise HTTPException(422, str(exc)) from exc
    return await quote_service.get_request(session, req.id)


@router.get("/quote-requests", response_model=list[QuoteRequestOut])
async def my_quote_requests(user: User = Depends(current_user), session: AsyncSession = Depends(get_session)):
    return await quote_service.list_client_requests(session, user)


@router.post("/quotes/{quote_id}/accept", response_model=QuoteOut)
async def accept_quote(quote_id: int, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)):
    try:
        return await quote_service.accept_quote(session, user, quote_id)
    except quote_service.QuoteError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/messages/{pro_id}")
async def message_pro(pro_id: int, body: MessageIn, user: User = Depends(current_user),
                      session: AsyncSession = Depends(get_session)):
    try:
        msg = await messaging.send_message(session, user, user.id, pro_id, body.body)
    except messaging.MessagingError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"id": msg.id}


@router.get("/export")
async def gdpr_export(user: User = Depends(current_user), session: AsyncSession = Depends(get_session)):
    return await user_service.gdpr_export(session, user)


@router.delete("", status_code=204)
async def gdpr_delete(user: User = Depends(current_user), session: AsyncSession = Depends(get_session)):
    await user_service.gdpr_delete(session, user)
