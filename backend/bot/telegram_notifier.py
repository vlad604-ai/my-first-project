"""Delivers platform notifications through the Telegram Bot API."""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from app.services.notifier import OutgoingMessage

log = logging.getLogger(__name__)


def to_markup(rows) -> InlineKeyboardMarkup | None:
    if not rows:
        return None
    kb = []
    for row in rows:
        buttons = []
        for b in row:
            if b.webapp_url:
                buttons.append(InlineKeyboardButton(text=b.text, web_app=WebAppInfo(url=b.webapp_url)))
            elif b.url:
                buttons.append(InlineKeyboardButton(text=b.text, url=b.url))
            else:
                buttons.append(InlineKeyboardButton(text=b.text, callback_data=b.callback or "noop"))
        kb.append(buttons)
    return InlineKeyboardMarkup(inline_keyboard=kb)


class TelegramNotifier:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def send(self, message: OutgoingMessage) -> bool:
        for attempt in range(3):
            try:
                await self.bot.send_message(message.chat_id, message.text, reply_markup=to_markup(message.buttons))
                return True
            except TelegramRetryAfter as exc:
                await asyncio.sleep(exc.retry_after)
            except TelegramForbiddenError:
                log.info("User %s blocked the bot", message.chat_id)
                return False
            except Exception:
                log.exception("Telegram send failed (attempt %s)", attempt + 1)
                await asyncio.sleep(1)
        return False
