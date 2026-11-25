"""Periodic jobs. Each job is idempotent and safe to run on several workers
(rows are claimed with SELECT ... FOR UPDATE SKIP LOCKED)."""
from __future__ import annotations

import logging
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models import (
    Booking,
    BookingStatus,
    PlatformSetting,
    Professional,
    QuoteRequest,
    QuoteRequestStatus,
)
from app.services import booking as booking_service
from app.services import notifications

log = logging.getLogger(__name__)
UTC = timezone.utc
AUTO_COMPLETE_DELAY = timedelta(hours=2)


def _booking_opts():
    return (selectinload(Booking.client), selectinload(Booking.professional).selectinload(Professional.user),
            selectinload(Booking.service))


async def send_reminders(session: AsyncSession, now: datetime | None = None) -> int:
    now = now or datetime.now(UTC)
    sent = 0
    for kind, delta, column in (("24h", timedelta(hours=24), Booking.reminder_24h_sent_at),
                                ("1h", timedelta(hours=1), Booking.reminder_1h_sent_at)):
        rows = (await session.execute(
            select(Booking).where(Booking.status == BookingStatus.CONFIRMED, column.is_(None),
                                  Booking.start_at > now, Booking.start_at <= now + delta)
            .options(*_booking_opts()).with_for_update(skip_locked=True, of=Booking).limit(200)
        )).scalars().all()
        for b in rows:
            # Skip the 24h reminder for bookings made less than ~25h before the start
            if kind == "24h" and b.created_at and b.start_at - b.created_at < timedelta(hours=25):
                b.reminder_24h_sent_at = now
                continue
            setattr(b, column.key, now)
            await notifications.reminder(b, kind)
            sent += 1
        await session.commit()
    return sent


async def expire_pending(session: AsyncSession, now: datetime | None = None) -> int:
    """Pending requests not answered in time are refused automatically (frees the slot)."""
    now = now or datetime.now(UTC)
    limit = now - timedelta(hours=settings.pending_booking_timeout_hours)
    rows = (await session.execute(
        select(Booking).where(Booking.status == BookingStatus.PENDING,
                              (Booking.created_at < limit) | (Booking.start_at <= now))
        .options(*_booking_opts()).with_for_update(skip_locked=True, of=Booking).limit(200)
    )).scalars().all()
    for b in rows:
        await booking_service.refuse_booking(session, b, None, "Sans réponse du professionnel", system=True)
    return len(rows)


async def auto_complete(session: AsyncSession, now: datetime | None = None) -> int:
    now = now or datetime.now(UTC)
    rows = (await session.execute(
        select(Booking).where(Booking.status == BookingStatus.CONFIRMED, Booking.end_at < now - AUTO_COMPLETE_DELAY)
        .options(*_booking_opts()).with_for_update(skip_locked=True, of=Booking).limit(200)
    )).scalars().all()
    for b in rows:
        await booking_service.complete_booking(session, b, None, now=now)
    return len(rows)


async def expire_quote_requests(session: AsyncSession, now: datetime | None = None) -> int:
    now = now or datetime.now(UTC)
    rows = (await session.execute(
        select(QuoteRequest).where(QuoteRequest.status == QuoteRequestStatus.OPEN, QuoteRequest.expires_at < now)
        .with_for_update(skip_locked=True)
    )).scalars().all()
    for r in rows:
        r.status = QuoteRequestStatus.EXPIRED
    await session.commit()
    return len(rows)


async def pro_daily_agenda(session: AsyncSession, now: datetime | None = None, hour: int = 19) -> int:
    """Once a day (after 19:00 local) send each pro tomorrow's appointments."""
    now = now or datetime.now(UTC)
    tz = ZoneInfo(settings.default_timezone)
    local = now.astimezone(tz)
    if local.hour < hour:
        return 0
    key = "job:pro_daily_agenda"
    marker = await session.get(PlatformSetting, key, with_for_update=True)
    today = local.date().isoformat()
    if marker and marker.value.get("date") == today:
        return 0
    if marker is None:
        marker = PlatformSetting(key=key, value={})
        session.add(marker)
    marker.value = {"date": today}
    await session.commit()

    start = datetime.combine(local.date() + timedelta(days=1), time(0), tz).astimezone(UTC)
    end = start + timedelta(days=1)
    rows = (await session.execute(
        select(Booking).where(Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING]),
                              Booking.start_at >= start, Booking.start_at < end)
        .options(*_booking_opts()).order_by(Booking.start_at)
    )).scalars().all()
    by_pro: dict[int, list[Booking]] = {}
    for b in rows:
        by_pro.setdefault(b.professional_id, []).append(b)
    for bookings in by_pro.values():
        await notifications.pro_daily_agenda(bookings[0].professional, bookings)
    return len(by_pro)
