"""Lightweight admin console in Telegram (the full one is the web dashboard)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.i18n import t
from app.models import Professional, ProStatus, Report, ReportStatus, Review, ReviewStatus, User
from app.services import admin as admin_service
from app.services import reviews as review_service
from app.services.text import escape_html, format_price, truncate
from bot.ui import btn, kb

router = Router(name="admin")


def _is_admin(user: User | None) -> bool:
    return bool(user and user.is_admin)


def _home(lang: str) -> list:
    return [btn(t("adm.home", lang), "adm:home")]


@router.message(Command("admin"))
@router.callback_query(F.data == "adm:home")
async def home(event: Message | CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    if not _is_admin(user):
        if isinstance(event, CallbackQuery):
            await event.answer()
        return
    s = await admin_service.platform_stats(session, 30)
    text = t("adm.stats", lang, users=s["users_total"], new=s["users_new"],
             active=s["professionals"].get("active", 0), pending=s["professionals"].get("pending", 0),
             bookings=s["bookings_total"], gmv=format_price(s["gmv_cents"]), reviews=s["reviews_pending"],
             reports=s["reports_open"], quotes=s["quote_requests"])
    markup = kb([btn(t("adm.pending_pros", lang), "adm:pros")],
                [btn(t("adm.reviews", lang), "adm:reviews"), btn(t("adm.reports", lang), "adm:reports")],
                [btn(t("btn.menu", lang), "menu:main")])
    if isinstance(event, CallbackQuery):
        await event.answer()
        await event.message.answer(text, reply_markup=markup)
    else:
        await event.answer(text, reply_markup=markup)


@router.callback_query(F.data == "adm:pros")
async def pending_pros(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    if not _is_admin(user):
        return
    await cb.answer()
    pros = (await session.execute(select(Professional).where(Professional.status == ProStatus.PENDING)
                                  .options(selectinload(Professional.category)).limit(10))).scalars().all()
    if not pros:
        await cb.message.answer(t("adm.none", lang), reply_markup=kb(_home(lang)))
        return
    for p in pros:
        await cb.message.answer(
            f"🆕 <b>{escape_html(p.business_name)}</b> · {escape_html(p.category.name(lang))}\n"
            f"📍 {escape_html(p.address or p.city or '-')} · {t('mode.' + p.work_mode.value, lang)}\n"
            f"<i>{escape_html(truncate(p.description or '', 300))}</i>",
            reply_markup=kb([btn(t("adm.approve", lang), f"adm:pro:ok:{p.id}"),
                             btn(t("adm.approve_verify", lang), f"adm:pro:verify:{p.id}")],
                            [btn(t("adm.reject", lang), f"adm:pro:reject:{p.id}"),
                             btn(t("btn.profile", lang), f"pro:view:{p.id}")]))


@router.callback_query(F.data.startswith("adm:pro:"))
async def pro_action(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    if not _is_admin(user):
        return
    _, _, action, pro_id = cb.data.split(":")
    status = {"ok": ProStatus.ACTIVE, "verify": ProStatus.ACTIVE, "reject": ProStatus.REJECTED,
              "suspend": ProStatus.SUSPENDED}[action]
    await admin_service.set_pro_status(session, user, int(pro_id), status,
                                       verify=True if action == "verify" else None)
    await cb.answer("✅")
    await cb.message.edit_reply_markup(reply_markup=None)


@router.callback_query(F.data == "adm:reviews")
async def pending_reviews(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    if not _is_admin(user):
        return
    await cb.answer()
    reviews = (await session.execute(select(Review).where(Review.status == ReviewStatus.PENDING)
                                     .options(selectinload(Review.professional)).limit(10))).scalars().all()
    if not reviews:
        await cb.message.answer(t("adm.none", lang), reply_markup=kb(_home(lang)))
        return
    for r in reviews:
        await cb.message.answer(
            f"{'⭐' * r.rating} · {escape_html(r.professional.business_name)}\n"
            f"<i>{escape_html(truncate(r.comment or '', 600))}</i>\nℹ️ {r.moderation_reason or '-'}",
            reply_markup=kb([btn(t("adm.publish", lang), f"adm:rv:1:{r.id}"),
                             btn(t("adm.reject", lang), f"adm:rv:0:{r.id}")]))


@router.callback_query(F.data.startswith("adm:rv:"))
async def review_action(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    if not _is_admin(user):
        return
    _, _, ok, rid = cb.data.split(":")
    await review_service.moderate_review(session, user, int(rid), ok == "1")
    await cb.answer("✅")
    await cb.message.edit_reply_markup(reply_markup=None)


@router.callback_query(F.data == "adm:reports")
async def reports(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    if not _is_admin(user):
        return
    await cb.answer()
    items = (await session.execute(select(Report).where(Report.status == ReportStatus.OPEN).limit(10))).scalars().all()
    if not items:
        await cb.message.answer(t("adm.none", lang), reply_markup=kb(_home(lang)))
        return
    for r in items:
        extra = [btn(t("btn.profile", lang), f"pro:view:{r.target_id}"),
                 btn(t("adm.suspend", lang), f"adm:pro:suspend:{r.target_id}")] \
            if r.target_type.value == "professional" else []
        await cb.message.answer(f"🚩 {r.target_type.value} #{escape_html(r.target_id)}\n{escape_html(truncate(r.reason, 600))}",
                                reply_markup=kb([btn(t("adm.resolve", lang), f"adm:rep:resolved:{r.id}"),
                                                 btn(t("adm.dismiss", lang), f"adm:rep:dismissed:{r.id}")], extra))


@router.callback_query(F.data.startswith("adm:rep:"))
async def report_action(cb: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    if not _is_admin(user):
        return
    _, _, status, rid = cb.data.split(":")
    await admin_service.resolve_report(session, user, int(rid), ReportStatus(status))
    await cb.answer("✅")
    await cb.message.edit_reply_markup(reply_markup=None)
