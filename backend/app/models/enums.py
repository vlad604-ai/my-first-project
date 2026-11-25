import enum


class StrEnum(str, enum.Enum):
    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return self.value


class WorkMode(StrEnum):
    ON_SITE = "on_site"  # client comes to the establishment
    MOBILE = "mobile"  # professional travels to the client
    BOTH = "both"


class ProStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REJECTED = "rejected"


class PriceType(StrEnum):
    FIXED = "fixed"
    FROM = "from"
    QUOTE = "quote"  # price on quote only


class BookingStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    REFUSED = "refused"


ACTIVE_BOOKING_STATUSES = (BookingStatus.PENDING, BookingStatus.CONFIRMED)


class BookingLocation(StrEnum):
    ON_SITE = "on_site"
    AT_CLIENT = "at_client"


class ReviewStatus(StrEnum):
    PENDING = "pending"
    PUBLISHED = "published"
    REJECTED = "rejected"


class QuoteRequestStatus(StrEnum):
    OPEN = "open"
    AWARDED = "awarded"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class Urgency(StrEnum):
    URGENT = "urgent"
    THIS_WEEK = "this_week"
    THIS_MONTH = "this_month"
    FLEXIBLE = "flexible"


class RecipientStatus(StrEnum):
    SENT = "sent"
    DECLINED = "declined"
    RESPONDED = "responded"


class QuoteStatus(StrEnum):
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class ReportStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ReportTarget(StrEnum):
    PROFESSIONAL = "professional"
    REVIEW = "review"
    USER = "user"
    MESSAGE = "message"


class SubscriptionStatus(StrEnum):
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
