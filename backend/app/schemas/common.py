"""API schemas (shared by every client: Mini App, web, future mobile apps)."""
from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CategoryOut(ORM):
    id: int
    slug: str
    parent_id: int | None
    names: dict
    icon: str | None
    keywords: list[str] = []
    default_work_mode: str
    supports_quotes: bool
    is_health: bool
    is_active: bool
    sort_order: int
    children: list[CategoryOut] = []


class CategoryIn(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9-]{2,64}$")
    parent_id: int | None = None
    names: dict[str, str]
    icon: str | None = None
    keywords: list[str] = []
    default_work_mode: str = "on_site"
    supports_quotes: bool = False
    is_health: bool = False
    is_active: bool = True
    sort_order: int = 0


class ServiceOut(ORM):
    id: int
    name: str
    description: str | None
    duration_min: int
    price_cents: int | None
    price_type: str
    location: str
    is_active: bool


class ServiceIn(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    duration_min: int = Field(ge=5, le=1440)
    price_cents: int | None = Field(default=None, ge=0)
    price_type: str = "fixed"
    location: str | None = None
    description: str | None = None
    is_active: bool = True


class SlotOut(BaseModel):
    start: datetime
    end: datetime
    freed: bool = False


class ProSummary(ORM):
    id: int
    business_name: str
    slug: str
    description: str | None
    category_id: int
    work_mode: str
    city: str | None
    postal_code: str | None
    lat: float | None
    lon: float | None
    service_radius_km: int
    is_verified: bool
    rating_avg: float
    rating_count: int
    completed_count: int
    logo_url: str | None
    accepts_quotes: bool


class ProDetail(ProSummary):
    address: str | None
    phone: str | None
    website: str | None
    specialties: list[str] = []
    services: list[ServiceOut] = []
    timezone: str
    status: str
    hours: dict[int, list[str]] = {}
    photos: list[dict] = []


class SearchResultOut(BaseModel):
    professional: ProSummary
    distance_km: float | None
    travel_minutes: int | None
    reference_service: ServiceOut | None
    min_price_cents: int | None
    next_slots: list[SlotOut]
    on_duty: bool
    sponsored: bool
    score: float


class SearchOut(BaseModel):
    total: int
    results: list[SearchResultOut]
    understood: dict | None = None
    summary: str | None = None


class NaturalSearchIn(BaseModel):
    text: str = Field(min_length=2, max_length=1500)
    previous: dict | None = None
    lat: float | None = None
    lon: float | None = None


class BookingIn(BaseModel):
    professional_id: int
    service_id: int
    start_at: datetime
    address: str | None = None
    lat: float | None = None
    lon: float | None = None
    client_note: str | None = Field(default=None, max_length=1000)
    is_urgent: bool = False


class RescheduleIn(BaseModel):
    start_at: datetime


class CancelIn(BaseModel):
    reason: str | None = Field(default=None, max_length=255)


class BookingOut(ORM):
    id: uuid.UUID
    reference: str
    client_id: int
    professional_id: int
    service_id: int | None
    service_name: str | None
    start_at: datetime
    end_at: datetime
    status: str
    location: str
    address: str | None
    price_cents: int | None
    is_urgent: bool
    client_note: str | None
    cancel_reason: str | None
    created_at: datetime


class ReviewIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class ReviewOut(ORM):
    id: int
    booking_id: uuid.UUID
    professional_id: int
    rating: int
    comment: str | None
    status: str
    moderation_reason: str | None
    pro_reply: str | None
    created_at: datetime


class QuoteRequestIn(BaseModel):
    category_id: int
    description: str = Field(min_length=10, max_length=4000)
    city: str | None = None
    postal_code: str | None = None
    lat: float | None = None
    lon: float | None = None
    budget_cents: int | None = Field(default=None, ge=0)
    urgency: str = "flexible"
    target_pro_id: int | None = None


class QuoteIn(BaseModel):
    amount_cents: int = Field(gt=0)
    message: str | None = Field(default=None, max_length=2000)
    estimated_days: int | None = Field(default=None, ge=0)


class QuoteOut(ORM):
    id: int
    request_id: int
    professional_id: int
    amount_cents: int
    message: str | None
    estimated_days: int | None
    valid_until: date | None
    status: str
    created_at: datetime


class QuoteRequestOut(ORM):
    id: int
    client_id: int
    category_id: int
    description: str
    city: str | None
    budget_cents: int | None
    urgency: str
    status: str
    created_at: datetime
    expires_at: datetime | None
    quotes: list[QuoteOut] = []


class TimeOffIn(BaseModel):
    start_at: datetime
    end_at: datetime
    reason: str | None = None


class HoursIn(BaseModel):
    """{"0": ["09:00-12:00", "14:00-18:00"], "5": [], ...} weekday 0 = Monday."""

    weekly: dict[int, list[str]]


class MessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=3000)


class UserOut(ORM):
    id: int
    telegram_id: int | None
    username: str | None
    first_name: str | None
    last_name: str | None
    language: str
    is_admin: bool
    is_banned: bool
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


CategoryOut.model_rebuild()
