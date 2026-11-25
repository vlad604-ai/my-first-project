from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.security import AuthError, decode_access_token
from app.db import get_session
from app.models import Professional, User
from app.services import professionals as pro_service

bearer = HTTPBearer(auto_error=False)


async def current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: AsyncSession = Depends(get_session),
) -> User:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        payload = decode_access_token(creds.credentials)
    except AuthError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token") from exc
    user = await session.get(User, int(payload["sub"]))
    if user is None or user.deleted_at is not None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unknown user")
    if user.is_banned:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account suspended")
    return user


async def optional_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: AsyncSession = Depends(get_session),
) -> User | None:
    if creds is None:
        return None
    try:
        return await current_user(creds, session)
    except HTTPException:
        return None


async def admin_user(user: User = Depends(current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin only")
    return user


async def current_pro(user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> Professional:
    pro = await pro_service.get_pro_for_user(session, user)
    if pro is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Professional account required")
    return pro
