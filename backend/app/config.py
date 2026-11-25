"""Application configuration loaded from environment variables (.env)."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore")

    # --- General ---
    app_name: str = "Universal Booking"
    environment: str = "development"  # development | production | test
    debug: bool = False
    log_level: str = "INFO"
    default_language: str = "fr"
    supported_languages: list[str] = ["fr", "en"]
    default_timezone: str = "Europe/Paris"
    holiday_country: str = "FR"

    # --- Database / cache ---
    database_url: str = "postgresql+asyncpg://ub:ub@localhost:5432/universal_booking"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    redis_url: str = "redis://localhost:6379/0"

    # --- Security ---
    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24
    cors_origins: list[str] = ["http://localhost:5173"]
    admin_email: str = "admin@example.com"
    admin_password: str = "change-me"
    rate_limit_per_minute: int = 30  # bot messages per user per minute

    # --- Telegram ---
    telegram_bot_token: str = ""
    telegram_bot_username: str = ""
    telegram_webhook_url: str = ""  # e.g. https://api.example.com ; empty => long polling
    telegram_webhook_secret: str = "change-me-webhook-secret"
    webapp_url: str = ""  # public URL of the Mini App (https), optional
    admin_telegram_ids: list[int] = Field(default_factory=list)

    # --- AI ---
    ai_enabled: bool = True
    anthropic_api_key: str = ""
    ai_model: str = "claude-opus-5-5"
    ai_effort: str = "low"
    ai_timeout_seconds: float = 20.0

    # --- Geocoding ---
    geocoder: str = "local"  # local | nominatim
    nominatim_url: str = "https://nominatim.openstreetmap.org"
    nominatim_user_agent: str = "universal-booking/1.0"
    average_travel_speed_kmh: float = 30.0

    # --- Business rules ---
    auto_approve_professionals: bool = False
    pending_booking_timeout_hours: int = 24
    quote_request_max_recipients: int = 15
    quote_request_ttl_days: int = 14
    search_max_candidates: int = 300
    payments_enabled: bool = False  # monetisation architecture ready, disabled in v1

    @property
    def is_test(self) -> bool:
        return self.environment == "test"

    def check_production(self) -> None:
        """Refuse to run in production with default secrets."""
        if self.environment != "production":
            return
        weak = [name for name, value in (("SECRET_KEY", self.secret_key), ("ADMIN_PASSWORD", self.admin_password),
                                         ("TELEGRAM_WEBHOOK_SECRET", self.telegram_webhook_secret))
                if value.startswith("change-me") or len(value) < 12]
        if weak:
            raise RuntimeError(f"Insecure production configuration, set: {', '.join(weak)}")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
