"""Reviews: only clients with a *completed* booking can review (one per booking).

Automatic moderation flags suspicious content (links, contact details, insults,
spam patterns) for manual review instead of publishing it.
"""
from __future__ import annotations

import re

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Booking, BookingStatus, Professional, Review, ReviewStatus, User
from app.services.audit import audit
from app.services.text import normalize

BANNED = {"connard", "salope", "encule", "merde", "pute", "batard", "nique", "arnaque", "escroc", "fuck", "shit"}
LINK_RE = re.compile(r"(https?://|www\.|\.com\b|\.fr\b|t\.me/)", re.I)
PHONE_RE = re.compile(r"(\+33|0)\s*[1-9](?:[\s.-]*\d{2}){4}")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


class ReviewError(Exception):
    pass


def moderate(comment: str | None) -> str | None:
    """Return a reason if the review needs manual moderation, else None."""
    if not comment:
        return None
    norm = normalize(comment)
    words = set(re.findall(r"[a-z]+", norm))
    if words & BANNED:
        return "offensive_or_accusatory_language"
    if PHONE_RE.search(comment) or EMAIL_RE.search(comment):
        return "contains_contact_details"
    if LINK_RE.search(comment):
        return "contains_link"
    if re.search(r"(.)\1{6,}", comment) or (len(comment) > 20 and comment.isupper()):
        return "spam_pattern"
    return None


async def create_review(session: AsyncSession, client: User, booking_id, rating: int, comment: str | None = None,
                        photos: list[str] | None = None) -> Review:
    booking = await session.get(Booking, booking_id)
    if booking is None or booking.client_id != client.id:
        raise ReviewError("not_your_booking")
    if booking.status != BookingStatus.COMPLETED:
        raise ReviewError("booking_not_completed")
    if not 1 <= int(rating) <= 5:
        raise ReviewError("invalid_rating")
    existing = (await session.execute(select(Review).where(Review.booking_id == booking.id))).scalar_one_or_none()
    if existing:
        raise ReviewError("already_reviewed")
    reason = moderate(comment)
    review = Review(booking_id=booking.id, client_id=client.id, professional_id=booking.professional_id,
                    rating=int(rating), comment=(comment or None) and comment[:2000], photos=photos or [],
                    status=ReviewStatus.PENDING if reason else ReviewStatus.PUBLISHED, moderation_reason=reason)
    session.add(review)
    await session.flush()
    await recompute_rating(session, booking.professional_id)
    await session.commit()
    return review


async def update_comment(session: AsyncSession, client: User, review_id: int, comment: str) -> Review:
    review = await session.get(Review, review_id)
    if review is None or review.client_id != client.id:
        raise ReviewError("not_your_review")
    review.comment = comment[:2000]
    reason = moderate(comment)
    if reason:
        review.status, review.moderation_reason = ReviewStatus.PENDING, reason
    await session.flush()
    await recompute_rating(session, review.professional_id)
    await session.commit()
    return review


async def recompute_rating(session: AsyncSession, pro_id: int) -> None:
    avg, count = (await session.execute(
        select(func.avg(Review.rating), func.count(Review.id))
        .where(Review.professional_id == pro_id, Review.status == ReviewStatus.PUBLISHED)
    )).one()
    pro = await session.get(Professional, pro_id)
    pro.rating_avg = round(float(avg or 0), 2)
    pro.rating_count = count or 0


async def moderate_review(session: AsyncSession, admin: User, review_id: int, approve: bool,
                          reason: str | None = None) -> Review:
    review = await session.get(Review, review_id)
    if review is None:
        raise ReviewError("unknown_review")
    review.status = ReviewStatus.PUBLISHED if approve else ReviewStatus.REJECTED
    review.moderation_reason = reason or review.moderation_reason
    await session.flush()
    await recompute_rating(session, review.professional_id)
    audit(session, "review.moderate", "review", review.id, admin.id, approve=approve)
    await session.commit()
    return review


async def reply(session: AsyncSession, pro: Professional, review_id: int, text: str) -> Review:
    review = await session.get(Review, review_id)
    if review is None or review.professional_id != pro.id:
        raise ReviewError("unknown_review")
    review.pro_reply = text[:1000]
    await session.commit()
    return review
