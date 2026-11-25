"""Structured representation of what the user asked for."""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

AvailabilityPreset = Literal["now", "30min", "1h", "3h", "today", "tomorrow"]


class SearchIntent(BaseModel):
    intent: Literal["search", "quote", "my_bookings", "help", "greeting", "other"] = "search"
    category_slug: str | None = None
    service_query: str | None = Field(None, description="Specific service wanted, e.g. 'coupe homme', 'fuite d'eau'")
    location_text: str | None = Field(None, description="City, postal code or address as written by the user")
    use_my_location: bool = False
    date_from: date | None = None
    date_to: date | None = None
    time_from: str | None = Field(None, description="HH:MM local time")
    time_to: str | None = Field(None, description="HH:MM local time")
    availability: AvailabilityPreset | None = None
    urgent: bool = False
    max_price_eur: float | None = None
    at_client: bool | None = Field(None, description="True if the professional must come to the client")
    radius_km: int | None = None
    quote_suggested: bool = False
    source: str = "rules"

    def merged_with(self, newer: SearchIntent) -> SearchIntent:
        """Conversational refinement: the newer message overrides, the rest is kept."""
        data = self.model_dump()
        for key, value in newer.model_dump().items():
            if key in ("intent", "source"):
                data[key] = value
            elif value not in (None, False, ""):
                data[key] = value
        # A new explicit date replaces a previous availability preset and vice versa.
        if newer.availability:
            data["date_from"] = data["date_to"] = None
        elif newer.date_from:
            data["availability"] = None
        if newer.location_text:
            data["use_my_location"] = False
        return SearchIntent(**data)

    @property
    def is_empty(self) -> bool:
        return not any([self.category_slug, self.service_query, self.location_text, self.date_from,
                        self.availability, self.max_price_eur, self.use_my_location])
