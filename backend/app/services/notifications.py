"""Business notifications (clients & professionals).

Callback data formats here are shared with the bot handlers (bot/callbacks.py).
"""
from __future__ import annotations

from datetime import datetime

from app.i18n import fmt_dt, t
from app.models import Booking, Professional, Quote, QuoteRequest, User
from app.services.notifier import Button, send
from app.services.text import escape_html, format_price


def _lang(user: User | None) -> str:
    return (user.language if user else None) or "fr"


def _pro_user(booking: Booking) -> User | None:
    return booking.professional.user if booking.professional else None


def _when(booking: Booking, lang: str) -> str:
    return fmt_dt(booking.start_at, booking.professional.timezone, lang)


def _summary(booking: Booking, lang: str) -> str:
    pro = booking.professional
    lines = [
        t("notif.summary", lang, ref=booking.reference, service=escape_html(booking.service_name or "-"),
          pro=escape_html(pro.business_name), when=_when(booking, lang)),
    ]
    if booking.price_cents is not None:
        lines.append(t("notif.price", lang, price=format_price(booking.price_cents)))
    if booking.location.value == "at_client" and booking.address:
        lines.append(t("notif.address", lang, address=escape_html(booking.address)))
    elif pro.address:
        lines.append(t("notif.address", lang, address=escape_html(f"{pro.address}, {pro.city or ''}")))
    return "\n".join(lines)


def _client_line(booking: Booking, lang: str) -> str:
    c = booking.client
    s = t("notif.client", lang, name=escape_html(c.display_name))
    if c.phone:
        s += f" · {escape_html(c.phone)}"
    if booking.client_note:
        s += "\n" + t("notif.note", lang, note=escape_html(booking.client_note))
    return s


async def booking_created(booking: Booking) -> None:
    client, pro_user = booking.client, _pro_user(booking)
    lc, lp = _lang(client), _lang(pro_user)
    if booking.status.value == "confirmed":
        await send(client.telegram_id, t("notif.client.confirmed", lc) + "\n\n" + _summary(booking, lc),
                   [[Button(t("btn.view_booking", lc), callback=f"bk:view:{booking.id}")]])
        await send(pro_user.telegram_id if pro_user else None,
                   t("notif.pro.new_confirmed", lp) + "\n\n" + _summary(booking, lp) + "\n" + _client_line(booking, lp),
                   [[Button(t("btn.view_booking", lp), callback=f"pbk:view:{booking.id}")]])
    else:
        key = "notif.client.pending_urgent" if booking.is_urgent else "notif.client.pending"
        await send(client.telegram_id, t(key, lc) + "\n\n" + _summary(booking, lc),
                   [[Button(t("btn.view_booking", lc), callback=f"bk:view:{booking.id}")]])
        head = "notif.pro.new_urgent" if booking.is_urgent else "notif.pro.new_request"
        await send(
            pro_user.telegram_id if pro_user else None,
            t(head, lp) + "\n\n" + _summary(booking, lp) + "\n" + _client_line(booking, lp),
            [[Button(t("btn.accept", lp), callback=f"pbk:confirm:{booking.id}"),
              Button(t("btn.refuse", lp), callback=f"pbk:refuse:{booking.id}")]],
        )


async def booking_confirmed(booking: Booking) -> None:
    lc = _lang(booking.client)
    await send(booking.client.telegram_id, t("notif.client.confirmed", lc) + "\n\n" + _summary(booking, lc),
               [[Button(t("btn.view_booking", lc), callback=f"bk:view:{booking.id}")]])


async def booking_refused(booking: Booking) -> None:
    lc = _lang(booking.client)
    reason = booking.cancel_reason or "-"
    await send(booking.client.telegram_id,
               t("notif.client.refused", lc, reason=escape_html(reason)) + "\n\n" + _summary(booking, lc),
               [[Button(t("btn.search_again", lc), callback="menu:search")]])


async def booking_cancelled(booking: Booking, by: str) -> None:
    client, pro_user = booking.client, _pro_user(booking)
    if by != "client":
        lc = _lang(client)
        await send(client.telegram_id, t("notif.client.cancelled_by_pro", lc) + "\n\n" + _summary(booking, lc),
                   [[Button(t("btn.rebook", lc), callback=f"pro:view:{booking.professional_id}")]])
    if by != "professional" and pro_user:
        lp = _lang(pro_user)
        await send(pro_user.telegram_id, t("notif.pro.cancelled", lp) + "\n\n" + _summary(booking, lp)
                   + "\n" + _client_line(booking, lp))


async def booking_rescheduled(booking: Booking, old_start: datetime, by: str) -> None:
    client, pro_user = booking.client, _pro_user(booking)
    tz = booking.professional.timezone
    for user, prefix in ((client, "bk"), (pro_user, "pbk")):
        if user is None:
            continue
        if (by == "client" and user is client) or (by == "professional" and user is pro_user):
            continue
        lang = _lang(user)
        await send(user.telegram_id,
                   t("notif.rescheduled", lang, old=fmt_dt(old_start, tz, lang)) + "\n\n" + _summary(booking, lang),
                   [[Button(t("btn.view_booking", lang), callback=f"{prefix}:view:{booking.id}")]])
    if by == "client" and booking.status.value == "pending" and pro_user:
        lp = _lang(pro_user)
        await send(pro_user.telegram_id,
                   t("notif.rescheduled", lp, old=fmt_dt(old_start, tz, lp)) + "\n\n" + _summary(booking, lp),
                   [[Button(t("btn.accept", lp), callback=f"pbk:confirm:{booking.id}"),
                     Button(t("btn.refuse", lp), callback=f"pbk:refuse:{booking.id}")]])
    elif by == "client" and pro_user:
        lp = _lang(pro_user)
        await send(pro_user.telegram_id,
                   t("notif.rescheduled", lp, old=fmt_dt(old_start, tz, lp)) + "\n\n" + _summary(booking, lp))


async def reminder(booking: Booking, kind: str) -> None:
    lc = _lang(booking.client)
    await send(booking.client.telegram_id, t(f"notif.reminder.{kind}", lc) + "\n\n" + _summary(booking, lc),
               [[Button(t("btn.view_booking", lc), callback=f"bk:view:{booking.id}")]])


async def review_request(booking: Booking) -> None:
    lc = _lang(booking.client)
    await send(booking.client.telegram_id,
               t("notif.review_request", lc, pro=escape_html(booking.professional.business_name)),
               [[Button(f"{'⭐' * n}", callback=f"rv:rate:{booking.id}:{n}") for n in (1, 2, 3)],
                [Button(f"{'⭐' * n}", callback=f"rv:rate:{booking.id}:{n}") for n in (4, 5)]])


async def pro_daily_agenda(pro: Professional, bookings: list[Booking]) -> None:
    user = pro.user
    lang = _lang(user)
    if not bookings:
        return
    lines = [t("notif.pro.tomorrow", lang, count=len(bookings))]
    for b in bookings:
        lines.append(f"• {fmt_dt(b.start_at, pro.timezone, lang)} — {escape_html(b.service_name or '')} "
                     f"({escape_html(b.client.display_name)})")
    await send(user.telegram_id, "\n".join(lines), [[Button(t("btn.agenda", lang), callback="pd:agenda:0")]])


async def new_message(recipient: User, sender_label: str, body: str, reply_callback: str) -> None:
    lang = _lang(recipient)
    await send(recipient.telegram_id,
               t("notif.new_message", lang, sender=escape_html(sender_label), body=escape_html(body[:1500])),
               [[Button(t("btn.reply", lang), callback=reply_callback)]])


async def quote_request_received(pro: Professional, req: QuoteRequest) -> None:
    lang = _lang(pro.user)
    budget = format_price(req.budget_cents) if req.budget_cents else t("quote.no_budget", lang)
    await send(pro.user.telegram_id,
               t("notif.pro.quote_request", lang, desc=escape_html(req.description[:800]),
                 city=escape_html(req.city or "-"), budget=budget, urgency=t(f"urgency.{req.urgency.value}", lang)),
               [[Button(t("btn.send_quote", lang), callback=f"pq:answer:{req.id}"),
                 Button(t("btn.decline", lang), callback=f"pq:decline:{req.id}")]])


async def quote_received(client: User, quote: Quote, pro: Professional) -> None:
    lang = _lang(client)
    await send(client.telegram_id,
               t("notif.client.quote", lang, pro=escape_html(pro.business_name),
                 amount=format_price(quote.amount_cents), msg=escape_html((quote.message or "")[:500])),
               [[Button(t("btn.compare_quotes", lang), callback=f"qr:view:{quote.request_id}")]])


async def quote_accepted(pro: Professional, quote: Quote, client: User) -> None:
    lang = _lang(pro.user)
    await send(pro.user.telegram_id,
               t("notif.pro.quote_accepted", lang, client=escape_html(client.display_name),
                 amount=format_price(quote.amount_cents)),
               [[Button(t("btn.contact_client", lang), callback=f"msg:pro:{client.id}")]])


async def pro_status_changed(pro: Professional, status: str) -> None:
    lang = _lang(pro.user)
    await send(pro.user.telegram_id, t(f"notif.pro.status.{status}", lang))
