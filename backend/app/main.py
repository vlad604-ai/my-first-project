"""FastAPI application: REST API v1 + Telegram webhook endpoint.

Run: uvicorn app.main:app --reload
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
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
    settings.check_production()
    if settings.telegram_bot_token and settings.public_url:
        from app.services.notifier import set_notifier
        from bot.main import build_bot, build_dispatcher, build_storage, set_commands
        from bot.telegram_notifier import TelegramNotifier

        _bot = build_bot()
        storage, redis = build_storage()
        _dispatcher = build_dispatcher(storage, redis)
        set_notifier(TelegramNotifier(_bot))
        try:
            await set_commands(_bot)
            await _bot.set_webhook(f"{settings.public_url}/telegram/webhook",
                                   secret_token=settings.telegram_secret_token,
                                   allowed_updates=_dispatcher.resolve_used_update_types())
            log.info("Telegram webhook registered on %s", settings.public_url)
            if settings.effective_webapp_url:
                from aiogram.types import MenuButtonWebApp, WebAppInfo

                await _bot.set_chat_menu_button(menu_button=MenuButtonWebApp(
                    text="Ouvrir", web_app=WebAppInfo(url=settings.effective_webapp_url)))
        except Exception:  # a Telegram hiccup must not prevent the API from starting
            log.exception("Telegram setup failed (check TELEGRAM_BOT_TOKEN)")
    scheduler = None
    if settings.run_scheduler:
        from worker.main import build_scheduler

        scheduler = build_scheduler()
        scheduler.start()
        log.info("In-process scheduler started")
    yield
    if scheduler is not None:
        scheduler.shutdown(wait=False)
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
    if x_telegram_bot_api_secret_token != settings.telegram_secret_token:
        raise HTTPException(403, "Forbidden")
    from aiogram.types import Update

    update = Update.model_validate(await request.json(), context={"bot": _bot})
    await _dispatcher.feed_update(_bot, update)
    return {"ok": True}


# --- Web build (Mini App at /, admin at /admin) served by the API when present ---------
WEB_DIR = Path(settings.web_dist_dir)
if not WEB_DIR.is_absolute():
    WEB_DIR = Path(__file__).resolve().parents[1] / WEB_DIR
if settings.serve_web and (WEB_DIR / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIR / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    async def spa(path: str):
        if path.startswith(("api/", "telegram/")):
            raise HTTPException(404)
        candidate = (WEB_DIR / path).resolve()
        if path and candidate.is_file() and WEB_DIR.resolve() in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(WEB_DIR / "index.html")
