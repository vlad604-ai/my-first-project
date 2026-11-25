"""Search engine: filters, geography, real availability, ranking."""
from datetime import datetime, timedelta, timezone

from app.models import WorkMode
from app.services import booking as bs
from app.services import search as s
from tests.conftest import category_id, local_dt, make_pro, make_user

UTC = timezone.utc
PARIS = (48.8566, 2.3522)
BOULOGNE = (48.8352, 2.2410)
LYON = (45.7640, 4.8357)


async def test_category_and_radius(session):
    near = await make_pro(session, name="Salon Paris", lat=48.86, lon=2.35)
    await make_pro(session, name="Salon Lyon", lat=LYON[0], lon=LYON[1])
    await make_pro(session, slug="dentiste", name="Dentiste Paris", lat=48.86, lon=2.35)
    q = s.SearchQuery(category_ids=[await category_id(session, "coiffeur")], lat=PARIS[0], lon=PARIS[1], radius_km=10)
    resp = await s.search(session, q)
    assert [r.professional.id for r in resp.results] == [near.id]
    assert resp.results[0].distance_km < 2


async def test_parent_category_includes_children(session):
    await make_pro(session, slug="coiffeur")
    await make_pro(session, slug="barbier")
    resp = await s.search(session, s.SearchQuery(category_ids=[await category_id(session, "beaute")]))
    assert resp.total == 2


async def test_mobile_pro_zone(session):
    plumber = await make_pro(session, slug="plombier", mode=WorkMode.MOBILE, radius=15, lat=BOULOGNE[0],
                             lon=BOULOGNE[1], services=[("Fuite", 60, 9000)])
    await make_pro(session, slug="plombier", mode=WorkMode.MOBILE, radius=3, lat=48.90, lon=2.45,
                   services=[("Fuite", 60, 9000)])
    q = s.SearchQuery(category_ids=[await category_id(session, "plombier")], lat=PARIS[0], lon=PARIS[1],
                      radius_km=1, at_client=True)
    resp = await s.search(session, q)
    # radius of the user is 1 km but the Boulogne plumber travels 15 km: proximity != reach
    assert [r.professional.id for r in resp.results] == [plumber.id]
    assert resp.results[0].travel_minutes is not None


async def test_availability_filter_uses_real_bookings(session):
    busy = await make_pro(session, name="Busy", hours={d: [(datetime.min.time().replace(hour=10),
                                                           datetime.min.time().replace(hour=11))] for d in range(7)},
                          services=[("Coupe", 60, 2000)])
    free = await make_pro(session, name="Free", services=[("Coupe", 60, 2000)])
    client = await make_user(session)
    await bs.create_booking(session, client, busy.id, busy.services[0].id, local_dt(2, 10))
    start, end = local_dt(2, 0), local_dt(3, 0)
    q = s.SearchQuery(category_ids=[await category_id(session, "coiffeur")], window_start=start, window_end=end)
    resp = await s.search(session, q)
    ids = [r.professional.id for r in resp.results]
    assert free.id in ids and busy.id not in ids
    assert all(r.next_slot and start <= r.next_slot.start < end for r in resp.results)


async def test_price_and_text(session):
    cheap = await make_pro(session, services=[("Coupe homme", 30, 2200), ("Couleur", 90, 8000)])
    await make_pro(session, services=[("Coupe homme", 30, 4500)])
    q = s.SearchQuery(category_ids=[await category_id(session, "coiffeur")], max_price_cents=3000, text="coupe homme")
    resp = await s.search(session, q)
    assert [r.professional.id for r in resp.results] == [cheap.id]
    assert resp.results[0].reference_service.name == "Coupe homme"


async def test_free_text_without_category(session):
    pro = await make_pro(session, slug="garage", name="Garage du Centre", services=[("Vidange", 60, 7900)])
    resp = await s.search(session, s.SearchQuery(text="vidange"))
    assert [r.professional.id for r in resp.results] == [pro.id]


async def test_urgent_on_duty(session):
    on_duty = await make_pro(session, slug="serrurier", mode=WorkMode.MOBILE, radius=10, accepts_urgent=True,
                             on_duty_until=datetime.now(UTC) + timedelta(hours=3), services=[("Ouverture", 30, 9000)])
    await make_pro(session, slug="serrurier", mode=WorkMode.MOBILE, radius=10, accepts_urgent=False,
                   services=[("Ouverture", 30, 9000)])
    q = s.SearchQuery(category_ids=[await category_id(session, "serrurier")], lat=PARIS[0], lon=PARIS[1], urgent=True)
    q.window_start, q.window_end = s.availability_window("now")
    resp = await s.search(session, q)
    assert [r.professional.id for r in resp.results] == [on_duty.id]
    assert resp.results[0].on_duty


async def test_sort_by_distance_and_pagination(session):
    ids = []
    for i in range(4):
        p = await make_pro(session, lat=PARIS[0] + i * 0.01, lon=PARIS[1])
        ids.append(p.id)
    q = s.SearchQuery(category_ids=[await category_id(session, "coiffeur")], lat=PARIS[0], lon=PARIS[1], radius_km=20,
                      sort="distance", limit=2)
    first = await s.search(session, q)
    q.offset = 2
    second = await s.search(session, q)
    assert first.total == 4
    assert [r.professional.id for r in first.results + second.results] == ids
