"""Geolocation: distances, bounding boxes and geocoding."""
from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass

import httpx
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import City
from app.services.text import normalize

log = logging.getLogger(__name__)
EARTH_RADIUS_KM = 6371.0088
RADIUS_CHOICES_KM = (1, 5, 10, 20, 50)
POSTAL_RE = re.compile(r"\b(\d{5})\b")


@dataclass
class GeoPoint:
    lat: float
    lon: float
    label: str | None = None
    postal_code: str | None = None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def bounding_box(lat: float, lon: float, radius_km: float) -> tuple[float, float, float, float]:
    dlat = math.degrees(radius_km / EARTH_RADIUS_KM)
    dlon = math.degrees(radius_km / (EARTH_RADIUS_KM * max(0.01, math.cos(math.radians(lat)))))
    return lat - dlat, lat + dlat, lon - dlon, lon + dlon


def sql_distance_km(lat_col, lon_col, lat: float, lon: float):
    """Haversine expression computed by PostgreSQL."""
    return (
        2
        * EARTH_RADIUS_KM
        * func.asin(
            func.sqrt(
                func.power(func.sin(func.radians(lat_col - lat) / 2), 2)
                + func.cos(func.radians(lat))
                * func.cos(func.radians(lat_col))
                * func.power(func.sin(func.radians(lon_col - lon) / 2), 2)
            )
        )
    )


def estimate_travel_minutes(distance_km: float) -> int:
    """Rough estimate (labelled as such in the UI): average urban speed."""
    return max(5, round(distance_km / settings.average_travel_speed_kmh * 60))


async def geocode(session: AsyncSession, query: str) -> GeoPoint | None:
    """Resolve a city name, postal code or address to coordinates."""
    query = (query or "").strip()
    if not query:
        return None
    point = await _geocode_local(session, query)
    if point is None and settings.geocoder == "nominatim":
        point = await _geocode_nominatim(query)
    return point


async def _geocode_local(session: AsyncSession, query: str) -> GeoPoint | None:
    m = POSTAL_RE.search(query)
    if m:
        cp = m.group(1)
        city = (
            await session.execute(select(City).where(City.postal_code == cp).order_by(City.population.desc()).limit(1))
        ).scalar_one_or_none()
        if city is None:  # same department, nearest known city
            city = (
                await session.execute(
                    select(City).where(City.postal_code.like(cp[:2] + "%")).order_by(City.population.desc()).limit(1)
                )
            ).scalar_one_or_none()
        if city:
            return GeoPoint(city.lat, city.lon, city.name, cp)
    norm = normalize(query).replace("-", " ")
    if not norm:
        return None
    city = (
        await session.execute(
            select(City)
            .where(or_(City.name_norm == norm, City.name_norm.like(norm + " %")))
            .order_by(City.population.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if city:
        return GeoPoint(city.lat, city.lon, city.name, city.postal_code)
    return None


async def find_city_in_text(session: AsyncSession, text: str) -> GeoPoint | None:
    """Find a known city mentioned anywhere in free text (longest match wins)."""
    norm = " " + normalize(text).replace("-", " ") + " "
    m = POSTAL_RE.search(text)
    if m:
        p = await _geocode_local(session, m.group(1))
        if p:
            return p
    rows = (await session.execute(select(City.name_norm, City.id).order_by(City.population.desc()))).all()
    best = None
    for name_norm, city_id in rows:
        if f" {name_norm} " in norm and (best is None or len(name_norm) > len(best[0])):
            best = (name_norm, city_id)
    if best:
        city = await session.get(City, best[1])
        return GeoPoint(city.lat, city.lon, city.name, city.postal_code)
    return None


async def _geocode_nominatim(query: str) -> GeoPoint | None:
    try:
        async with httpx.AsyncClient(timeout=8, headers={"User-Agent": settings.nominatim_user_agent}) as client:
            r = await client.get(
                f"{settings.nominatim_url}/search",
                params={"q": query, "format": "json", "limit": 1, "countrycodes": "fr", "addressdetails": 1},
            )
            r.raise_for_status()
            data = r.json()
    except Exception as exc:  # network errors must never break the bot
        log.warning("Nominatim geocoding failed: %s", exc)
        return None
    if not data:
        return None
    item = data[0]
    addr = item.get("address", {})
    label = addr.get("city") or addr.get("town") or addr.get("village") or item.get("display_name", "")[:60]
    return GeoPoint(float(item["lat"]), float(item["lon"]), label, addr.get("postcode"))


async def reverse_city(session: AsyncSession, lat: float, lon: float) -> str | None:
    """Nearest known city for a GPS position (local table)."""
    dist = sql_distance_km(City.lat, City.lon, lat, lon)
    row = (await session.execute(select(City.name, dist.label("d")).order_by(dist).limit(1))).first()
    if row and row.d < 30:
        return row.name
    return None
