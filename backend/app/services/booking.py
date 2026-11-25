"""Booking engine: create, confirm, refuse, cancel, reschedule, complete.

Concurrency safety is layered:
1. `SELECT ... FOR UPDATE` on the professional row serialises concurrent
   booking attempts for the same professional;
2. the requested start is re-validated against the live availability engine;
3. the PostgreSQL exclusion constraint `ex_bookings_no_overlap` is the final,
   unbypassable guarantee (IntegrityError -> SlotUnavailable).
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import replace
from datetime import datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    ACTIVE_BOOKING_STATUSES,
    Booking,
    BookingEvent,
    BookingLocation,
    BookingStatus,
    ProStatus,
    Professional,
    Service,
    User,
)
from app.services import availability, notifications
from app.services.audit import audit
from app.services.geo import haversine_km
from app.services.text import booking_reference

log = logging.getLogger(__name__)
UTC = timezone.utc


class BookingError(Exception):
    code = "booking_error"

    def __init__(self, message: str = "", code: str | None = None):
        super().__init__(message or self.code)
        if code:
            self.code = code


class SlotUnavailable(BookingError):
    code = "slot_unavailable"


class NotAllowed(BookingError):
    code = "not_allowed"


class InvalidState(BookingError):
    code = "invalid_state"


async def load_booking(session: AsyncSession, booking_id) -> Booking | None:
    if isinstance(booking_id, str):
        try:
            booking_id = uuid.UUID(booking_id)
        except ValueError:
            return None
    return (
        await session.execute(
            select(Booking)
            .where(Booking.id == booking_id)
            .options(
                selectinload(Booking.client),
                selectinload(Booking.professional).selectinload(Professional.user),
                selectinload(Booking.service),
                selectinload(Booking.events),
            )
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()


def _is_on_duty(pro: Professional, now: datetime) -> bool:
    return bool(pro.accepts_urgent and pro.on_duty_until and pro.on_duty_until > now)


async def _validate_slot(
    session: AsyncSession,
    pro: Professional,
    start_at: datetime,
    duration_min: int,
    urgent: bool,
    exclude_booking_id=None,
) -> None:
    now = datetime.now(UTC)
    window_end = start_at + timedelta(minutes=1)
    ctxs = await availability.load_contexts(session, [pro], start_at, window_end + timedelta(minutes=duration_min),
                                            exclude_booking_id)
    ctx = ctxs[pro.id]
    if urgent:
        if not _is_on_duty(pro, now):
            raise SlotUnavailable("Professional is not available for urgent interventions")
        # On-duty pros accept interventions outside normal hours, as long as they
        # don't collide with an existing booking or closure.
        full_day = [(time(0, 0), time(23, 59))]
        ctx = replace(ctx, weekly={d: full_day for d in range(7)}, min_notice_min=0, slot_step_min=5, closed_days=set())
    slots = availability.compute_slots(ctx, duration_min, start_at, window_end, now=now, limit=1)
    if not slots or slots[0].start != start_at:
        raise SlotUnavailable("This time slot is no longer available")


async def create_booking(
    session: AsyncSession,
    client: User,
    professional_id: int,
    service_id: int,
    start_at: datetime,
    *,
    location: BookingLocation | None = None,
    address: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    client_note: str | None = None,
    is_urgent: bool = False,
    source: str = "telegram",
) -> Booking:
    if start_at.tzinfo is None:
        raise BookingError("start_at must be timezone-aware", "invalid_datetime")
    start_at = start_at.astimezone(UTC)
    if client.is_banned:
        raise NotAllowed("Account suspended")

    # (1) serialise per professional
    pro = (
        await session.execute(select(Professional).where(Professional.id == professional_id).with_for_update())
    ).scalar_one_or_none()
    if pro is None or pro.status != ProStatus.ACTIVE:
        raise NotAllowed("Professional unavailable", "pro_unavailable")
    if pro.user_id == client.id:
        raise NotAllowed("You cannot book yourself", "self_booking")
    service = await session.get(Service, service_id)
    if service is None or service.professional_id != pro.id or not service.is_active:
        raise BookingError("Unknown service", "unknown_service")

    loc = location or service.location
    if loc == BookingLocation.AT_CLIENT:
        if not pro.is_mobile:
            raise BookingError("This professional does not travel", "not_mobile")
        if not address and (lat is None or lon is None):
            raise BookingError("An address is required for an intervention", "address_required")
        if lat is not None and lon is not None and pro.lat is not None and pro.lon is not None:
            if haversine_km(pro.lat, pro.lon, lat, lon) > max(pro.service_radius_km, 0) + 0.5:
                raise BookingError("Address outside the intervention area", "out_of_zone")

    # (2) re-validate against live availability
    await _validate_slot(session, pro, start_at, service.duration_min, is_urgent)

    end_at = start_at + timedelta(minutes=service.duration_min)
    status = BookingStatus.CONFIRMED if (pro.auto_confirm and not is_urgent) else BookingStatus.PENDING
    booking = Booking(
        reference=booking_reference(),
        client_id=client.id,
        professional_id=pro.id,
        service_id=service.id,
        start_at=start_at,
        end_at=end_at,
        block_end_at=end_at + timedelta(minutes=pro.travel_buffer_min or 0),
        status=status,
        location=loc,
        address=address,
        lat=lat,
        lon=lon,
        client_note=(client_note or None) and client_note[:1000],
        service_name=service.name,
        price_cents=service.price_cents,
        is_urgent=is_urgent,
        source=source,
        confirmed_at=datetime.now(UTC) if status == BookingStatus.CONFIRMED else None,
    )
    session.add(booking)
    try:
        await session.flush()  # (3) exclusion constraint fires here
    except IntegrityError as exc:
        await session.rollback()
        if "ex_bookings_no_overlap" in str(exc.orig) or "reference" not in str(exc.orig):
            raise SlotUnavailable("This time slot was just taken") from exc
        raise
    session.add(BookingEvent(booking_id=booking.id, type="created", actor_user_id=client.id,
                             data={"status": status.value, "urgent": is_urgent}))
    audit(session, "booking.create", "booking", booking.id, client.id, status=status.value)
    await session.commit()

    booking = await load_booking(session, booking.id)
    await notifications.booking_created(booking)
    return booking


def _actor_role(booking: Booking, user: User) -> str | None:
    if user.is_admin:
        return "admin"
    if booking.client_id == user.id:
        return "client"
    if booking.professional and booking.professional.user_id == user.id:
        return "professional"
    return None


async def confirm_booking(session: AsyncSession, booking: Booking, actor: User) -> Booking:
    if _actor_role(booking, actor) not in ("professional", "admin"):
        raise NotAllowed()
    if booking.status != BookingStatus.PENDING:
        raise InvalidState("Only pending bookings can be confirmed")
    if booking.start_at <= datetime.now(UTC):
        raise InvalidState("Booking already started")
    booking.status = BookingStatus.CONFIRMED
    booking.confirmed_at = datetime.now(UTC)
    session.add(BookingEvent(booking_id=booking.id, type="confirmed", actor_user_id=actor.id))
    audit(session, "booking.confirm", "booking", booking.id, actor.id)
    await session.commit()
    await notifications.booking_confirmed(booking)
    return booking


async def refuse_booking(session: AsyncSession, booking: Booking, actor: User, reason: str | None = None,
                         system: bool = False) -> Booking:
    if not system and _actor_role(booking, actor) not in ("professional", "admin"):
        raise NotAllowed()
    if booking.status != BookingStatus.PENDING:
        raise InvalidState("Only pending bookings can be refused")
    booking.status = BookingStatus.REFUSED
    booking.cancel_reason = reason
    booking.cancelled_at = datetime.now(UTC)
    booking.cancelled_by = "system" if system else "professional"
    session.add(BookingEvent(booking_id=booking.id, type="refused", actor_user_id=None if system else actor.id,
                             data={"reason": reason}))
    audit(session, "booking.refuse", "booking", booking.id, None if system else actor.id, reason=reason)
    await session.commit()
    await notifications.booking_refused(booking)
    return booking


async def cancel_booking(session: AsyncSession, booking: Booking, actor: User, reason: str | None = None) -> Booking:
    role = _actor_role(booking, actor)
    if role is None:
        raise NotAllowed()
    if booking.status not in ACTIVE_BOOKING_STATUSES:
        raise InvalidState("Booking is not active")
    if booking.start_at <= datetime.now(UTC) and role != "admin":
        raise InvalidState("Booking already started")
    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = datetime.now(UTC)
    booking.cancelled_by = role
    booking.cancel_reason = reason
    session.add(BookingEvent(booking_id=booking.id, type="cancelled", actor_user_id=actor.id,
                             data={"by": role, "reason": reason}))
    audit(session, "booking.cancel", "booking", booking.id, actor.id, by=role)
    await session.commit()
    await notifications.booking_cancelled(booking, by=role)
    return booking


async def reschedule_booking(session: AsyncSession, booking: Booking, actor: User, new_start: datetime) -> Booking:
    role = _actor_role(booking, actor)
    if role not in ("client", "admin", "professional"):
        raise NotAllowed()
    if booking.status not in ACTIVE_BOOKING_STATUSES:
        raise InvalidState("Booking is not active")
    if booking.start_at <= datetime.now(UTC):
        raise InvalidState("Booking already started")
    new_start = new_start.astimezone(UTC)
    pro = (
        await session.execute(
            select(Professional).where(Professional.id == booking.professional_id).with_for_update()
        )
    ).scalar_one()
    duration = int((booking.end_at - booking.start_at).total_seconds() // 60)
    await _validate_slot(session, pro, new_start, duration, urgent=False, exclude_booking_id=booking.id)
    old_start = booking.start_at
    booking.start_at = new_start
    booking.end_at = new_start + timedelta(minutes=duration)
    booking.block_end_at = booking.end_at + timedelta(minutes=pro.travel_buffer_min or 0)
    booking.reminder_24h_sent_at = None
    booking.reminder_1h_sent_at = None
    if role == "client" and not pro.auto_confirm:
        booking.status = BookingStatus.PENDING
        booking.confirmed_at = None
    session.add(BookingEvent(booking_id=booking.id, type="rescheduled", actor_user_id=actor.id,
                             data={"from": old_start.isoformat(), "to": new_start.isoformat(), "by": role}))
    audit(session, "booking.reschedule", "booking", booking.id, actor.id, by=role)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise SlotUnavailable("This time slot was just taken") from exc
    booking = await load_booking(session, booking.id)
    await notifications.booking_rescheduled(booking, old_start, by=role)
    return booking


async def complete_booking(session: AsyncSession, booking: Booking, actor: User | None = None,
                           now: datetime | None = None) -> Booking:
    """Mark as completed (by the pro, an admin, or the system after end time)."""
    if actor is not None and _actor_role(booking, actor) not in ("professional", "admin"):
        raise NotAllowed()
    if booking.status != BookingStatus.CONFIRMED:
        raise InvalidState("Only confirmed bookings can be completed")
    if booking.start_at > (now or datetime.now(UTC)):
        raise InvalidState("Booking has not started yet")
    booking.status = BookingStatus.COMPLETED
    pro = await session.get(Professional, booking.professional_id)
    pro.completed_count = (pro.completed_count or 0) + 1
    booking.review_requested_at = datetime.now(UTC)
    session.add(BookingEvent(booking_id=booking.id, type="completed", actor_user_id=actor.id if actor else None))
    await session.commit()
    await notifications.review_request(booking)
    return booking


async def list_client_bookings(session: AsyncSession, user: User, upcoming: bool = True, limit: int = 20):
    now = datetime.now(UTC)
    q = (
        select(Booking)
        .where(Booking.client_id == user.id)
        .options(selectinload(Booking.professional), selectinload(Booking.service))
    )
    if upcoming:
        q = q.where(Booking.end_at >= now, Booking.status.in_(ACTIVE_BOOKING_STATUSES)).order_by(Booking.start_at)
    else:
        q = q.where((Booking.end_at < now) | Booking.status.notin_(ACTIVE_BOOKING_STATUSES)).order_by(
            Booking.start_at.desc()
        )
    return list((await session.execute(q.limit(limit))).scalars())


async def list_pro_bookings(session: AsyncSession, pro: Professional, start: datetime, end: datetime,
                            statuses=ACTIVE_BOOKING_STATUSES):
    q = (
        select(Booking)
        .where(Booking.professional_id == pro.id, Booking.start_at >= start, Booking.start_at < end,
               Booking.status.in_(statuses))
        .options(selectinload(Booking.client), selectinload(Booking.service))
        .order_by(Booking.start_at)
    )
    return list((await session.execute(q)).scalars())


async def list_pending_for_pro(session: AsyncSession, pro: Professional):
    q = (
        select(Booking)
        .where(Booking.professional_id == pro.id, Booking.status == BookingStatus.PENDING,
               Booking.start_at > datetime.now(UTC))
        .options(selectinload(Booking.client), selectinload(Booking.service))
        .order_by(Booking.start_at)
    )
    return list((await session.execute(q)).scalars())
