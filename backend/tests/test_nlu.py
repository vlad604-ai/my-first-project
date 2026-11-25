"""Natural-language understanding (rules engine, no API key)."""
from datetime import date, datetime, timedelta, timezone

import pytest

from app.services.ai import assistant
from app.services.ai.intent import SearchIntent

UTC = timezone.utc
NOW = datetime(2026, 11, 25, 10, 0, tzinfo=UTC)  # Wednesday


@pytest.mark.parametrize("text,slug", [
    ("Je cherche un plombier à Paris disponible demain.", "plombier"),
    ("Trouve-moi un dentiste disponible vendredi matin.", "dentiste"),
    ("J'ai besoin d'un électricien pour installer trois prises à Boulogne.", "electricien"),
    ("Je cherche un coiffeur pour une coupe homme à moins de 30 euros.", "coiffeur"),
    ("Trouve-moi un garage ouvert samedi.", "garage"),
    ("Je souhaite refaire ma salle de bain de 8 m² à Boulogne-Billancourt.", "renovation"),
    ("Je cherche un mécanicien pour réparer ma voiture.", "mecanicien"),
    ("fuite d'eau dans la cuisine", "plombier"),
    ("ma porte est claquée", "serrurier"),
])
async def test_category_detection(session, text, slug):
    intent = await assistant.understand(session, text, now=NOW)
    assert intent.category_slug == slug


async def test_full_extraction(session):
    i = await assistant.understand(session, "Je cherche un plombier à Paris disponible demain.", now=NOW)
    assert i.location_text == "paris" and i.date_from == date(2026, 11, 26)
    i = await assistant.understand(session, "Trouve-moi un dentiste disponible vendredi matin.", now=NOW)
    assert i.date_from == date(2026, 11, 27) and (i.time_from, i.time_to) == ("08:00", "12:00")
    i = await assistant.understand(session, "un coiffeur pour une coupe homme à moins de 30 euros", now=NOW)
    assert i.max_price_eur == 30 and "coupe homme" in i.service_query
    i = await assistant.understand(session, "électricien pour installer trois prises à Boulogne", now=NOW)
    assert i.location_text == "boulogne billancourt"
    i = await assistant.understand(session, "Je souhaite refaire ma salle de bain de 8 m² à Boulogne-Billancourt.",
                                   now=NOW)
    assert i.intent == "quote" and i.quote_suggested


async def test_urgency_and_presets(session):
    i = await assistant.understand(session, "serrurier urgent 75011", now=NOW)
    assert i.urgent and i.availability == "now" and i.location_text == "75011"
    i = await assistant.understand(session, "un kiné dans l'heure", now=NOW)
    assert i.availability == "1h"
    i = await assistant.understand(session, "coiffeur ce week-end", now=NOW)
    assert i.date_from == date(2026, 11, 28) and i.date_to == date(2026, 11, 29)
    i = await assistant.understand(session, "dentiste le 3 décembre vers 14h", now=NOW)
    assert i.date_from == date(2026, 12, 3) and i.time_from == "13:00" and i.time_to == "15:00"
    i = await assistant.understand(session, "garage entre 50 et 80 euros", now=NOW)
    assert i.max_price_eur == 80


async def test_conversation_refinement(session):
    first = await assistant.understand(session, "un plombier à Paris demain", now=NOW)
    refined = await assistant.understand(session, "plutôt samedi", previous=first, now=NOW)
    assert refined.category_slug == "plombier"
    assert refined.location_text == "paris"
    assert refined.date_from == date(2026, 11, 28)
    cheaper = await assistant.understand(session, "moins de 80 €", previous=refined, now=NOW)
    assert cheaper.max_price_eur == 80 and cheaper.category_slug == "plombier"


async def test_non_search_intents(session):
    assert (await assistant.understand(session, "bonjour", now=NOW)).intent == "greeting"
    assert (await assistant.understand(session, "mes rendez-vous", now=NOW)).intent == "my_bookings"
    assert (await assistant.understand(session, "merci", now=NOW)).intent == "other"
    # Unknown words become a free-text search (matched against real names/services only)
    gibberish = await assistant.understand(session, "blablabla", now=NOW)
    assert gibberish.category_slug is None and gibberish.service_query == "blablabla"


async def test_intent_to_query(session):
    intent = SearchIntent(category_slug="plombier", location_text="Boulogne-Billancourt", availability="today",
                          max_price_eur=100, at_client=True)
    resolved = await assistant.intent_to_query(session, intent, None, now=NOW)
    q = resolved.query
    assert q.category_ids and q.lat == pytest.approx(48.835, abs=0.01) and q.max_price_cents == 10000
    assert q.window_start == NOW and q.window_end > NOW and q.at_client
    unknown = await assistant.intent_to_query(session, SearchIntent(location_text="Atlantide"), None, now=NOW)
    assert unknown.location is None and unknown.location_unknown == "Atlantide"
    _ = timedelta  # keep import used
