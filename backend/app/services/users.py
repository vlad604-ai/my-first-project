from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Favorite, Message, Professional, User
from app.services.audit import audit

UTC = timezone.utc


async def get_or_create_telegram_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    language_code: str | None = None,
) -> User:
    user = (await session.execute(select(User).where(User.telegram_id == telegram_id))).scalar_one_or_none()
    lang = (language_code or "fr")[:2]
    if lang not in settings.supported_languages:
        lang = settings.default_language
    if user is None:
        user = User(telegram_id=telegram_id, username=username, first_name=first_name, last_name=last_name,
                    language=lang, is_admin=telegram_id in settings.admin_telegram_ids)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    changed = False
    for attr, value in (("username", username), ("first_name", first_name), ("last_name", last_name)):
        if value and getattr(user, attr) != value:
            setattr(user, attr, value)
            changed = True
    if telegram_id in settings.admin_telegram_ids and not user.is_admin:
        user.is_admin = True
        changed = True
    if changed:
        await session.commit()
    return user


async def set_location(session: AsyncSession, user: User, lat: float, lon: float, label: str | None) -> None:
    user.last_lat, user.last_lon, user.last_city = lat, lon, label
    await session.commit()


async def toggle_favorite(session: AsyncSession, user: User, pro_id: int) -> bool:
    """Returns True if now favourite."""
    fav = (await session.execute(select(Favorite).where(Favorite.user_id == user.id,
                                                        Favorite.professional_id == pro_id))).scalar_one_or_none()
    if fav:
        await session.delete(fav)
        await session.commit()
        return False
    session.add(Favorite(user_id=user.id, professional_id=pro_id))
    await session.commit()
    return True


async def list_favorites(session: AsyncSession, user: User) -> list[Professional]:
    rows = await session.execute(
        select(Professional).join(Favorite, Favorite.professional_id == Professional.id)
        .where(Favorite.user_id == user.id).order_by(Favorite.created_at.desc())
    )
    return list(rows.scalars())


async def is_favorite(session: AsyncSession, user: User, pro_id: int) -> bool:
    return (await session.execute(select(Favorite.id).where(Favorite.user_id == user.id,
                                                            Favorite.professional_id == pro_id))).first() is not None


async def gdpr_export(session: AsyncSession, user: User) -> dict:
    """Personal data export (RGPD art. 15/20)."""
    from app.models import Booking, Review

    bookings = (await session.execute(select(Booking).where(Booking.client_id == user.id))).scalars().all()
    reviews = (await session.execute(select(Review).where(Review.client_id == user.id))).scalars().all()
    msgs = (await session.execute(select(Message).where(Message.sender_user_id == user.id))).scalars().all()
    return {
        "user": {"id": user.id, "telegram_id": user.telegram_id, "username": user.username,
                 "first_name": user.first_name, "last_name": user.last_name, "phone": user.phone,
                 "language": user.language, "created_at": user.created_at.isoformat()},
        "bookings": [{"reference": b.reference, "service": b.service_name, "start_at": b.start_at.isoformat(),
                      "status": b.status.value} for b in bookings],
        "reviews": [{"rating": r.rating, "comment": r.comment, "created_at": r.created_at.isoformat()}
                    for r in reviews],
        "messages": [{"body": m.body, "created_at": m.created_at.isoformat()} for m in msgs],
    }


async def gdpr_delete(session: AsyncSession, user: User) -> None:
    """Right to erasure: anonymise the account, keep bookings for pros' accounting."""
    user.username = user.first_name = user.last_name = user.phone = user.email = None
    user.last_lat = user.last_lon = None
    user.last_city = None
    user.telegram_id = None
    user.deleted_at = datetime.now(UTC)
    await session.execute(update(Message).where(Message.sender_user_id == user.id).values(body="[supprimé]"))
    audit(session, "user.gdpr_delete", "user", user.id, user.id)
    await session.commit()
