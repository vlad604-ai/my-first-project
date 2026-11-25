"""Unit tests of the pure slot engine."""
from datetime import date, datetime, time, timedelta, timezone

from app.services.availability import Interval, ProAvailabilityContext, compute_slots
from app.services.holidays import easter_sunday, is_public_holiday

UTC = timezone.utc
# A Monday far from DST changes, in UTC for readability (Paris = UTC+1 in winter)
NOW = datetime(2030, 1, 7, 6, 0, tzinfo=UTC)  # Monday 07:00 Paris


def ctx(**kw) -> ProAvailabilityContext:
    base = dict(timezone="Europe/Paris", weekly={0: [(time(9), time(12)), (time(14), time(18))]},
                slot_step_min=30, min_notice_min=0, max_advance_days=60)
    base.update(kw)
    return ProAvailabilityContext(**base)


def day_window():
    return NOW, NOW + timedelta(days=1)


def hhmm(slots):
    return [(s.start + timedelta(hours=1)).strftime("%H:%M") for s in slots]  # back to Paris time


def test_opening_hours_and_break():
    slots = compute_slots(ctx(), 60, *day_window(), now=NOW)
    assert hhmm(slots) == ["09:00", "09:30", "10:00", "10:30", "11:00", "14:00", "14:30", "15:00", "15:30",
                           "16:00", "16:30", "17:00"]


def test_closed_day_returns_nothing():
    tuesday = NOW + timedelta(days=1)
    assert compute_slots(ctx(), 30, tuesday, tuesday + timedelta(days=1), now=NOW) == []


def test_existing_booking_blocks_overlaps():
    busy = [Interval(datetime(2030, 1, 7, 9, 0, tzinfo=UTC), datetime(2030, 1, 7, 10, 0, tzinfo=UTC))]  # 10-11 Paris
    slots = compute_slots(ctx(busy=busy), 60, *day_window(), now=NOW)
    assert "09:30" not in hhmm(slots) and "10:00" not in hhmm(slots) and "10:30" not in hhmm(slots)
    assert "09:00" in hhmm(slots) and "11:00" in hhmm(slots)


def test_travel_buffer_is_respected():
    # booking 10:00-11:00 Paris, blocked until 11:30 because of a 30 min travel buffer
    busy = [Interval(datetime(2030, 1, 7, 9, 0, tzinfo=UTC), datetime(2030, 1, 7, 10, 30, tzinfo=UTC))]
    slots = compute_slots(ctx(busy=busy, travel_buffer_min=30), 30, *day_window(), now=NOW)
    labels = hhmm(slots)
    assert "11:00" not in labels  # inside the previous booking's buffer
    assert "09:00" in labels  # 09:00-09:30 + 30 min buffer ends exactly at 10:00
    assert "09:30" not in labels  # its own buffer would overlap the 10:00 booking
    assert "11:30" in labels


def test_closure_removes_slots():
    closure = [Interval(datetime(2030, 1, 7, 13, 0, tzinfo=UTC), datetime(2030, 1, 7, 23, 0, tzinfo=UTC))]
    assert hhmm(compute_slots(ctx(closures=closure), 60, *day_window(), now=NOW))[-1] == "11:00"


def test_holiday_closed_day():
    c = ctx(closed_days={date(2030, 1, 7)})
    assert compute_slots(c, 30, *day_window(), now=NOW) == []


def test_min_notice_and_horizon():
    now = datetime(2030, 1, 7, 9, 10, tzinfo=UTC)  # 10:10 Paris
    slots = compute_slots(ctx(min_notice_min=60), 30, now, now + timedelta(days=1), now=now)
    assert hhmm(slots)[0] == "11:30"  # 10:10 + 60 min = 11:10 -> next grid slot 11:30
    assert compute_slots(ctx(max_advance_days=1), 30, NOW + timedelta(days=7), NOW + timedelta(days=8), now=NOW) == []


def test_hour_range_filter():
    slots = compute_slots(ctx(), 30, *day_window(), now=NOW, hour_range=(14, 16))
    assert hhmm(slots) == ["14:00", "14:30", "15:00", "15:30"]


def test_limit():
    assert len(compute_slots(ctx(), 30, *day_window(), now=NOW, limit=3)) == 3


def test_service_must_fit_in_one_opening_interval():
    # 4h does not fit in 09-12 and only fits once in 14-18; breaks are never crossed
    assert hhmm(compute_slots(ctx(), 240, *day_window(), now=NOW)) == ["14:00"]


def test_french_holidays():
    assert easter_sunday(2026) == date(2026, 4, 5)
    assert is_public_holiday(date(2026, 7, 14))
    assert is_public_holiday(date(2026, 4, 6))  # Easter Monday
    assert not is_public_holiday(date(2026, 7, 15))
