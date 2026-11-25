# Mettre Universal Booking en ligne avec Render (sans rien installer)

Durée : environ 15 minutes. Vous n'avez besoin que de Telegram et d'un navigateur.
Tout le reste (base de données, serveur, sécurité, rappels, Mini App) se crée automatiquement.

> Les noms des boutons de Render peuvent légèrement changer avec le temps : si un libellé diffère un peu,
> choisissez l'option la plus proche.

---

## Étape 1 — Fusionner le code sur GitHub (1 min)

1. Ouvrez https://github.com/vlad604-ai/my-first-project/pull/2
2. Cliquez sur le bouton vert **Merge pull request**, puis **Confirm merge**.

## Étape 2 — Créer votre bot dans Telegram (3 min)

1. Dans Telegram, recherchez **BotFather** (compte avec le badge bleu ✔️) et appuyez sur **Démarrer**.
2. Envoyez `/newbot`.
3. Envoyez un nom, par exemple : `Universal Booking`
4. Envoyez un identifiant qui finit par `bot`, par exemple : `UniversalBookingVlad_bot`
   (s'il est déjà pris, ajoutez des chiffres).
5. BotFather vous répond avec un long code : c'est le **jeton** (ex. `7123456789:AAH...`).
   Gardez ce message, ne le partagez avec personne.
6. Recherchez maintenant **userinfobot**, appuyez sur **Démarrer** : il affiche votre **Id** (un nombre).
   Notez-le : c'est lui qui vous donnera les droits d'administrateur.

## Étape 3 — Créer le service sur Render (5 min)

1. Allez sur https://render.com et cliquez sur **Get Started** / **Sign up**, puis **GitHub** pour vous
   connecter avec votre compte GitHub. Autorisez Render à accéder au dépôt `my-first-project`.
2. Dans le tableau de bord Render, cliquez sur **New +** puis **Blueprint**.
3. Choisissez le dépôt **my-first-project**. Render lit le fichier `render.yaml` et affiche ce qu'il va créer :
   - `universal-booking` (l'application),
   - `universal-booking-db` (la base de données),
   - `universal-booking-redis` (la mémoire du bot).
4. Render vous demande de remplir quelques champs :

   | Champ | Que mettre |
   |---|---|
   | `TELEGRAM_BOT_TOKEN` | le jeton reçu de BotFather (étape 2.5) |
   | `TELEGRAM_BOT_USERNAME` | l'identifiant du bot, **sans** le @ (ex. `UniversalBookingVlad_bot`) |
   | `ADMIN_TELEGRAM_IDS` | votre Id Telegram (étape 2.6), ex. `123456789` |
   | `ANTHROPIC_API_KEY` | laissez **vide** (optionnel, voir plus bas) |

5. Cliquez sur **Apply** (ou **Deploy Blueprint**). Render demande une carte bancaire, car l'application et la
   base de données sont sur des offres payantes (environ 7 $ + 6 $ par mois à la date de rédaction ; vérifiez
   les prix affichés par Render avant de valider).
6. Patientez 5 à 10 minutes. Quand `universal-booking` affiche **Live** (en vert), c'est en ligne.

## Étape 4 — Utiliser votre bot

- Dans Telegram, ouvrez votre bot et envoyez `/start`. Essayez : *« un coiffeur à Paris demain »*.
- Le bouton **Ouvrir** à côté de la zone de saisie lance la Mini App.
- `/pro` : créez une fiche professionnelle (faites-le pour tester).
- `/admin` : comme vous êtes administrateur, vous pouvez valider la fiche pro que vous venez de créer.

Au départ la plateforme est **vide** : aucun professionnel n'est inscrit. C'est normal pour un vrai lancement.
Pour tester avec 31 professionnels fictifs : Render → `universal-booking` → **Environment** → passez `SEED_DEMO`
à `true` → **Save changes** (le service redémarre). Remettez-le à `false` avant d'ouvrir au public et
prévenez-moi : il faudra aussi effacer ces fiches fictives.

## Étape 5 — Le tableau de bord administrateur web

1. Sur Render, ouvrez le service `universal-booking`. Son adresse est affichée en haut,
   du type `https://universal-booking-xxxx.onrender.com`.
2. Ajoutez `/admin` à la fin de l'adresse et ouvrez-la.
3. E-mail : `admin@example.com`. Mot de passe : dans Render → `universal-booking` → **Environment** →
   ligne `ADMIN_PASSWORD` → cliquez sur l'œil 👁 pour l'afficher.

---

## Questions fréquentes

**Le bot ne répond pas.** Render → `universal-booking` → **Logs** : copiez les lignes rouges et envoyez-les-moi.
Vérifiez aussi que le jeton a été collé en entier, sans espace.

**Activer l'intelligence artificielle Claude (optionnel).** Créez une clé sur https://console.anthropic.com,
puis Render → **Environment** → `ANTHROPIC_API_KEY` → collez la clé → **Save changes**. Sans clé, le bot
comprend déjà les demandes grâce à son moteur intégré.

**Mettre à jour l'application.** Chaque fois qu'une modification est fusionnée sur GitHub (branche `main`),
Render la déploie automatiquement.

**Réduire le coût pour un simple essai.** Dans `render.yaml`, `plan: starter` peut devenir `plan: free` et
`basic-256mb` peut devenir `free`. Inconvénients : le service s'endort après une période d'inactivité (premier
message lent, rappels non envoyés pendant le sommeil) et la base gratuite est limitée dans le temps. À réserver
aux tests.

**Sécurité.** Les mots de passe et clés secrètes sont générés automatiquement par Render ; l'application refuse
de démarrer en production si un secret est trop faible.
