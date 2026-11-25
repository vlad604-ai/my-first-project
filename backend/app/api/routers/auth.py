from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from passlib.hash import pbkdf2_sha256
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.security import AuthError, create_access_token, validate_telegram_init_data
from app.db import get_session
from app.models import User
from app.schemas.common import TokenOut, UserOut
from app.services.audit import audit
from app.services.users import get_or_create_telegram_user

router = APIRouter(prefix="/auth", tags=["auth"])


class TelegramAuthIn(BaseModel):
    init_data: str


class PasswordLoginIn(BaseModel):
    email: str
    password: str


@router.post("/telegram", response_model=TokenOut)
async def telegram_login(body: TelegramAuthIn, session: AsyncSession = Depends(get_session)):
    """Exchange Telegram Mini App initData for an API token."""
    try:
        tg = validate_telegram_init_data(body.init_data)
    except AuthError as exc:
        raise HTTPException(401, str(exc)) from exc
    if "id" not in tg:
        raise HTTPException(401, "invalid user")
    user = await get_or_create_telegram_user(session, int(tg["id"]), tg.get("username"), tg.get("first_name"),
                                             tg.get("last_name"), tg.get("language_code"))
    if user.is_banned:
        raise HTTPException(403, "Account suspended")
    return TokenOut(access_token=create_access_token(user.id, "admin" if user.is_admin else "user"),
                    user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
async def password_login(body: PasswordLoginIn, session: AsyncSession = Depends(get_session)):
    """E-mail/password login (admin web dashboard; future web/mobile clients)."""
    user = (await session.execute(select(User).where(User.email == body.email.lower().strip()))).scalar_one_or_none()
    if user is None or not user.password_hash or not pbkdf2_sha256.verify(body.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    if user.is_banned:
        raise HTTPException(403, "Account suspended")
    audit(session, "auth.login", "user", user.id, user.id)
    await session.commit()
    return TokenOut(access_token=create_access_token(user.id, "admin" if user.is_admin else "user"),
                    user=UserOut.model_validate(user))
