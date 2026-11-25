"""Authentication: Telegram Mini App initData validation and JWT tokens."""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qsl

from jose import JWTError, jwt

from app.config import settings


class AuthError(Exception):
    pass


def validate_telegram_init_data(init_data: str, bot_token: str | None = None, max_age_seconds: int = 86400) -> dict:
    """Validate `Telegram.WebApp.initData` (https://core.telegram.org/bots/webapps#validating-data).

    Returns the parsed `user` object. Raises AuthError if the signature is invalid or too old.
    """
    token = bot_token or settings.telegram_bot_token
    if not token:
        raise AuthError("bot token not configured")
    pairs = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=False))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise AuthError("missing hash")
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret_key = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    computed = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed, received_hash):
        raise AuthError("invalid signature")
    auth_date = int(pairs.get("auth_date", "0"))
    if max_age_seconds and time.time() - auth_date > max_age_seconds:
        raise AuthError("init data expired")
    try:
        return json.loads(pairs.get("user", "{}"))
    except json.JSONDecodeError as exc:
        raise AuthError("invalid user payload") from exc


def sign_init_data(user: dict, bot_token: str, auth_date: int | None = None) -> str:
    """Build a valid initData string (used by tests and local development tools)."""
    from urllib.parse import urlencode

    pairs = {"auth_date": str(auth_date or int(time.time())), "user": json.dumps(user, separators=(",", ":"))}
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    pairs["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(pairs)


def create_access_token(user_id: int, role: str = "user", expires_minutes: int | None = None) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes or settings.jwt_expire_minutes)
    return jwt.encode({"sub": str(user_id), "role": role, "exp": exp}, settings.secret_key,
                      algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise AuthError("invalid token") from exc
