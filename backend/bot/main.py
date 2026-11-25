"""Bot bootstrap: long polling (dev) or webhook (prod, served by FastAPI).

Run in polling mode:  python -m bot.main
"""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, ErrorEvent

from app.config import settings
from app.logging_setup import setup_logging
from app.services.notifier import set_notifier
from bot.handlers import admin, booking, common, messages, pro, quotes, search
from bot.middlewares import DbUserMiddleware, ThrottlingMiddleware
from bot.telegram_notifier import TelegramNotifier

log = logging.getLogger(__name__)


def build_storage() -> tuple[BaseStorage, object | None]:
    """Redis-backed FSM (survives restarts, multi-instance) with memory fallback."""
    try:
        from aiogram.fsm.storage.redis import RedisStorage
        from redis.asyncio import Redis

        redis = Redis.from_url(settings.redis_url)
        return RedisStorage(redis, state_ttl=7 * 86400, data_ttl=7 * 86400), redis
    except Exception:  # pragma: no cover
        log.warning("Redis unavailable: using in-memory FSM storage")
        return MemoryStorage(), None


def build_bot() -> Bot:
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set (see .env.example)")
    return Bot(settings.telegram_bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


def build_dispatcher(storage: BaseStorage | None = None, redis=None) -> Dispatcher:
    dp = Dispatcher(storage=storage or MemoryStorage())
    dp.update.outer_middleware(ThrottlingMiddleware(redis=redis))
    dp.message.middleware(DbUserMiddleware())
    dp.callback_query.middleware(DbUserMiddleware())
    # Order matters: specific flows first, free-text AI search last.
    dp.include_routers(common.router, admin.router, pro.router, booking.router, quotes.router, messages.router,
                       search.router)

    @dp.errors()
    async def on_error(event: ErrorEvent) -> bool:
        log.exception("Unhandled bot error", exc_info=event.exception)
        upd = event.update
        target = upd.message or (upd.callback_query.message if upd.callback_query else None)
        if target is not None:
            try:
                from app.i18n import t

                await target.answer(t("err.generic", "fr"))
            except Exception:
                pass
        return True

    return dp


async def set_commands(bot: Bot) -> None:
    for lang in ("fr", "en"):
        from app.i18n import t

        await bot.set_my_commands(
            [BotCommand(command="start", description=t("cmd.start", lang)),
             BotCommand(command="menu", description=t("cmd.menu", lang)),
             BotCommand(command="pro", description=t("cmd.pro", lang)),
             BotCommand(command="help", description=t("cmd.help", lang)),
             BotCommand(command="cancel", description=t("cmd.cancel", lang))],
            language_code=lang if lang != "fr" else None,
        )


async def main() -> None:
    setup_logging()
    settings.check_production()
    bot = build_bot()
    storage, redis = build_storage()
    dp = build_dispatcher(storage, redis)
    set_notifier(TelegramNotifier(bot))
    await set_commands(bot)
    await bot.delete_webhook(drop_pending_updates=False)
    log.info("Bot started in long-polling mode")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
