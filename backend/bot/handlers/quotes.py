"""Quote requests: client publication & comparison, professional answers."""
from __future__ import annotations

import json
import re

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.i18n import t
from app.models import Category, Professional, Urgency, User
from app.services import professionals as pro_service
from app.services import quotes as quote_service
from app.services.ai import assistant
from app.services.ai.intent import SearchIntent
from app.services.geo import geocode, reverse_city
from app.services.text import escape_html, format_price, stars, truncate
from bot.states import ProEdit, QuoteFlow
from bot.ui import REMOVE_KB, back_menu, btn, category_name, chunk, kb, location_request_kb

router = Router(name="quotes")
AMOUNT_RE = re.compile(r"(\d+(?:[.,]\d{1,2})?)")


def _parse_amount(text: str) -> int | None:
    m = AMOUNT_RE.search(text.replace(" ", ""))
    return int(round(float(m.group(1).replace(",", ".")) * 100)) if m else None


# ---------------------------------------------------------------------------
# Client side
# ---------------------------------------------------------------------------
@router.callback_query(F.data == "menu:quote")
async def quote_start(cb: CallbackQuery, state: FSMContext, lang: str) -> None:
    await cb.answer()
    await state.set_state(QuoteFlow.description)
    await state.update_data(q_category=None, q_target=None, q_city=None, q_lat=None, q_lon=None, q_postal=None)
    await cb.message.answer(t("quote.ask_description", lang), reply_markup=kb([btn(t("btn.cancel", lang), "menu:main")]))


@router.callback_query(F.data == "quote:fromsearch")
async def quote_from_search(cb: CallbackQuery, session: AsyncSession, state: FSMContext, user: User, lang: str) -> None:
    await cb.answer()
    data = await state.get_data()
    cat_id, city, lat, lon = None, None, None, None
    if data.get("intent"):
        intent = SearchIntent(**json.loads(data["intent"]))
        resolved = await assistant.intent_to_query(session, intent, user)
        cat_id = resolved.category.id if resolved.category else None
        if resolved.location:
            city, lat, lon = resolved.location.label, resolved.location.lat, resolved.location.lon
    await state.set_state(QuoteFlow.description)
    await state.update_data(q_category=cat_id, q_target=None, q_city=city, q_lat=lat, q_lon=lon, q_postal=None)
    await cb.message.answer(t("quote.ask_description", lang), reply_markup=kb([btn(t("btn.cancel", lang), "menu:main")]))


@router.callback_query(F.data.startswith("quote:pro:"))
async def quote_to_pro(cb: CallbackQuery, session: AsyncSession, state: FSMContext, lang: str) -> None:
    await cb.answer()
    pro = await session.get(Professional, int(cb.data.split(":")[2]))
    if pro is None:
        return
    await state.set_state(QuoteFlow.description)
    await state.update_data(q_category=pro.category_id, q_target=pro.id, q_city=None, q_lat=None, q_lon=None,
                            q_postal=None)
    await cb.message.answer(t("quote.ask_description_pro", lang, name=escape_html(pro.business_name)),
                            reply_markup=kb([btn(t("btn.cancel", lang), "menu:main")]))


@router.message(StateFilter(QuoteFlow.description), F.text)
async def quote_description(message: Message, session: AsyncSession, state: FSMContext, user: User, lang: str) -> None:
    if len(message.text.strip()) < 10:
        await message.answer(t("quote.description_short", lang))
        return
    await state.update_data(q_description=message.text.strip()[:4000])
    data = await state.get_data()
    if not data.get("q_category"):
        intent = await assistant.understand(session, message.text)
        if intent.category_slug:
            cat = (await session.execute(select(Category).where(Category.slug == intent.category_slug))).scalar_one()
            await state.update_data(q_category=cat.id)
        if intent.location_text and not data.get("q_city"):
            point = await geocode(session, intent.location_text)
            if point:
                await state.update_data(q_city=point.label, q_lat=point.lat, q_lon=point.lon,
                                        q_postal=point.postal_code)
    data = await state.get_data()
    if not data.get("q_category"):
        await _ask_category(message, session, lang, None)
        return
    cat = await session.get(Category, data["q_category"])
    await state.set_state(QuoteFlow.category)
    await message.answer(t("quote.confirm_category", lang, name=category_name(cat, lang)), reply_markup=kb(
        [btn(t("btn.yes", lang), "qc:ok"), btn(t("btn.change", lang), "qc:root")]))


async def _ask_category(message: Message, session: AsyncSession, lang: str, parent_id: int | None) -> None:
    q = select(Category).where(Category.is_active.is_(True))
    q = q.where(Category.parent_id.is_(None)) if parent_id is None else q.where(Category.parent_id == parent_id)
    cats = (await session.execute(q.order_by(Category.sort_order))).scalars().all()
    rows = chunk([btn(category_name(c, lang), f"qc:{c.id}") for c in cats], 2)
    rows.append([btn(t("btn.cancel", lang), "menu:main")])
    await message.answer(t("quote.choose_category", lang), reply_markup=kb(*rows))


@router.callback_query(F.data.startswith("qc:"))
async def quote_category(cb: CallbackQuery, session: AsyncSession, state: FSMContext, user: User, lang: str) -> None:
    await cb.answer()
    value = cb.data.split(":")[1]
    if value == "root":
        await _ask_category(cb.message, session, lang, None)
        return
    if value != "ok":
        cat_id = int(value)
        has_children = (await session.execute(select(Category.id).where(Category.parent_id == cat_id))).first()
        if has_children:
            await _ask_category(cb.message, session, lang, cat_id)
            return
        await state.update_data(q_category=cat_id)
    data = await state.get_data()
    if data.get("q_city"):
        await _ask_budget(cb.message, state, lang)
        return
    await state.set_state(QuoteFlow.location)
    await cb.message.answer(t("quote.ask_location", lang), reply_markup=location_request_kb(lang))


@router.message(StateFilter(QuoteFlow.location), F.location)
async def quote_location_gps(message: Message, session: AsyncSession, state: FSMContext, lang: str) -> None:
    lat, lon = message.location.latitude, message.location.longitude
    await state.update_data(q_lat=lat, q_lon=lon, q_city=await reverse_city(session, lat, lon))
    await message.answer("📍 ✅", reply_markup=REMOVE_KB)
    await _ask_budget(message, state, lang)


@router.message(StateFilter(QuoteFlow.location), F.text)
async def quote_location_text(message: Message, session: AsyncSession, state: FSMContext, lang: str) -> None:
    point = await geocode(session, message.text)
    if point is None:
        await message.answer(t("loc.unknown", lang))
        return
    await state.update_data(q_lat=point.lat, q_lon=point.lon, q_city=point.label, q_postal=point.postal_code)
    await message.answer("📍 ✅", reply_markup=REMOVE_KB)
    await _ask_budget(message, state, lang)


async def _ask_budget(message: Message, state: FSMContext, lang: str) -> None:
    await state.set_state(QuoteFlow.budget)
    await message.answer(t("quote.ask_budget", lang), reply_markup=kb(
        [btn("< 500 €", "qb:50000"), btn("500–2 000 €", "qb:200000"), btn("2 000–10 000 €", "qb:1000000")],
        [btn("> 10 000 €", "qb:5000000"), btn(t("btn.skip", lang), "qb:0")]))


@router.callback_query(StateFilter(QuoteFlow.budget), F.data.startswith("qb:"))
async def quote_budget_btn(cb: CallbackQuery, state: FSMContext, lang: str) -> None:
    await cb.answer()
    value = int(cb.data.split(":")[1])
    await state.update_data(q_budget=value or None)
    await _ask_urgency(cb.message, state, lang)


@router.message(StateFilter(QuoteFlow.budget), F.text)
async def quote_budget_text(message: Message, state: FSMContext, lang: str) -> None:
    await state.update_data(q_budget=_parse_amount(message.text))
    await _ask_urgency(message, state, lang)


async def _ask_urgency(message: Message, state: FSMContext, lang: str) -> None:
    await state.set_state(QuoteFlow.urgency)
    await message.answer(t("quote.ask_urgency", lang), reply_markup=kb(
        [btn(t("urgency.urgent", lang), "qu:urgent"), btn(t("urgency.this_week", lang), "qu:this_week")],
        [btn(t("urgency.this_month", lang), "qu:this_month"), btn(t("urgency.flexible", lang), "qu:flexible")]))


@router.callback_query(StateFilter(QuoteFlow.urgency), F.data.startswith("qu:"))
async def quote_submit(cb: CallbackQuery, session: AsyncSession, state: FSMContext, user: User, lang: str) -> None:
    data = await state.get_data()
    await state.set_state(None)
    try:
        req, n = await quote_service.create_request(
            session, user, data["q_category"], data["q_description"], city=data.get("q_city"),
            postal_code=data.get("q_postal"), lat=data.get("q_lat"), lon=data.get("q_lon"),
            budget_cents=data.get("q_budget"), urgency=Urgency(cb.data.split(":")[1]),
            target_pro_id=data.get("q_target"))
    except quote_service.QuoteError as exc:
        await cb.answer()
        await cb.message.answer(t(f"quote.err.{exc}", lang), reply_markup=kb(back_menu(lang)))
        return
    await cb.answer("✅")
    key = "quote.sent" if n else "quote.sent_none"
    await cb.message.answer(t(key, lang, n=n), reply_markup=kb(
        [btn(t("menu.my_quotes", lang), "menu:my_quotes")], back_menu(lang)))


@router.callback_query(F.data == "menu:my_quotes")
async def my_quotes(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    await cb.answer()
    reqs = await quote_service.list_client_requests(session, user)
    if not reqs:
        await cb.message.answer(t("quote.none", lang), reply_markup=kb(
            [btn(t("menu.quote", lang), "menu:quote")], back_menu(lang)))
        return
    rows = [[btn(f"{t('qstatus.' + r.status.value, lang)} · {truncate(r.description, 30)} ({len(r.quotes)})",
                 f"qr:view:{r.id}")] for r in reqs]
    rows.append(back_menu(lang))
    await cb.message.answer(t("quote.my_title", lang), reply_markup=kb(*rows))


@router.callback_query(F.data.startswith("qr:view:"))
async def view_request(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    await cb.answer()
    req = await quote_service.get_request(session, int(cb.data.split(":")[2]))
    if req is None or req.client_id != user.id:
        return
    lines = [t("quote.request_title", lang, status=t("qstatus." + req.status.value, lang)),
             f"{category_name(req.category, lang)} · {escape_html(req.city or '-')}",
             f"<i>{escape_html(truncate(req.description, 400))}</i>",
             t("quote.recipients", lang, n=len(req.recipients)), ""]
    rows = []
    quotes = sorted(req.quotes, key=lambda q: q.amount_cents)
    if not quotes:
        lines.append(t("quote.no_offers_yet", lang))
    for i, q in enumerate(quotes, 1):
        p = q.professional
        lines.append(f"<b>{i}. {escape_html(p.business_name)}</b>{' ✅' if p.is_verified else ''} — "
                     f"<b>{format_price(q.amount_cents)}</b> · {stars(p.rating_avg, p.rating_count)}"
                     + (f" · {q.estimated_days} j" if q.estimated_days else "")
                     + f" · {t('quote.status.' + q.status.value, lang)}")
        if q.message:
            lines.append(f"   <i>{escape_html(truncate(q.message, 200))}</i>")
        row = [btn(t("btn.profile", lang) + f" {i}", f"pro:view:{p.id}"),
               btn(t("btn.contact", lang) + f" {i}", f"msg:cli:{p.id}")]
        if req.status.value == "open" and q.status.value == "sent":
            row.append(btn(t("btn.accept", lang) + f" {i}", f"qa:{q.id}"))
        rows.append(row)
    if req.status.value == "open":
        rows.append([btn(t("btn.close_request", lang), f"qx:{req.id}")])
    rows.append([btn(t("btn.back", lang), "menu:my_quotes")])
    await cb.message.answer("\n".join(lines)[:4000], reply_markup=kb(*rows))


@router.callback_query(F.data.startswith("qa:"))
async def accept_quote(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    try:
        quote = await quote_service.accept_quote(session, user, int(cb.data.split(":")[1]))
    except quote_service.QuoteError as exc:
        await cb.answer(t(f"quote.err.{exc}", lang), show_alert=True)
        return
    await cb.answer("✅")
    await cb.message.answer(t("quote.accepted", lang, name=escape_html(quote.professional.business_name)),
                            reply_markup=kb([btn(t("btn.contact", lang), f"msg:cli:{quote.professional_id}")],
                                            back_menu(lang)))


@router.callback_query(F.data.startswith("qx:"))
async def close_request(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    await quote_service.cancel_request(session, user, int(cb.data.split(":")[1]))
    await cb.answer("✅")
    await cb.message.answer(t("quote.closed", lang), reply_markup=kb(back_menu(lang)))


# ---------------------------------------------------------------------------
# Professional side
# ---------------------------------------------------------------------------
@router.callback_query(F.data.startswith("pq:answer:"))
async def pro_answer(cb: CallbackQuery, session: AsyncSession, user: User, lang: str, state: FSMContext) -> None:
    await cb.answer()
    pro = await pro_service.get_pro_for_user(session, user)
    req = await quote_service.get_request(session, int(cb.data.split(":")[2]))
    if pro is None or req is None:
        return
    await state.set_state(ProEdit.quote_amount)
    await state.update_data(pq_request=req.id)
    await cb.message.answer(t("pq.ask_amount", lang, desc=escape_html(truncate(req.description, 300))))


@router.message(StateFilter(ProEdit.quote_amount), F.text)
async def pro_amount(message: Message, state: FSMContext, lang: str) -> None:
    amount = _parse_amount(message.text)
    if not amount:
        await message.answer(t("pq.invalid_amount", lang))
        return
    await state.update_data(pq_amount=amount)
    await state.set_state(ProEdit.quote_message)
    await message.answer(t("pq.ask_message", lang), reply_markup=kb([btn(t("btn.skip", lang), "pq:nomsg")]))


async def _submit(target: Message, session: AsyncSession, user: User, state: FSMContext, lang: str,
                  text: str | None) -> None:
    data = await state.get_data()
    await state.set_state(None)
    pro = await pro_service.get_pro_for_user(session, user)
    try:
        await quote_service.submit_quote(session, pro, data["pq_request"], data["pq_amount"], text)
    except quote_service.QuoteError as exc:
        await target.answer(t(f"quote.err.{exc}", lang))
        return
    await target.answer(t("pq.sent", lang), reply_markup=kb([btn(t("btn.pro_space", lang), "pd:home")]))


@router.message(StateFilter(ProEdit.quote_message), F.text)
async def pro_message(message: Message, session: AsyncSession, user: User, state: FSMContext, lang: str) -> None:
    await _submit(message, session, user, state, lang, message.text)


@router.callback_query(F.data == "pq:nomsg")
async def pro_nomsg(cb: CallbackQuery, session: AsyncSession, user: User, state: FSMContext, lang: str) -> None:
    await cb.answer()
    await _submit(cb.message, session, user, state, lang, None)


@router.callback_query(F.data.startswith("pq:decline:"))
async def pro_decline(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    pro = await pro_service.get_pro_for_user(session, user)
    if pro:
        try:
            await quote_service.decline_request(session, pro, int(cb.data.split(":")[2]))
        except quote_service.QuoteError:
            pass
    await cb.answer("👌")
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
