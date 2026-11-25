"""Administration: moderation, verification, platform statistics, monetisation config."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Booking,
    BookingStatus,
    Category,
    PlatformSetting,
    Professional,
    ProStatus,
    QuoteRequest,
    Report,
    ReportStatus,
    Review,
    ReviewStatus,
    User,
)
from app.services import notifications
from app.services.audit import audit

UTC = timezone.utc


class AdminError(Exception):
    pass


async def set_pro_status(session: AsyncSession, admin: User, pro_id: int, status: ProStatus,
                         verify: bool | None = None) -> Professional:
    pro = (await session.execute(select(Professional).where(Professional.id == pro_id)
                                 .options(selectinload(Professional.user)))).scalar_one_or_none()
    if pro is None:
        raise AdminError("unknown_professional")
    previous = pro.status
    pro.status = status
    if verify is not None:
        pro.is_verified = verify
        pro.verified_at = datetime.now(UTC) if verify else None
    audit(session, "pro.status", "professional", pro.id, admin.id, status=status.value, verify=verify)
    await session.commit()
    if previous != status:
        await notifications.pro_status_changed(pro, status.value)
    return pro


async def set_user_banned(session: AsyncSession, admin: User, user_id: int, banned: bool) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise AdminError("unknown_user")
    if user.is_admin and banned:
        raise AdminError("cannot_ban_admin")
    user.is_banned = banned
    audit(session, "user.ban" if banned else "user.unban", "user", user.id, admin.id)
    await session.commit()
    return user


async def resolve_report(session: AsyncSession, admin: User, report_id: int, status: ReportStatus,
                         note: str | None = None) -> Report:
    rep = await session.get(Report, report_id)
    if rep is None:
        raise AdminError("unknown_report")
    rep.status, rep.admin_note = status, note
    audit(session, "report.resolve", "report", rep.id, admin.id, status=status.value)
    await session.commit()
    return rep


async def platform_stats(session: AsyncSession, days: int = 30) -> dict:
    since = datetime.now(UTC) - timedelta(days=days)
    users = await session.scalar(select(func.count(User.id)).where(User.deleted_at.is_(None)))
    new_users = await session.scalar(select(func.count(User.id)).where(User.created_at >= since))
    pros = dict((s.value, c) for s, c in (await session.execute(
        select(Professional.status, func.count(Professional.id)).group_by(Professional.status))).all())
    bookings = dict((s.value, c) for s, c in (await session.execute(
        select(Booking.status, func.count(Booking.id)).where(Booking.created_at >= since)
        .group_by(Booking.status))).all())
    gmv = await session.scalar(select(func.coalesce(func.sum(Booking.price_cents), 0)).where(
        Booking.created_at >= since, Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED])))
    daily = (await session.execute(
        select(func.date_trunc("day", Booking.created_at).label("d"), func.count(Booking.id))
        .where(Booking.created_at >= since).group_by("d").order_by("d"))).all()
    top_categories = (await session.execute(
        select(Category.slug, Category.names, func.count(Booking.id).label("n"))
        .join(Professional, Professional.category_id == Category.id)
        .join(Booking, Booking.professional_id == Professional.id)
        .where(Booking.created_at >= since).group_by(Category.id).order_by(func.count(Booking.id).desc()).limit(8)
    )).all()
    return {
        "period_days": days,
        "users_total": users or 0,
        "users_new": new_users or 0,
        "professionals": pros,
        "bookings": bookings,
        "bookings_total": sum(bookings.values()),
        "gmv_cents": gmv or 0,
        "reviews_pending": await session.scalar(select(func.count(Review.id))
                                                .where(Review.status == ReviewStatus.PENDING)) or 0,
        "reports_open": await session.scalar(select(func.count(Report.id))
                                             .where(Report.status == ReportStatus.OPEN)) or 0,
        "quote_requests": await session.scalar(select(func.count(QuoteRequest.id))
                                               .where(QuoteRequest.created_at >= since)) or 0,
        "daily_bookings": _fill_days(since, {d.date(): c for d, c in daily}),
        "top_categories": [{"slug": s, "name": n.get("fr", s), "bookings": c} for s, n, c in top_categories],
    }


def _fill_days(since: datetime, counts: dict) -> list[dict]:
    """Continuous daily series (zero for days without bookings)."""
    out, day, today = [], since.date(), datetime.now(UTC).date()
    while day <= today:
        out.append({"day": day.isoformat(), "count": counts.get(day, 0)})
        day += timedelta(days=1)
    return out


async def get_setting(session: AsyncSession, key: str, default: dict | None = None) -> dict:
    row = await session.get(PlatformSetting, key)
    return row.value if row else (default or {})


async def put_setting(session: AsyncSession, admin: User, key: str, value: dict) -> dict:
    row = await session.get(PlatformSetting, key)
    if row is None:
        row = PlatformSetting(key=key, value=value)
        session.add(row)
    else:
        row.value = value
    audit(session, "setting.update", "setting", key, admin.id, value=value)
    await session.commit()
    return value
