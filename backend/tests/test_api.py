"""REST API (same services as the bot)."""
import httpx
import pytest
from passlib.hash import pbkdf2_sha256

from app.api.security import sign_init_data, validate_telegram_init_data, AuthError
from app.config import settings
from app.main import app
from app.models import ProStatus, User
from tests.conftest import local_dt, make_pro, make_user


@pytest.fixture
async def client():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def tg_token(client, tg_id=777, first_name="Alice") -> str:
    init = sign_init_data({"id": tg_id, "first_name": first_name, "language_code": "fr"}, settings.telegram_bot_token)
    r = await client.post("/api/v1/auth/telegram", json={"init_data": init})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_init_data_signature():
    init = sign_init_data({"id": 1, "first_name": "A"}, "123:abc")
    assert validate_telegram_init_data(init, "123:abc")["id"] == 1
    with pytest.raises(AuthError):
        validate_telegram_init_data(init, "123:other")
    with pytest.raises(AuthError):
        validate_telegram_init_data(init.replace("A", "B"), "123:abc")


async def test_health_and_categories(client):
    assert (await client.get("/health")).json() == {"status": "ok"}
    cats = (await client.get("/api/v1/categories")).json()
    slugs = {c["slug"] for c in cats}
    assert {"sante", "batiment", "beaute", "automobile", "services"} <= slugs
    building = next(c for c in cats if c["slug"] == "batiment")
    assert any(ch["slug"] == "plombier" for ch in building["children"])


async def test_search_endpoints(client, session):
    await make_pro(session, slug="plombier", name="Plomberie Test", mode="mobile", radius=15,
                   services=[("Réparation fuite", 60, 9000)])
    r = await client.get("/api/v1/search", params={"category": "plombier", "location": "Paris", "available": "tomorrow"})
    assert r.status_code == 200 and r.json()["total"] == 1
    assert r.json()["results"][0]["next_slots"]
    r = await client.post("/api/v1/search/natural", json={"text": "Je cherche un plombier à Paris disponible demain"})
    body = r.json()
    assert body["understood"]["category_slug"] == "plombier" and body["total"] == 1 and "Plombier" in body["summary"]
    assert (await client.get("/api/v1/search", params={"category": "nope"})).status_code == 404


async def test_booking_via_api(client, session):
    pro = await make_pro(session)
    token = await tg_token(client)
    h = {"Authorization": f"Bearer {token}"}
    slots = (await client.get(f"/api/v1/professionals/{pro.id}/availability",
                              params={"service_id": pro.services[0].id, "days": 3})).json()
    assert slots
    payload = {"professional_id": pro.id, "service_id": pro.services[0].id, "start_at": slots[0]["start"]}
    r = await client.post("/api/v1/me/bookings", json=payload, headers=h)
    assert r.status_code == 201, r.text
    booking = r.json()
    assert booking["status"] == "confirmed"
    again = await client.post("/api/v1/me/bookings", json=payload, headers=h)
    assert again.status_code == 409 and again.json()["detail"]["code"] == "slot_unavailable"
    slots_after = (await client.get(f"/api/v1/professionals/{pro.id}/availability",
                                    params={"service_id": pro.services[0].id, "days": 3})).json()
    assert slots[0]["start"] not in [s["start"] for s in slots_after]
    r = await client.post(f"/api/v1/me/bookings/{booking['id']}/cancel", json={"reason": "test"}, headers=h)
    assert r.json()["status"] == "cancelled"
    assert (await client.get("/api/v1/me/bookings", headers=h)).json() == []
    assert (await client.post("/api/v1/me/bookings", json=payload)).status_code == 401


async def test_pro_api(client, session):
    token = await tg_token(client, 888, "Bob")
    h = {"Authorization": f"Bearer {token}"}
    from tests.conftest import category_id

    r = await client.post("/api/v1/pro", headers=h, json={
        "business_name": "Bob Plomberie", "category_id": await category_id(session, "plombier"), "work_mode": "mobile",
        "address": "75011", "service_radius_km": 10})
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "pending"  # needs admin validation
    r = await client.post("/api/v1/pro/services", headers=h, json={"name": "Fuite", "duration_min": 60,
                                                                   "price_cents": 8000})
    assert r.status_code == 201 and r.json()["location"] == "at_client"
    r = await client.put("/api/v1/pro/hours", headers=h, json={"weekly": {"0": ["9-12", "14-18"], "6": []}})
    assert r.status_code == 200
    me = (await client.get("/api/v1/pro/me", headers=h)).json()
    assert me["hours"]["0"] == ["09:00-12:00", "14:00-18:00"] and me["hours"]["1"] == []
    assert (await client.put("/api/v1/pro/hours", headers=h, json={"weekly": {"0": ["12-9"]}})).status_code == 422
    assert (await client.get("/api/v1/pro/stats", headers=h)).json()["bookings_total"] == 0


async def test_admin_api(client, session):
    admin = User(email="root@example.com", password_hash=pbkdf2_sha256.hash("s3cret"), is_admin=True)
    session.add(admin)
    await session.commit()
    pending = await make_pro(session, status=ProStatus.PENDING)
    assert (await client.post("/api/v1/auth/login", json={"email": "root@example.com", "password": "bad"})
            ).status_code == 401
    token = (await client.post("/api/v1/auth/login", json={"email": "root@example.com", "password": "s3cret"})
             ).json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    stats = (await client.get("/api/v1/admin/stats", headers=h)).json()
    assert stats["professionals"]["pending"] == 1
    r = await client.post(f"/api/v1/admin/professionals/{pending.id}/status", headers=h,
                          json={"status": "active", "verify": True})
    assert r.json() == {"id": pending.id, "status": "active", "is_verified": True}
    r = await client.post("/api/v1/admin/categories", headers=h, json={
        "slug": "toiletteur", "parent_id": None, "names": {"fr": "Toiletteur", "en": "Groomer"},
        "keywords": ["toilettage", "chien"], "default_work_mode": "on_site"})
    assert r.status_code == 201
    assert any(c["slug"] == "toiletteur" for c in (await client.get("/api/v1/categories")).json())
    audit = (await client.get("/api/v1/admin/audit", headers=h)).json()
    assert {"pro.status", "category.create"} <= {a["action"] for a in audit}
    # a normal user is refused
    user_token = await tg_token(client, 999)
    assert (await client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {user_token}"})
            ).status_code == 403


async def test_gdpr_export_and_delete(client, session):
    pro = await make_pro(session)
    token = await tg_token(client, 4242, "Zoé")
    h = {"Authorization": f"Bearer {token}"}
    await client.post("/api/v1/me/bookings", headers=h, json={
        "professional_id": pro.id, "service_id": pro.services[0].id, "start_at": local_dt(2, 10).isoformat()})
    export = (await client.get("/api/v1/me/export", headers=h)).json()
    assert export["user"]["first_name"] == "Zoé" and len(export["bookings"]) == 1
    assert (await client.delete("/api/v1/me", headers=h)).status_code == 204
    assert (await client.get("/api/v1/me", headers=h)).status_code == 401
    _ = make_user
