"""All ORM models.

Kept in a single module so relationships resolve without import cycles;
grouped by domain with section comments.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, time

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Table,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, TimestampMixin
from app.models.enums import (
    BookingLocation,
    BookingStatus,
    PriceType,
    ProStatus,
    QuoteRequestStatus,
    QuoteStatus,
    RecipientStatus,
    ReportStatus,
    ReportTarget,
    ReviewStatus,
    SubscriptionStatus,
    Urgency,
    WorkMode,
)


def _enum(e, name: str):
    return Enum(e, name=name, values_callable=lambda x: [m.value for m in x], native_enum=False, length=32)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Channel identities. Telegram is the first channel, but not the only one.
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    username: Mapped[str | None] = mapped_column(String(64))
    first_name: Mapped[str | None] = mapped_column(String(128))
    last_name: Mapped[str | None] = mapped_column(String(128))
    phone: Mapped[str | None] = mapped_column(String(32))
    language: Mapped[str] = mapped_column(String(8), default="fr", server_default="fr")
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    last_lat: Mapped[float | None] = mapped_column(Float)
    last_lon: Mapped[float | None] = mapped_column(Float)
    last_city: Mapped[str | None] = mapped_column(String(128))
    search_radius_km: Mapped[int] = mapped_column(Integer, default=10, server_default="10")
    gdpr_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    professional: Mapped[Professional | None] = relationship(back_populates="user", uselist=False)

    @property
    def display_name(self) -> str:
        parts = [p for p in (self.first_name, self.last_name) if p]
        if parts:
            return " ".join(parts)
        return f"@{self.username}" if self.username else f"Utilisateur #{self.id}"


# ---------------------------------------------------------------------------
# Catalog: categories (tree) and geocoding reference
# ---------------------------------------------------------------------------
class Category(TimestampMixin, Base):
    """Category or sub-category (parent_id != NULL). New trades are data, not code."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), index=True)
    names: Mapped[dict] = mapped_column(JSONB, default=dict)  # {"fr": "...", "en": "..."}
    icon: Mapped[str | None] = mapped_column(String(16))
    keywords: Mapped[list] = mapped_column(JSONB, default=list)  # NLU synonyms (lowercase)
    default_work_mode: Mapped[WorkMode] = mapped_column(_enum(WorkMode, "work_mode"), default=WorkMode.ON_SITE)
    supports_instant: Mapped[bool] = mapped_column(Boolean, default=True)
    supports_quotes: Mapped[bool] = mapped_column(Boolean, default=False)
    is_health: Mapped[bool] = mapped_column(Boolean, default=False)  # stricter data rules
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    parent: Mapped[Category | None] = relationship(remote_side="Category.id", back_populates="children")
    children: Mapped[list[Category]] = relationship(back_populates="parent", order_by="Category.sort_order")

    def name(self, lang: str = "fr") -> str:
        return self.names.get(lang) or self.names.get("fr") or self.slug


class City(Base):
    """Local geocoding reference (city / postal code -> coordinates)."""

    __tablename__ = "cities"
    __table_args__ = (Index("ix_cities_name_norm", "name_norm"), Index("ix_cities_postal", "postal_code"))

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    name_norm: Mapped[str] = mapped_column(String(128))
    postal_code: Mapped[str] = mapped_column(String(10))
    department: Mapped[str | None] = mapped_column(String(64))
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    population: Mapped[int] = mapped_column(Integer, default=0)


# ---------------------------------------------------------------------------
# Professionals
# ---------------------------------------------------------------------------
professional_categories = Table(
    "professional_categories",
    Base.metadata,
    Column("professional_id", ForeignKey("professionals.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)


class Professional(TimestampMixin, Base):
    __tablename__ = "professionals"
    __table_args__ = (
        Index("ix_professionals_geo", "lat", "lon"),
        Index("ix_professionals_status_category", "status", "category_id"),
        CheckConstraint("service_radius_km >= 0", name="radius_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    business_name: Mapped[str] = mapped_column(String(160))
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True)
    specialties: Mapped[list] = mapped_column(JSONB, default=list)
    work_mode: Mapped[WorkMode] = mapped_column(_enum(WorkMode, "work_mode"), default=WorkMode.ON_SITE)

    # Location
    address: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(128))
    postal_code: Mapped[str | None] = mapped_column(String(10), index=True)
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)
    service_radius_km: Mapped[int] = mapped_column(Integer, default=0)  # mobile pros
    travel_buffer_min: Mapped[int] = mapped_column(Integer, default=0)  # time between interventions

    # Contact & media
    phone: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(255))
    logo_file_id: Mapped[str | None] = mapped_column(String(255))  # Telegram file_id
    logo_url: Mapped[str | None] = mapped_column(String(512))

    # Status / trust
    status: Mapped[ProStatus] = mapped_column(_enum(ProStatus, "pro_status"), default=ProStatus.PENDING)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Booking rules
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Paris")
    auto_confirm: Mapped[bool] = mapped_column(Boolean, default=True)
    slot_step_min: Mapped[int] = mapped_column(Integer, default=15)
    min_notice_min: Mapped[int] = mapped_column(Integer, default=60)
    max_advance_days: Mapped[int] = mapped_column(Integer, default=60)
    closed_on_holidays: Mapped[bool] = mapped_column(Boolean, default=True)

    # Instant availability ("Disponible maintenant") for urgent interventions
    accepts_urgent: Mapped[bool] = mapped_column(Boolean, default=False)
    on_duty_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Quotes
    accepts_quotes: Mapped[bool] = mapped_column(Boolean, default=False)
    quote_keywords: Mapped[list] = mapped_column(JSONB, default=list)  # types of jobs wanted
    quote_min_budget_cents: Mapped[int | None] = mapped_column(Integer)

    # Denormalised counters (kept in sync by services)
    rating_avg: Mapped[float] = mapped_column(Float, default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    completed_count: Mapped[int] = mapped_column(Integer, default=0)

    # Monetisation
    sponsored_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="professional")
    category: Mapped[Category] = relationship(lazy="selectin")
    extra_categories: Mapped[list[Category]] = relationship(secondary=professional_categories)
    services: Mapped[list[Service]] = relationship(
        back_populates="professional", cascade="all, delete-orphan", order_by="Service.id", lazy="selectin"
    )
    working_hours: Mapped[list[WorkingHours]] = relationship(
        back_populates="professional", cascade="all, delete-orphan"
    )
    time_off: Mapped[list[TimeOff]] = relationship(back_populates="professional", cascade="all, delete-orphan")
    photos: Mapped[list[ProfessionalPhoto]] = relationship(
        back_populates="professional", cascade="all, delete-orphan", order_by="ProfessionalPhoto.sort_order"
    )

    @property
    def is_mobile(self) -> bool:
        return self.work_mode in (WorkMode.MOBILE, WorkMode.BOTH)

    @property
    def is_on_site(self) -> bool:
        return self.work_mode in (WorkMode.ON_SITE, WorkMode.BOTH)


class ProfessionalPhoto(Base):
    __tablename__ = "professional_photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    professional_id: Mapped[int] = mapped_column(ForeignKey("professionals.id", ondelete="CASCADE"), index=True)
    file_id: Mapped[str | None] = mapped_column(String(255))
    url: Mapped[str | None] = mapped_column(String(512))
    caption: Mapped[str | None] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    professional: Mapped[Professional] = relationship(back_populates="photos")


class Service(TimestampMixin, Base):
    __tablename__ = "services"
    __table_args__ = (
        CheckConstraint("duration_min > 0 AND duration_min <= 1440", name="duration_range"),
        CheckConstraint("price_cents IS NULL OR price_cents >= 0", name="price_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    professional_id: Mapped[int] = mapped_column(ForeignKey("professionals.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(Text)
    duration_min: Mapped[int] = mapped_column(Integer, default=30)
    price_cents: Mapped[int | None] = mapped_column(Integer)
    price_type: Mapped[PriceType] = mapped_column(_enum(PriceType, "price_type"), default=PriceType.FIXED)
    location: Mapped[BookingLocation] = mapped_column(
        _enum(BookingLocation, "booking_location"), default=BookingLocation.ON_SITE
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    professional: Mapped[Professional] = relationship(back_populates="services")


class WorkingHours(Base):
    """Weekly opening intervals. Several rows per weekday model breaks (pauses)."""

    __tablename__ = "working_hours"
    __table_args__ = (
        CheckConstraint("weekday BETWEEN 0 AND 6", name="weekday_range"),
        CheckConstraint("end_time > start_time", name="interval_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    professional_id: Mapped[int] = mapped_column(ForeignKey("professionals.id", ondelete="CASCADE"), index=True)
    weekday: Mapped[int] = mapped_column(SmallInteger)  # 0 = Monday
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)

    professional: Mapped[Professional] = relationship(back_populates="working_hours")


class TimeOff(Base):
    """Closures / holidays / absences of a professional."""

    __tablename__ = "time_off"
    __table_args__ = (CheckConstraint("end_at > start_at", name="interval_order"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    professional_id: Mapped[int] = mapped_column(ForeignKey("professionals.id", ondelete="CASCADE"), index=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str | None] = mapped_column(String(255))

    professional: Mapped[Professional] = relationship(back_populates="time_off")


class CustomHoliday(Base):
    """Platform-wide extra closed days (in addition to computed public holidays)."""

    __tablename__ = "custom_holidays"

    id: Mapped[int] = mapped_column(primary_key=True)
    country: Mapped[str] = mapped_column(String(2), default="FR")
    day: Mapped[date] = mapped_column(Date)
    name: Mapped[str] = mapped_column(String(128))


# ---------------------------------------------------------------------------
# Bookings
# ---------------------------------------------------------------------------
class Booking(TimestampMixin, Base):
    """A reservation.

    `block_end_at` = end_at + travel buffer. A PostgreSQL exclusion constraint
    (created in the migration) forbids two active bookings of the same
    professional whose [start_at, block_end_at) ranges overlap: double bookings
    are impossible even under concurrency.
    """

    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("end_at > start_at", name="interval_order"),
        CheckConstraint("block_end_at >= end_at", name="block_after_end"),
        Index("ix_bookings_pro_start", "professional_id", "start_at"),
        Index("ix_bookings_client", "client_id", "start_at"),
        Index("ix_bookings_status_start", "status", "start_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reference: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    professional_id: Mapped[int] = mapped_column(ForeignKey("professionals.id", ondelete="CASCADE"))
    service_id: Mapped[int | None] = mapped_column(ForeignKey("services.id", ondelete="SET NULL"))
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    block_end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[BookingStatus] = mapped_column(
        _enum(BookingStatus, "booking_status"), default=BookingStatus.PENDING
    )
    location: Mapped[BookingLocation] = mapped_column(
        _enum(BookingLocation, "booking_location"), default=BookingLocation.ON_SITE
    )
    address: Mapped[str | None] = mapped_column(String(255))
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)
    client_note: Mapped[str | None] = mapped_column(String(1000))  # never medical data
    service_name: Mapped[str | None] = mapped_column(String(160))  # snapshot
    price_cents: Mapped[int | None] = mapped_column(Integer)  # snapshot
    is_urgent: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String(16), default="telegram")
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_by: Mapped[str | None] = mapped_column(String(16))  # client | professional | system | admin
    cancel_reason: Mapped[str | None] = mapped_column(String(255))
    reminder_24h_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reminder_1h_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    commission_cents: Mapped[int | None] = mapped_column(Integer)  # monetisation hook

    client: Mapped[User] = relationship(foreign_keys=[client_id])
    professional: Mapped[Professional] = relationship()
    service: Mapped[Service | None] = relationship()
    events: Mapped[list[BookingEvent]] = relationship(
        back_populates="booking", cascade="all, delete-orphan", order_by="BookingEvent.id"
    )


class BookingEvent(Base):
    __tablename__ = "booking_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(32))
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    data: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    booking: Mapped[Booking] = relationship(back_populates="events")


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------
class Review(TimestampMixin, Base):
    __tablename__ = "reviews"
    __table_args__ = (CheckConstraint("rating BETWEEN 1 AND 5", name="rating_range"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"), unique=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    professional_id: Mapped[int] = mapped_column(ForeignKey("professionals.id", ondelete="CASCADE"), index=True)
    rating: Mapped[int] = mapped_column(SmallInteger)
    comment: Mapped[str | None] = mapped_column(Text)
    photos: Mapped[list] = mapped_column(JSONB, default=list)  # Telegram file_ids
    status: Mapped[ReviewStatus] = mapped_column(_enum(ReviewStatus, "review_status"), default=ReviewStatus.PENDING)
    moderation_reason: Mapped[str | None] = mapped_column(String(255))
    pro_reply: Mapped[str | None] = mapped_column(Text)

    client: Mapped[User] = relationship()
    professional: Mapped[Professional] = relationship()


# ---------------------------------------------------------------------------
# Quote requests (devis)
# ---------------------------------------------------------------------------
class QuoteRequest(TimestampMixin, Base):
    __tablename__ = "quote_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    description: Mapped[str] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(128))
    postal_code: Mapped[str | None] = mapped_column(String(10))
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)
    budget_cents: Mapped[int | None] = mapped_column(Integer)
    urgency: Mapped[Urgency] = mapped_column(_enum(Urgency, "urgency"), default=Urgency.FLEXIBLE)
    status: Mapped[QuoteRequestStatus] = mapped_column(
        _enum(QuoteRequestStatus, "quote_request_status"), default=QuoteRequestStatus.OPEN
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    client: Mapped[User] = relationship()
    category: Mapped[Category] = relationship()
    recipients: Mapped[list[QuoteRecipient]] = relationship(back_populates="request", cascade="all, delete-orphan")
    quotes: Mapped[list[Quote]] = relationship(back_populates="request", cascade="all, delete-orphan")


class QuoteRecipient(Base):
    __tablename__ = "quote_recipients"
    __table_args__ = (UniqueConstraint("request_id", "professional_id", name="uq_quote_recipient"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("quote_requests.id", ondelete="CASCADE"), index=True)
    professional_id: Mapped[int] = mapped_column(ForeignKey("professionals.id", ondelete="CASCADE"), index=True)
    status: Mapped[RecipientStatus] = mapped_column(
        _enum(RecipientStatus, "recipient_status"), default=RecipientStatus.SENT
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    request: Mapped[QuoteRequest] = relationship(back_populates="recipients")
    professional: Mapped[Professional] = relationship()


class Quote(TimestampMixin, Base):
    __tablename__ = "quotes"
    __table_args__ = (UniqueConstraint("request_id", "professional_id", name="uq_quote_per_pro"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("quote_requests.id", ondelete="CASCADE"), index=True)
    professional_id: Mapped[int] = mapped_column(ForeignKey("professionals.id", ondelete="CASCADE"), index=True)
    amount_cents: Mapped[int] = mapped_column(Integer)
    message: Mapped[str | None] = mapped_column(Text)
    estimated_days: Mapped[int | None] = mapped_column(Integer)
    valid_until: Mapped[date | None] = mapped_column(Date)
    status: Mapped[QuoteStatus] = mapped_column(_enum(QuoteStatus, "quote_status"), default=QuoteStatus.SENT)

    request: Mapped[QuoteRequest] = relationship(back_populates="quotes")
    professional: Mapped[Professional] = relationship()


# ---------------------------------------------------------------------------
# Social: favorites, messages, reports
# ---------------------------------------------------------------------------
class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "professional_id", name="uq_favorite"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    professional_id: Mapped[int] = mapped_column(ForeignKey("professionals.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    professional: Mapped[Professional] = relationship()


class Message(Base):
    """Client <-> professional messages (thread = client_id + professional_id)."""

    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_thread", "client_id", "professional_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    professional_id: Mapped[int] = mapped_column(ForeignKey("professionals.id", ondelete="CASCADE"))
    sender_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    body: Mapped[str] = mapped_column(Text)
    booking_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("bookings.id", ondelete="SET NULL"))
    quote_request_id: Mapped[int | None] = mapped_column(ForeignKey("quote_requests.id", ondelete="SET NULL"))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Report(TimestampMixin, Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    target_type: Mapped[ReportTarget] = mapped_column(_enum(ReportTarget, "report_target"))
    target_id: Mapped[str] = mapped_column(String(64))
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[ReportStatus] = mapped_column(_enum(ReportStatus, "report_status"), default=ReportStatus.OPEN)
    admin_note: Mapped[str | None] = mapped_column(Text)


# ---------------------------------------------------------------------------
# Monetisation (ready, payments disabled in v1)
# ---------------------------------------------------------------------------
class Plan(TimestampMixin, Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(64))
    price_cents_monthly: Mapped[int] = mapped_column(Integer, default=0)
    commission_bps: Mapped[int] = mapped_column(Integer, default=0)  # 100 bps = 1 %
    features: Mapped[dict] = mapped_column(JSONB, default=dict)
    ranking_boost: Mapped[float] = mapped_column(Float, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Subscription(TimestampMixin, Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    professional_id: Mapped[int] = mapped_column(ForeignKey("professionals.id", ondelete="CASCADE"), index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"))
    status: Mapped[SubscriptionStatus] = mapped_column(
        _enum(SubscriptionStatus, "subscription_status"), default=SubscriptionStatus.ACTIVE
    )
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    provider: Mapped[str | None] = mapped_column(String(32))  # stripe, telegram_stars, ...
    provider_ref: Mapped[str | None] = mapped_column(String(128))

    plan: Mapped[Plan] = relationship()


class PlatformSetting(Base):
    __tablename__ = "platform_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[dict] = mapped_column(JSONB, default=dict)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_entity", "entity", "entity_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(64))
    entity: Mapped[str] = mapped_column(String(32))
    entity_id: Mapped[str | None] = mapped_column(String(64))
    data: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
