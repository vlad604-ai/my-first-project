"""Seed reference data (categories, cities, plans) and optional demo data.

Usage:
    python -m scripts.seed            # reference data only (idempotent)
    python -m scripts.seed --demo     # + demo professionals, clients, bookings, reviews
"""
from __future__ import annotations

import argparse
import asyncio
import random
from datetime import datetime, time, timedelta, timezone

from passlib.hash import pbkdf2_sha256
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.data.categories import CATEGORIES
from app.data.cities_fr import CITIES_FR
from app.db import SessionLocal
from app.models import (
    Booking,
    BookingLocation,
    BookingStatus,
    Category,
    City,
    Plan,
    PriceType,
    Professional,
    ProStatus,
    Review,
    ReviewStatus,
    Service,
    User,
    WorkingHours,
    WorkMode,
)
from app.services.reviews import recompute_rating
from app.services.text import booking_reference, normalize, slugify

UTC = timezone.utc


async def seed_categories(session: AsyncSession) -> int:
    count = 0

    async def upsert(data: dict, parent: Category | None, order: int) -> Category:
        nonlocal count
        cat = (await session.execute(select(Category).where(Category.slug == data["slug"]))).scalar_one_or_none()
        mode = data.get("mode") or (parent.default_work_mode.value if parent else "on_site")
        values = dict(
            names={"fr": data["fr"], "en": data["en"]}, icon=data.get("icon"),
            keywords=data.get("keywords", []), default_work_mode=WorkMode(mode),
            supports_quotes=data.get("quotes", parent.supports_quotes if parent else False),
            is_health=data.get("health", parent.is_health if parent else False),
            parent_id=parent.id if parent else None, sort_order=order,
        )
        if cat is None:
            cat = Category(slug=data["slug"], **values)
            session.add(cat)
            count += 1
        else:
            for k, v in values.items():
                setattr(cat, k, v)
        await session.flush()
        for i, child in enumerate(data.get("children", [])):
            await upsert(child, cat, i)
        return cat

    for i, root in enumerate(CATEGORIES):
        await upsert(root, None, i)
    return count


async def seed_cities(session: AsyncSession) -> int:
    existing = set((await session.execute(select(City.postal_code))).scalars().all())
    n = 0
    for name, cp, dept, lat, lon, pop in CITIES_FR:
        if cp in existing:
            continue
        session.add(City(name=name, name_norm=normalize(name).replace("-", " "), postal_code=cp, department=dept,
                         lat=lat, lon=lon, population=pop))
        n += 1
    return n


async def seed_plans(session: AsyncSession) -> None:
    plans = [
        ("free", "Gratuit", 0, 0, 0.0, {"max_services": 5, "max_photos": 5, "quotes_per_month": 5}),
        ("pro", "Pro", 1900, 0, 0.5, {"max_services": 30, "max_photos": 20, "quotes_per_month": 50,
                                      "stats": True}),
        ("premium", "Premium", 4900, 0, 1.0, {"max_services": 100, "max_photos": 20, "quotes_per_month": None,
                                              "stats": True, "highlight": True}),
        ("commission", "Commission", 0, 800, 0.2, {"max_services": 30, "paid_bookings": True}),
    ]
    for code, name, price, bps, boost, features in plans:
        if (await session.execute(select(Plan).where(Plan.code == code))).scalar_one_or_none() is None:
            session.add(Plan(code=code, name=name, price_cents_monthly=price, commission_bps=bps,
                             ranking_boost=boost, features=features))


async def seed_admin(session: AsyncSession) -> None:
    admin = (await session.execute(select(User).where(User.email == settings.admin_email))).scalar_one_or_none()
    if admin is None:
        session.add(User(email=settings.admin_email, password_hash=pbkdf2_sha256.hash(settings.admin_password),
                         first_name="Admin", is_admin=True, language="fr"))


async def seed_reference(session: AsyncSession) -> None:
    await seed_categories(session)
    await seed_cities(session)
    await seed_plans(session)
    await session.commit()


# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------
HOURS = {
    "office": {d: [(time(9), time(12)), (time(14), time(18))] for d in range(5)},
    "salon": {d: [(time(9, 30), time(12, 30)), (time(13, 30), time(19))] for d in range(1, 6)},
    "artisan": {d: [(time(8), time(18))] for d in range(6)},
    "garage": {**{d: [(time(8), time(12)), (time(14), time(18, 30))] for d in range(5)},
               5: [(time(9), time(12))]},
    "restaurant": {d: [(time(12), time(14, 30)), (time(19), time(22, 30))] for d in range(1, 7)},
}

DEMO_PROS = [
    # name, category, city, mode, radius, hours, description, services[(name, min, eur, loc)]
    ("Plomberie Express Paris", "plombier", "Paris 11e", "mobile", 15, "artisan",
     "Dépannage plomberie 7j/7 : fuites, WC bouchés, chauffe-eau. Intervention rapide.",
     [("Recherche et réparation de fuite", 60, 90, "at_client"), ("Débouchage canalisation", 45, 80, "at_client"),
      ("Remplacement chauffe-eau", 180, None, "at_client")]),
    ("Aqua Services Boulogne", "plombier", "Boulogne-Billancourt", "mobile", 12, "artisan",
     "Plombier chauffagiste, devis gratuit, artisan certifié RGE.",
     [("Réparation fuite d'eau", 60, 85, "at_client"), ("Installation robinetterie", 60, 70, "at_client")]),
    ("Volt & Co Électricité", "electricien", "Boulogne-Billancourt", "mobile", 15, "artisan",
     "Électricien qualifié : installation de prises, tableaux électriques, mise aux normes.",
     [("Installation de prise électrique", 45, 60, "at_client"), ("Diagnostic panne électrique", 60, 75, "at_client"),
      ("Mise aux normes tableau", 240, None, "at_client")]),
    ("Lumière Électrique Paris", "electricien", "Paris 15e", "mobile", 10, "artisan",
     "Dépannage électrique et installation d'éclairage.",
     [("Pose de luminaire", 60, 65, "at_client"), ("Installation de 3 prises", 90, 150, "at_client")]),
    ("Serrurerie Rapide 75", "serrurier", "Paris 9e", "mobile", 10, "artisan",
     "Ouverture de porte claquée en 30 min, changement de serrure.",
     [("Ouverture de porte claquée", 30, 89, "at_client"), ("Changement de serrure", 60, 150, "at_client")]),
    ("Rénov'Habitat", "renovation", "Boulogne-Billancourt", "mobile", 25, "office",
     "Rénovation complète : salles de bain, cuisines, appartements. Devis détaillé sous 48h.",
     [("Visite technique et devis", 60, 0, "at_client")]),
    ("Atelier Bois & Cuisine", "menuisier", "Paris 12e", "mobile", 20, "artisan",
     "Menuisier agenceur : cuisines équipées, placards sur mesure, parquets.",
     [("Pose de cuisine équipée", 480, None, "at_client"), ("Métré et conseil", 60, 50, "at_client")]),
    ("Couleurs de Paris", "peintre", "Paris 17e", "mobile", 15, "artisan",
     "Peinture intérieure, papier peint, ravalement.",
     [("Devis peinture sur place", 45, 0, "at_client")]),
    ("Dr Claire Martin", "medecin-generaliste", "Paris 15e", "on_site", 0, "office",
     "Médecin généraliste conventionné secteur 1.",
     [("Consultation", 20, 30, "on_site"), ("Téléconsultation", 15, 30, "on_site")]),
    ("Dr Karim Benali", "medecin-generaliste", "Boulogne-Billancourt", "on_site", 0, "office",
     "Médecine générale, suivi des enfants et adultes.", [("Consultation", 20, 30, "on_site")]),
    ("Cabinet Dentaire du Parc", "dentiste", "Paris 16e", "on_site", 0, "office",
     "Soins dentaires, détartrage, urgences dentaires.",
     [("Consultation dentaire", 30, 30, "on_site"), ("Détartrage", 45, 60, "on_site")]),
    ("Sourire Boulogne", "dentiste", "Boulogne-Billancourt", "on_site", 0, "office",
     "Centre dentaire ouvert le vendredi soir.", [("Bilan dentaire", 30, 30, "on_site")]),
    ("Kiné Santé Montrouge", "kinesitherapeute", "Montrouge", "both", 5, "office",
     "Rééducation, kiné du sport, à domicile possible.",
     [("Séance de kinésithérapie", 30, 35, "on_site"), ("Séance à domicile", 30, 45, "at_client")]),
    ("Studio Coupe Homme", "coiffeur", "Paris 11e", "on_site", 0, "salon",
     "Salon spécialisé homme : coupes modernes, dégradés.",
     [("Coupe homme", 30, 25, "on_site"), ("Coupe + barbe", 45, 35, "on_site")]),
    ("L'Atelier Coiffure", "coiffeur", "Paris 3e", "on_site", 0, "salon",
     "Coiffure mixte, couleurs végétales.",
     [("Coupe femme", 45, 45, "on_site"), ("Coupe homme", 30, 28, "on_site"), ("Couleur", 90, 70, "on_site")]),
    ("Le Barbier de Belleville", "barbier", "Paris 20e", "on_site", 0, "salon",
     "Rasage traditionnel à l'ancienne.", [("Taille de barbe", 30, 20, "on_site"), ("Rasage complet", 30, 25, "on_site")]),
    ("Nails Factory", "onglerie", "Paris 9e", "on_site", 0, "salon",
     "Manucure, pose de gel, nail art.", [("Manucure", 45, 30, "on_site"), ("Pose gel", 75, 45, "on_site")]),
    ("Zen Massage à domicile", "masseur", "Paris 7e", "mobile", 10, "salon",
     "Massages bien-être à domicile.", [("Massage relaxant 1h", 60, 80, "at_client")]),
    ("Garage du Point du Jour", "garage", "Boulogne-Billancourt", "on_site", 0, "garage",
     "Garage toutes marques ouvert le samedi matin : entretien, vidange, pneus.",
     [("Vidange", 60, 79, "on_site"), ("Révision complète", 120, 189, "on_site"),
      ("Montage de pneus", 45, 40, "on_site")]),
    ("Auto Service Bastille", "garage", "Paris 11e", "on_site", 0, "garage",
     "Entretien et réparation toutes marques.", [("Diagnostic électronique", 45, 50, "on_site"),
                                                 ("Vidange", 60, 85, "on_site")]),
    ("Méca'Mobile", "mecanicien", "Paris 15e", "mobile", 15, "artisan",
     "Mécanicien à domicile : batterie, plaquettes, diagnostic.",
     [("Changement de batterie", 45, 60, "at_client"), ("Diagnostic panne", 60, 70, "at_client")]),
    ("Cabinet Leroy Avocats", "avocat", "Paris 8e", "on_site", 0, "office",
     "Droit de la famille, droit du travail.", [("Première consultation", 60, 120, "on_site")]),
    ("Compta Facile", "comptable", "Levallois-Perret", "on_site", 0, "office",
     "Expert-comptable pour indépendants et TPE.", [("Rendez-vous découverte", 45, 0, "on_site")]),
    ("Coach Thomas Fitness", "coach-sportif", "Paris 16e", "both", 10, "artisan",
     "Coaching personnalisé, perte de poids, préparation physique.",
     [("Séance coaching 1h", 60, 55, "at_client")]),
    ("Prof Maths Réussite", "professeur-particulier", "Paris 5e", "both", 8, "office",
     "Cours de maths et physique du collège à la prépa.", [("Cours particulier 1h", 60, 40, "at_client")]),
    ("Clinique Vétérinaire Saint-Michel", "veterinaire", "Paris 6e", "on_site", 0, "office",
     "Vétérinaires chiens, chats, NAC.", [("Consultation vétérinaire", 30, 45, "on_site"),
                                          ("Vaccination", 20, 60, "on_site")]),
    ("Propre & Net Services", "nettoyage", "Issy-les-Moulineaux", "mobile", 20, "artisan",
     "Ménage à domicile et nettoyage de bureaux.", [("Ménage 2h", 120, 50, "at_client")]),
    ("Studio Lumière Photo", "photographe", "Paris 18e", "both", 30, "office",
     "Portraits, mariages, photos corporate.", [("Séance portrait", 60, 120, "on_site")]),
    ("Le Bistrot des Halles", "restaurant", "Paris", "on_site", 0, "restaurant",
     "Cuisine française de saison.", [("Table pour 2", 90, None, "on_site")]),
    ("Coiffure Lyon Presqu'île", "coiffeur", "Lyon", "on_site", 0, "salon",
     "Salon de coiffure au cœur de Lyon.", [("Coupe homme", 30, 26, "on_site"), ("Coupe femme", 45, 42, "on_site")]),
    ("Plombier Marseille Dépannage", "plombier", "Marseille", "mobile", 20, "artisan",
     "Dépannage plomberie Marseille et alentours.", [("Réparation fuite", 60, 95, "at_client")]),
]


async def seed_demo(session: AsyncSession) -> None:
    rng = random.Random(42)
    if (await session.execute(select(Professional.id).limit(1))).first():
        print("Demo data already present, skipping.")
        return
    cats = {c.slug: c for c in (await session.execute(select(Category))).scalars()}
    cities = {c.name: c for c in (await session.execute(select(City))).scalars()}

    clients = []
    for i, (fn, ln) in enumerate([("Julie", "Moreau"), ("Lucas", "Bernard"), ("Emma", "Petit"), ("Hugo", "Durand"),
                                  ("Léa", "Roux"), ("Nathan", "Fournier")]):
        u = User(telegram_id=900000000 + i, first_name=fn, last_name=ln, username=f"demo_{fn.lower()}",
                 language="fr", last_lat=48.8566, last_lon=2.3522, last_city="Paris")
        session.add(u)
        clients.append(u)
    await session.flush()

    now = datetime.now(UTC)
    for idx, (name, cat_slug, city_name, mode, radius, hours, desc, services) in enumerate(DEMO_PROS):
        city = cities[city_name]
        owner = User(telegram_id=910000000 + idx, first_name=name.split()[0], username=f"demo_pro_{idx}",
                     language="fr")
        session.add(owner)
        await session.flush()
        pro = Professional(
            user_id=owner.id, business_name=name, slug=slugify(name), description=desc,
            category_id=cats[cat_slug].id, work_mode=WorkMode(mode),
            address=f"{rng.randint(1, 120)} rue de la République", city=city.name.split(" ")[0]
            if city.name.startswith("Paris") else city.name, postal_code=city.postal_code,
            lat=city.lat + rng.uniform(-0.008, 0.008), lon=city.lon + rng.uniform(-0.01, 0.01),
            service_radius_km=radius, travel_buffer_min=20 if mode != "on_site" else 0,
            phone=f"01 {rng.randint(40, 79)} {rng.randint(10, 99)} {rng.randint(10, 99)} {rng.randint(10, 99)}",
            status=ProStatus.ACTIVE, is_verified=idx % 3 != 2, verified_at=now if idx % 3 != 2 else None,
            auto_confirm=mode == "on_site", accepts_quotes=cats[cat_slug].supports_quotes,
            accepts_urgent=mode != "on_site" and cat_slug in ("plombier", "serrurier", "electricien", "mecanicien"),
            on_duty_until=now + timedelta(hours=8) if cat_slug in ("plombier", "serrurier") else None,
            sponsored_until=now + timedelta(days=30) if idx in (0, 13) else None,
            timezone=settings.default_timezone, min_notice_min=30 if mode != "on_site" else 60,
        )
        session.add(pro)
        await session.flush()
        for wd, ranges in HOURS[hours].items():
            for a, b in ranges:
                session.add(WorkingHours(professional_id=pro.id, weekday=wd, start_time=a, end_time=b))
        svc_objs = []
        for sname, dur, eur, loc in services:
            s = Service(professional_id=pro.id, name=sname, duration_min=dur,
                        price_cents=None if eur is None else int(eur * 100),
                        price_type=PriceType.QUOTE if eur is None else PriceType.FIXED,
                        location=BookingLocation(loc))
            session.add(s)
            svc_objs.append(s)
        await session.flush()

        # Past completed bookings + reviews (historical demo data)
        for k in range(rng.randint(1, 5)):
            client = clients[(idx + k) % len(clients)]
            svc = svc_objs[0]
            start = (now - timedelta(days=rng.randint(3, 60))).replace(minute=0, second=0, microsecond=0)
            start = start.replace(hour=10 + k % 6)
            b = Booking(reference=booking_reference(), client_id=client.id, professional_id=pro.id,
                        service_id=svc.id, start_at=start, end_at=start + timedelta(minutes=svc.duration_min),
                        block_end_at=start + timedelta(minutes=svc.duration_min + pro.travel_buffer_min),
                        status=BookingStatus.COMPLETED, location=svc.location, service_name=svc.name,
                        price_cents=svc.price_cents, confirmed_at=start - timedelta(days=2), source="demo",
                        address="10 rue de Paris" if svc.location == BookingLocation.AT_CLIENT else None)
            session.add(b)
            await session.flush()
            rating = rng.choice([4, 5, 5, 5, 4, 3])
            comment = rng.choice(["Très professionnel, je recommande !", "Ponctuel et efficace.",
                                  "Travail soigné, prix correct.", "Bon accueil, un peu d'attente.",
                                  "Excellent service, merci !"])
            session.add(Review(booking_id=b.id, client_id=client.id, professional_id=pro.id, rating=rating,
                               comment=comment, status=ReviewStatus.PUBLISHED))
            pro.completed_count += 1
        await session.flush()
        await recompute_rating(session, pro.id)
    await session.commit()
    print(f"Demo data: {len(DEMO_PROS)} professionals, {len(clients)} clients.")


async def main(demo: bool) -> None:
    async with SessionLocal() as session:
        await seed_reference(session)
        await seed_admin(session)
        await session.commit()
        if demo:
            await seed_demo(session)
    print("Seed completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    asyncio.run(main(parser.parse_args().demo))
