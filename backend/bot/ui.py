"""Keyboards and message formatting for the bot."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    WebAppInfo,
)

from app.config import settings
from app.i18n import fmt_day, fmt_dt, fmt_time, t
from app.models import Booking, Category, Professional, Review, Service
from app.services.availability import Slot
from app.services.search import SearchResult
from app.services.text import escape_html, format_price, stars, truncate

UTC = timezone.utc
STATUS_ICONS = {"pending": "⏳", "confirmed": "✅", "cancelled": "❌", "completed": "🏁", "refused": "🚫"}


def btn(text: str, data: str | None = None, url: str | None = None, webapp: str | None = None
        ) -> InlineKeyboardButton:
    if webapp:
        return InlineKeyboardButton(text=text, web_app=WebAppInfo(url=webapp))
    if url:
        return InlineKeyboardButton(text=text, url=url)
    return InlineKeyboardButton(text=text, callback_data=data or "noop")


def kb(*rows: list[InlineKeyboardButton]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[r for r in rows if r])


def chunk(buttons: list[InlineKeyboardButton], size: int) -> list[list[InlineKeyboardButton]]:
    return [buttons[i:i + size] for i in range(0, len(buttons), size)]


def back_menu(lang: str) -> list[InlineKeyboardButton]:
    return [btn(t("btn.menu", lang), "menu:main")]


def main_menu(lang: str, is_pro: bool, is_admin: bool) -> InlineKeyboardMarkup:
    rows = [
        [btn(t("menu.search", lang), "menu:search"), btn(t("menu.now", lang), "menu:now")],
        [btn(t("menu.categories", lang), "cat:root"), btn(t("menu.nearby", lang), "menu:nearby")],
        [btn(t("menu.bookings", lang), "menu:bookings"), btn(t("menu.favorites", lang), "menu:favorites")],
        [btn(t("menu.quote", lang), "menu:quote"), btn(t("menu.my_quotes", lang), "menu:my_quotes")],
        [btn(t("menu.pro_space", lang) if is_pro else t("menu.become_pro", lang), "pd:home"),
         btn(t("menu.settings", lang), "menu:settings")],
    ]
    if settings.effective_webapp_url:
        rows.insert(0, [btn(t("menu.webapp", lang), webapp=settings.effective_webapp_url)])
    if is_admin:
        rows.append([btn(t("menu.admin", lang), "adm:home")])
    return kb(*rows)


def location_request_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("btn.share_location", lang), request_location=True)],
                  [KeyboardButton(text=t("btn.cancel", lang))]],
        resize_keyboard=True, one_time_keyboard=True,
    )


REMOVE_KB = ReplyKeyboardRemove()


def radius_kb(lang: str, current: int) -> InlineKeyboardMarkup:
    from app.services.geo import RADIUS_CHOICES_KM

    return kb(
        [btn(("• " if r == current else "") + f"{r} km", f"rad:{r}") for r in RADIUS_CHOICES_KM],
        back_menu(lang),
    )


def availability_presets_kb(lang: str) -> InlineKeyboardMarkup:
    return kb(
        [btn(t("avail.now", lang), "now:now"), btn(t("avail.30min", lang), "now:30min"),
         btn(t("avail.1h", lang), "now:1h")],
        [btn(t("avail.3h", lang), "now:3h"), btn(t("avail.today", lang), "now:today"),
         btn(t("avail.tomorrow", lang), "now:tomorrow")],
        back_menu(lang),
    )


def category_name(cat: Category, lang: str) -> str:
    return f"{cat.icon or '•'} {cat.name(lang)}"


# ---------------------------------------------------------------------------
# Professional cards
# ---------------------------------------------------------------------------
def slot_label(slot: Slot, tz: str, lang: str) -> str:
    now = datetime.now(UTC).astimezone(ZoneInfo(tz))
    local = slot.start.astimezone(ZoneInfo(tz))
    if local.date() == now.date():
        day = t("day.today", lang)
    elif local.date() == now.date() + timedelta(days=1):
        day = t("day.tomorrow", lang)
    else:
        day = fmt_day(local.date(), lang)
    return f"{day} {local:%H:%M}" + (" 🔥" if slot.freed else "")


def result_card(r: SearchResult, lang: str) -> str:
    pro = r.professional
    lines = [f"<b>{escape_html(pro.business_name)}</b>" + (" ✅" if pro.is_verified else "")
             + (" · " + t("card.sponsored", lang) if r.sponsored else "")]
    lines.append(f"{pro.category.icon or ''} {escape_html(pro.category.name(lang))} · {stars(pro.rating_avg, pro.rating_count)}")
    if pro.description:
        lines.append(f"<i>{escape_html(truncate(pro.description, 140))}</i>")
    loc = escape_html(pro.city or "")
    if r.distance_km is not None:
        loc += f" · {r.distance_km:.1f} km"
    if pro.is_mobile:
        loc += " · " + t("card.travels", lang, km=pro.service_radius_km)
        if r.travel_minutes:
            loc += " · " + t("card.travel_time", lang, min=r.travel_minutes)
    lines.append(f"📍 {loc}")
    if r.reference_service:
        s = r.reference_service
        lines.append(f"💶 {escape_html(s.name)} : {format_price(s.price_cents, s.price_type.value)} · {s.duration_min} min")
    if r.next_slots:
        lines.append("🗓 " + ", ".join(slot_label(s, pro.timezone, lang) for s in r.next_slots))
    elif r.on_duty:
        lines.append("🚨 " + t("card.urgent_ok", lang))
    else:
        lines.append("🗓 " + t("card.no_slot", lang))
    return "\n".join(lines)


def result_kb(r: SearchResult, lang: str) -> InlineKeyboardMarkup:
    pro = r.professional
    row2 = []
    if r.next_slots and r.reference_service:
        row2 = [btn("⚡ " + slot_label(s, pro.timezone, lang),
                    f"bt:{r.reference_service.id}:{int(s.start.timestamp() // 60)}") for s in r.next_slots[:2]]
    rows = [[btn(t("btn.profile", lang), f"pro:view:{pro.id}"), btn(t("btn.book", lang), f"pro:book:{pro.id}")]]
    if row2:
        rows.append(row2)
    if r.on_duty and r.reference_service and not r.next_slots:
        rows.append([btn(t("btn.urgent_request", lang), f"bu:{r.reference_service.id}")])
    return kb(*rows)


def pro_profile_text(pro: Professional, reviews: list[Review], lang: str, next_slots: list[Slot] | None = None,
                     favorite: bool = False) -> str:
    lines = [f"<b>{escape_html(pro.business_name)}</b>" + (" ✅ " + t("card.verified", lang) if pro.is_verified else "")]
    lines.append(f"{pro.category.icon or ''} {escape_html(pro.category.name(lang))}"
                 + (f" · {escape_html(', '.join(pro.specialties))}" if pro.specialties else ""))
    lines.append(stars(pro.rating_avg, pro.rating_count) + " · " + t("card.completed", lang, n=pro.completed_count))
    if pro.description:
        lines.append(f"\n{escape_html(truncate(pro.description, 700))}")
    lines.append("")
    if pro.is_on_site and (pro.address or pro.city):
        lines.append(f"📍 {escape_html(', '.join(x for x in (pro.address, pro.postal_code, pro.city) if x))}")
    if pro.is_mobile:
        lines.append("🚗 " + t("card.zone", lang, city=escape_html(pro.city or "-"), km=pro.service_radius_km))
    if pro.phone:
        lines.append(f"📞 {escape_html(pro.phone)}")
    if pro.website:
        lines.append(f"🌐 {escape_html(pro.website)}")
    services = [s for s in pro.services if s.is_active]
    if services:
        lines.append("\n<b>" + t("card.services", lang) + "</b>")
        for s in services[:12]:
            lines.append(f"• {escape_html(s.name)} — {format_price(s.price_cents, s.price_type.value)} "
                         f"({s.duration_min} min{', ' + t('card.at_home', lang) if s.location.value == 'at_client' else ''})")
    if pro.working_hours:
        lines.append("\n<b>" + t("card.hours", lang) + "</b>")
        lines.append(hours_summary(pro, lang))
    if next_slots:
        lines.append("\n🗓 " + t("card.next_slots", lang) + " : "
                     + ", ".join(slot_label(s, pro.timezone, lang) for s in next_slots))
    if reviews:
        lines.append("\n<b>" + t("card.reviews", lang) + "</b>")
        for r in reviews[:3]:
            name = r.client.first_name if r.client and r.client.first_name else t("card.client", lang)
            lines.append(f"{'⭐' * r.rating} <i>{escape_html(truncate(r.comment or '', 160))}</i> — {escape_html(name)}")
            if r.pro_reply:
                lines.append(f"   ↳ <i>{escape_html(truncate(r.pro_reply, 120))}</i>")
    if pro.category.is_health:
        lines.append("\n<i>" + t("card.health_notice", lang) + "</i>")
    return "\n".join(lines)


def hours_summary(pro: Professional, lang: str) -> str:
    from app.i18n import WEEKDAYS_SHORT

    by_day: dict[int, list[str]] = {d: [] for d in range(7)}
    for wh in sorted(pro.working_hours, key=lambda w: (w.weekday, w.start_time)):
        by_day[wh.weekday].append(f"{wh.start_time:%H:%M}-{wh.end_time:%H:%M}")
    names = WEEKDAYS_SHORT.get(lang, WEEKDAYS_SHORT["fr"])
    return "\n".join(f"{names[d]} : {', '.join(v) if v else t('hours.closed', lang)}" for d, v in by_day.items())


def pro_profile_kb(pro: Professional, lang: str, favorite: bool, has_photos: bool) -> InlineKeyboardMarkup:
    rows = [
        [btn(t("btn.book", lang), f"pro:book:{pro.id}"), btn(t("btn.contact", lang), f"msg:cli:{pro.id}")],
        [btn(("💔 " if favorite else "❤️ ") + t("btn.unfavorite" if favorite else "btn.favorite", lang),
             f"fav:{pro.id}"),
         btn(t("btn.reviews", lang), f"pro:reviews:{pro.id}")],
    ]
    extra = []
    if has_photos:
        extra.append(btn(t("btn.photos", lang), f"pro:photos:{pro.id}"))
    if pro.accepts_quotes:
        extra.append(btn(t("btn.ask_quote", lang), f"quote:pro:{pro.id}"))
    if extra:
        rows.append(extra)
    rows.append([btn(t("btn.report", lang), f"rep:pro:{pro.id}"), btn(t("btn.menu", lang), "menu:main")])
    return kb(*rows)


# ---------------------------------------------------------------------------
# Booking UI
# ---------------------------------------------------------------------------
def services_kb(pro: Professional, lang: str) -> InlineKeyboardMarkup:
    rows = []
    for s in pro.services:
        if not s.is_active:
            continue
        label = f"{s.name} · {format_price(s.price_cents, s.price_type.value)} · {s.duration_min}′"
        rows.append([btn(truncate(label, 60), f"bs:{s.id}")])
    rows.append([btn(t("btn.back", lang), f"pro:view:{pro.id}")])
    return kb(*rows)


def calendar_kb(service: Service, days_with_slots: dict[date, int], start: date, lang: str, prefix: str = "bd",
                ref: str | None = None, page_prefix: str = "bw") -> InlineKeyboardMarkup:
    """14-day calendar. Days without availability are not clickable."""
    ref = ref or str(service.id)
    buttons = []
    for i in range(14):
        d = start + timedelta(days=i)
        n = days_with_slots.get(d, 0)
        label = f"{fmt_day(d, lang)}" if n else f"· {d.day}"
        buttons.append(btn(label, f"{prefix}:{ref}:{d:%Y%m%d}" if n else "noop"))
    rows = chunk(buttons, 3)
    offset = (start - datetime.now(UTC).date()).days
    nav = []
    if offset > 0:
        nav.append(btn("◀️", f"{page_prefix}:{ref}:{max(0, offset - 14)}"))
    nav.append(btn("▶️", f"{page_prefix}:{ref}:{offset + 14}"))
    rows.append(nav)
    return kb(*rows)


def slots_kb(slots: list[Slot], tz: str, ref: str, lang: str, prefix: str = "bt", back: str | None = None
             ) -> InlineKeyboardMarkup:
    buttons = [btn(fmt_time(s.start, tz) + (" 🔥" if s.freed else ""), f"{prefix}:{ref}:{int(s.start.timestamp() // 60)}")
               for s in slots[:60]]
    rows = chunk(buttons, 4)
    if back:
        rows.append([btn(t("btn.back", lang), back)])
    return kb(*rows)


def booking_text(b: Booking, lang: str, for_pro: bool = False) -> str:
    pro = b.professional
    lines = [f"{STATUS_ICONS.get(b.status.value, '')} <b>{t('status.' + b.status.value, lang)}</b> · <code>{b.reference}</code>",
             f"<b>{escape_html(b.service_name or '-')}</b>"]
    if for_pro:
        lines.append(f"👤 {escape_html(b.client.display_name)}" + (f" · {escape_html(b.client.phone)}" if b.client.phone else ""))
    else:
        lines.append(f"🏷 {escape_html(pro.business_name)}")
    lines.append(f"🗓 {fmt_dt(b.start_at, pro.timezone, lang)} ({int((b.end_at - b.start_at).total_seconds() // 60)} min)")
    if b.price_cents is not None:
        lines.append(f"💶 {format_price(b.price_cents)}")
    if b.location.value == "at_client":
        lines.append(f"🏠 {escape_html(b.address or '-')}")
    elif pro.address:
        lines.append(f"📍 {escape_html(pro.address)}, {escape_html(pro.city or '')}")
    if b.client_note:
        lines.append(f"📝 {escape_html(b.client_note)}")
    if b.is_urgent:
        lines.append("🚨 " + t("booking.urgent", lang))
    if b.cancel_reason and b.status.value in ("cancelled", "refused"):
        lines.append(f"ℹ️ {escape_html(b.cancel_reason)}")
    return "\n".join(lines)
