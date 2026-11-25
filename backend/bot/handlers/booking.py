"""Client booking flow, my bookings, cancel, reschedule, reviews."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.i18n import fmt_day, fmt_dt, t
from app.models import BookingLocation, Review, Service, User
from app.services import availability
from app.services import booking as booking_service
from app.services import professionals as pro_service
from app.services import reviews as review_service
from app.services.geo import geocode, reverse_city
from app.services.text import escape_html, format_price
from bot.states import BookingFlow, ReviewFlow
from bot.ui import (
    REMOVE_KB,
    STATUS_ICONS,
    back_menu,
    booking_text,
    btn,
    calendar_kb,
    kb,
    location_request_kb,
    services_kb,
    slots_kb,
)

router = Router(name="booking")
UTC = timezone.utc


def _from_epoch_min(value: str) -> datetime:
    return datetime.fromtimestamp(int(value) * 60, tz=UTC)


async def _service(session: AsyncSession, service_id: int) -> Service | None:
    svc = await session.get(Service, service_id)
    return svc if svc and svc.is_active else None


# ---------------------------------------------------------------------------
# Service -> day -> slot
# ---------------------------------------------------------------------------
@router.callback_query(F.data.startswith("pro:book:"))
async def choose_service(cb: CallbackQuery, session: AsyncSession, lang: str) -> None:
    await cb.answer()
    pro = await pro_service.get_public_pro(session, int(cb.data.split(":")[2]))
    if pro is None or pro.status.value != "active":
        await cb.message.answer(t("pro.not_found", lang))
        return
    active = [s for s in pro.services if s.is_active]
    if not active:
        await cb.message.answer(t("booking.no_services", lang))
        return
    if len(active) == 1:
        await _send_calendar(cb.message, session, active[0], 0, lang)
        return
    await cb.message.answer(t("booking.choose_service", lang, pro=escape_html(pro.business_name)),
                            reply_markup=services_kb(pro, lang))


async def _days_with_slots(session: AsyncSession, pro, duration: int, start_day: date,
                           exclude_booking_id=None) -> dict[date, int]:
    start, _ = availability.local_day_window(start_day, pro.timezone)
    end = start + timedelta(days=14)
    slots = await availability.get_slots(session, pro, duration, max(start, datetime.now(UTC)), end,
                                         exclude_booking_id=exclude_booking_id)
    return {d: len(v) for d, v in availability.group_by_local_day(slots, pro.timezone).items()}


async def _send_calendar(message: Message, session: AsyncSession, svc: Service, offset: int, lang: str,
                         edit: bool = False) -> None:
    pro = await pro_service.get_public_pro(session, svc.professional_id)
    start_day = datetime.now(UTC).date() + timedelta(days=offset)
    days = await _days_with_slots(session, pro, svc.duration_min, start_day)
    text = t("booking.choose_day", lang, service=escape_html(svc.name), pro=escape_html(pro.business_name),
             price=format_price(svc.price_cents, svc.price_type.value), duration=svc.duration_min)
    if not days:
        text += "\n\n" + t("booking.no_slot_period", lang)
    markup = calendar_kb(svc, days, start_day, lang)
    markup.inline_keyboard.append([btn(t("btn.back", lang), f"pro:view:{pro.id}")])
    if edit:
        try:
            await message.edit_text(text, reply_markup=markup)
            return
        except Exception:
            pass
    await message.answer(text, reply_markup=markup)


@router.callback_query(F.data.startswith("bs:"))
async def service_chosen(cb: CallbackQuery, session: AsyncSession, lang: str) -> None:
    await cb.answer()
    svc = await _service(session, int(cb.data.split(":")[1]))
    if svc:
        await _send_calendar(cb.message, session, svc, 0, lang, edit=True)


@router.callback_query(F.data.startswith("bw:"))
async def calendar_page(cb: CallbackQuery, session: AsyncSession, lang: str) -> None:
    await cb.answer()
    _, sid, offset = cb.data.split(":")
    svc = await _service(session, int(sid))
    if svc:
        await _send_calendar(cb.message, session, svc, max(0, int(offset)), lang, edit=True)


@router.callback_query(F.data.startswith("bd:"))
async def day_chosen(cb: CallbackQuery, session: AsyncSession, lang: str) -> None:
    await cb.answer()
    _, sid, ymd = cb.data.split(":")
    svc = await _service(session, int(sid))
    if not svc:
        return
    pro = await pro_service.get_public_pro(session, svc.professional_id)
    day = datetime.strptime(ymd, "%Y%m%d").date()
    start, end = availability.local_day_window(day, pro.timezone)
    slots = await availability.get_slots(session, pro, svc.duration_min, start, end)
    if not slots:
        await cb.message.answer(t("booking.day_full", lang))
        return
    await cb.message.edit_text(
        t("booking.choose_time", lang, day=fmt_day(day, lang)),
        reply_markup=slots_kb(slots, pro.timezone, str(svc.id), lang, back=f"bs:{svc.id}"))


@router.callback_query(F.data.startswith("bt:"))
async def slot_chosen(cb: CallbackQuery, session: AsyncSession, user: User, lang: str, state: FSMContext) -> None:
    await cb.answer()
    _, sid, epoch = cb.data.split(":")
    svc = await _service(session, int(sid))
    if not svc:
        return
    await state.update_data(bk_service=svc.id, bk_start=int(epoch), bk_urgent=False, bk_note=None,
                            bk_address=None, bk_lat=None, bk_lon=None)
    if svc.location == BookingLocation.AT_CLIENT:
        await _ask_address(cb.message, state, lang)
    else:
        await _confirm_screen(cb.message, session, state, lang)


@router.callback_query(F.data.startswith("bu:"))
async def urgent_request(cb: CallbackQuery, session: AsyncSession, lang: str, state: FSMContext) -> None:
    """Urgent intervention with an on-duty mobile professional (validated by the pro)."""
    await cb.answer()
    svc = await _service(session, int(cb.data.split(":")[1]))
    if not svc:
        return
    now = datetime.now(UTC)
    start = now + timedelta(minutes=5 - now.minute % 5 + 5)
    start = start.replace(second=0, microsecond=0)
    await state.update_data(bk_service=svc.id, bk_start=int(start.timestamp() // 60), bk_urgent=True,
                            bk_note=None, bk_address=None, bk_lat=None, bk_lon=None)
    await _ask_address(cb.message, state, lang)


async def _ask_address(message: Message, state: FSMContext, lang: str) -> None:
    await state.set_state(BookingFlow.address)
    await message.answer(t("booking.ask_address", lang), reply_markup=location_request_kb(lang))


@router.message(StateFilter(BookingFlow.address), F.location)
async def address_location(message: Message, session: AsyncSession, state: FSMContext, lang: str) -> None:
    lat, lon = message.location.latitude, message.location.longitude
    city = await reverse_city(session, lat, lon)
    await state.update_data(bk_lat=lat, bk_lon=lon, bk_address=t("booking.gps_address", lang, city=city or "GPS"))
    await state.set_state(None)
    await message.answer("📍 ✅", reply_markup=REMOVE_KB)
    await _confirm_screen(message, session, state, lang)


@router.message(StateFilter(BookingFlow.address), F.text)
async def address_text(message: Message, session: AsyncSession, state: FSMContext, lang: str) -> None:
    text = message.text.strip()
    if len(text) < 5:
        await message.answer(t("booking.address_invalid", lang))
        return
    point = await geocode(session, text)
    await state.update_data(bk_address=text[:255], bk_lat=point.lat if point else None,
                            bk_lon=point.lon if point else None)
    await state.set_state(None)
    await message.answer("🏠 ✅", reply_markup=REMOVE_KB)
    await _confirm_screen(message, session, state, lang)


async def _confirm_screen(message: Message, session: AsyncSession, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    svc = await _service(session, data["bk_service"])
    pro = await pro_service.get_public_pro(session, svc.professional_id)
    start = _from_epoch_min(data["bk_start"])
    lines = [t("booking.confirm_title", lang), "",
             f"🏷 <b>{escape_html(pro.business_name)}</b>",
             f"💼 {escape_html(svc.name)} · {svc.duration_min} min",
             f"💶 {format_price(svc.price_cents, svc.price_type.value)}",
             f"🗓 {fmt_dt(start, pro.timezone, lang)}" if not data.get("bk_urgent") else "🚨 " + t("booking.urgent", lang)]
    if data.get("bk_address"):
        lines.append(f"🏠 {escape_html(data['bk_address'])}")
    elif pro.address:
        lines.append(f"📍 {escape_html(pro.address)}, {escape_html(pro.city or '')}")
    if data.get("bk_note"):
        lines.append(f"📝 {escape_html(data['bk_note'])}")
    lines.append("")
    lines.append(t("booking.auto_confirm" if pro.auto_confirm and not data.get("bk_urgent")
                   else "booking.manual_confirm", lang))
    if pro.category and pro.category.is_health:
        lines.append("<i>" + t("booking.health_note", lang) + "</i>")
    await message.answer("\n".join(lines), reply_markup=kb(
        [btn(t("btn.confirm_booking", lang), "bc")],
        [btn(t("btn.add_note", lang), "bn"), btn(t("btn.cancel", lang), "menu:main")]))


@router.callback_query(F.data == "bn")
async def add_note(cb: CallbackQuery, state: FSMContext, lang: str) -> None:
    await cb.answer()
    await state.set_state(BookingFlow.note)
    await cb.message.answer(t("booking.ask_note", lang))


@router.message(StateFilter(BookingFlow.note), F.text)
async def note_text(message: Message, session: AsyncSession, state: FSMContext, lang: str) -> None:
    await state.update_data(bk_note=message.text[:500])
    await state.set_state(None)
    await _confirm_screen(message, session, state, lang)


@router.callback_query(F.data == "bc")
async def confirm_booking(cb: CallbackQuery, session: AsyncSession, user: User, lang: str, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get("bk_service"):
        await cb.answer(t("search.expired", lang), show_alert=True)
        return
    svc = await _service(session, data["bk_service"])
    try:
        booking = await booking_service.create_booking(
            session, user, svc.professional_id, svc.id, _from_epoch_min(data["bk_start"]),
            address=data.get("bk_address"), lat=data.get("bk_lat"), lon=data.get("bk_lon"),
            client_note=data.get("bk_note"), is_urgent=bool(data.get("bk_urgent")), source="telegram",
        )
    except booking_service.BookingError as exc:
        await cb.answer()
        await cb.message.answer(t(f"booking.err.{exc.code}", lang), reply_markup=kb(
            [btn(t("btn.other_slot", lang), f"bs:{svc.id}")], back_menu(lang)))
        return
    await state.update_data(bk_service=None, bk_start=None)
    await cb.answer("✅")
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    # The notification service already sent the detailed confirmation to the client.
    await cb.message.answer(t("booking.done", lang, ref=booking.reference), reply_markup=kb(
        [btn(t("menu.bookings", lang), "menu:bookings")], back_menu(lang)))


# ---------------------------------------------------------------------------
# My bookings
# ---------------------------------------------------------------------------
async def show_my_bookings(message: Message, session: AsyncSession, user: User, lang: str,
                           history: bool = False) -> None:
    items = await booking_service.list_client_bookings(session, user, upcoming=not history)
    if not items:
        await message.answer(t("bookings.none_history" if history else "bookings.none", lang), reply_markup=kb(
            [btn(t("btn.history", lang), "bk:history")] if not history else [], back_menu(lang)))
        return
    rows = []
    for b in items:
        label = f"{STATUS_ICONS.get(b.status.value, '')} {fmt_dt(b.start_at, b.professional.timezone, lang)} · " \
                f"{b.professional.business_name}"
        rows.append([btn(label[:60], f"bk:view:{b.id}")])
    if not history:
        rows.append([btn(t("btn.history", lang), "bk:history")])
    rows.append(back_menu(lang))
    await message.answer(t("bookings.history" if history else "bookings.title", lang), reply_markup=kb(*rows))


@router.callback_query(F.data == "menu:bookings")
async def my_bookings(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    await cb.answer()
    await show_my_bookings(cb.message, session, user, lang)


@router.callback_query(F.data == "bk:history")
async def my_history(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    await cb.answer()
    await show_my_bookings(cb.message, session, user, lang, history=True)


@router.callback_query(F.data.startswith("bk:view:"))
async def view_booking(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    await cb.answer()
    b = await booking_service.load_booking(session, cb.data.split(":", 2)[2])
    if b is None or b.client_id != user.id:
        await cb.message.answer(t("bookings.not_found", lang))
        return
    rows = []
    if b.status.value in ("pending", "confirmed") and b.start_at > datetime.now(UTC):
        rows.append([btn(t("btn.reschedule", lang), f"rs:{b.id}"), btn(t("btn.cancel_booking", lang),
                                                                        f"bk:cancel:{b.id}")])
    if b.status.value == "completed":
        reviewed = (await session.execute(select(Review.id).where(Review.booking_id == b.id))).first()
        if not reviewed:
            rows.append([btn(f"{'⭐' * n}", f"rv:rate:{b.id}:{n}") for n in range(1, 6)])
    rows.append([btn(t("btn.contact", lang), f"msg:cli:{b.professional_id}"),
                 btn(t("btn.profile", lang), f"pro:view:{b.professional_id}")])
    rows.append([btn(t("btn.back", lang), "menu:bookings")])
    await cb.message.answer(booking_text(b, lang), reply_markup=kb(*rows))


@router.callback_query(F.data.startswith("bk:cancel:"))
async def cancel_ask(cb: CallbackQuery, lang: str) -> None:
    await cb.answer()
    bid = cb.data.split(":", 2)[2]
    await cb.message.answer(t("bookings.cancel_confirm", lang), reply_markup=kb(
        [btn(t("btn.yes_cancel", lang), f"bk:cancelyes:{bid}"), btn(t("btn.no", lang), f"bk:view:{bid}")]))


@router.callback_query(F.data.startswith("bk:cancelyes:"))
async def cancel_do(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    b = await booking_service.load_booking(session, cb.data.split(":", 2)[2])
    if b is None:
        await cb.answer()
        return
    try:
        await booking_service.cancel_booking(session, b, user, t("bookings.cancelled_by_client", lang))
    except booking_service.BookingError as exc:
        await cb.answer(t(f"booking.err.{exc.code}", lang), show_alert=True)
        return
    await cb.answer("✅")
    await cb.message.edit_text(t("bookings.cancelled", lang, ref=b.reference), reply_markup=kb(back_menu(lang)))


# ---------------------------------------------------------------------------
# Reschedule
# ---------------------------------------------------------------------------
async def _reschedule_calendar(message: Message, session: AsyncSession, user: User, lang: str, bid: str,
                               offset: int, edit: bool) -> None:
    b = await booking_service.load_booking(session, bid)
    if b is None or b.client_id != user.id:
        return
    duration = int((b.end_at - b.start_at).total_seconds() // 60)
    start_day = datetime.now(UTC).date() + timedelta(days=offset)
    days = await _days_with_slots(session, b.professional, duration, start_day, exclude_booking_id=b.id)
    markup = calendar_kb(b.service or Service(id=0), days, start_day, lang, prefix="rsd", ref=str(b.id),
                         page_prefix="rsw")
    text = t("booking.reschedule_title", lang, current=fmt_dt(b.start_at, b.professional.timezone, lang))
    if edit:
        try:
            await message.edit_text(text, reply_markup=markup)
            return
        except Exception:
            pass
    await message.answer(text, reply_markup=markup)


@router.callback_query(F.data.startswith("rs:"))
async def reschedule(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    await cb.answer()
    await _reschedule_calendar(cb.message, session, user, lang, cb.data[3:], 0, edit=False)


@router.callback_query(F.data.startswith("rsw:"))
async def reschedule_page(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    await cb.answer()
    _, bid, offset = cb.data.split(":")
    await _reschedule_calendar(cb.message, session, user, lang, bid, int(offset), edit=True)


@router.callback_query(F.data.startswith("rsd:"))
async def reschedule_day(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    await cb.answer()
    _, bid, ymd = cb.data.split(":")
    b = await booking_service.load_booking(session, bid)
    if b is None or b.client_id != user.id:
        return
    duration = int((b.end_at - b.start_at).total_seconds() // 60)
    start, end = availability.local_day_window(datetime.strptime(ymd, "%Y%m%d").date(), b.professional.timezone)
    slots = await availability.get_slots(session, b.professional, duration, start, end, exclude_booking_id=b.id)
    await cb.message.edit_text(t("booking.choose_new_time", lang),
                               reply_markup=slots_kb(slots, b.professional.timezone, bid, lang, prefix="rst",
                                                     back=f"rs:{bid}"))


@router.callback_query(F.data.startswith("rst:"))
async def reschedule_slot(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    await cb.answer()
    _, bid, epoch = cb.data.split(":")
    b = await booking_service.load_booking(session, bid)
    if b is None:
        return
    await cb.message.edit_text(
        t("booking.reschedule_confirm", lang, when=fmt_dt(_from_epoch_min(epoch), b.professional.timezone, lang)),
        reply_markup=kb([btn(t("btn.confirm", lang), f"rsc:{bid}:{epoch}"), btn(t("btn.back", lang), f"rs:{bid}")]))


@router.callback_query(F.data.startswith("rsc:"))
async def reschedule_do(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    _, bid, epoch = cb.data.split(":")
    b = await booking_service.load_booking(session, bid)
    if b is None:
        await cb.answer()
        return
    try:
        b = await booking_service.reschedule_booking(session, b, user, _from_epoch_min(epoch))
    except booking_service.BookingError as exc:
        await cb.answer(t(f"booking.err.{exc.code}", lang), show_alert=True)
        return
    await cb.answer("✅")
    await cb.message.edit_text(t("booking.rescheduled", lang) + "\n\n" + booking_text(b, lang),
                               reply_markup=kb(back_menu(lang)))


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------
@router.callback_query(F.data.startswith("rv:rate:"))
async def rate(cb: CallbackQuery, session: AsyncSession, user: User, lang: str, state: FSMContext) -> None:
    _, _, bid, n = cb.data.split(":")
    try:
        review = await review_service.create_review(session, user, bid, int(n))
    except review_service.ReviewError as exc:
        await cb.answer(t(f"review.err.{exc}", lang), show_alert=True)
        return
    await cb.answer("⭐" * int(n))
    await state.set_state(ReviewFlow.comment)
    await state.update_data(review_id=review.id)
    await cb.message.answer(t("review.ask_comment", lang), reply_markup=kb([btn(t("btn.skip", lang), "rv:skip")]))


@router.callback_query(F.data == "rv:skip")
async def review_skip(cb: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.set_state(None)
    await cb.answer()
    await cb.message.answer(t("review.thanks", lang), reply_markup=kb(back_menu(lang)))


@router.message(StateFilter(ReviewFlow.comment), F.text)
async def review_comment(message: Message, session: AsyncSession, user: User, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    await state.set_state(None)
    review = await review_service.update_comment(session, user, data["review_id"], message.text)
    key = "review.thanks_moderation" if review.status.value == "pending" else "review.thanks"
    await message.answer(t(key, lang), reply_markup=kb(back_menu(lang)))


@router.message(StateFilter(ReviewFlow.comment), F.photo)
async def review_photo(message: Message, session: AsyncSession, user: User, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    review = await session.get(Review, data["review_id"])
    if review and review.client_id == user.id and len(review.photos or []) < 5:
        review.photos = [*(review.photos or []), message.photo[-1].file_id]
        await session.commit()
    if message.caption:
        await review_service.update_comment(session, user, data["review_id"], message.caption)
    await message.answer(t("review.photo_added", lang), reply_markup=kb([btn(t("btn.done", lang), "rv:skip")]))
