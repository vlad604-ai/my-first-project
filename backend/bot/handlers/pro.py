"""Professional space inside Telegram."""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.i18n import WEEKDAYS, fmt_day, fmt_dt, fmt_time, t
from app.models import Category, Professional, User, WorkMode
from app.services import availability
from app.services import booking as booking_service
from app.services import professionals as pro_service
from app.services import quotes as quote_service
from app.services.geo import RADIUS_CHOICES_KM, reverse_city
from app.services.text import escape_html, format_price, truncate
from bot.states import ProEdit, ProOnboarding
from bot.ui import REMOVE_KB, booking_text, btn, category_name, chunk, hours_summary, kb, location_request_kb

router = Router(name="pro")
UTC = timezone.utc


def _home_btn(lang: str) -> list:
    return [btn(t("btn.pro_space", lang), "pd:home")]


async def _require_pro(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> Professional | None:
    pro = await pro_service.get_pro_for_user(session, user)
    if pro is None:
        await cb.answer(t("pro.not_registered", lang), show_alert=True)
    return pro


async def _edit_or_send(cb: CallbackQuery, text: str, markup) -> None:
    try:
        await cb.message.edit_text(text, reply_markup=markup, disable_web_page_preview=True)
    except Exception:
        await cb.message.answer(text, reply_markup=markup, disable_web_page_preview=True)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
async def dashboard(target: Message | CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    pro = await pro_service.get_pro_for_user(session, user)
    message = target.message if isinstance(target, CallbackQuery) else target
    if pro is None:
        text = t("pro.intro", lang, app=settings.app_name)
        markup = kb([btn(t("btn.create_pro", lang), "pd:create")], [btn(t("btn.menu", lang), "menu:main")])
    else:
        now = datetime.now(UTC)
        day_start, day_end = availability.local_day_window(now.astimezone(ZoneInfo(pro.timezone)).date(), pro.timezone)
        today = await booking_service.list_pro_bookings(session, pro, day_start, day_end)
        pending = await booking_service.list_pending_for_pro(session, pro)
        inbox = await quote_service.pro_inbox(session, pro)
        on_duty = pro.on_duty_until and pro.on_duty_until > now
        text = t("pro.dashboard", lang, name=escape_html(pro.business_name), status=t(f"prostatus.{pro.status.value}", lang),
                 today=len(today), pending=len(pending), quotes=len(inbox),
                 rating=f"{pro.rating_avg:.1f}" if pro.rating_count else "-", reviews=pro.rating_count)
        if on_duty:
            text += "\n" + t("pro.on_duty_until", lang, time=fmt_time(pro.on_duty_until, pro.timezone))
        if pro.status.value == "pending":
            text += "\n\n" + t("pro.pending_notice", lang)
        if not any(s.is_active for s in pro.services):
            text += "\n\n" + t("pro.no_services_notice", lang)
        rows = [
            [btn(t("pd.agenda", lang), "pd:agenda:0"), btn(t("pd.pending", lang, n=len(pending)), "pd:pending")],
            [btn(t("pd.services", lang), "pd:services"), btn(t("pd.hours", lang), "pd:hours")],
            [btn(t("pd.closures", lang), "pd:closures"), btn(t("pd.quotes", lang, n=len(inbox)), "pd:quotes")],
            [btn(t("pd.profile", lang), "pd:profile"), btn(t("pd.settings", lang), "pd:settings")],
            [btn(t("pd.clients", lang), "pd:clients"), btn(t("pd.stats", lang), "pd:stats")],
        ]
        if pro.is_mobile:
            rows.append([btn(t("pd.duty_off" if on_duty else "pd.duty_on", lang), "pd:duty")])
        rows.append([btn(t("pd.view_public", lang), f"pro:view:{pro.id}"), btn(t("btn.menu", lang), "menu:main")])
        markup = kb(*rows)
    if isinstance(target, CallbackQuery):
        await _edit_or_send(target, text, markup)
    else:
        await message.answer(text, reply_markup=markup)


@router.message(Command("pro"))
async def cmd_pro(message: Message, session: AsyncSession, user: User, lang: str, state: FSMContext) -> None:
    await state.set_state(None)
    await dashboard(message, session, user, lang)


@router.callback_query(F.data == "pd:home")
async def cb_home(cb: CallbackQuery, session: AsyncSession, user: User, lang: str, state: FSMContext) -> None:
    await state.set_state(None)
    await cb.answer()
    await dashboard(cb, session, user, lang)


# ---------------------------------------------------------------------------
# Onboarding
# ---------------------------------------------------------------------------
@router.callback_query(F.data == "pd:create")
async def onboarding_start(cb: CallbackQuery, session: AsyncSession, user: User, lang: str, state: FSMContext) -> None:
    await cb.answer()
    if await pro_service.get_pro_for_user(session, user):
        await dashboard(cb, session, user, lang)
        return
    await state.set_state(ProOnboarding.name)
    await cb.message.answer(t("onb.ask_name", lang), reply_markup=kb([btn(t("btn.cancel", lang), "menu:main")]))


@router.message(StateFilter(ProOnboarding.name), F.text)
async def onb_name(message: Message, session: AsyncSession, state: FSMContext, lang: str) -> None:
    name = message.text.strip()
    if not 2 <= len(name) <= 160:
        await message.answer(t("onb.name_invalid", lang))
        return
    await state.update_data(onb_name=name)
    await state.set_state(ProOnboarding.category)
    await _onb_categories(message, session, lang, None)


async def _onb_categories(message: Message, session: AsyncSession, lang: str, parent_id: int | None,
                          edit: bool = False) -> None:
    q = select(Category).where(Category.is_active.is_(True))
    q = q.where(Category.parent_id.is_(None)) if parent_id is None else q.where(Category.parent_id == parent_id)
    cats = (await session.execute(q.order_by(Category.sort_order))).scalars().all()
    rows = chunk([btn(category_name(c, lang), f"pc:{c.id}") for c in cats], 2)
    if parent_id is not None:
        rows.append([btn(t("btn.back", lang), "pc:root")])
    text = t("onb.ask_category", lang)
    if edit:
        try:
            await message.edit_text(text, reply_markup=kb(*rows))
            return
        except Exception:
            pass
    await message.answer(text, reply_markup=kb(*rows))


@router.callback_query(StateFilter(ProOnboarding.category), F.data.startswith("pc:"))
async def onb_category(cb: CallbackQuery, session: AsyncSession, state: FSMContext, lang: str) -> None:
    await cb.answer()
    value = cb.data.split(":")[1]
    if value == "root":
        await _onb_categories(cb.message, session, lang, None, edit=True)
        return
    cat = await session.get(Category, int(value))
    children = (await session.execute(select(Category.id).where(Category.parent_id == cat.id))).first()
    if children:
        await _onb_categories(cb.message, session, lang, cat.id, edit=True)
        return
    await state.update_data(onb_category=cat.id)
    await state.set_state(ProOnboarding.work_mode)
    await cb.message.edit_text(t("onb.ask_mode", lang, cat=category_name(cat, lang)), reply_markup=kb(
        [btn(t("mode.on_site", lang), "pm:on_site")], [btn(t("mode.mobile", lang), "pm:mobile")],
        [btn(t("mode.both", lang), "pm:both")]))


@router.callback_query(StateFilter(ProOnboarding.work_mode), F.data.startswith("pm:"))
async def onb_mode(cb: CallbackQuery, state: FSMContext, lang: str) -> None:
    await cb.answer()
    mode = cb.data.split(":")[1]
    await state.update_data(onb_mode=mode)
    await state.set_state(ProOnboarding.location)
    key = "onb.ask_address" if mode == "on_site" else "onb.ask_base"
    await cb.message.answer(t(key, lang), reply_markup=location_request_kb(lang))


@router.message(StateFilter(ProOnboarding.location), F.location | F.text)
async def onb_location(message: Message, session: AsyncSession, state: FSMContext, lang: str) -> None:
    if message.location:
        lat, lon = message.location.latitude, message.location.longitude
        await state.update_data(onb_lat=lat, onb_lon=lon, onb_address=await reverse_city(session, lat, lon) or "GPS")
    else:
        from app.services.geo import geocode

        point = await geocode(session, message.text)
        if point is None:
            await message.answer(t("loc.unknown", lang))
            return
        await state.update_data(onb_address=message.text.strip()[:255], onb_lat=None, onb_lon=None)
    await message.answer("📍 ✅", reply_markup=REMOVE_KB)
    data = await state.get_data()
    if data["onb_mode"] != "on_site":
        await state.set_state(ProOnboarding.radius)
        await message.answer(t("onb.ask_radius", lang), reply_markup=kb(
            [btn(f"{r} km", f"pr:{r}") for r in (5, 10, 20, 30, 50)]))
    else:
        await state.set_state(ProOnboarding.description)
        await message.answer(t("onb.ask_description", lang), reply_markup=kb([btn(t("btn.skip", lang), "pd:skipdesc")]))


@router.callback_query(StateFilter(ProOnboarding.radius), F.data.startswith("pr:"))
async def onb_radius(cb: CallbackQuery, state: FSMContext, lang: str) -> None:
    await cb.answer()
    await state.update_data(onb_radius=int(cb.data.split(":")[1]))
    await state.set_state(ProOnboarding.description)
    await cb.message.answer(t("onb.ask_description", lang), reply_markup=kb([btn(t("btn.skip", lang), "pd:skipdesc")]))


async def _finish_onboarding(message: Message, session: AsyncSession, user: User, state: FSMContext, lang: str,
                             description: str | None) -> None:
    data = await state.get_data()
    await state.set_state(None)
    try:
        pro = await pro_service.create_professional(
            session, user, data["onb_name"], data["onb_category"], WorkMode(data["onb_mode"]),
            city_or_address=data.get("onb_address") if data.get("onb_lat") is None else None,
            lat=data.get("onb_lat"), lon=data.get("onb_lon"), service_radius_km=data.get("onb_radius", 0),
            description=description,
        )
    except pro_service.ProError as exc:
        await message.answer(t(f"pro.err.{exc}", lang))
        return
    if data.get("onb_lat") is not None and data.get("onb_address"):
        pro.city = data["onb_address"]
        await session.commit()
    await message.answer(t("onb.done_active" if pro.status.value == "active" else "onb.done_pending", lang),
                         reply_markup=kb([btn(t("pd.add_service", lang), "psv:add")], _home_btn(lang)))


@router.message(StateFilter(ProOnboarding.description), F.text)
async def onb_description(message: Message, session: AsyncSession, user: User, state: FSMContext, lang: str) -> None:
    await _finish_onboarding(message, session, user, state, lang, message.text.strip()[:2000])


@router.callback_query(F.data == "pd:skipdesc")
async def onb_skip(cb: CallbackQuery, session: AsyncSession, user: User, state: FSMContext, lang: str) -> None:
    await cb.answer()
    await _finish_onboarding(cb.message, session, user, state, lang, None)


# ---------------------------------------------------------------------------
# Agenda & booking requests
# ---------------------------------------------------------------------------
@router.callback_query(F.data.startswith("pd:agenda:"))
async def agenda(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    pro = await _require_pro(cb, session, user, lang)
    if not pro:
        return
    await cb.answer()
    offset = int(cb.data.split(":")[2])
    day = datetime.now(ZoneInfo(pro.timezone)).date() + timedelta(days=offset)
    start, end = availability.local_day_window(day, pro.timezone)
    items = await booking_service.list_pro_bookings(session, pro, start, end)
    lines = [t("pd.agenda_title", lang, day=fmt_day(day, lang))]
    rows = []
    if not items:
        lines.append(t("pd.agenda_empty", lang))
    for b in items:
        icon = "⏳" if b.status.value == "pending" else "✅"
        label = f"{icon} {fmt_time(b.start_at, pro.timezone)} {b.service_name or ''} · {b.client.display_name}"
        rows.append([btn(truncate(label, 60), f"pbk:view:{b.id}")])
    rows.append([btn("◀️", f"pd:agenda:{offset - 1}"), btn(t("day.today", lang), "pd:agenda:0"),
                 btn("▶️", f"pd:agenda:{offset + 1}")])
    rows.append(_home_btn(lang))
    await _edit_or_send(cb, "\n".join(lines), kb(*rows))


@router.callback_query(F.data == "pd:pending")
async def pending(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    pro = await _require_pro(cb, session, user, lang)
    if not pro:
        return
    await cb.answer()
    items = await booking_service.list_pending_for_pro(session, pro)
    if not items:
        await _edit_or_send(cb, t("pd.no_pending", lang), kb(_home_btn(lang)))
        return
    rows = [[btn(truncate(f"⏳ {fmt_dt(b.start_at, pro.timezone, lang)} · {b.client.display_name}", 60),
                 f"pbk:view:{b.id}")] for b in items]
    rows.append(_home_btn(lang))
    await _edit_or_send(cb, t("pd.pending_title", lang), kb(*rows))


async def _pro_booking(cb: CallbackQuery, session: AsyncSession, user: User):
    b = await booking_service.load_booking(session, cb.data.split(":", 2)[2])
    if b is None or b.professional.user_id != user.id:
        return None
    return b


@router.callback_query(F.data.startswith("pbk:view:"))
async def pro_booking_view(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    await cb.answer()
    b = await _pro_booking(cb, session, user)
    if b is None:
        return
    now = datetime.now(UTC)
    rows = []
    if b.status.value == "pending":
        rows.append([btn(t("btn.accept", lang), f"pbk:confirm:{b.id}"), btn(t("btn.refuse", lang), f"pbk:refuse:{b.id}")])
    if b.status.value == "confirmed" and b.start_at <= now:
        rows.append([btn(t("btn.mark_done", lang), f"pbk:done:{b.id}")])
    if b.status.value in ("pending", "confirmed") and b.start_at > now:
        rows.append([btn(t("btn.cancel_booking", lang), f"pbk:cancel:{b.id}")])
    rows.append([btn(t("btn.contact_client", lang), f"msg:pro:{b.client_id}")])
    rows.append(_home_btn(lang))
    await cb.message.answer(booking_text(b, lang, for_pro=True), reply_markup=kb(*rows))


@router.callback_query(F.data.startswith("pbk:confirm:"))
async def pro_confirm(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    b = await _pro_booking(cb, session, user)
    if b is None:
        await cb.answer()
        return
    try:
        await booking_service.confirm_booking(session, b, user)
    except booking_service.BookingError as exc:
        await cb.answer(t(f"booking.err.{exc.code}", lang), show_alert=True)
        return
    await cb.answer("✅")
    await cb.message.edit_text(booking_text(b, lang, for_pro=True), reply_markup=kb(_home_btn(lang)))


@router.callback_query(F.data.startswith("pbk:refuse:"))
async def pro_refuse_ask(cb: CallbackQuery, session: AsyncSession, user: User, lang: str, state: FSMContext) -> None:
    b = await _pro_booking(cb, session, user)
    await cb.answer()
    if b is None:
        return
    await state.set_state(ProEdit.refuse_reason)
    await state.update_data(refuse_id=str(b.id))
    await cb.message.answer(t("pd.refuse_reason", lang), reply_markup=kb([btn(t("btn.skip", lang), "pbk:refuseno")]))


async def _do_refuse(target: Message, session: AsyncSession, user: User, state: FSMContext, lang: str,
                     reason: str | None) -> None:
    data = await state.get_data()
    await state.set_state(None)
    b = await booking_service.load_booking(session, data.get("refuse_id", ""))
    if b is None or b.professional.user_id != user.id:
        return
    try:
        await booking_service.refuse_booking(session, b, user, reason)
    except booking_service.BookingError as exc:
        await target.answer(t(f"booking.err.{exc.code}", lang))
        return
    await target.answer(t("pd.refused", lang), reply_markup=kb(_home_btn(lang)))


@router.message(StateFilter(ProEdit.refuse_reason), F.text)
async def pro_refuse_reason(message: Message, session: AsyncSession, user: User, state: FSMContext, lang: str) -> None:
    await _do_refuse(message, session, user, state, lang, message.text[:255])


@router.callback_query(F.data == "pbk:refuseno")
async def pro_refuse_noreason(cb: CallbackQuery, session: AsyncSession, user: User, state: FSMContext, lang: str) -> None:
    await cb.answer()
    await _do_refuse(cb.message, session, user, state, lang, None)


@router.callback_query(F.data.startswith("pbk:done:"))
async def pro_done(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    b = await _pro_booking(cb, session, user)
    if b is None:
        await cb.answer()
        return
    try:
        await booking_service.complete_booking(session, b, user)
    except booking_service.BookingError as exc:
        await cb.answer(t(f"booking.err.{exc.code}", lang), show_alert=True)
        return
    await cb.answer("🏁")
    await cb.message.edit_text(booking_text(b, lang, for_pro=True), reply_markup=kb(_home_btn(lang)))


@router.callback_query(F.data.startswith("pbk:cancel:"))
async def pro_cancel(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    b = await _pro_booking(cb, session, user)
    if b is None:
        await cb.answer()
        return
    try:
        await booking_service.cancel_booking(session, b, user, t("pd.cancelled_by_pro", lang))
    except booking_service.BookingError as exc:
        await cb.answer(t(f"booking.err.{exc.code}", lang), show_alert=True)
        return
    await cb.answer("✅")
    await cb.message.edit_text(booking_text(b, lang, for_pro=True), reply_markup=kb(_home_btn(lang)))


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------
@router.callback_query(F.data == "pd:services")
async def services(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    pro = await _require_pro(cb, session, user, lang)
    if not pro:
        return
    await cb.answer()
    rows = []
    for s in pro.services:
        icon = "🟢" if s.is_active else "⚪"
        rows.append([btn(truncate(f"{icon} {s.name} · {format_price(s.price_cents, s.price_type.value)} · "
                                  f"{s.duration_min}′", 60), f"psv:toggle:{s.id}")])
    rows.append([btn(t("pd.add_service", lang), "psv:add")])
    rows.append(_home_btn(lang))
    await _edit_or_send(cb, t("pd.services_title", lang), kb(*rows))


@router.callback_query(F.data.startswith("psv:toggle:"))
async def service_toggle(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    pro = await _require_pro(cb, session, user, lang)
    if not pro:
        return
    sid = int(cb.data.split(":")[2])
    svc = next((s for s in pro.services if s.id == sid), None)
    if svc:
        await pro_service.update_service(session, pro, sid, is_active=not svc.is_active)
    cb.data = "pd:services"
    await services(cb, session, user, lang)


@router.callback_query(F.data == "psv:add")
async def service_add(cb: CallbackQuery, session: AsyncSession, user: User, lang: str, state: FSMContext) -> None:
    if not await _require_pro(cb, session, user, lang):
        return
    await cb.answer()
    await state.set_state(ProEdit.service_name)
    await cb.message.answer(t("psv.ask_name", lang))


@router.message(StateFilter(ProEdit.service_name), F.text)
async def service_name(message: Message, state: FSMContext, lang: str) -> None:
    await state.update_data(svc_name=message.text.strip()[:160])
    await state.set_state(ProEdit.service_duration)
    await message.answer(t("psv.ask_duration", lang), reply_markup=kb(
        [btn(f"{m} min", f"psvd:{m}") for m in (15, 30, 45, 60)],
        [btn(f"{m // 60}h{m % 60:02d}" if m % 60 else f"{m // 60}h", f"psvd:{m}") for m in (90, 120, 180, 240)]))


async def _ask_price(message: Message, state: FSMContext, lang: str) -> None:
    await state.set_state(ProEdit.service_price)
    await message.answer(t("psv.ask_price", lang), reply_markup=kb([btn(t("psv.on_quote", lang), "psvp:quote")]))


@router.callback_query(StateFilter(ProEdit.service_duration), F.data.startswith("psvd:"))
async def service_duration_btn(cb: CallbackQuery, state: FSMContext, lang: str) -> None:
    await cb.answer()
    await state.update_data(svc_duration=int(cb.data.split(":")[1]))
    await _ask_price(cb.message, state, lang)


@router.message(StateFilter(ProEdit.service_duration), F.text)
async def service_duration_text(message: Message, state: FSMContext, lang: str) -> None:
    m = re.search(r"(\d+)\s*h\s*(\d+)?|(\d+)", message.text)
    minutes = None
    if m and m.group(1):
        minutes = int(m.group(1)) * 60 + int(m.group(2) or 0)
    elif m:
        minutes = int(m.group(3))
    if not minutes or not 5 <= minutes <= 1440:
        await message.answer(t("psv.invalid_duration", lang))
        return
    await state.update_data(svc_duration=minutes)
    await _ask_price(message, state, lang)


async def _create_service(target: Message, session: AsyncSession, user: User, state: FSMContext, lang: str,
                          price_cents: int | None) -> None:
    data = await state.get_data()
    await state.set_state(None)
    pro = await pro_service.get_pro_for_user(session, user)
    try:
        await pro_service.add_service(session, pro, data["svc_name"], data["svc_duration"], price_cents)
    except pro_service.ProError as exc:
        await target.answer(t(f"pro.err.{exc}", lang))
        return
    await target.answer(t("psv.added", lang), reply_markup=kb(
        [btn(t("pd.add_service", lang), "psv:add"), btn(t("pd.services", lang), "pd:services")], _home_btn(lang)))


@router.message(StateFilter(ProEdit.service_price), F.text)
async def service_price(message: Message, session: AsyncSession, user: User, state: FSMContext, lang: str) -> None:
    m = re.search(r"(\d+(?:[.,]\d{1,2})?)", message.text)
    if not m:
        await message.answer(t("psv.invalid_price", lang))
        return
    await _create_service(message, session, user, state, lang, int(round(float(m.group(1).replace(",", ".")) * 100)))


@router.callback_query(StateFilter(ProEdit.service_price), F.data == "psvp:quote")
async def service_price_quote(cb: CallbackQuery, session: AsyncSession, user: User, state: FSMContext, lang: str) -> None:
    await cb.answer()
    await _create_service(cb.message, session, user, state, lang, None)


# ---------------------------------------------------------------------------
# Working hours
# ---------------------------------------------------------------------------
@router.callback_query(F.data == "pd:hours")
async def hours(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    pro = await _require_pro(cb, session, user, lang)
    if not pro:
        return
    await cb.answer()
    names = WEEKDAYS.get(lang, WEEKDAYS["fr"])
    rows = chunk([btn(names[d].capitalize(), f"ph:{d}") for d in range(7)], 4)
    rows.append([btn(t("ph.copy_monday", lang), "ph:copy")])
    rows.append(_home_btn(lang))
    await _edit_or_send(cb, t("ph.title", lang) + "\n\n" + hours_summary(pro, lang), kb(*rows))


@router.callback_query(F.data == "ph:copy")
async def hours_copy(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    pro = await _require_pro(cb, session, user, lang)
    if not pro:
        return
    weekly = await pro_service.get_weekly_hours(session, pro.id)
    for d in range(1, 5):
        weekly[d] = list(weekly[0])
    await pro_service.set_weekly_hours(session, pro, weekly)
    cb.data = "pd:hours"
    await hours(cb, session, user, lang)


@router.callback_query(F.data.regexp(r"^ph:\d$"))
async def hours_day(cb: CallbackQuery, state: FSMContext, lang: str) -> None:
    await cb.answer()
    day = int(cb.data.split(":")[1])
    await state.set_state(ProEdit.hours)
    await state.update_data(ph_day=day)
    await cb.message.answer(t("ph.ask", lang, day=WEEKDAYS.get(lang, WEEKDAYS["fr"])[day]))


@router.message(StateFilter(ProEdit.hours), F.text)
async def hours_set(message: Message, session: AsyncSession, user: User, state: FSMContext, lang: str) -> None:
    try:
        ranges = pro_service.parse_day_ranges(message.text)
    except pro_service.ProError:
        await message.answer(t("ph.invalid", lang))
        return
    data = await state.get_data()
    await state.set_state(None)
    pro = await pro_service.get_pro_for_user(session, user)
    await pro_service.set_day_hours(session, pro, data["ph_day"], ranges)
    pro = await pro_service.get_pro_for_user(session, user)
    await message.answer(t("ph.saved", lang) + "\n\n" + hours_summary(pro, lang),
                         reply_markup=kb([btn(t("pd.hours", lang), "pd:hours")], _home_btn(lang)))


# ---------------------------------------------------------------------------
# Closures
# ---------------------------------------------------------------------------
@router.callback_query(F.data == "pd:closures")
async def closures(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    pro = await _require_pro(cb, session, user, lang)
    if not pro:
        return
    await cb.answer()
    items = await pro_service.list_time_off(session, pro)
    rows = [[btn(f"🗑 {fmt_day(o.start_at.date(), lang)} → {fmt_day((o.end_at - timedelta(seconds=1)).date(), lang)}"
                 + (f" · {o.reason}" if o.reason else ""), f"pcl:del:{o.id}")] for o in items]
    rows.append([btn(t("pcl.add", lang), "pcl:add")])
    rows.append(_home_btn(lang))
    text = t("pcl.title", lang) + ("\n" + t("pcl.holidays_on" if pro.closed_on_holidays else "pcl.holidays_off", lang))
    await _edit_or_send(cb, text, kb(*rows))


@router.callback_query(F.data == "pcl:add")
async def closure_add(cb: CallbackQuery, state: FSMContext, lang: str) -> None:
    await cb.answer()
    await state.set_state(ProEdit.closure)
    await cb.message.answer(t("pcl.ask", lang))


@router.message(StateFilter(ProEdit.closure), F.text)
async def closure_set(message: Message, session: AsyncSession, user: User, state: FSMContext, lang: str) -> None:
    pro = await pro_service.get_pro_for_user(session, user)
    try:
        start, end = pro_service.parse_date_range(message.text, pro.timezone)
        _, conflicts = await pro_service.add_time_off(session, pro, start, end)
    except pro_service.ProError:
        await message.answer(t("pcl.invalid", lang))
        return
    await state.set_state(None)
    text = t("pcl.saved", lang)
    if conflicts:
        text += "\n⚠️ " + t("pcl.conflicts", lang, n=conflicts)
    await message.answer(text, reply_markup=kb([btn(t("pd.closures", lang), "pd:closures")], _home_btn(lang)))


@router.callback_query(F.data.startswith("pcl:del:"))
async def closure_delete(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    pro = await _require_pro(cb, session, user, lang)
    if not pro:
        return
    try:
        await pro_service.delete_time_off(session, pro, int(cb.data.split(":")[2]))
    except pro_service.ProError:
        pass
    cb.data = "pd:closures"
    await closures(cb, session, user, lang)


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------
PROFILE_FIELDS = ("description", "phone", "address", "website", "specialties", "logo", "photos")


@router.callback_query(F.data == "pd:profile")
async def profile(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    pro = await _require_pro(cb, session, user, lang)
    if not pro:
        return
    await cb.answer()
    text = t("pf.title", lang, name=escape_html(pro.business_name), desc=escape_html(truncate(pro.description or "-", 300)),
             phone=escape_html(pro.phone or "-"), address=escape_html(pro.address or pro.city or "-"),
             website=escape_html(pro.website or "-"), specialties=escape_html(", ".join(pro.specialties or []) or "-"),
             photos=len(pro.photos))
    rows = chunk([btn(t(f"pf.{f}", lang), f"pf:{f}") for f in PROFILE_FIELDS], 2)
    if settings.telegram_bot_username:
        rows.append([btn(t("pf.share", lang), url=f"https://t.me/share/url?url=https://t.me/"
                                                  f"{settings.telegram_bot_username}?start=pro_{pro.id}")])
    rows.append(_home_btn(lang))
    await _edit_or_send(cb, text, kb(*rows))


@router.callback_query(F.data.startswith("pf:"))
async def profile_field(cb: CallbackQuery, state: FSMContext, lang: str) -> None:
    await cb.answer()
    field = cb.data.split(":")[1]
    if field not in PROFILE_FIELDS:
        return
    if field in ("logo", "photos"):
        await state.set_state(ProEdit.photos)
        await state.update_data(pf_field=field)
        await cb.message.answer(t(f"pf.ask_{field}", lang), reply_markup=kb([btn(t("btn.done", lang), "pd:profile")]))
        return
    await state.set_state(ProEdit.field)
    await state.update_data(pf_field=field)
    await cb.message.answer(t(f"pf.ask_{field}", lang))


@router.message(StateFilter(ProEdit.field), F.text)
async def profile_field_set(message: Message, session: AsyncSession, user: User, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    field = data.get("pf_field")
    pro = await pro_service.get_pro_for_user(session, user)
    value = message.text.strip()
    if field == "specialties":
        value = [v.strip()[:40] for v in value.split(",") if v.strip()][:10]
    elif field == "phone" and not re.fullmatch(r"[+\d][\d .-]{6,20}", value):
        await message.answer(t("pf.invalid_phone", lang))
        return
    else:
        value = value[:2000 if field == "description" else 255]
    await pro_service.update_profile(session, pro, **{field: value})
    await state.set_state(None)
    await message.answer(t("pf.saved", lang), reply_markup=kb([btn(t("pd.profile", lang), "pd:profile")], _home_btn(lang)))


@router.message(StateFilter(ProEdit.photos), F.photo)
async def profile_photo(message: Message, session: AsyncSession, user: User, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    pro = await pro_service.get_pro_for_user(session, user)
    file_id = message.photo[-1].file_id
    if data.get("pf_field") == "logo":
        await pro_service.update_profile(session, pro, logo_file_id=file_id)
        await state.set_state(None)
        await message.answer(t("pf.saved", lang), reply_markup=kb([btn(t("pd.profile", lang), "pd:profile")]))
        return
    try:
        await pro_service.add_photo(session, pro, file_id=file_id, caption=(message.caption or None))
    except pro_service.ProError as exc:
        await message.answer(t(f"pro.err.{exc}", lang))
        return
    await message.answer(t("pf.photo_added", lang), reply_markup=kb([btn(t("btn.done", lang), "pd:profile")]))


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
def _onoff(v: bool) -> str:
    return "✅" if v else "❌"


@router.callback_query(F.data == "pd:settings")
async def pro_settings(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    pro = await _require_pro(cb, session, user, lang)
    if not pro:
        return
    await cb.answer()
    text = t("pst.title", lang, mode=t(f"mode.{pro.work_mode.value}", lang), radius=pro.service_radius_km,
             buffer=pro.travel_buffer_min, step=pro.slot_step_min, notice=pro.min_notice_min)
    rows = [
        [btn(f"{_onoff(pro.auto_confirm)} {t('pst.auto_confirm', lang)}", "pst:toggle:auto_confirm")],
        [btn(f"{_onoff(pro.accepts_quotes)} {t('pst.accepts_quotes', lang)}", "pst:toggle:accepts_quotes")],
        [btn(f"{_onoff(pro.closed_on_holidays)} {t('pst.holidays', lang)}", "pst:toggle:closed_on_holidays")],
    ]
    if pro.is_mobile:
        rows.append([btn(f"{_onoff(pro.accepts_urgent)} {t('pst.urgent', lang)}", "pst:toggle:accepts_urgent")])
        rows.append([btn(f"📏 {r} km", f"pst:radius:{r}") for r in RADIUS_CHOICES_KM])
        rows.append([btn(f"🚗 +{m}′", f"pst:buffer:{m}") for m in (0, 15, 30, 45, 60)])
    rows.append([btn(f"⏱ {m}′", f"pst:step:{m}") for m in (10, 15, 30, 60)])
    rows.append([btn(f"⏳ {label}", f"pst:notice:{m}") for label, m in (("0", 0), ("1h", 60), ("3h", 180),
                                                                         ("24h", 1440))])
    rows.append(_home_btn(lang))
    await _edit_or_send(cb, text, kb(*rows))


@router.callback_query(F.data.startswith("pst:"))
async def pro_settings_set(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    pro = await _require_pro(cb, session, user, lang)
    if not pro:
        return
    _, kind, value = cb.data.split(":")
    if kind == "toggle" and value in ("auto_confirm", "accepts_quotes", "accepts_urgent", "closed_on_holidays"):
        await pro_service.update_profile(session, pro, **{value: not getattr(pro, value)})
    elif kind == "radius":
        await pro_service.update_profile(session, pro, service_radius_km=int(value))
    elif kind == "buffer":
        await pro_service.update_profile(session, pro, travel_buffer_min=int(value))
    elif kind == "step":
        await pro_service.update_profile(session, pro, slot_step_min=int(value))
    elif kind == "notice":
        await pro_service.update_profile(session, pro, min_notice_min=int(value))
    cb.data = "pd:settings"
    await pro_settings(cb, session, user, lang)


@router.callback_query(F.data == "pd:duty")
async def duty(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    pro = await _require_pro(cb, session, user, lang)
    if not pro:
        return
    await cb.answer()
    if pro.on_duty_until and pro.on_duty_until > datetime.now(UTC):
        await pro_service.set_on_duty(session, pro, None)
        await dashboard(cb, session, user, lang)
        return
    await _edit_or_send(cb, t("duty.ask", lang), kb([btn(f"{h}h", f"pdu:{h}") for h in (1, 2, 4, 8, 12)],
                                                    _home_btn(lang)))


@router.callback_query(F.data.startswith("pdu:"))
async def duty_set(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    pro = await _require_pro(cb, session, user, lang)
    if not pro:
        return
    try:
        await pro_service.set_on_duty(session, pro, int(cb.data.split(":")[1]))
    except pro_service.ProError as exc:
        await cb.answer(t(f"pro.err.{exc}", lang), show_alert=True)
        return
    await cb.answer("🚨")
    await dashboard(cb, session, user, lang)


# ---------------------------------------------------------------------------
# Quotes inbox, clients, stats
# ---------------------------------------------------------------------------
@router.callback_query(F.data == "pd:quotes")
async def quotes_inbox(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    pro = await _require_pro(cb, session, user, lang)
    if not pro:
        return
    await cb.answer()
    reqs = await quote_service.pro_inbox(session, pro)
    if not reqs:
        text = t("pd.quotes_empty", lang) + ("" if pro.accepts_quotes else "\n" + t("pd.quotes_disabled", lang))
        await _edit_or_send(cb, text, kb(_home_btn(lang)))
        return
    for r in reqs[:10]:
        budget = format_price(r.budget_cents) if r.budget_cents else t("quote.no_budget", lang)
        await cb.message.answer(
            f"📝 <b>{escape_html(r.category.name(lang))}</b> · {escape_html(r.city or '-')} · {budget} · "
            f"{t('urgency.' + r.urgency.value, lang)}\n<i>{escape_html(truncate(r.description, 600))}</i>",
            reply_markup=kb([btn(t("btn.send_quote", lang), f"pq:answer:{r.id}"),
                             btn(t("btn.decline", lang), f"pq:decline:{r.id}")]))
    await cb.message.answer("—", reply_markup=kb(_home_btn(lang)))


@router.callback_query(F.data == "pd:clients")
async def clients(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    pro = await _require_pro(cb, session, user, lang)
    if not pro:
        return
    await cb.answer()
    items = await pro_service.pro_clients(session, pro)
    if not items:
        await _edit_or_send(cb, t("pd.clients_empty", lang), kb(_home_btn(lang)))
        return
    rows = [[btn(truncate(f"👤 {c['user'].display_name} · {c['bookings']} RDV · {c['last']:%d/%m}", 60),
                 f"msg:pro:{c['user'].id}")] for c in items[:30]]
    rows.append(_home_btn(lang))
    await _edit_or_send(cb, t("pd.clients_title", lang), kb(*rows))


@router.callback_query(F.data == "pd:stats")
async def stats(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    pro = await _require_pro(cb, session, user, lang)
    if not pro:
        return
    await cb.answer()
    s = await pro_service.pro_stats(session, pro)
    by = s["by_status"]
    text = t("pd.stats_text", lang, total=s["bookings_total"],
             confirmed=by.get("confirmed", {}).get("count", 0), completed=by.get("completed", {}).get("count", 0),
             cancelled=by.get("cancelled", {}).get("count", 0), refused=by.get("refused", {}).get("count", 0),
             rate=f"{s['cancellation_rate'] * 100:.0f}", revenue=format_price(s["estimated_revenue_cents"]),
             clients=s["unique_clients"], favorites=s["favorites"], upcoming=s["upcoming"],
             rating=f"{s['rating_avg']:.1f}", reviews=s["rating_count"], done=s["completed_total"])
    await _edit_or_send(cb, text, kb(_home_btn(lang)))
