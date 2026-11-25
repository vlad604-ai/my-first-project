"""Professional space: onboarding, profile, services, schedule, closures, stats."""
from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models import (
    Booking,
    BookingLocation,
    BookingStatus,
    Category,
    Favorite,
    PriceType,
    Professional,
    ProfessionalPhoto,
    ProStatus,
    Review,
    ReviewStatus,
    Service,
    TimeOff,
    User,
    WorkingHours,
    WorkMode,
)
from app.services.audit import audit
from app.services.geo import geocode
from app.services.text import slugify

UTC = timezone.utc
TIME_RANGE_RE = re.compile(r"(\d{1,2})[:h]?(\d{2})?\s*-\s*(\d{1,2})[:h]?(\d{2})?")


class ProError(Exception):
    pass


async def get_pro_for_user(session: AsyncSession, user: User) -> Professional | None:
    return (
        await session.execute(
            select(Professional).where(Professional.user_id == user.id)
            .options(selectinload(Professional.services), selectinload(Professional.working_hours),
                     selectinload(Professional.category), selectinload(Professional.photos))
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()


async def get_public_pro(session: AsyncSession, pro_id: int) -> Professional | None:
    return (
        await session.execute(
            select(Professional).where(Professional.id == pro_id)
            .options(selectinload(Professional.services), selectinload(Professional.working_hours),
                     selectinload(Professional.category), selectinload(Professional.photos),
                     selectinload(Professional.user))
        )
    ).scalar_one_or_none()


async def _unique_slug(session: AsyncSession, base: str) -> str:
    slug, n = base, 1
    while (await session.execute(select(Professional.id).where(Professional.slug == slug))).first():
        n += 1
        slug = f"{base}-{n}"
    return slug


async def create_professional(
    session: AsyncSession,
    user: User,
    business_name: str,
    category_id: int,
    work_mode: WorkMode,
    city_or_address: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    service_radius_km: int = 0,
    description: str | None = None,
    phone: str | None = None,
) -> Professional:
    if await get_pro_for_user(session, user):
        raise ProError("already_pro")
    category = await session.get(Category, category_id)
    if category is None or not category.is_active:
        raise ProError("unknown_category")
    address, city, postal = None, None, None
    if city_or_address and (lat is None or lon is None):
        point = await geocode(session, city_or_address)
        if point is None:
            raise ProError("unknown_location")
        lat, lon, city, postal = point.lat, point.lon, point.label, point.postal_code
        if point.label and point.label.lower() not in city_or_address.lower():
            address = city_or_address
        elif not re.fullmatch(r"\s*\d{5}\s*", city_or_address) and city_or_address.strip().lower() != (
                point.label or "").lower():
            address = city_or_address
    pro = Professional(
        user_id=user.id,
        business_name=business_name.strip()[:160],
        slug=await _unique_slug(session, slugify(business_name)),
        category_id=category_id,
        work_mode=work_mode,
        address=address,
        city=city,
        postal_code=postal,
        lat=lat,
        lon=lon,
        service_radius_km=service_radius_km if work_mode != WorkMode.ON_SITE else 0,
        travel_buffer_min=20 if work_mode != WorkMode.ON_SITE else 0,
        description=description,
        phone=phone,
        status=ProStatus.ACTIVE if settings.auto_approve_professionals else ProStatus.PENDING,
        accepts_quotes=category.supports_quotes,
        timezone=settings.default_timezone,
    )
    session.add(pro)
    await session.flush()
    # Sensible default schedule: Mon-Fri 9-12 / 14-18 (editable)
    for wd in range(5):
        session.add(WorkingHours(professional_id=pro.id, weekday=wd, start_time=time(9), end_time=time(12)))
        session.add(WorkingHours(professional_id=pro.id, weekday=wd, start_time=time(14), end_time=time(18)))
    audit(session, "pro.create", "professional", pro.id, user.id)
    await session.commit()
    return await get_pro_for_user(session, user)


async def update_profile(session: AsyncSession, pro: Professional, **fields) -> Professional:
    allowed = {"business_name", "description", "phone", "email", "website", "address", "service_radius_km",
               "travel_buffer_min", "auto_confirm", "accepts_quotes", "accepts_urgent", "slot_step_min",
               "min_notice_min", "max_advance_days", "closed_on_holidays", "work_mode", "specialties",
               "quote_keywords", "logo_file_id", "logo_url", "quote_min_budget_cents"}
    for key, value in fields.items():
        if key not in allowed:
            raise ProError(f"field_not_editable:{key}")
        setattr(pro, key, value)
    if "address" in fields and fields["address"]:
        point = await geocode(session, fields["address"])
        if point:
            pro.lat, pro.lon, pro.city, pro.postal_code = point.lat, point.lon, point.label, point.postal_code
    await session.commit()
    return pro


def parse_day_ranges(text: str) -> list[tuple[time, time]]:
    """'9-12, 14h-18h30' -> [(09:00, 12:00), (14:00, 18:30)]. 'fermé' -> []."""
    text = text.strip().lower()
    if text in ("ferme", "fermé", "closed", "-", "0", "off"):
        return []
    ranges = []
    for m in TIME_RANGE_RE.finditer(text):
        h1, m1, h2, m2 = int(m.group(1)), int(m.group(2) or 0), int(m.group(3)), int(m.group(4) or 0)
        if not (0 <= h1 <= 23 and 0 <= h2 <= 24 and m1 < 60 and m2 < 60):
            raise ProError("invalid_time")
        start, end = time(h1, m1), time(23, 59) if h2 == 24 else time(h2, m2)
        if end <= start:
            raise ProError("invalid_range")
        ranges.append((start, end))
    if not ranges:
        raise ProError("invalid_format")
    ranges.sort()
    for (_, b1), (a2, _) in zip(ranges, ranges[1:], strict=False):
        if a2 < b1:
            raise ProError("overlapping_ranges")
    return ranges


async def set_day_hours(session: AsyncSession, pro: Professional, weekday: int, ranges: list[tuple[time, time]]):
    await session.execute(delete(WorkingHours).where(WorkingHours.professional_id == pro.id,
                                                     WorkingHours.weekday == weekday))
    for start, end in ranges:
        session.add(WorkingHours(professional_id=pro.id, weekday=weekday, start_time=start, end_time=end))
    await session.commit()


async def set_weekly_hours(session: AsyncSession, pro: Professional, weekly: dict[int, list[tuple[time, time]]]):
    await session.execute(delete(WorkingHours).where(WorkingHours.professional_id == pro.id))
    for wd, ranges in weekly.items():
        for start, end in ranges:
            session.add(WorkingHours(professional_id=pro.id, weekday=wd, start_time=start, end_time=end))
    await session.commit()


async def get_weekly_hours(session: AsyncSession, pro_id: int) -> dict[int, list[tuple[time, time]]]:
    rows = (await session.execute(select(WorkingHours).where(WorkingHours.professional_id == pro_id)
                                  .order_by(WorkingHours.weekday, WorkingHours.start_time))).scalars()
    out: dict[int, list[tuple[time, time]]] = {d: [] for d in range(7)}
    for r in rows:
        out[r.weekday].append((r.start_time, r.end_time))
    return out


async def add_service(session: AsyncSession, pro: Professional, name: str, duration_min: int,
                      price_cents: int | None, price_type: PriceType = PriceType.FIXED,
                      location: BookingLocation | None = None, description: str | None = None) -> Service:
    if not 5 <= duration_min <= 1440:
        raise ProError("invalid_duration")
    if price_cents is not None and price_cents < 0:
        raise ProError("invalid_price")
    if location is None:
        location = BookingLocation.AT_CLIENT if pro.work_mode == WorkMode.MOBILE else BookingLocation.ON_SITE
    svc = Service(professional_id=pro.id, name=name.strip()[:160], duration_min=duration_min,
                  price_cents=price_cents, price_type=PriceType.QUOTE if price_cents is None else price_type,
                  location=location, description=description)
    session.add(svc)
    await session.commit()
    return svc


async def update_service(session: AsyncSession, pro: Professional, service_id: int, **fields) -> Service:
    svc = await session.get(Service, service_id)
    if svc is None or svc.professional_id != pro.id:
        raise ProError("unknown_service")
    for k in ("name", "duration_min", "price_cents", "price_type", "location", "description", "is_active"):
        if k in fields:
            setattr(svc, k, fields[k])
    await session.commit()
    return svc


async def delete_service(session: AsyncSession, pro: Professional, service_id: int) -> None:
    svc = await session.get(Service, service_id)
    if svc is None or svc.professional_id != pro.id:
        raise ProError("unknown_service")
    svc.is_active = False  # soft delete: bookings keep their reference
    await session.commit()


def parse_date_range(text: str, tz_name: str) -> tuple[datetime, datetime]:
    """'24/12/2026' or '24/12/2026-02/01/2027' (inclusive days) in local time."""
    parts = [p.strip() for p in re.split(r"\s*(?:-|au|→|to)\s*", text.strip()) if p.strip()]
    if not 1 <= len(parts) <= 2:
        raise ProError("invalid_format")
    days = []
    for p in parts:
        m = re.fullmatch(r"(\d{1,2})[/.](\d{1,2})(?:[/.](\d{2,4}))?", p)
        if not m:
            raise ProError("invalid_format")
        y = int(m.group(3)) if m.group(3) else datetime.now().year
        y = y + 2000 if y < 100 else y
        try:
            days.append(date(y, int(m.group(2)), int(m.group(1))))
        except ValueError as exc:
            raise ProError("invalid_date") from exc
    start_d, end_d = days[0], days[-1]
    if end_d < start_d:
        raise ProError("invalid_range")
    tz = ZoneInfo(tz_name)
    return (datetime.combine(start_d, time(0), tz).astimezone(UTC),
            datetime.combine(end_d + timedelta(days=1), time(0), tz).astimezone(UTC))


async def add_time_off(session: AsyncSession, pro: Professional, start_at: datetime, end_at: datetime,
                       reason: str | None = None) -> tuple[TimeOff, int]:
    """Adds a closure. Returns (closure, number of active bookings conflicting) so the UI can warn."""
    if end_at <= start_at:
        raise ProError("invalid_range")
    off = TimeOff(professional_id=pro.id, start_at=start_at, end_at=end_at, reason=reason)
    session.add(off)
    conflicts = await session.scalar(
        select(func.count(Booking.id)).where(
            Booking.professional_id == pro.id, Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
            Booking.start_at < end_at, Booking.end_at > start_at)
    )
    await session.commit()
    return off, conflicts or 0


async def list_time_off(session: AsyncSession, pro: Professional) -> list[TimeOff]:
    rows = await session.execute(select(TimeOff).where(TimeOff.professional_id == pro.id,
                                                       TimeOff.end_at > datetime.now(UTC)).order_by(TimeOff.start_at))
    return list(rows.scalars())


async def delete_time_off(session: AsyncSession, pro: Professional, off_id: int) -> None:
    off = await session.get(TimeOff, off_id)
    if off is None or off.professional_id != pro.id:
        raise ProError("unknown_time_off")
    await session.delete(off)
    await session.commit()


async def set_on_duty(session: AsyncSession, pro: Professional, hours: int | None) -> None:
    """'Disponible maintenant' for urgent interventions (mobile pros)."""
    if hours:
        if not pro.is_mobile:
            raise ProError("not_mobile")
        pro.accepts_urgent = True
        pro.on_duty_until = datetime.now(UTC) + timedelta(hours=hours)
    else:
        pro.on_duty_until = None
    await session.commit()


async def add_photo(session: AsyncSession, pro: Professional, file_id: str | None = None, url: str | None = None,
                    caption: str | None = None) -> ProfessionalPhoto:
    count = await session.scalar(select(func.count(ProfessionalPhoto.id))
                                 .where(ProfessionalPhoto.professional_id == pro.id))
    if count >= 20:
        raise ProError("too_many_photos")
    photo = ProfessionalPhoto(professional_id=pro.id, file_id=file_id, url=url, caption=caption, sort_order=count)
    session.add(photo)
    await session.commit()
    return photo


async def pro_stats(session: AsyncSession, pro: Professional, days: int = 30) -> dict:
    since = datetime.now(UTC) - timedelta(days=days)
    rows = (await session.execute(
        select(Booking.status, func.count(Booking.id), func.coalesce(func.sum(Booking.price_cents), 0))
        .where(Booking.professional_id == pro.id, Booking.created_at >= since).group_by(Booking.status)
    )).all()
    by_status = {s.value: {"count": c, "amount_cents": a} for s, c, a in rows}
    clients = await session.scalar(select(func.count(func.distinct(Booking.client_id)))
                                   .where(Booking.professional_id == pro.id))
    favorites = await session.scalar(select(func.count(Favorite.id)).where(Favorite.professional_id == pro.id))
    upcoming = await session.scalar(select(func.count(Booking.id)).where(
        Booking.professional_id == pro.id, Booking.start_at >= datetime.now(UTC),
        Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])))
    total = sum(v["count"] for v in by_status.values())
    cancelled = by_status.get("cancelled", {}).get("count", 0)
    revenue = by_status.get("completed", {}).get("amount_cents", 0) + by_status.get("confirmed", {}).get(
        "amount_cents", 0)
    return {
        "period_days": days,
        "bookings_total": total,
        "by_status": by_status,
        "cancellation_rate": round(cancelled / total, 3) if total else 0.0,
        "estimated_revenue_cents": revenue,
        "unique_clients": clients or 0,
        "favorites": favorites or 0,
        "upcoming": upcoming or 0,
        "rating_avg": pro.rating_avg,
        "rating_count": pro.rating_count,
        "completed_total": pro.completed_count,
    }


async def pro_clients(session: AsyncSession, pro: Professional, limit: int = 50) -> list[dict]:
    rows = (await session.execute(
        select(User, func.count(Booking.id).label("n"), func.max(Booking.start_at).label("last"))
        .join(Booking, Booking.client_id == User.id)
        .where(Booking.professional_id == pro.id)
        .group_by(User.id).order_by(func.max(Booking.start_at).desc()).limit(limit)
    )).all()
    return [{"user": u, "bookings": n, "last": last} for u, n, last in rows]


async def published_reviews(session: AsyncSession, pro_id: int, limit: int = 10) -> list[Review]:
    rows = await session.execute(
        select(Review).where(Review.professional_id == pro_id, Review.status == ReviewStatus.PUBLISHED)
        .options(selectinload(Review.client)).order_by(Review.created_at.desc()).limit(limit)
    )
    return list(rows.scalars())
