from datetime import datetime, timedelta, timezone

import pytest

from app.models import BookingStatus, ReviewStatus, Urgency, WorkMode
from app.services import booking as bs
from app.services import quotes as qs
from app.services import reviews as rs
from tests.conftest import category_id, local_dt, make_pro, make_user

UTC = timezone.utc


async def test_quote_request_dispatch_and_accept(session, memory_notifier):
    reno1 = await make_pro(session, slug="renovation", mode=WorkMode.MOBILE, radius=20, accepts_quotes=True,
                           lat=48.835, lon=2.241)
    reno2 = await make_pro(session, slug="renovation", mode=WorkMode.MOBILE, radius=20, accepts_quotes=True,
                           lat=48.84, lon=2.25, quote_keywords=["cuisine"])  # only wants kitchens
    far = await make_pro(session, slug="renovation", mode=WorkMode.MOBILE, radius=20, accepts_quotes=True,
                         lat=45.76, lon=4.83)
    client = await make_user(session)
    req, n = await qs.create_request(session, client, await category_id(session, "renovation"),
                                     "Je souhaite refaire ma salle de bain de 8 m2", city="Boulogne-Billancourt",
                                     lat=48.8352, lon=2.2410, budget_cents=800000, urgency=Urgency.THIS_MONTH)
    assert n == 1
    assert any(m.chat_id == reno1.user.telegram_id for m in memory_notifier.sent)
    assert not any(m.chat_id in (reno2.user.telegram_id, far.user.telegram_id) for m in memory_notifier.sent)

    with pytest.raises(qs.QuoteError):  # not a recipient
        await qs.submit_quote(session, far, req.id, 500000)
    quote = await qs.submit_quote(session, reno1, req.id, 750000, "Devis détaillé", 10)
    with pytest.raises(qs.QuoteError):
        await qs.submit_quote(session, reno1, req.id, 700000)
    accepted = await qs.accept_quote(session, client, quote.id)
    assert accepted.status.value == "accepted"
    req = await qs.get_request(session, req.id)
    assert req.status.value == "awarded"


async def test_quote_targeted_pro(session):
    pro = await make_pro(session, slug="renovation", accepts_quotes=True, lat=45.76, lon=4.83)
    client = await make_user(session)
    _, n = await qs.create_request(session, client, await category_id(session, "renovation"),
                                   "Rénovation complète d'un appartement", lat=48.85, lon=2.35, target_pro_id=pro.id)
    assert n == 1


async def _completed_booking(session):
    pro = await make_pro(session)
    client = await make_user(session)
    b = await bs.create_booking(session, client, pro.id, pro.services[0].id, local_dt(2, 10))
    b.status = BookingStatus.COMPLETED  # simulate time passing (state only, the booking row is real)
    await session.commit()
    return pro, client, b


async def test_review_only_after_completion(session):
    pro = await make_pro(session)
    client = await make_user(session)
    b = await bs.create_booking(session, client, pro.id, pro.services[0].id, local_dt(2, 10))
    with pytest.raises(rs.ReviewError):
        await rs.create_review(session, client, b.id, 5, "Top")


async def test_review_rating_and_moderation(session):
    pro, client, b = await _completed_booking(session)
    stranger = await make_user(session)
    with pytest.raises(rs.ReviewError):
        await rs.create_review(session, stranger, b.id, 1, "Fake")
    review = await rs.create_review(session, client, b.id, 4, "Très bien")
    assert review.status == ReviewStatus.PUBLISHED
    await session.refresh(pro)
    assert pro.rating_avg == 4 and pro.rating_count == 1
    with pytest.raises(rs.ReviewError):
        await rs.create_review(session, client, b.id, 5)
    review = await rs.update_comment(session, client, review.id, "Appelez-moi au 06 12 34 56 78")
    assert review.status == ReviewStatus.PENDING
    await session.refresh(pro)
    assert pro.rating_count == 0  # hidden until moderated


@pytest.mark.parametrize("comment,flag", [
    ("Super prestation", None), ("Allez sur www.concurrent.fr", "contains_link"),
    ("C'est un escroc", "offensive_or_accusatory_language"), ("ARNAQUE TOTALE NE PAS Y ALLER", "offensive_or_accusatory_language"),
    ("contact@test.com", "contains_contact_details"), ("TRES TRES MAUVAIS SERVICE VRAIMENT", "spam_pattern"),
])
def test_moderation_rules(comment, flag):
    assert rs.moderate(comment) == flag


async def test_jobs_reminders_expiry_autocomplete(session, memory_notifier):
    from worker import jobs

    pro = await make_pro(session, auto_confirm=True)
    pending_pro = await make_pro(session, auto_confirm=False)
    client = await make_user(session)
    soon = await bs.create_booking(session, client, pro.id, pro.services[0].id, local_dt(1, 10))
    # Reminder 1h: pretend we are 50 minutes before the appointment
    sent = await jobs.send_reminders(session, now=soon.start_at - timedelta(minutes=50))
    assert sent >= 1
    assert any("1 heure" in m.text for m in memory_notifier.sent)
    assert await jobs.send_reminders(session, now=soon.start_at - timedelta(minutes=50)) == 0  # idempotent

    p = await bs.create_booking(session, client, pending_pro.id, pending_pro.services[0].id, local_dt(3, 10))
    assert await jobs.expire_pending(session, now=datetime.now(UTC) + timedelta(hours=30)) == 1
    await session.refresh(p)
    assert p.status == BookingStatus.REFUSED

    done = await jobs.auto_complete(session, now=soon.end_at + timedelta(hours=3))
    assert done == 1
    await session.refresh(soon)
    assert soon.status == BookingStatus.COMPLETED
    assert any("Notez" in m.text for m in memory_notifier.sent)
