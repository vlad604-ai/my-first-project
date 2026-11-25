"""End-to-end bot tests: real updates go through the aiogram dispatcher, handlers,
services and database. Only the Telegram HTTP layer is replaced by a recorder."""
from __future__ import annotations

import itertools
from datetime import datetime, timezone

import pytest
from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.methods import TelegramMethod
from aiogram.types import CallbackQuery, Chat, Message, Update
from aiogram.types import User as TgUser
from sqlalchemy import select

from app.models import Booking, BookingStatus, Professional, User
from bot.main import build_dispatcher
from tests.conftest import make_pro

UTC = timezone.utc
_ids = itertools.count(1)
_DP = None


def dispatcher():
    """Routers are module singletons: build the dispatcher once per test session."""
    global _DP
    if _DP is None:
        _DP = build_dispatcher()
    return _DP


class RecordingSession(BaseSession):
    def __init__(self):
        super().__init__()
        self.calls: list[TelegramMethod] = []

    async def make_request(self, bot, method, timeout=None):
        self.calls.append(method)
        returning = getattr(method, "__returning__", None)
        chat_id = getattr(method, "chat_id", None) or 1
        if returning is Message or "Message" in str(returning):
            return Message(message_id=next(_ids), date=datetime.now(UTC), chat=Chat(id=chat_id, type="private"),
                           text=getattr(method, "text", None) or getattr(method, "caption", None))
        if "list" in str(returning).lower():
            return []
        return True

    async def stream_content(self, *a, **kw):  # pragma: no cover
        yield b""

    async def close(self):
        pass

    def texts(self) -> list[str]:
        return [getattr(c, "text", None) or getattr(c, "caption", None) or "" for c in self.calls]

    def buttons(self) -> list[tuple[str, str]]:
        out = []
        for c in self.calls:
            markup = getattr(c, "reply_markup", None)
            for row in getattr(markup, "inline_keyboard", None) or []:
                for b in row:
                    out.append((b.text, b.callback_data))
        return out

    def reset(self):
        self.calls.clear()


class BotHarness:
    def __init__(self, tg_id: int = 424242, first_name: str = "Julie"):
        self.session = RecordingSession()
        self.bot = Bot("123456:TEST-TOKEN", session=self.session)
        self.dp = dispatcher()
        self.user = TgUser(id=tg_id, is_bot=False, first_name=first_name, language_code="fr")
        self.chat = Chat(id=tg_id, type="private")

    async def send(self, text: str | None = None, **extra) -> None:
        msg = Message(message_id=next(_ids), date=datetime.now(UTC), chat=self.chat, from_user=self.user, text=text,
                      **extra)
        await self.dp.feed_update(self.bot, Update(update_id=next(_ids), message=msg))

    async def click(self, data: str) -> None:
        msg = Message(message_id=next(_ids), date=datetime.now(UTC), chat=self.chat,
                      from_user=TgUser(id=1, is_bot=True, first_name="bot"), text="…")
        cb = CallbackQuery(id=str(next(_ids)), from_user=self.user, chat_instance="x", message=msg, data=data)
        await self.dp.feed_update(self.bot, Update(update_id=next(_ids), callback_query=cb))

    def find_button(self, prefix: str) -> str:
        for _, data in reversed(self.session.buttons()):
            if data and data.startswith(prefix):
                return data
        raise AssertionError(f"No button starting with {prefix}: {self.session.buttons()}")


@pytest.fixture
def harness():
    return BotHarness()


async def test_start_privacy_and_menu(harness, session):
    await harness.send("/start")
    assert any("Bienvenue" in t for t in harness.session.texts())
    await harness.click("gdpr:accept")
    assert any("Menu principal" in t for t in harness.session.texts())
    user = (await session.execute(select(User).where(User.telegram_id == harness.user.id))).scalar_one()
    assert user.gdpr_consent_at is not None


async def test_natural_language_search_to_confirmed_booking(harness, session):
    pro = await make_pro(session, slug="coiffeur", name="Studio Coupe Homme",
                         services=[("Coupe homme", 30, 2500), ("Couleur", 90, 7000)])
    await harness.send("/start")
    await harness.click("gdpr:accept")
    harness.session.reset()

    await harness.send("Je cherche un coiffeur pour une coupe homme à moins de 30 euros")
    texts = "\n".join(harness.session.texts())
    assert "J'ai compris" in texts and "Studio Coupe Homme" in texts and "Coupe homme" in texts

    await harness.click(f"pro:book:{pro.id}")  # -> choose service
    await harness.click(harness.find_button("bs:"))  # -> calendar
    await harness.click(harness.find_button("bd:"))  # -> slots of the day
    await harness.click(harness.find_button("bt:"))  # -> confirmation screen
    assert any("Récapitulatif" in t for t in harness.session.texts())
    await harness.click("bc")
    assert any("Réservation enregistrée" in t for t in harness.session.texts())

    booking = (await session.execute(select(Booking).where(Booking.professional_id == pro.id))).scalar_one()
    assert booking.status == BookingStatus.CONFIRMED
    # the professional received a notification through the notifier
    from app.services.notifier import get_notifier

    assert any(m.chat_id == pro.user.telegram_id for m in get_notifier().sent)

    # My bookings -> view -> cancel
    harness.session.reset()
    await harness.click("menu:bookings")
    await harness.click(harness.find_button("bk:view:"))
    await harness.click(harness.find_button("bk:cancel:"))
    await harness.click(harness.find_button("bk:cancelyes:"))
    await session.refresh(booking)
    assert booking.status == BookingStatus.CANCELLED


async def test_professional_onboarding(session):
    h = BotHarness(tg_id=515151, first_name="Marc")
    await h.send("/pro")
    assert any("Développez votre activité" in t for t in h.session.texts())
    await h.click("pd:create")
    await h.send("Marc Électricité")
    await h.click(h.find_button("pc:"))  # first root category (Santé) -> sub-categories
    from tests.conftest import category_id

    await h.click(f"pc:{await category_id(session, 'electricien')}")
    # category with children asked again only if needed; pick electricien directly
    await h.click("pm:mobile")
    await h.send("Boulogne-Billancourt")
    await h.click("pr:20")
    await h.send("Électricien certifié, 15 ans d'expérience.")
    assert any("Compte créé" in t for t in h.session.texts())
    pro = (await session.execute(select(Professional).where(Professional.business_name == "Marc Électricité"))
           ).scalar_one()
    assert pro.status.value == "pending" and pro.service_radius_km == 20 and abs(pro.lat - 48.835) < 0.01

    # add a service through the dashboard
    await h.click("psv:add")
    await h.send("Installation de prise")
    await h.click("psvd:45")
    await h.send("60")
    await session.refresh(pro)
    pro = (await session.execute(select(Professional).where(Professional.id == pro.id)
                                 .execution_options(populate_existing=True))).scalar_one()
    assert [s.name for s in pro.services] == ["Installation de prise"] and pro.services[0].price_cents == 6000

    # set Saturday hours
    await h.click("ph:5")
    await h.send("9h-12h30")
    from app.services.professionals import get_weekly_hours

    weekly = await get_weekly_hours(session, pro.id)
    assert [(a.strftime("%H:%M"), b.strftime("%H:%M")) for a, b in weekly[5]] == [("09:00", "12:30")]


async def test_pro_accepts_pending_request(session):
    pro = await make_pro(session, auto_confirm=False)
    client = BotHarness(tg_id=616161)
    await client.click(f"pro:book:{pro.id}")
    await client.click(client.find_button("bd:"))
    await client.click(client.find_button("bt:"))
    await client.click("bc")
    booking = (await session.execute(select(Booking).where(Booking.professional_id == pro.id))).scalar_one()
    assert booking.status == BookingStatus.PENDING

    pro_bot = BotHarness(tg_id=pro.user.telegram_id, first_name="Pro")
    await pro_bot.click(f"pbk:confirm:{booking.id}")
    await session.refresh(booking)
    assert booking.status == BookingStatus.CONFIRMED


async def test_location_flow_for_urgent_search(session):
    await make_pro(session, slug="serrurier", mode="mobile", radius=15, accepts_urgent=True,
                   on_duty_until=datetime(2099, 1, 1, tzinfo=UTC), services=[("Ouverture de porte", 30, 9000)])
    h = BotHarness(tg_id=717171)
    await h.send("serrurier urgent")
    assert any("Où avez-vous besoin" in t for t in h.session.texts())
    await h.send("75011")
    texts = "\n".join(h.session.texts())
    assert "Position enregistrée" in texts and "Ouverture de porte" in texts and "Paris 11e" in texts
