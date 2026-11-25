"""Client <-> pro messaging and abuse reports."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.i18n import t
from app.models import Professional, ReportTarget, User
from app.services import messaging
from app.services import professionals as pro_service
from app.services.text import escape_html
from bot.states import ContactFlow, ReportFlow
from bot.ui import back_menu, btn, kb

router = Router(name="messages")


@router.callback_query(F.data.startswith("msg:cli:"))
async def contact_pro(cb: CallbackQuery, session: AsyncSession, user: User, lang: str, state: FSMContext) -> None:
    await cb.answer()
    pro_id = int(cb.data.split(":")[2])
    pro = await session.get(Professional, pro_id)
    if pro is None:
        return
    if pro.user_id == user.id:
        await cb.message.answer(t("msg.self", lang))
        return
    history = await messaging.thread(session, user.id, pro_id, limit=5)
    await state.set_state(ContactFlow.message)
    await state.update_data(msg_client=user.id, msg_pro=pro_id)
    text = t("msg.ask", lang, name=escape_html(pro.business_name))
    if history:
        text += "\n\n" + "\n".join(
            f"{'➡️' if m.sender_user_id == user.id else '⬅️'} {escape_html(m.body[:200])}" for m in history)
    await cb.message.answer(text, reply_markup=kb([btn(t("btn.cancel", lang), "menu:main")]))


@router.callback_query(F.data.startswith("msg:pro:"))
async def contact_client(cb: CallbackQuery, session: AsyncSession, user: User, lang: str, state: FSMContext) -> None:
    await cb.answer()
    pro = await pro_service.get_pro_for_user(session, user)
    if pro is None:
        return
    client_id = int(cb.data.split(":")[2])
    client = await session.get(User, client_id)
    history = await messaging.thread(session, client_id, pro.id, limit=5)
    await state.set_state(ContactFlow.message)
    await state.update_data(msg_client=client_id, msg_pro=pro.id)
    text = t("msg.ask", lang, name=escape_html(client.display_name if client else "client"))
    if history:
        text += "\n\n" + "\n".join(
            f"{'➡️' if m.sender_user_id == user.id else '⬅️'} {escape_html(m.body[:200])}" for m in history)
    await cb.message.answer(text, reply_markup=kb([btn(t("btn.cancel", lang), "menu:main")]))


@router.message(StateFilter(ContactFlow.message), F.text)
async def send(message: Message, session: AsyncSession, user: User, lang: str, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(None)
    try:
        await messaging.send_message(session, user, data["msg_client"], data["msg_pro"], message.text)
    except messaging.MessagingError as exc:
        await message.answer(t(f"msg.err.{exc}", lang))
        return
    await message.answer(t("msg.sent", lang), reply_markup=kb(back_menu(lang)))


@router.callback_query(F.data.startswith("rep:"))
async def report_start(cb: CallbackQuery, state: FSMContext, lang: str) -> None:
    await cb.answer()
    _, target, target_id = cb.data.split(":")
    await state.set_state(ReportFlow.reason)
    await state.update_data(rep_target=target, rep_id=target_id)
    await cb.message.answer(t("report.ask", lang), reply_markup=kb([btn(t("btn.cancel", lang), "menu:main")]))


@router.message(StateFilter(ReportFlow.reason), F.text)
async def report_send(message: Message, session: AsyncSession, user: User, lang: str, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(None)
    target = {"pro": ReportTarget.PROFESSIONAL, "review": ReportTarget.REVIEW, "user": ReportTarget.USER}.get(
        data.get("rep_target"), ReportTarget.PROFESSIONAL)
    await messaging.report(session, user, target, data.get("rep_id"), message.text)
    await message.answer(t("report.thanks", lang), reply_markup=kb(back_menu(lang)))
