"""Bot middlewares: DB session + current user, throttling, error reporting."""
from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.config import settings
from app.db import SessionLocal
from app.i18n import t
from app.services.users import get_or_create_telegram_user

log = logging.getLogger(__name__)


class DbUserMiddleware(BaseMiddleware):
    """Opens one DB session per update and loads (or creates) the Telegram user."""

    async def __call__(self, handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject, data: dict[str, Any]) -> Any:
        tg_user = data.get("event_from_user")
        async with SessionLocal() as session:
            data["session"] = session
            if tg_user is not None and not tg_user.is_bot:
                user = await get_or_create_telegram_user(session, tg_user.id, tg_user.username, tg_user.first_name,
                                                         tg_user.last_name, tg_user.language_code)
                if user.is_banned:
                    if isinstance(event, Message):
                        await event.answer(t("err.banned", user.language))
                    elif isinstance(event, CallbackQuery):
                        await event.answer(t("err.banned", user.language), show_alert=True)
                    return None
                data["user"] = user
                data["lang"] = user.language or "fr"
            return await handler(event, data)


class ThrottlingMiddleware(BaseMiddleware):
    """Sliding-window rate limit per Telegram user (Redis when available, memory otherwise)."""

    def __init__(self, limit_per_minute: int | None = None, redis=None) -> None:
        self.limit = limit_per_minute or settings.rate_limit_per_minute
        self.redis = redis
        self.hits: dict[int, deque[float]] = defaultdict(deque)

    async def _allowed(self, user_id: int) -> bool:
        if self.redis is not None:
            try:
                key = f"ub:rl:{user_id}:{int(time.time() // 60)}"
                n = await self.redis.incr(key)
                if n == 1:
                    await self.redis.expire(key, 70)
                return n <= self.limit
            except Exception:  # Redis down: fall back to memory
                log.warning("Redis throttling unavailable, using memory")
                self.redis = None
        now = time.monotonic()
        q = self.hits[user_id]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(now)
        return True

    async def __call__(self, handler, event: TelegramObject, data: dict[str, Any]) -> Any:
        tg_user = data.get("event_from_user")
        if tg_user is not None and not await self._allowed(tg_user.id):
            if isinstance(event, CallbackQuery):
                await event.answer(t("err.too_fast", (tg_user.language_code or "fr")[:2]), show_alert=False)
            elif isinstance(event, Message):
                await event.answer(t("err.too_fast", (tg_user.language_code or "fr")[:2]))
            return None
        return await handler(event, data)
