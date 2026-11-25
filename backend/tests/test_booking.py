"""Booking engine against the real database (no simulation)."""
import asyncio
import uuid
from datetime import timedelta

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.db import SessionLocal
from app.models import Booking, BookingStatus, WorkMode
from app.services import booking as bs
from tests.conftest import local_dt, make_pro, make_user


async def test_auto_confirmed_booking(session, memory_notifier):
    pro = await make_pro(session)
    client = await make_user(session)
    b = await bs.create_booking(session, client, pro.id, pro.services[0].id, local_dt(2, 10))
    assert b.status == BookingStatus.CONFIRMED
    assert b.reference.startswith("UB-")
    assert b.end_at - b.start_at == timedelta(minutes=30)
    # client + pro notified
    chats = {m.chat_id for m in memory_notifier.sent}
    assert client.telegram_id in chats and pro.user.telegram_id in chats


async def test_manual_validation_flow(session, memory_notifier):
    pro = await make_pro(session, auto_confirm=False)
    client = await make_user(session)
    b = await bs.create_booking(session, client, pro.id, pro.services[0].id, local_dt(2, 10))
    assert b.status == BookingStatus.PENDING
    pro_msg = [m for m in memory_notifier.sent if m.chat_id == pro.user.telegram_id][-1]
    assert any(btn.callback == f"pbk:confirm:{b.id}" for row in pro_msg.buttons for btn in row)
    b = await bs.confirm_booking(session, b, pro.user)
    assert b.status == BookingStatus.CONFIRMED


async def test_refuse_frees_slot(session):
    pro = await make_pro(session, auto_confirm=False)
    c1, c2 = await make_user(session), await make_user(session)
    start = local_dt(2, 10)
    b = await bs.create_booking(session, c1, pro.id, pro.services[0].id, start)
    await bs.refuse_booking(session, b, pro.user, "Indisponible")
    b2 = await bs.create_booking(session, c2, pro.id, pro.services[0].id, start)
    assert b2.status == BookingStatus.PENDING


async def test_double_booking_rejected(session):
    pro = await make_pro(session)
    c1, c2 = await make_user(session), await make_user(session)
    start = local_dt(3, 11)
    await bs.create_booking(session, c1, pro.id, pro.services[0].id, start)
    with pytest.raises(bs.SlotUnavailable):
        await bs.create_booking(session, c2, pro.id, pro.services[0].id, start)
    with pytest.raises(bs.SlotUnavailable):  # partial overlap
        await bs.create_booking(session, c2, pro.id, pro.services[0].id, start + timedelta(minutes=15))


async def test_concurrent_bookings_only_one_wins():
    async with SessionLocal() as s:
        pro = await make_pro(s)
        clients = [await make_user(s) for _ in range(8)]
        service_id = pro.services[0].id
    start = local_dt(4, 15)

    async def attempt(client):
        async with SessionLocal() as s:
            c = await s.get(type(client), client.id)
            try:
                await bs.create_booking(s, c, pro.id, service_id, start)
                return True
            except bs.SlotUnavailable:
                return False

    results = await asyncio.gather(*(attempt(c) for c in clients))
    assert results.count(True) == 1
    async with SessionLocal() as s:
        n = len((await s.execute(select(Booking).where(Booking.professional_id == pro.id))).scalars().all())
    assert n == 1


async def test_exclusion_constraint_is_last_line_of_defence(session):
    """Even a raw insert bypassing the service cannot create an overlap."""
    pro = await make_pro(session)
    client = await make_user(session)
    start = local_dt(5, 10)
    await bs.create_booking(session, client, pro.id, pro.services[0].id, start)
    with pytest.raises(IntegrityError):
        await session.execute(text(
            "INSERT INTO bookings (id, reference, client_id, professional_id, start_at, end_at, block_end_at, status,"
            " location, is_urgent, source, created_at, updated_at) VALUES (:id, 'UB-RAW', :c, :p, :s, :e, :e,"
            " 'confirmed', 'on_site', false, 'test', now(), now())"),
            {"id": uuid.uuid4(), "c": client.id, "p": pro.id, "s": start + timedelta(minutes=10),
             "e": start + timedelta(minutes=40)})
    await session.rollback()


async def test_travel_buffer_between_interventions(session):
    pro = await make_pro(session, slug="plombier", mode=WorkMode.MOBILE, radius=20, buffer=30,
                         services=[("Fuite", 60, 9000)])
    c1, c2 = await make_user(session), await make_user(session)
    start = local_dt(2, 9)
    await bs.create_booking(session, c1, pro.id, pro.services[0].id, start, address="1 rue A, Paris",
                            lat=48.86, lon=2.35)
    with pytest.raises(bs.SlotUnavailable):  # 10:00 is inside the 30 min travel buffer
        await bs.create_booking(session, c2, pro.id, pro.services[0].id, start + timedelta(minutes=60),
                                address="2 rue B, Paris", lat=48.86, lon=2.35)
    b = await bs.create_booking(session, c2, pro.id, pro.services[0].id, start + timedelta(minutes=90),
                                address="2 rue B, Paris", lat=48.86, lon=2.35)
    assert b.block_end_at - b.end_at == timedelta(minutes=30)


async def test_outside_opening_hours_rejected(session):
    pro = await make_pro(session)
    client = await make_user(session)
    with pytest.raises(bs.SlotUnavailable):
        await bs.create_booking(session, client, pro.id, pro.services[0].id, local_dt(2, 22))


async def test_mobile_out_of_zone(session):
    pro = await make_pro(session, slug="plombier", mode=WorkMode.MOBILE, radius=5)
    client = await make_user(session)
    with pytest.raises(bs.BookingError) as exc:
        await bs.create_booking(session, client, pro.id, pro.services[0].id, local_dt(2, 10),
                                address="Marseille", lat=43.2965, lon=5.3698)
    assert exc.value.code == "out_of_zone"


async def test_self_booking_forbidden(session):
    pro = await make_pro(session)
    with pytest.raises(bs.NotAllowed):
        await bs.create_booking(session, pro.user, pro.id, pro.services[0].id, local_dt(2, 10))


async def test_inactive_pro_cannot_be_booked(session):
    from app.models import ProStatus

    pro = await make_pro(session, status=ProStatus.PENDING)
    client = await make_user(session)
    with pytest.raises(bs.NotAllowed):
        await bs.create_booking(session, client, pro.id, pro.services[0].id, local_dt(2, 10))


async def test_cancel_and_rebook(session, memory_notifier):
    pro = await make_pro(session)
    c1, c2 = await make_user(session), await make_user(session)
    start = local_dt(2, 14)
    b = await bs.create_booking(session, c1, pro.id, pro.services[0].id, start)
    with pytest.raises(bs.NotAllowed):
        await bs.cancel_booking(session, b, c2)  # a stranger cannot cancel
    await bs.cancel_booking(session, b, c1, "Empêchement")
    assert b.status == BookingStatus.CANCELLED
    assert any(m.chat_id == pro.user.telegram_id and "annulé" in m.text.lower() for m in memory_notifier.sent)
    b2 = await bs.create_booking(session, c2, pro.id, pro.services[0].id, start)
    assert b2.status == BookingStatus.CONFIRMED


async def test_reschedule(session):
    pro = await make_pro(session)
    c1, c2 = await make_user(session), await make_user(session)
    b1 = await bs.create_booking(session, c1, pro.id, pro.services[0].id, local_dt(2, 10))
    await bs.create_booking(session, c2, pro.id, pro.services[0].id, local_dt(2, 11))
    with pytest.raises(bs.SlotUnavailable):
        await bs.reschedule_booking(session, b1, c1, local_dt(2, 11))
    # moving by 15 minutes overlaps itself: allowed because its own booking is excluded
    b1 = await bs.reschedule_booking(session, b1, c1, local_dt(2, 10, 15))
    assert b1.start_at == local_dt(2, 10, 15)
    assert len(b1.events) >= 2


async def test_complete_requires_started(session):
    pro = await make_pro(session)
    client = await make_user(session)
    b = await bs.create_booking(session, client, pro.id, pro.services[0].id, local_dt(2, 10))
    with pytest.raises(bs.InvalidState):
        await bs.complete_booking(session, b, pro.user)
