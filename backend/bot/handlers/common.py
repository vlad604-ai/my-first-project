"""/start, main menu, settings, location, privacy (RGPD)."""
from __future__ import annotations

import json

from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.i18n import t
from app.models import User
from app.services import professionals as pro_service
from app.services import users as user_service
from app.services.geo import geocode, reverse_city
from bot.states import LocationInput
from bot.ui import REMOVE_KB, back_menu, btn, kb, location_request_kb, main_menu, radius_kb

router = Router(name="common")


async def show_menu(target: Message | CallbackQuery, session: AsyncSession, user: User, lang: str,
                    edit: bool = False) -> None:
    pro = await pro_service.get_pro_for_user(session, user)
    from app.services.text import escape_html

    text = t("menu.title", lang, name=f" · {escape_html(user.first_name)}" if user.first_name else "")
    markup = main_menu(lang, pro is not None, user.is_admin)
    if isinstance(target, CallbackQuery):
        if edit and target.message:
            try:
                await target.message.edit_text(text, reply_markup=markup)
                return
            except Exception:
                pass
        await target.message.answer(text, reply_markup=markup)
    else:
        await target.answer(text, reply_markup=markup)


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, session: AsyncSession, user: User, lang: str,
                    state: FSMContext) -> None:
    await state.clear()
    if command.args and command.args.startswith("pro_") and command.args[4:].isdigit():
        from bot.handlers.search import send_profile

        await send_profile(message, session, user, lang, int(command.args[4:]))
        return
    if user.gdpr_consent_at is None:
        await message.answer(t("start.welcome", lang, app=settings.app_name), reply_markup=REMOVE_KB)
        await message.answer(t("start.privacy", lang),
                             reply_markup=kb([btn(t("btn.accept_privacy", lang), "gdpr:accept")]))
        return
    await show_menu(message, session, user, lang)


@router.callback_query(F.data == "gdpr:accept")
async def gdpr_accept(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    from datetime import datetime, timezone

    user.gdpr_consent_at = datetime.now(timezone.utc)
    await session.commit()
    await cb.answer()
    await cb.message.edit_text(t("start.privacy_ok", lang))
    await cb.message.answer(t("start.how_to", lang))
    await show_menu(cb, session, user, lang)


@router.message(Command("menu"))
@router.callback_query(F.data == "menu:main")
async def menu(event: Message | CallbackQuery, session: AsyncSession, user: User, lang: str,
               state: FSMContext) -> None:
    await state.set_state(None)
    if isinstance(event, CallbackQuery):
        await event.answer()
        await show_menu(event, session, user, lang, edit=True)
    else:
        await show_menu(event, session, user, lang)


@router.message(Command("help"))
async def cmd_help(message: Message, lang: str) -> None:
    await message.answer(t("help.text", lang), reply_markup=kb(back_menu(lang)))


@router.message(Command("cancel"))
@router.message(F.text.in_({"Annuler", "Cancel", "❌ Annuler", "❌ Cancel"}))
async def cmd_cancel(message: Message, state: FSMContext, session: AsyncSession, user: User, lang: str) -> None:
    await state.set_state(None)
    await message.answer(t("common.cancelled", lang), reply_markup=REMOVE_KB)
    await show_menu(message, session, user, lang)


@router.callback_query(F.data == "noop")
async def noop(cb: CallbackQuery) -> None:
    await cb.answer()


# ---------------------------------------------------------------------------
# Location
# ---------------------------------------------------------------------------
@router.callback_query(F.data == "menu:nearby")
async def nearby(cb: CallbackQuery, state: FSMContext, lang: str) -> None:
    await cb.answer()
    await state.set_state(LocationInput.waiting)
    await state.update_data(after_location="nearby", intent=None)
    await cb.message.answer(t("loc.ask", lang), reply_markup=location_request_kb(lang))


@router.message(StateFilter(None, LocationInput.waiting), F.location)
async def on_location(message: Message, session: AsyncSession, user: User, lang: str, state: FSMContext) -> None:
    # Other flows (booking address, quotes, pro onboarding) handle locations in their own states.
    lat, lon = message.location.latitude, message.location.longitude
    label = await reverse_city(session, lat, lon)
    await user_service.set_location(session, user, lat, lon, label)
    await _after_location(message, session, user, lang, state, label or t("search.my_position", lang))


@router.message(StateFilter(LocationInput.waiting), F.text)
async def on_location_text(message: Message, session: AsyncSession, user: User, lang: str, state: FSMContext
                           ) -> None:
    point = await geocode(session, message.text)
    if point is None:
        await message.answer(t("loc.unknown", lang))
        return
    await user_service.set_location(session, user, point.lat, point.lon, point.label)
    await _after_location(message, session, user, lang, state, point.label or message.text)


async def _after_location(message: Message, session: AsyncSession, user: User, lang: str, state: FSMContext,
                          label: str) -> None:
    data = await state.get_data()
    after = data.get("after_location")
    await state.set_state(None)
    await message.answer(t("loc.saved", lang, place=label), reply_markup=REMOVE_KB)
    if data.get("intent"):  # re-run the pending search with the new position
        from bot.handlers.search import run_search
        from app.services.ai.intent import SearchIntent

        intent = SearchIntent(**json.loads(data["intent"]))
        intent.location_text = None
        intent.use_my_location = True
        await run_search(message, session, user, lang, state, intent)
        return
    if after == "nearby":
        await message.answer(t("loc.choose_radius", lang), reply_markup=radius_kb(lang, user.search_radius_km))
    else:
        await show_menu(message, session, user, lang)


@router.callback_query(F.data.startswith("rad:"))
async def set_radius(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    user.search_radius_km = int(cb.data.split(":")[1])
    await session.commit()
    await cb.answer(t("loc.radius_set", lang, km=user.search_radius_km))
    from bot.handlers.search import categories_root

    await categories_root(cb, session, lang, edit=True)


# ---------------------------------------------------------------------------
# Settings & privacy
# ---------------------------------------------------------------------------
@router.callback_query(F.data == "menu:settings")
async def settings_menu(cb: CallbackQuery, user: User, lang: str) -> None:
    await cb.answer()
    place = user.last_city or (t("search.my_position", lang) if user.last_lat else t("settings.no_location", lang))
    await cb.message.edit_text(
        t("settings.title", lang, lang_name=t("lang.name", lang), place=place, km=user.search_radius_km),
        reply_markup=kb(
            [btn("🇫🇷 Français", "lang:fr"), btn("🇬🇧 English", "lang:en")],
            [btn(t("btn.change_location", lang), "menu:nearby"),
             btn(t("btn.radius", lang), "set:radius")],
            [btn(t("btn.export_data", lang), "gdpr:export"), btn(t("btn.delete_account", lang), "gdpr:delete")],
            back_menu(lang),
        ),
    )


@router.callback_query(F.data == "set:radius")
async def radius_menu(cb: CallbackQuery, user: User, lang: str) -> None:
    await cb.answer()
    await cb.message.edit_text(t("loc.choose_radius", lang), reply_markup=radius_kb(lang, user.search_radius_km))


@router.callback_query(F.data.startswith("lang:"))
async def set_language(cb: CallbackQuery, session: AsyncSession, user: User, state: FSMContext) -> None:
    code = cb.data.split(":")[1]
    if code in settings.supported_languages:
        user.language = code
        await session.commit()
    await cb.answer(t("settings.lang_set", user.language))
    await show_menu(cb, session, user, user.language, edit=True)


@router.callback_query(F.data == "gdpr:export")
async def gdpr_export(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    data = await user_service.gdpr_export(session, user)
    payload = json.dumps(data, ensure_ascii=False, indent=2).encode()
    await cb.answer()
    await cb.message.answer_document(BufferedInputFile(payload, filename="mes-donnees.json"),
                                     caption=t("gdpr.export_caption", lang))


@router.callback_query(F.data == "gdpr:delete")
async def gdpr_delete_confirm(cb: CallbackQuery, lang: str) -> None:
    await cb.answer()
    await cb.message.edit_text(t("gdpr.delete_confirm", lang), reply_markup=kb(
        [btn(t("btn.confirm_delete", lang), "gdpr:delete:yes"), btn(t("btn.cancel", lang), "menu:settings")]))


@router.callback_query(F.data == "gdpr:delete:yes")
async def gdpr_delete(cb: CallbackQuery, session: AsyncSession, user: User, lang: str, state: FSMContext) -> None:
    await state.clear()
    await user_service.gdpr_delete(session, user)
    await cb.answer()
    await cb.message.edit_text(t("gdpr.deleted", lang))
