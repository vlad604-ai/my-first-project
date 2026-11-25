"""Availability engine.

The core (`compute_slots`) is a pure function: given opening rules, closures and
busy intervals it returns bookable start times. It is used by the booking
service (strict validation before insert), by search (next availability) and by
the "available now" feature. Nothing here is simulated: every busy interval
comes from real bookings in the database.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import ACTIVE_BOOKING_STATUSES, Booking, BookingStatus, CustomHoliday, Professional, TimeOff, WorkingHours
from app.services.holidays import is_public_holiday

UTC = timezone.utc


@dataclass(frozen=True)
class Interval:
    start: datetime
    end: datetime

    def overlaps(self, other: Interval) -> bool:
        return self.start < other.end and other.start < self.end


@dataclass
class ProAvailabilityContext:
    """Everything needed to compute slots for one professional."""

    timezone: str
    weekly: dict[int, list[tuple[time, time]]]  # weekday -> intervals
    closures: list[Interval] = field(default_factory=list)
    busy: list[Interval] = field(default_factory=list)  # [start, block_end) of active bookings
    closed_days: set[date] = field(default_factory=set)
    travel_buffer_min: int = 0
    slot_step_min: int = 15
    min_notice_min: int = 60
    max_advance_days: int = 60
    freed: list[Interval] = field(default_factory=list)  # recently cancelled (last-minute openings)


@dataclass(frozen=True)
class Slot:
    start: datetime  # UTC aware
    end: datetime
    freed: bool = False  # True if it was released by a recent cancellation


def compute_slots(
    ctx: ProAvailabilityContext,
    duration_min: int,
    window_start: datetime,
    window_end: datetime,
    now: datetime | None = None,
    limit: int | None = None,
    hour_range: tuple[float, float] | None = None,
) -> list[Slot]:
    """Return bookable slots whose start lies in [window_start, window_end).

    Rules applied:
    * weekly opening intervals (breaks = gaps between intervals);
    * public holidays / custom closed days and pro closures (time off);
    * existing active bookings including the travel buffer *after* each booking;
    * the candidate's own travel buffer must not overlap the next booking;
    * minimum notice and maximum advance booking horizon.
    """
    if duration_min <= 0:
        return []
    now = (now or datetime.now(UTC)).astimezone(UTC)
    tz = ZoneInfo(ctx.timezone)
    earliest = max(window_start.astimezone(UTC), now + timedelta(minutes=ctx.min_notice_min))
    horizon = now + timedelta(days=ctx.max_advance_days)
    latest = min(window_end.astimezone(UTC), horizon)
    if earliest >= latest:
        return []

    duration = timedelta(minutes=duration_min)
    buffer = timedelta(minutes=ctx.travel_buffer_min)
    step = timedelta(minutes=max(5, ctx.slot_step_min))
    blocked = sorted([(b, False) for b in ctx.busy] + [(c, True) for c in ctx.closures], key=lambda x: x[0].start)

    slots: list[Slot] = []
    day = earliest.astimezone(tz).date()
    last_day = latest.astimezone(tz).date()
    while day <= last_day:
        if day not in ctx.closed_days:
            for open_t, close_t in sorted(ctx.weekly.get(day.weekday(), [])):
                open_dt = datetime.combine(day, open_t, tz).astimezone(UTC)
                close_dt = datetime.combine(day, close_t, tz).astimezone(UTC)
                # Align candidates to the step grid starting at the opening time.
                cursor = open_dt
                if cursor < earliest:
                    jumps = -(-(earliest - cursor) // step)  # ceil division
                    cursor = cursor + step * jumps
                while cursor + duration <= close_dt and cursor < latest:
                    # The service itself must fit inside the opening interval; the
                    # travel buffer only has to avoid other bookings / closures.
                    occupied = Interval(cursor, cursor + duration + buffer)
                    service_iv = Interval(cursor, cursor + duration)
                    conflict = None
                    for b, is_closure in blocked:
                        if b.start >= occupied.end:
                            break
                        if is_closure:
                            if b.overlaps(service_iv):
                                conflict = b
                                break
                        elif b.overlaps(occupied):
                            conflict = b
                            break
                    if conflict is None and hour_range is not None:
                        loc = cursor.astimezone(tz)
                        hh = loc.hour + loc.minute / 60
                        if not (hour_range[0] <= hh < hour_range[1]):
                            cursor += step
                            continue
                    if conflict is None:
                        freed = any(f.overlaps(service_iv) for f in ctx.freed)
                        slots.append(Slot(cursor, cursor + duration, freed))
                        if limit and len(slots) >= limit:
                            return slots
                        cursor += step
                    else:
                        # Jump past the conflict, staying on the grid.
                        jumps = max(1, -(-(conflict.end - cursor) // step))
                        cursor += step * jumps
        day += timedelta(days=1)
    return slots


# ---------------------------------------------------------------------------
# DB loading helpers
# ---------------------------------------------------------------------------
async def load_contexts(
    session: AsyncSession,
    pros: Sequence[Professional],
    window_start: datetime,
    window_end: datetime,
    exclude_booking_id=None,
) -> dict[int, ProAvailabilityContext]:
    """Batch-load availability data for many professionals (3 queries total)."""
    if not pros:
        return {}
    ids = [p.id for p in pros]
    margin = timedelta(days=1)

    wh_rows = (await session.execute(select(WorkingHours).where(WorkingHours.professional_id.in_(ids)))).scalars()
    weekly: dict[int, dict[int, list[tuple[time, time]]]] = defaultdict(lambda: defaultdict(list))
    for wh in wh_rows:
        weekly[wh.professional_id][wh.weekday].append((wh.start_time, wh.end_time))

    off_rows = (
        await session.execute(
            select(TimeOff).where(
                TimeOff.professional_id.in_(ids),
                TimeOff.end_at > window_start - margin,
                TimeOff.start_at < window_end + margin,
            )
        )
    ).scalars()
    closures: dict[int, list[Interval]] = defaultdict(list)
    for off in off_rows:
        closures[off.professional_id].append(Interval(off.start_at, off.end_at))

    bq = select(Booking.id, Booking.professional_id, Booking.start_at, Booking.block_end_at, Booking.status,
                Booking.cancelled_at, Booking.end_at).where(
        Booking.professional_id.in_(ids),
        Booking.block_end_at > window_start - margin,
        Booking.start_at < window_end + margin,
        Booking.status.in_([*ACTIVE_BOOKING_STATUSES, BookingStatus.CANCELLED]),
    )
    busy: dict[int, list[Interval]] = defaultdict(list)
    freed: dict[int, list[Interval]] = defaultdict(list)
    recent = datetime.now(UTC) - timedelta(hours=24)
    for row in (await session.execute(bq)).all():
        if exclude_booking_id is not None and row.id == exclude_booking_id:
            continue
        if row.status in ACTIVE_BOOKING_STATUSES:
            busy[row.professional_id].append(Interval(row.start_at, row.block_end_at))
        elif row.cancelled_at and row.cancelled_at >= recent:
            freed[row.professional_id].append(Interval(row.start_at, row.end_at))

    closed_days = await _closed_days(session, window_start, window_end)

    out: dict[int, ProAvailabilityContext] = {}
    for p in pros:
        out[p.id] = ProAvailabilityContext(
            timezone=p.timezone or settings.default_timezone,
            weekly=dict(weekly.get(p.id, {})),
            closures=closures.get(p.id, []),
            busy=busy.get(p.id, []),
            closed_days=closed_days if p.closed_on_holidays else set(),
            travel_buffer_min=p.travel_buffer_min or 0,
            slot_step_min=p.slot_step_min or 15,
            min_notice_min=p.min_notice_min if p.min_notice_min is not None else 60,
            max_advance_days=p.max_advance_days or 60,
            freed=freed.get(p.id, []),
        )
    return out


async def _closed_days(session: AsyncSession, start: datetime, end: datetime) -> set[date]:
    days: set[date] = set()
    d = (start - timedelta(days=1)).date()
    while d <= (end + timedelta(days=1)).date():
        if is_public_holiday(d, settings.holiday_country):
            days.add(d)
        d += timedelta(days=1)
    rows = (
        await session.execute(
            select(CustomHoliday.day).where(
                and_(CustomHoliday.day >= start.date(), CustomHoliday.day <= end.date())
            )
        )
    ).scalars()
    days.update(rows)
    return days


async def get_slots(
    session: AsyncSession,
    pro: Professional,
    duration_min: int,
    window_start: datetime,
    window_end: datetime,
    limit: int | None = None,
    exclude_booking_id=None,
    now: datetime | None = None,
) -> list[Slot]:
    ctxs = await load_contexts(session, [pro], window_start, window_end, exclude_booking_id)
    return compute_slots(ctxs[pro.id], duration_min, window_start, window_end, now=now, limit=limit)


def group_by_local_day(slots: Iterable[Slot], tz_name: str) -> dict[date, list[Slot]]:
    tz = ZoneInfo(tz_name)
    out: dict[date, list[Slot]] = defaultdict(list)
    for s in slots:
        out[s.start.astimezone(tz).date()].append(s)
    return dict(out)


def local_day_window(day: date, tz_name: str) -> tuple[datetime, datetime]:
    tz = ZoneInfo(tz_name)
    start = datetime.combine(day, time(0), tz).astimezone(UTC)
    return start, start + timedelta(days=1)
