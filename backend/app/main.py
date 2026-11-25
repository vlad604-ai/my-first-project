"""FastAPI application: REST API v1 + Telegram webhook endpoint.

Run: uvicorn app.main:app --reload
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.routers import admin, auth, me, pro, public
from app.config import settings
from app.db import engine
from app.logging_setup import setup_logging

log = logging.getLogger(__name__)
_bot = None
_dispatcher = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _bot, _dispatcher
    setup_logging()
    if settings.telegram_bot_token and settings.telegram_webhook_url:
        from app.services.notifier import set_notifier
        from bot.main import build_bot, build_dispatcher, build_storage, set_commands
        from bot.telegram_notifier import TelegramNotifier

        _bot = build_bot()
        storage, redis = build_storage()
        _dispatcher = build_dispatcher(storage, redis)
        set_notifier(TelegramNotifier(_bot))
        await set_commands(_bot)
        await _bot.set_webhook(f"{settings.telegram_webhook_url.rstrip('/')}/telegram/webhook",
                               secret_token=settings.telegram_webhook_secret,
                               allowed_updates=_dispatcher.resolve_used_update_types())
        log.info("Telegram webhook registered")
    yield
    if _bot is not None:
        await _bot.session.close()
    await engine.dispose()


app = FastAPI(title=f"{settings.app_name} API", version="1.0.0", lifespan=lifespan,
              docs_url="/docs" if settings.environment != "production" else None)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

API_PREFIX = "/api/v1"
for r in (public.router, auth.router, me.router, pro.router, admin.router):
    app.include_router(r, prefix=API_PREFIX)


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    log.exception("Unhandled API error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
async def health():
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.post("/telegram/webhook", include_in_schema=False)
async def telegram_webhook(request: Request, x_telegram_bot_api_secret_token: str | None = Header(None)):
    if _bot is None or _dispatcher is None:
        raise HTTPException(503, "Bot not configured")
    if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        raise HTTPException(403, "Forbidden")
    from aiogram.types import Update

    update = Update.model_validate(await request.json(), context={"bot": _bot})
    await _dispatcher.feed_update(_bot, update)
    return {"ok": True}
