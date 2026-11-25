"""Test fixtures: a real PostgreSQL database built with the Alembic migrations."""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

TEST_DB = os.environ.get("TEST_DATABASE_URL", "postgresql+asyncpg://ub:ub@localhost:5432/universal_booking_test")
os.environ["DATABASE_URL"] = TEST_DB
os.environ["ENVIRONMENT"] = "test"
os.environ["ANTHROPIC_API_KEY"] = ""  # tests never call the LLM
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "123456:TEST-TOKEN")
os.environ["AUTO_APPROVE_PROFESSIONALS"] = "false"

import pytest  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.db import SessionLocal, engine  # noqa: E402
from app.models import (  # noqa: E402
    BookingLocation,
    Category,
    PriceType,
    Professional,
    ProStatus,
    Service,
    User,
    WorkingHours,
    WorkMode,
)
from app.services import notifier as notifier_module  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
UTC = timezone.utc
PARIS = ZoneInfo("Europe/Paris")
KEEP_TABLES = {"categories", "cities", "plans", "alembic_version"}


@pytest.fixture(scope="session", autouse=True)
async def database():
    env = {**os.environ, "DATABASE_URL": TEST_DB}
    for cmd in (["alembic", "downgrade", "base"], ["alembic", "upgrade", "head"]):
        res = subprocess.run([sys.executable, "-m", *cmd], cwd=ROOT, env=env, capture_output=True, text=True)
        assert res.returncode == 0, res.stderr
    from scripts.seed import seed_reference

    async with SessionLocal() as s:
        await seed_reference(s)
    yield
    await engine.dispose()


@pytest.fixture(autouse=True)
async def clean_db():
    async with engine.begin() as conn:
        rows = await conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
        tables = [r[0] for r in rows if r[0] not in KEEP_TABLES]
        await conn.execute(text(f"TRUNCATE {', '.join(tables)} RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture(autouse=True)
def memory_notifier():
    n = notifier_module.MemoryNotifier()
    notifier_module.set_notifier(n)
    return n


@pytest.fixture
async def session():
    async with SessionLocal() as s:
        yield s


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------
_counter = {"n": 0}


async def make_user(session, **kw) -> User:
    _counter["n"] += 1
    n = _counter["n"]
    user = User(telegram_id=kw.pop("telegram_id", 5_000_000 + n), first_name=kw.pop("first_name", f"User{n}"),
                language="fr", **kw)
    session.add(user)
    await session.commit()
    return user


async def category_id(session, slug: str) -> int:
    from sqlalchemy import select

    return (await session.execute(select(Category.id).where(Category.slug == slug))).scalar_one()


async def make_pro(session, *, slug="coiffeur", name=None, lat=48.8566, lon=2.3522, mode=WorkMode.ON_SITE,
                   radius=0, buffer=0, auto_confirm=True, hours=None, services=None, status=ProStatus.ACTIVE,
                   min_notice=0, step=15, **kw) -> Professional:
    owner = await make_user(session)
    _counter["n"] += 1
    pro = Professional(
        user_id=owner.id, business_name=name or f"Pro {_counter['n']}", slug=f"pro-{_counter['n']}",
        category_id=await category_id(session, slug), work_mode=mode, lat=lat, lon=lon, city="Paris",
        service_radius_km=radius, travel_buffer_min=buffer, status=status, auto_confirm=auto_confirm,
        min_notice_min=min_notice, slot_step_min=step, closed_on_holidays=False, timezone="Europe/Paris", **kw)
    session.add(pro)
    await session.flush()
    # default: open every day 08:00-20:00
    for wd, ranges in (hours or {d: [(time(8), time(20))] for d in range(7)}).items():
        for a, b in ranges:
            session.add(WorkingHours(professional_id=pro.id, weekday=wd, start_time=a, end_time=b))
    loc = BookingLocation.AT_CLIENT if mode == WorkMode.MOBILE else BookingLocation.ON_SITE
    for sname, dur, price in (services or [("Coupe homme", 30, 2500)]):
        session.add(Service(professional_id=pro.id, name=sname, duration_min=dur, price_cents=price,
                            price_type=PriceType.FIXED if price is not None else PriceType.QUOTE, location=loc))
    await session.commit()
    from app.services.professionals import get_public_pro

    return await get_public_pro(session, pro.id)


def local_dt(days_ahead: int, hour: int, minute: int = 0) -> datetime:
    """Aware datetime in Paris `days_ahead` days from today at hour:minute (UTC-normalised)."""
    d = datetime.now(PARIS).date() + timedelta(days=days_ahead)
    return datetime.combine(d, time(hour, minute), PARIS).astimezone(UTC)
