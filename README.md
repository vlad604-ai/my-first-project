# Universal Booking — le Doctolib universel de Telegram

Plateforme de réservation multi-secteurs accessible depuis Telegram : n'importe quel client trouve n'importe quel
professionnel (santé, bâtiment, beauté, automobile, avocats, coachs, vétérinaires…), compare, réserve un créneau
réel ou demande des devis ; chaque professionnel gère son activité depuis son espace pro.

Telegram est le **premier canal**, pas une limite : toute la logique métier vit dans une couche de services
partagée, exposée par une API REST que pourront utiliser un site public, des apps iOS/Android et des espaces
client/pro web.

---

## Sommaire

1. [Fonctionnalités](#fonctionnalités)
2. [Architecture](#architecture)
3. [Démarrage rapide](#démarrage-rapide)
4. [Configuration (.env)](#configuration)
5. [Mettre le bot en ligne sur Telegram](#mettre-le-bot-en-ligne-sur-telegram)
6. [Tests](#tests)
7. [API REST](#api-rest)
8. [Sécurité, RGPD et données de santé](#sécurité-rgpd-et-données-de-santé)
9. [Ce qui n'est pas (encore) fait](#limites-connues-et-prochaines-étapes)

---

## Fonctionnalités

### Espace client (bot + Mini App)
- **Recherche en langage naturel** : « Je cherche un plombier à Paris disponible demain », « coiffeur homme à moins
  de 30 € », « garage ouvert samedi ». Métier, prestation, lieu, date/heure, urgence et budget sont extraits, puis
  la recherche est **toujours faite dans la base** (aucun professionnel, prix ou créneau inventé).
- **Affinage conversationnel** : « plutôt samedi », « moins de 80 € », « à Vincennes » modifient la recherche en cours.
- Recherche par catégorie / sous-catégorie, par position Telegram, adresse, ville ou code postal, rayon
  1/5/10/20/50 km, tri distance / note / prix / disponibilité, pagination.
- **Disponible maintenant** : maintenant, 30 min, 1 h, 3 h, aujourd'hui, demain ; créneaux libérés par une
  annulation récente signalés 🔥 ; artisans « de garde » pour les urgences (intervention validée par le pro).
- Fiches pro : logo, description, spécialités, galerie, prestations et tarifs, horaires, zone d'intervention,
  coordonnées, avis, nombre de prestations, badge **vérifié** (posé par un admin), boutons Contacter / Réserver.
- Réservation en quelques clics : prestation → calendrier 14 jours → créneau → adresse (si à domicile) → note →
  confirmation. Mes rendez-vous, historique, **déplacement**, **annulation**, favoris, messagerie avec le pro,
  signalement, avis (note, commentaire, photos) après prestation terminée.
- **Demandes de devis** : description libre → métier détecté automatiquement → diffusion aux pros pertinents
  (catégorie, zone, budget minimum, types de chantiers acceptés) → réception et **comparaison** des devis →
  acceptation → mise en relation.
- Paramètres : langue (FR/EN), position, rayon, **export RGPD** et **suppression du compte**.

### Espace professionnel (dans Telegram, `/pro`)
- Inscription guidée en 5 étapes (nom, métier, mode de travail, adresse ou zone de départ + rayon, description).
- Deux modèles : **en établissement** et **mobile** (zone d'intervention, rayon, adresse de départ, temps de
  battement entre interventions, estimation du temps de trajet).
- Tableau de bord : agenda jour par jour, demandes à valider (accepter / refuser avec motif), prestations
  (durée, prix fixe ou sur devis), horaires avec pauses, fermetures/congés (avec alerte sur les RDV en conflit),
  jours fériés, profil et photos, réglages (confirmation auto, pas des créneaux, délai de prévenance, devis,
  urgences), mode « disponible maintenant », boîte de devis, clients, statistiques, lien de partage de la fiche.

### Moteur de réservation
- Disponibilités calculées en temps réel à partir des horaires, pauses, fermetures, jours fériés (calcul local,
  Pâques compris), réservations existantes, temps de déplacement, délai de prévenance et horizon maximal.
- Statuts : `pending`, `confirmed`, `cancelled`, `completed`, `refused` ; identifiant UUID + référence lisible
  (`UB-XXXXXXX`) ; historique d'événements par réservation.
- **Doubles réservations impossibles**, sur trois niveaux :
  1. verrou `SELECT … FOR UPDATE` sur le professionnel (sérialise les tentatives concurrentes) ;
  2. revalidation du créneau par le moteur de disponibilités juste avant l'insertion ;
  3. **contrainte d'exclusion PostgreSQL** (`EXCLUDE USING gist` sur `tstzrange(début, fin + battement)`), qui
     rejette tout chevauchement même en cas d'insertion directe en base. Testé avec 8 réservations concurrentes.

### Notifications Telegram (worker)
Client : confirmation, demande en attente, refus, rappels **24 h** et **1 h**, modification, annulation, demande d'avis.
Pro : nouvelle demande (boutons Accepter/Refuser), nouvelle réservation confirmée, annulation, nouveau message,
nouvelle demande de devis, agenda du lendemain (19 h). Le worker expire aussi les demandes sans réponse, clôture
les prestations passées et les demandes de devis échues. Chaque tâche est idempotente et sûre en multi-instances
(`FOR UPDATE SKIP LOCKED`).

### Administration
- **Dans le bot** (`/admin`) : statistiques, validation des pros, modération des avis, signalements.
- **Tableau de bord web** (`/admin`) : KPI et graphique des réservations, professionnels (valider, badge vérifié,
  suspendre, refuser), avis, signalements, réservations, utilisateurs (suspension), **catégories et métiers**
  (ajout sans toucher au code, mots-clés pour l'IA), formules d'abonnement et commission, journal d'audit.

### Monétisation (architecture prête, paiement désactivé en v1)
Formules configurables (`free`, `pro`, `premium`, `commission`) avec prix mensuel, commission en points de base,
boost de classement et fonctionnalités ; abonnements par pro (`provider`, `provider_ref` pour Stripe / Telegram
Stars…), mise en avant sponsorisée (bornée dans le score pour que la pertinence reste prioritaire), champ
`commission_cents` sur les réservations, commission par défaut réglable dans l'admin.

---

## Architecture

```
                    ┌──────────────┐   ┌──────────────────┐   ┌───────────────┐
 Telegram users ──▶ │  Bot aiogram │   │ Mini App / Admin │   │ Apps futures  │
                    │ (webhook ou  │   │  React + TS      │   │ (iOS/Android, │
                    │   polling)   │   │  + Tailwind      │   │  site public) │
                    └──────┬───────┘   └────────┬─────────┘   └──────┬────────┘
                           │                    │   REST /api/v1      │
                           │            ┌───────▼─────────────────────▼──┐
                           │            │        FastAPI (app/api)        │
                           │            └───────────────┬─────────────────┘
                           └────────────────┬───────────┘
                                ┌───────────▼────────────┐       ┌───────────────┐
                                │ Services métier (app/  │──────▶│ Claude (NLU,  │
                                │ services) : booking,   │       │ optionnel)    │
                                │ availability, search,  │       └───────────────┘
                                │ ai, quotes, reviews…   │
                                └──┬──────────────┬──────┘
                       ┌───────────▼───┐   ┌──────▼──────┐   ┌──────────────────┐
                       │ PostgreSQL 16 │   │ Redis (FSM, │   │ Worker APScheduler│
                       │ (+ btree_gist)│   │ rate limit) │   │ rappels, expirat. │
                       └───────────────┘   └─────────────┘   └──────────────────┘
```

- Les **notifications** passent par une interface `Notifier` agnostique : Telegram n'est qu'un adaptateur
  (un adaptateur push/e-mail/SMS se branche de la même manière).
- L'**IA** est isolée dans `app/services/ai` : `llm.py` (Claude, sortie structurée validée par Pydantic, effort
  configurable, repli serveur en cas de refus), `nlu.py` (moteur de règles FR/EN sans clé API, utilisé en repli),
  `assistant.py` (fusion, contexte conversationnel, conversion en requête SQL). Le modèle ne fait **qu'extraire des
  contraintes** ; il ne voit ni ne produit jamais de professionnels, prix ou créneaux, et la catégorie qu'il
  renvoie est validée contre la base.
- **Proximité ≠ disponibilité** : la recherche géographique (Haversine en SQL + boîte englobante indexée)
  filtre la zone ; un pro n'est annoncé disponible que si le moteur de créneaux trouve un vrai créneau libre.
  Un pro mobile est retenu si le client est dans **sa** zone d'intervention, même hors du rayon choisi.
- **Nouveaux métiers = données** : catégories arborescentes en base, avec noms traduits, icône, mots-clés NLU,
  mode de travail par défaut, support des devis et indicateur « santé ».

### Structure

```
backend/
  app/
    config.py, db.py, logging_setup.py, main.py   # configuration, SQLAlchemy async, FastAPI
    models/          # ORM (utilisateurs, catégories, pros, prestations, horaires, fermetures, réservations,
                     #      avis, devis, favoris, messages, signalements, plans, abonnements, audit)
    services/        # logique métier, partagée par le bot, l'API et le worker
      availability.py  booking.py  search.py  geo.py  holidays.py  notifications.py  notifier.py
      professionals.py  quotes.py  reviews.py  messaging.py  users.py  admin.py  audit.py
      ai/ (intent.py, nlu.py, llm.py, assistant.py)
    api/             # routers public, auth, me, pro, admin + sécurité (initData Telegram, JWT)
    schemas/         # schémas Pydantic de l'API
    i18n/            # fr.py (référence), en.py ; repli automatique sur le français
    data/            # arbre des catégories, référentiel de villes
  bot/               # aiogram 3 : handlers (common, search, booking, quotes, messages, pro, admin),
                     # middlewares (session DB, anti-abus), claviers, notifier Telegram
  worker/            # tâches planifiées
  alembic/           # migrations (dont la contrainte anti-chevauchement)
  scripts/seed.py    # données de référence + démo
  tests/             # 73 tests (PostgreSQL réel)
web/                 # Vite + React + TypeScript + Tailwind : Mini App (/) et admin (/admin)
docker-compose.yml   # db, redis, migrate, api, bot (profil polling), worker, web
```

---

## Démarrage rapide

### Le plus simple — en ligne avec Render, sans rien installer

Suivez le guide pas à pas **[DEPLOIEMENT_RENDER.md](DEPLOIEMENT_RENDER.md)** : `render.yaml` crée
l'application, PostgreSQL et Redis en un clic. Un seul service fait tourner l'API, le bot (webhook enregistré
automatiquement sur l'adresse Render), les rappels et la Mini App ; seul le jeton Telegram est à saisir.

### Option A — Docker

```bash
cp .env.example .env          # puis renseignez TELEGRAM_BOT_TOKEN (et ANTHROPIC_API_KEY si souhaité)
make up                       # = docker compose --profile polling up -d --build
```

- API : http://localhost:8000/docs · Mini App : http://localhost:8080 · Admin : http://localhost:8080/admin
  (identifiants `ADMIN_EMAIL` / `ADMIN_PASSWORD`).
- Le service `migrate` applique les migrations puis charge les données (`SEED_FLAGS=--demo` : 31 pros de démo).

### Option B — En local

Prérequis : Python 3.12+, Node 20+, PostgreSQL 14+ (extensions `btree_gist` et `unaccent`, fournies par
`postgresql-contrib`), Redis (facultatif : repli mémoire).

```bash
createuser -s ub && createdb -O ub universal_booking      # mot de passe : ALTER USER ub PASSWORD 'ub';
cp .env.example .env
make install
make migrate                 # alembic upgrade head
make demo                    # catégories, villes, formules, admin + données de démo
make api                     # http://localhost:8000/docs
make bot                     # bot en long polling (nécessite TELEGRAM_BOT_TOKEN)
make worker                  # rappels & tâches planifiées
make web                     # http://localhost:5173 (Mini App) et /admin
```

---

## Configuration

Toutes les variables sont documentées dans [`.env.example`](.env.example). Les principales :

| Variable | Rôle |
|---|---|
| `DATABASE_URL`, `REDIS_URL` | PostgreSQL (asyncpg) et Redis |
| `SECRET_KEY` | signature des JWT — **obligatoire en production** (l'app refuse de démarrer avec la valeur par défaut) |
| `TELEGRAM_BOT_TOKEN` | jeton du bot (@BotFather) |
| `TELEGRAM_WEBHOOK_URL` | vide = long polling ; sinon URL HTTPS publique de l'API (webhook enregistré au démarrage) |
| `TELEGRAM_WEBHOOK_SECRET` | secret vérifié sur chaque appel du webhook |
| `WEBAPP_URL` | URL HTTPS de la Mini App (ajoute le bouton « Ouvrir l'application » dans le menu) |
| `ADMIN_TELEGRAM_IDS` | identifiants Telegram administrateurs (`/admin` dans le bot) |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | compte du tableau de bord web (créé par le seed) |
| `ANTHROPIC_API_KEY` | active la compréhension par Claude ; vide = moteur de règles local |
| `AI_MODEL`, `AI_EFFORT` | modèle (`claude-opus-5-5` par défaut) et niveau d'effort (`low` suffit pour de l'extraction) |
| `GEOCODER` | `local` (référentiel de ~75 villes françaises fourni) ou `nominatim` (OpenStreetMap, couverture complète) |
| `AUTO_APPROVE_PROFESSIONALS` | `false` : les nouveaux pros attendent la validation d'un admin |
| `PENDING_BOOKING_TIMEOUT_HOURS` | délai avant refus automatique d'une demande non traitée |

**Clé Claude** : créez-la sur https://console.anthropic.com puis renseignez `ANTHROPIC_API_KEY`. Les requêtes
utilisent les sorties structurées et le repli serveur en cas de refus du modèle ; toute erreur (réseau, quota,
refus) bascule silencieusement sur le moteur de règles, le bot ne tombe jamais.

---

## Mettre le bot en ligne sur Telegram

1. @BotFather → `/newbot` → copiez le jeton dans `TELEGRAM_BOT_TOKEN`, le nom dans `TELEGRAM_BOT_USERNAME`.
2. Développement : `make bot` (long polling).
3. Production : déployez l'API derrière HTTPS, définissez `TELEGRAM_WEBHOOK_URL=https://api.votre-domaine.fr` ;
   l'API enregistre le webhook `/telegram/webhook` (avec `secret_token`) au démarrage. Le service `bot` n'est
   alors plus nécessaire (profil `polling`).
4. Mini App : hébergez `web/` en HTTPS, renseignez `WEBAPP_URL`, puis @BotFather → `/mybots` → *Bot Settings* →
   *Menu Button* (ou `/newapp`) avec la même URL. L'authentification de la Mini App vérifie la signature HMAC de
   `initData` côté serveur.
5. Ajoutez votre identifiant Telegram à `ADMIN_TELEGRAM_IDS` pour accéder à `/admin` dans le bot.

---

## Tests

```bash
make test       # 73 tests sur une vraie base PostgreSQL (TEST_DATABASE_URL, par défaut universal_booking_test)
make lint       # ruff + typecheck TypeScript
```

La base de test est construite **par les migrations Alembic** (downgrade/upgrade complet), ce qui teste aussi les
migrations. Couverture :
- moteur de créneaux (horaires, pauses, battements, fermetures, jours fériés, préavis, horizon) ;
- réservation : auto/manuelle, refus, annulation, déplacement, zone d'intervention, **8 réservations concurrentes
  pour un seul gagnant**, contrainte d'exclusion vérifiée par insertion SQL directe ;
- recherche : catégories parentes, rayon vs zone des pros mobiles, disponibilités réelles, prix, texte, urgences,
  tri et pagination ;
- NLU : tous les exemples du cahier des charges, dates relatives, budget, urgence, affinage conversationnel ;
- devis (diffusion ciblée, refus des non-destinataires, acceptation), avis (uniquement après prestation, modération) ;
- worker (rappels idempotents, expiration, clôture automatique) ;
- API (auth Telegram signée, réservation, 409 sur créneau pris, espace pro, admin, RGPD) ;
- **bot de bout en bout** : vraies mises à jour Telegram injectées dans le dispatcher aiogram (seule la couche HTTP
  Telegram est simulée) — onboarding pro, recherche en langage naturel → réservation → annulation, validation par
  le pro, demande de localisation ;
- intégrité des traductions (toute clé utilisée existe).

---

## API REST

Documentation interactive : `/docs` (désactivée en production). Préfixe `/api/v1`.

| Domaine | Endpoints principaux |
|---|---|
| Public | `GET /categories`, `GET /cities?q=`, `GET /search`, `POST /search/natural`, `GET /professionals/{id}`, `/availability`, `/reviews` |
| Auth | `POST /auth/telegram` (initData Mini App → JWT), `POST /auth/login` (e-mail/mot de passe) |
| Client | `GET/POST /me/bookings`, `POST /me/bookings/{id}/cancel|reschedule|review`, `/me/favorites`, `/me/quote-requests`, `POST /me/quotes/{id}/accept`, `POST /me/messages/{pro_id}`, `GET /me/export`, `DELETE /me` |
| Pro | `POST /pro`, `GET/PATCH /pro/me`, `/pro/services`, `PUT /pro/hours`, `/pro/time-off`, `GET /pro/bookings`, `POST /pro/bookings/{id}/confirm|refuse|cancel|complete`, `/pro/stats`, `/pro/duty`, `/pro/quote-requests` |
| Admin | `/admin/stats`, `/admin/users`, `/admin/professionals`, `/admin/categories`, `/admin/reviews`, `/admin/reports`, `/admin/bookings`, `/admin/plans`, `/admin/settings/{key}`, `/admin/audit` |

---

## Sécurité, RGPD et données de santé

- Authentification : signature HMAC de `initData` (Mini App), JWT signés, mots de passe PBKDF2, rôles
  client / pro / admin vérifiés côté serveur, secret de webhook Telegram.
- Anti-abus : limitation de débit par utilisateur (Redis, repli mémoire), plafond de messages/heure, plafond de
  demandes de devis ouvertes, comptes suspendables, signalements, avis réservés aux clients ayant réellement
  terminé une prestation (un avis par réservation) + modération automatique (liens, coordonnées, insultes, spam).
- Messagerie relayée par la plateforme : les numéros des clients ne sont pas exposés.
- Journal d'audit des opérations sensibles ; logs JSON en production.
- RGPD : consentement au premier lancement, export JSON des données (bot et API), droit à l'effacement
  (anonymisation, les réservations restent pour la comptabilité des pros sans données personnelles).
- **Santé** : catégories marquées `is_health`. Aucune donnée médicale n'est demandée ni stockée ; avertissements
  explicites dans les fiches et à la réservation (la note ne doit contenir aucune information de santé). Stocker
  des données de santé exigerait un hébergement certifié HDS et une analyse d'impact (AIPD) : non couvert ici.

---

## Limites connues et prochaines étapes

Volontairement hors périmètre de cette version, avec l'architecture prête :
- **Paiement** : formules, commissions et abonnements sont modélisés et administrables, mais aucun prestataire
  (Stripe, Telegram Stars) n'est branché (`PAYMENTS_ENABLED=false`).
- **Temps de trajet** : estimation à vitesse moyenne (`AVERAGE_TRAVEL_SPEED_KMH`), affichée comme telle ; une API
  d'itinéraires (OSRM, Google) peut remplacer `estimate_travel_minutes`.
- **Géocodage** : le référentiel local couvre ~75 villes ; `GEOCODER=nominatim` donne une couverture complète
  (respecter la politique d'usage d'OSM ou auto-héberger Nominatim).
- **Langues** : le français est complet ; l'anglais couvre les parcours principaux (repli automatique sur le
  français pour le reste). Ajouter une langue = un fichier `app/i18n/<code>.py`.
- **Espace pro web et apps mobiles** : l'API pro existe ; l'interface web pro et les apps restent à construire.
- **Montée en charge** : la recherche charge au plus `SEARCH_MAX_CANDIDATES` pros après filtrage SQL ; au-delà de
  dizaines de milliers de pros par zone, passer à PostGIS et à un cache des disponibilités.
