"""Search: AI free text, categories, 'available now', nearby, profiles, favorites."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.i18n import t
from app.models import Category, User
from app.services import availability
from app.services import professionals as pro_service
from app.services import search as search_service
from app.services import users as user_service
from app.services.ai import assistant
from app.services.ai.intent import SearchIntent
from app.services.text import escape_html
from bot.states import LocationInput
from bot.ui import (
    availability_presets_kb,
    back_menu,
    btn,
    category_name,
    chunk,
    kb,
    location_request_kb,
    pro_profile_kb,
    pro_profile_text,
    result_card,
    result_kb,
)

router = Router(name="search")
UTC = timezone.utc
PAGE_SIZE = 5


async def _save_intent(state: FSMContext, intent: SearchIntent, offset: int = 0, sort: str | None = None) -> None:
    await state.update_data(intent=intent.model_dump_json(), offset=offset, sort=sort)


async def _load_intent(state: FSMContext) -> SearchIntent | None:
    data = await state.get_data()
    raw = data.get("intent")
    return SearchIntent(**json.loads(raw)) if raw else None


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------
@router.callback_query(F.data == "menu:search")
async def search_prompt(cb: CallbackQuery, state: FSMContext, lang: str) -> None:
    await cb.answer()
    await state.update_data(intent=None)
    await cb.message.answer(t("search.prompt", lang), reply_markup=kb(
        [btn(t("menu.categories", lang), "cat:root"), btn(t("menu.now", lang), "menu:now")], back_menu(lang)))


@router.message(StateFilter(None), F.text & ~F.text.startswith("/"))
async def free_text(message: Message, session: AsyncSession, user: User, lang: str, state: FSMContext) -> None:
    """Natural-language entry point: the AI only extracts constraints, the DB answers."""
    await message.bot.send_chat_action(message.chat.id, "typing")
    previous = await _load_intent(state)
    intent = await assistant.understand(session, message.text, previous)
    if intent.intent == "my_bookings":
        from bot.handlers.booking import show_my_bookings

        await show_my_bookings(message, session, user, lang)
        return
    if intent.intent in ("greeting", "help"):
        await message.answer(t("search.greeting", lang), reply_markup=kb(
            [btn(t("menu.categories", lang), "cat:root"), btn(t("menu.now", lang), "menu:now")], back_menu(lang)))
        return
    if intent.intent == "other" or intent.is_empty:
        await message.answer(t("search.not_understood", lang), reply_markup=kb(
            [btn(t("menu.categories", lang), "cat:root")], back_menu(lang)))
        return
    await run_search(message, session, user, lang, state, intent)


async def run_search(message: Message, session: AsyncSession, user: User, lang: str, state: FSMContext,
                     intent: SearchIntent, offset: int = 0, sort: str | None = None) -> None:
    resolved = await assistant.intent_to_query(session, intent, user)
    await _save_intent(state, intent, offset, sort)
    if resolved.location_unknown:
        await message.answer(t("search.location_unknown", lang, place=escape_html(resolved.location_unknown)))
    needs_location = resolved.location is None and (intent.at_client or intent.urgent or intent.use_my_location
                                                     or intent.availability)
    if needs_location:
        await state.set_state(LocationInput.waiting)
        await message.answer(t("search.need_location", lang), reply_markup=location_request_kb(lang))
        return
    q = resolved.query
    q.limit, q.offset = PAGE_SIZE, offset
    if sort:
        q.sort = sort
    response = await search_service.search(session, q)
    summary = assistant.describe(intent, resolved, lang)
    if not response.results:
        rows = [[btn(t("btn.widen_radius", lang), "sr:widen")]] if resolved.location else []
        if intent.date_from or intent.availability:
            rows.append([btn(t("btn.any_date", lang), "sr:anydate")])
        if resolved.category and resolved.category.supports_quotes:
            rows.append([btn(t("btn.ask_quote", lang), "quote:fromsearch")])
        rows.append(back_menu(lang))
        await message.answer(t("search.no_results", lang, summary=summary), reply_markup=kb(*rows))
        return
    if offset == 0:
        head = t("search.understood", lang, summary=summary, total=response.total)
        if resolved.location is None:
            head += "\n" + t("search.tip_location", lang)
        await message.answer(head)
    for r in response.results:
        pro = r.professional
        text = result_card(r, lang)
        markup = result_kb(r, lang)
        if pro.logo_file_id:
            try:
                await message.answer_photo(pro.logo_file_id, caption=text, reply_markup=markup)
                continue
            except Exception:
                pass
        await message.answer(text, reply_markup=markup, disable_web_page_preview=True)
    rows = []
    if offset + PAGE_SIZE < response.total:
        rows.append([btn(t("btn.more_results", lang, n=response.total - offset - PAGE_SIZE),
                         f"sr:more:{offset + PAGE_SIZE}")])
    rows.append([btn(t("sort.distance", lang), "sr:sort:distance"), btn(t("sort.rating", lang), "sr:sort:rating"),
                 btn(t("sort.price", lang), "sr:sort:price"), btn(t("sort.soonest", lang), "sr:sort:soonest")])
    if intent.quote_suggested and resolved.category and resolved.category.supports_quotes:
        rows.append([btn(t("btn.ask_quote", lang), "quote:fromsearch")])
    rows.append(back_menu(lang))
    await message.answer(t("search.refine_tip", lang), reply_markup=kb(*rows))


@router.callback_query(F.data.startswith("sr:"))
async def search_nav(cb: CallbackQuery, session: AsyncSession, user: User, lang: str, state: FSMContext) -> None:
    intent = await _load_intent(state)
    await cb.answer()
    if intent is None:
        await cb.message.answer(t("search.expired", lang))
        return
    data = await state.get_data()
    parts = cb.data.split(":")
    if parts[1] == "more":
        await run_search(cb.message, session, user, lang, state, intent, int(parts[2]), data.get("sort"))
    elif parts[1] == "sort":
        await run_search(cb.message, session, user, lang, state, intent, 0, parts[2])
    elif parts[1] == "widen":
        intent.radius_km = min(50, (intent.radius_km or user.search_radius_km or 10) * 2 + 5)
        await run_search(cb.message, session, user, lang, state, intent)
    elif parts[1] == "anydate":
        intent.date_from = intent.date_to = intent.availability = None
        intent.time_from = intent.time_to = None
        await run_search(cb.message, session, user, lang, state, intent)


# ---------------------------------------------------------------------------
# Available now
# ---------------------------------------------------------------------------
@router.callback_query(F.data == "menu:now")
async def now_menu(cb: CallbackQuery, lang: str) -> None:
    await cb.answer()
    await cb.message.answer(t("now.title", lang), reply_markup=availability_presets_kb(lang))


@router.callback_query(F.data.startswith("now:"))
async def now_search(cb: CallbackQuery, session: AsyncSession, user: User, lang: str, state: FSMContext) -> None:
    await cb.answer()
    preset = cb.data.split(":")[1]
    previous = await _load_intent(state) or SearchIntent()
    intent = previous.merged_with(SearchIntent(availability=preset, urgent=preset == "now"))
    intent.date_from = intent.date_to = None
    if user.last_lat is not None:
        intent.use_my_location = True
    await run_search(cb.message, session, user, lang, state, intent)


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------
@router.callback_query(F.data == "cat:root")
async def categories_root(cb: CallbackQuery, session: AsyncSession, lang: str, edit: bool = False) -> None:
    await cb.answer()
    roots = (await session.execute(select(Category).where(Category.parent_id.is_(None), Category.is_active.is_(True))
                                   .order_by(Category.sort_order))).scalars().all()
    rows = chunk([btn(category_name(c, lang), f"cat:{c.id}") for c in roots], 2)
    rows.append(back_menu(lang))
    text = t("cat.choose", lang)
    try:
        await cb.message.edit_text(text, reply_markup=kb(*rows))
    except Exception:
        await cb.message.answer(text, reply_markup=kb(*rows))


@router.callback_query(F.data.regexp(r"^cat:\d+$"))
async def category_pick(cb: CallbackQuery, session: AsyncSession, user: User, lang: str, state: FSMContext) -> None:
    cat_id = int(cb.data.split(":")[1])
    cat = await session.get(Category, cat_id)
    if cat is None:
        await cb.answer()
        return
    children = (await session.execute(select(Category).where(Category.parent_id == cat.id,
                                                             Category.is_active.is_(True))
                                      .order_by(Category.sort_order))).scalars().all()
    await cb.answer()
    if children:
        rows = chunk([btn(category_name(c, lang), f"cat:{c.id}") for c in children], 2)
        rows.append([btn(t("cat.all_of", lang, name=cat.name(lang)), f"catall:{cat.id}")])
        rows.append([btn(t("btn.back", lang), "cat:root")])
        await cb.message.edit_text(t("cat.choose_sub", lang, name=category_name(cat, lang)), reply_markup=kb(*rows))
        return
    await _search_category(cb, session, user, lang, state, cat)


@router.callback_query(F.data.startswith("catall:"))
async def category_all(cb: CallbackQuery, session: AsyncSession, user: User, lang: str, state: FSMContext) -> None:
    await cb.answer()
    cat = await session.get(Category, int(cb.data.split(":")[1]))
    if cat:
        await _search_category(cb, session, user, lang, state, cat)


async def _search_category(cb: CallbackQuery, session: AsyncSession, user: User, lang: str, state: FSMContext,
                           cat: Category) -> None:
    previous = await _load_intent(state)
    intent = SearchIntent(category_slug=cat.slug, use_my_location=user.last_lat is not None)
    if previous and previous.availability:  # coming from "available now"
        intent.availability = previous.availability
        intent.urgent = previous.urgent
    intent.at_client = True if cat.default_work_mode.value == "mobile" else None
    await run_search(cb.message, session, user, lang, state, intent)


# ---------------------------------------------------------------------------
# Professional profile
# ---------------------------------------------------------------------------
async def send_profile(message: Message, session: AsyncSession, user: User, lang: str, pro_id: int) -> None:
    pro = await pro_service.get_public_pro(session, pro_id)
    if pro is None or (pro.status.value != "active" and pro.user_id != user.id and not user.is_admin):
        await message.answer(t("pro.not_found", lang))
        return
    reviews = await pro_service.published_reviews(session, pro.id, 3)
    now = datetime.now(UTC)
    services = [s for s in pro.services if s.is_active]
    slots = []
    if services:
        shortest = min(services, key=lambda s: s.duration_min)
        slots = await availability.get_slots(session, pro, shortest.duration_min, now, now + timedelta(days=14),
                                             limit=4)
    fav = await user_service.is_favorite(session, user, pro.id)
    text = pro_profile_text(pro, reviews, lang, slots, fav)
    markup = pro_profile_kb(pro, lang, fav, bool(pro.photos))
    if pro.logo_file_id and len(text) <= 1024:
        try:
            await message.answer_photo(pro.logo_file_id, caption=text, reply_markup=markup)
            return
        except Exception:
            pass
    await message.answer(text, reply_markup=markup, disable_web_page_preview=True)


@router.callback_query(F.data.startswith("pro:view:"))
async def profile(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    await cb.answer()
    await send_profile(cb.message, session, user, lang, int(cb.data.split(":")[2]))


@router.callback_query(F.data.startswith("pro:reviews:"))
async def profile_reviews(cb: CallbackQuery, session: AsyncSession, lang: str) -> None:
    await cb.answer()
    pro_id = int(cb.data.split(":")[2])
    reviews = await pro_service.published_reviews(session, pro_id, 15)
    if not reviews:
        await cb.message.answer(t("reviews.none", lang))
        return
    lines = [t("card.reviews", lang)]
    for r in reviews:
        name = r.client.first_name if r.client and r.client.first_name else t("card.client", lang)
        lines.append(f"\n{'⭐' * r.rating} — {escape_html(name)}, {r.created_at:%d/%m/%Y}")
        if r.comment:
            lines.append(f"<i>{escape_html(r.comment[:400])}</i>")
        if r.pro_reply:
            lines.append(f"↳ {escape_html(r.pro_reply[:300])}")
    await cb.message.answer("\n".join(lines)[:4000], reply_markup=kb([btn(t("btn.back", lang), f"pro:view:{pro_id}")]))


@router.callback_query(F.data.startswith("pro:photos:"))
async def profile_photos(cb: CallbackQuery, session: AsyncSession, lang: str) -> None:
    await cb.answer()
    pro = await pro_service.get_public_pro(session, int(cb.data.split(":")[2]))
    if not pro or not pro.photos:
        return
    media = [InputMediaPhoto(media=p.file_id or p.url, caption=p.caption) for p in pro.photos[:10]
             if p.file_id or p.url]
    if media:
        await cb.message.answer_media_group(media)


# ---------------------------------------------------------------------------
# Favorites
# ---------------------------------------------------------------------------
@router.callback_query(F.data.startswith("fav:"))
async def toggle_fav(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    is_fav = await user_service.toggle_favorite(session, user, int(cb.data.split(":")[1]))
    await cb.answer(t("fav.added" if is_fav else "fav.removed", lang))


@router.callback_query(F.data == "menu:favorites")
async def favorites(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    await cb.answer()
    pros = await user_service.list_favorites(session, user)
    if not pros:
        await cb.message.answer(t("fav.none", lang), reply_markup=kb(back_menu(lang)))
        return
    rows = [[btn(f"❤️ {p.business_name}", f"pro:view:{p.id}")] for p in pros[:30]]
    rows.append(back_menu(lang))
    await cb.message.answer(t("fav.title", lang), reply_markup=kb(*rows))
