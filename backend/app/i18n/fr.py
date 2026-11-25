"""French catalog (reference language). HTML parse mode: escape < > & in literals."""

MESSAGES = {
    # --- Commands / generic ---------------------------------------------------
    "cmd.start": "Démarrer", "cmd.menu": "Menu principal", "cmd.pro": "Espace professionnel",
    "cmd.help": "Aide", "cmd.cancel": "Annuler l'action en cours",
    "lang.name": "Français",
    "common.cancelled": "Action annulée.",
    "err.generic": "😕 Une erreur est survenue. Réessayez dans un instant.",
    "err.banned": "⛔ Votre compte est suspendu. Contactez le support.",
    "err.too_fast": "⏳ Doucement… réessayez dans quelques secondes.",
    "day.today": "Aujourd'hui", "day.tomorrow": "Demain",

    # --- Start / menu ---------------------------------------------------------
    "start.welcome": "👋 Bienvenue sur <b>{app}</b> !\n\nTrouvez et réservez n'importe quel professionnel "
                     "directement depuis Telegram : santé, artisans, beauté, auto, avocats, coachs…",
    "start.privacy": "🔒 Pour fonctionner, nous enregistrons votre identifiant Telegram, vos réservations et, si vous "
                     "la partagez, votre position. Vos données ne sont jamais revendues et vous pouvez les exporter "
                     "ou les supprimer à tout moment (Paramètres).\n\n<i>Aucune donnée médicale n'est demandée ni "
                     "conservée : ne partagez pas d'informations de santé dans les notes ou messages.</i>",
    "start.privacy_ok": "✅ Merci !",
    "start.how_to": "💡 Écrivez simplement ce que vous cherchez, par exemple :\n"
                    "• <i>Je cherche un plombier à Paris disponible demain</i>\n"
                    "• <i>Un coiffeur pour une coupe homme à moins de 30 €</i>\n"
                    "• <i>Un garage ouvert samedi à Boulogne</i>",
    "menu.title": "🏠 <b>Menu principal</b>{name}\n\nQue puis-je faire pour vous ? Vous pouvez aussi m'écrire "
                  "librement votre besoin.",
    "menu.search": "🔎 Rechercher", "menu.now": "⚡ Disponible maintenant", "menu.categories": "📂 Catégories",
    "menu.nearby": "📍 Autour de moi", "menu.bookings": "📅 Mes rendez-vous", "menu.favorites": "❤️ Favoris",
    "menu.quote": "📝 Demander un devis", "menu.my_quotes": "📨 Mes devis", "menu.pro_space": "💼 Espace pro",
    "menu.become_pro": "💼 Devenir pro", "menu.settings": "⚙️ Paramètres", "menu.admin": "🛡 Administration",
    "menu.webapp": "📱 Ouvrir l'application",
    "help.text": "<b>Comment ça marche ?</b>\n\n1️⃣ Décrivez votre besoin en langage naturel ou parcourez les "
                 "catégories.\n2️⃣ Comparez les professionnels : avis, tarifs, distance, prochaines disponibilités.\n"
                 "3️⃣ Réservez un créneau en quelques clics, ou demandez des devis pour un projet.\n"
                 "4️⃣ Recevez confirmations et rappels ici même.\n\nCommandes : /menu, /pro, /cancel",

    # --- Buttons --------------------------------------------------------------
    "btn.menu": "🏠 Menu", "btn.back": "⬅️ Retour", "btn.cancel": "❌ Annuler", "btn.skip": "Passer ➡️",
    "btn.done": "✅ Terminé", "btn.yes": "✅ Oui", "btn.no": "Non", "btn.change": "✏️ Changer",
    "btn.confirm": "✅ Confirmer", "btn.accept_privacy": "✅ J'accepte",
    "btn.share_location": "📍 Partager ma position", "btn.profile": "👁 Voir le profil", "btn.book": "📅 Réserver",
    "btn.contact": "💬 Contacter", "btn.favorite": "Favori", "btn.unfavorite": "Retirer des favoris",
    "btn.reviews": "⭐ Avis", "btn.photos": "🖼 Photos", "btn.ask_quote": "📝 Demander un devis",
    "btn.report": "🚩 Signaler", "btn.urgent_request": "🚨 Demander une intervention urgente",
    "btn.more_results": "➕ Plus de résultats ({n})", "btn.widen_radius": "📏 Élargir la zone",
    "btn.any_date": "📅 Toutes dates", "btn.confirm_booking": "✅ Confirmer la réservation",
    "btn.add_note": "📝 Ajouter une note", "btn.other_slot": "🗓 Choisir un autre créneau",
    "btn.view_booking": "📄 Voir le rendez-vous", "btn.history": "🗂 Historique",
    "btn.reschedule": "🔁 Déplacer", "btn.cancel_booking": "❌ Annuler le RDV", "btn.yes_cancel": "Oui, annuler",
    "btn.accept": "✅ Accepter", "btn.refuse": "🚫 Refuser", "btn.mark_done": "🏁 Prestation terminée",
    "btn.contact_client": "💬 Contacter le client", "btn.reply": "↩️ Répondre", "btn.search_again": "🔎 Nouvelle recherche",
    "btn.rebook": "📅 Reprendre RDV", "btn.agenda": "📅 Mon agenda", "btn.send_quote": "💶 Envoyer un devis",
    "btn.decline": "🙅 Pas intéressé", "btn.compare_quotes": "📊 Comparer les devis",
    "btn.close_request": "🔒 Clôturer la demande", "btn.pro_space": "💼 Espace pro",
    "btn.create_pro": "🚀 Créer mon compte pro", "btn.change_location": "📍 Ma position",
    "btn.radius": "📏 Rayon", "btn.export_data": "📦 Exporter mes données",
    "btn.delete_account": "🗑 Supprimer mon compte", "btn.confirm_delete": "🗑 Oui, tout supprimer",

    # --- Location ---------------------------------------------------------------
    "loc.ask": "📍 Partagez votre position avec le bouton ci-dessous, ou écrivez une ville, une adresse ou un "
               "code postal.",
    "loc.unknown": "🤔 Je ne trouve pas ce lieu. Essayez une ville ou un code postal (ex : <i>75011</i>).",
    "loc.saved": "📍 Position enregistrée : <b>{place}</b>",
    "loc.choose_radius": "📏 Dans quel rayon voulez-vous chercher ?",
    "loc.radius_set": "Rayon : {km} km",

    # --- Search ---------------------------------------------------------------
    "search.prompt": "🔎 Dites-moi ce que vous cherchez, en une phrase.\n\nExemples :\n"
                     "• <i>Un dentiste disponible vendredi matin</i>\n"
                     "• <i>Électricien pour installer 3 prises à Boulogne</i>\n"
                     "• <i>Coiffeur homme à moins de 30 € aujourd'hui</i>",
    "search.greeting": "👋 Bonjour ! Décrivez-moi votre besoin (métier, lieu, date, budget) et je vous trouve les "
                       "professionnels disponibles.",
    "search.not_understood": "🤔 Je n'ai pas bien compris. Précisez le métier ou le service recherché "
                             "(ex : <i>plombier à Lyon demain</i>), ou parcourez les catégories.",
    "search.understood": "🔎 <b>J'ai compris :</b> {summary}\n<b>{total}</b> professionnel(s) trouvé(s).",
    "search.no_results": "😕 Aucun professionnel disponible ne correspond à :\n{summary}\n\nEssayez d'élargir la "
                         "zone ou les dates.",
    "search.need_location": "📍 Où avez-vous besoin du professionnel ? Partagez votre position ou écrivez une ville "
                            "/ un code postal.",
    "search.location_unknown": "⚠️ Lieu « {place} » non reconnu, je cherche sans ce critère.",
    "search.tip_location": "💡 Partagez votre position (📍 Autour de moi) pour voir les plus proches en premier.",
    "search.refine_tip": "💬 Vous pouvez affiner en écrivant par ex. <i>plutôt samedi</i>, <i>moins de 50 €</i>, "
                         "<i>à Vincennes</i>…",
    "search.expired": "⌛ Cette recherche a expiré, relancez-la.",
    "search.my_position": "Ma position", "search.at_home": "à domicile",
    "sort.distance": "📍 Distance", "sort.rating": "⭐ Note", "sort.price": "💶 Prix", "sort.soonest": "⚡ Dispo",
    "avail.now": "Maintenant", "avail.30min": "Dans 30 min", "avail.1h": "Dans l'heure",
    "avail.3h": "Dans les 3 h", "avail.today": "Aujourd'hui", "avail.tomorrow": "Demain",
    "now.title": "⚡ <b>Disponible maintenant</b>\nQuand avez-vous besoin d'un professionnel ?",
    "cat.choose": "📂 Choisissez une catégorie :", "cat.choose_sub": "{name} — précisez :",
    "cat.all_of": "Tous : {name}",

    # --- Cards ----------------------------------------------------------------
    "card.sponsored": "<i>Sponsorisé</i>", "card.verified": "Professionnel vérifié",
    "card.travels": "se déplace ({km} km)", "card.travel_time": "≈ {min} min de trajet (estimation)",
    "card.urgent_ok": "Disponible pour une intervention urgente", "card.no_slot": "Pas de créneau sur la période",
    "card.completed": "{n} prestation(s) réalisée(s)", "card.zone": "Intervient autour de {city} (rayon {km} km)",
    "card.services": "Prestations & tarifs", "card.hours": "Horaires", "card.next_slots": "Prochaines dispos",
    "card.reviews": "⭐ Avis clients", "card.client": "Client", "card.at_home": "à domicile",
    "card.health_notice": "Données de santé : ne transmettez aucune information médicale via le bot. Elles seront "
                          "échangées directement avec le praticien.",
    "hours.closed": "fermé",
    "pro.not_found": "Ce professionnel n'est pas disponible.",
    "reviews.none": "Pas encore d'avis.",
    "fav.added": "❤️ Ajouté aux favoris", "fav.removed": "Retiré des favoris",
    "fav.none": "Vous n'avez pas encore de favoris.", "fav.title": "❤️ Vos professionnels favoris :",

    # --- Booking --------------------------------------------------------------
    "booking.choose_service": "📋 Quelle prestation souhaitez-vous chez <b>{pro}</b> ?",
    "booking.no_services": "Ce professionnel n'a pas encore publié de prestations.",
    "booking.choose_day": "📅 <b>{service}</b> chez {pro}\n💶 {price} · ⏱ {duration} min\n\nChoisissez un jour :",
    "booking.no_slot_period": "Aucun créneau libre sur ces 14 jours, essayez la période suivante ▶️",
    "booking.day_full": "Ce jour est complet, choisissez-en un autre.",
    "booking.choose_time": "🕒 Créneaux libres — {day} :",
    "booking.ask_address": "🏠 À quelle adresse doit intervenir le professionnel ? Écrivez l'adresse complète ou "
                           "partagez votre position.",
    "booking.address_invalid": "Adresse trop courte, merci de préciser.",
    "booking.gps_address": "Position GPS partagée ({city})",
    "booking.confirm_title": "🧾 <b>Récapitulatif</b>",
    "booking.auto_confirm": "✅ Confirmation immédiate.",
    "booking.manual_confirm": "⏳ Le professionnel doit valider votre demande : vous serez notifié.",
    "booking.health_note": "Ne mentionnez aucune information médicale dans la note.",
    "booking.ask_note": "📝 Votre note pour le professionnel (accès, digicode, précisions…) :",
    "booking.urgent": "Intervention urgente",
    "booking.done": "🎉 Réservation enregistrée ! Référence <code>{ref}</code>.",
    "booking.reschedule_title": "🔁 Déplacer le rendez-vous (actuellement {current}).\nChoisissez un nouveau jour :",
    "booking.choose_new_time": "🕒 Choisissez le nouvel horaire :",
    "booking.reschedule_confirm": "Confirmer le déplacement au <b>{when}</b> ?",
    "booking.rescheduled": "✅ Rendez-vous déplacé.",
    "booking.err.slot_unavailable": "😕 Ce créneau vient d'être pris ou n'est plus disponible. Choisissez-en un autre.",
    "booking.err.pro_unavailable": "Ce professionnel n'accepte pas de réservation pour le moment.",
    "booking.err.self_booking": "Vous ne pouvez pas réserver chez vous-même.",
    "booking.err.unknown_service": "Prestation introuvable.",
    "booking.err.not_mobile": "Ce professionnel ne se déplace pas.",
    "booking.err.address_required": "Une adresse est nécessaire pour une intervention.",
    "booking.err.out_of_zone": "📍 Votre adresse est en dehors de la zone d'intervention de ce professionnel.",
    "booking.err.not_allowed": "Action non autorisée.",
    "booking.err.invalid_state": "Ce rendez-vous ne peut plus être modifié.",
    "booking.err.invalid_datetime": "Date invalide.",
    "booking.err.booking_error": "Réservation impossible.",
    "bookings.title": "📅 <b>Vos prochains rendez-vous</b>", "bookings.history": "🗂 <b>Historique</b>",
    "bookings.none": "Vous n'avez aucun rendez-vous à venir.", "bookings.none_history": "Aucun historique.",
    "bookings.not_found": "Rendez-vous introuvable.",
    "bookings.cancel_confirm": "Voulez-vous vraiment annuler ce rendez-vous ?",
    "bookings.cancelled": "❌ Rendez-vous <code>{ref}</code> annulé.",
    "bookings.cancelled_by_client": "Annulé par le client",
    "status.pending": "En attente", "status.confirmed": "Confirmé", "status.cancelled": "Annulé",
    "status.completed": "Terminé", "status.refused": "Refusé",

    # --- Reviews --------------------------------------------------------------
    "review.ask_comment": "Merci ! Ajoutez un commentaire (et éventuellement des photos) ou passez :",
    "review.thanks": "🙏 Merci pour votre avis !",
    "review.thanks_moderation": "🙏 Merci ! Votre avis sera publié après vérification par notre équipe.",
    "review.photo_added": "📷 Photo ajoutée.",
    "review.err.not_your_booking": "Ce rendez-vous ne vous appartient pas.",
    "review.err.booking_not_completed": "Vous pourrez laisser un avis une fois la prestation terminée.",
    "review.err.invalid_rating": "Note invalide.", "review.err.already_reviewed": "Vous avez déjà laissé un avis.",
    "review.err.not_your_review": "Avis introuvable.",

    # --- Messages / reports ---------------------------------------------------
    "msg.ask": "💬 Votre message pour <b>{name}</b> :", "msg.sent": "✅ Message envoyé.",
    "msg.self": "C'est votre propre fiche 🙂",
    "msg.err.empty": "Message vide.", "msg.err.rate_limited": "Trop de messages, réessayez plus tard.",
    "msg.err.not_a_participant": "Action non autorisée.", "msg.err.banned": "Compte suspendu.",
    "msg.err.unknown_professional": "Professionnel introuvable.",
    "report.ask": "🚩 Décrivez le problème (faux profil, comportement abusif, arnaque…) :",
    "report.thanks": "Merci, notre équipe va examiner ce signalement.",

    # --- Quotes (client) ------------------------------------------------------
    "quote.ask_description": "📝 Décrivez votre projet en quelques phrases (nature des travaux, surface, délais…).\n"
                             "<i>Ex : Je souhaite refaire ma salle de bain de 8 m² à Boulogne-Billancourt.</i>",
    "quote.ask_description_pro": "📝 Décrivez votre projet pour <b>{name}</b> :",
    "quote.description_short": "Merci de détailler un peu plus votre projet (10 caractères minimum).",
    "quote.confirm_category": "Votre demande concerne : <b>{name}</b> ?",
    "quote.choose_category": "Quel type de professionnel recherchez-vous ?",
    "quote.ask_location": "📍 Où se situe le projet ? Ville, code postal ou position.",
    "quote.ask_budget": "💶 Avez-vous un budget indicatif ? (boutons ou montant en €)",
    "quote.ask_urgency": "⏱ Quel est votre délai ?",
    "quote.sent": "✅ Demande envoyée à <b>{n}</b> professionnel(s) correspondant(s). Vous serez notifié à chaque "
                  "devis reçu.",
    "quote.sent_none": "📭 Demande enregistrée, mais aucun professionnel ne correspond pour l'instant dans votre "
                       "zone. Elle reste ouverte : vous pourrez la consulter dans « Mes devis ».",
    "quote.none": "Vous n'avez aucune demande de devis.",
    "quote.my_title": "📨 <b>Vos demandes de devis</b>",
    "quote.request_title": "📨 <b>Demande de devis</b> — {status}",
    "quote.recipients": "Transmise à {n} professionnel(s).",
    "quote.no_offers_yet": "⏳ Aucun devis reçu pour l'instant.",
    "quote.accepted": "🤝 Devis de <b>{name}</b> accepté ! Il a été prévenu ; échangez directement pour planifier.",
    "quote.closed": "Demande clôturée.", "quote.no_budget": "budget non précisé",
    "quote.status.sent": "reçu", "quote.status.accepted": "✅ accepté", "quote.status.rejected": "non retenu",
    "quote.status.withdrawn": "retiré",
    "quote.err.description_too_short": "Description trop courte.",
    "quote.err.too_many_open_requests": "Vous avez trop de demandes ouvertes.",
    "quote.err.request_closed": "Cette demande est clôturée.", "quote.err.not_a_recipient": "Demande introuvable.",
    "quote.err.invalid_amount": "Montant invalide.", "quote.err.already_quoted": "Vous avez déjà envoyé un devis.",
    "quote.err.unknown_quote": "Devis introuvable.", "quote.err.unknown_request": "Demande introuvable.",
    "qstatus.open": "🟢 Ouverte", "qstatus.awarded": "🤝 Attribuée", "qstatus.closed": "🔒 Clôturée",
    "qstatus.cancelled": "❌ Annulée", "qstatus.expired": "⌛ Expirée",
    "urgency.urgent": "🚨 Urgent", "urgency.this_week": "Cette semaine", "urgency.this_month": "Ce mois-ci",
    "urgency.flexible": "Flexible",

    # --- Quotes (pro) -----------------------------------------------------------
    "pq.ask_amount": "💶 Montant de votre devis en € TTC pour :\n<i>{desc}</i>",
    "pq.invalid_amount": "Montant invalide, ex : 1250 ou 1250,50",
    "pq.ask_message": "✍️ Ajoutez un message (détail, délais, conditions) ou passez :",
    "pq.sent": "✅ Devis envoyé au client.",

    # --- Settings / RGPD ------------------------------------------------------
    "settings.title": "⚙️ <b>Paramètres</b>\nLangue : {lang_name}\nPosition : {place}\nRayon de recherche : {km} km",
    "settings.no_location": "non définie", "settings.lang_set": "Langue mise à jour ✅",
    "gdpr.export_caption": "📦 Vos données personnelles (RGPD).",
    "gdpr.delete_confirm": "⚠️ Supprimer définitivement votre compte ? Vos informations personnelles seront "
                           "effacées. Cette action est irréversible.",
    "gdpr.deleted": "✅ Votre compte a été supprimé. Merci d'avoir utilisé le service.",

    # --- Pro space ------------------------------------------------------------
    "pro.intro": "💼 <b>Développez votre activité avec {app}</b>\n\n• Une vitrine professionnelle consultable par "
                 "des milliers de clients\n• Un agenda en ligne et des réservations 24/7 sans double réservation\n"
                 "• Des demandes de devis qualifiées\n• Des rappels automatiques pour réduire les absences\n\n"
                 "L'inscription prend 2 minutes.",
    "pro.not_registered": "Créez d'abord votre compte pro.",
    "pro.dashboard": "💼 <b>{name}</b>\nStatut : {status}\n\n📅 Aujourd'hui : <b>{today}</b> RDV\n"
                     "⏳ Demandes en attente : <b>{pending}</b>\n📝 Demandes de devis : <b>{quotes}</b>\n"
                     "⭐ Note : {rating} ({reviews} avis)",
    "pro.on_duty_until": "🚨 Disponible pour urgences jusqu'à {time}",
    "pro.pending_notice": "🕵️ Votre profil est en cours de vérification. Complétez vos prestations et horaires en "
                          "attendant : il sera visible dès sa validation.",
    "pro.no_services_notice": "➕ Ajoutez au moins une prestation pour recevoir des réservations.",
    "prostatus.pending": "🕵️ en vérification", "prostatus.active": "🟢 actif", "prostatus.suspended": "⛔ suspendu",
    "prostatus.rejected": "🚫 refusé",
    "pro.err.already_pro": "Vous avez déjà un compte pro.", "pro.err.unknown_category": "Catégorie inconnue.",
    "pro.err.unknown_location": "Adresse introuvable, essayez une ville ou un code postal.",
    "pro.err.invalid_duration": "Durée invalide.", "pro.err.invalid_price": "Prix invalide.",
    "pro.err.unknown_service": "Prestation introuvable.", "pro.err.not_mobile":
        "Le mode urgence est réservé aux professionnels qui se déplacent.",
    "pro.err.too_many_photos": "Maximum 20 photos.",
    "pd.agenda": "📅 Agenda", "pd.pending": "⏳ Demandes ({n})", "pd.services": "📋 Prestations",
    "pd.hours": "🕒 Horaires", "pd.closures": "🏖 Fermetures", "pd.quotes": "📝 Devis ({n})",
    "pd.profile": "🪪 Profil", "pd.settings": "⚙️ Réglages", "pd.clients": "👥 Clients", "pd.stats": "📊 Stats",
    "pd.duty_on": "🚨 Me rendre disponible maintenant", "pd.duty_off": "⏹ Arrêter le mode urgence",
    "pd.view_public": "👁 Ma fiche publique", "pd.add_service": "➕ Ajouter une prestation",
    "pd.agenda_title": "📅 <b>Agenda — {day}</b>", "pd.agenda_empty": "Aucun rendez-vous ce jour.",
    "pd.no_pending": "✅ Aucune demande en attente.", "pd.pending_title": "⏳ <b>Demandes à valider</b>",
    "pd.refuse_reason": "Motif du refus (envoyé au client) ou passez :", "pd.refused": "Demande refusée.",
    "pd.cancelled_by_pro": "Annulé par le professionnel",
    "pd.services_title": "📋 <b>Vos prestations</b>\nTouchez une prestation pour l'activer / la désactiver.",
    "pd.quotes_empty": "📭 Aucune nouvelle demande de devis.",
    "pd.quotes_disabled": "Activez « Accepter les devis » dans Réglages pour en recevoir.",
    "pd.clients_empty": "Pas encore de clients.", "pd.clients_title": "👥 <b>Vos clients</b> (touchez pour écrire)",
    "pd.stats_text": "📊 <b>Statistiques (30 jours)</b>\n\nRéservations : <b>{total}</b>\n✅ Confirmées : {confirmed}\n"
                     "🏁 Terminées : {completed}\n❌ Annulées : {cancelled} · 🚫 Refusées : {refused}\n"
                     "Taux d'annulation : {rate} %\n💶 CA estimé : <b>{revenue}</b>\n\n👥 Clients uniques : {clients}\n"
                     "❤️ En favori : {favorites}\n📅 RDV à venir : {upcoming}\n⭐ {rating}/5 ({reviews} avis)\n"
                     "🏆 Prestations réalisées : {done}",
    "onb.ask_name": "🚀 C'est parti !\n\n1/5 — Quel est le <b>nom commercial</b> de votre activité ?",
    "onb.name_invalid": "Nom invalide (2 à 160 caractères).",
    "onb.ask_category": "2/5 — Quel est votre <b>métier</b> ?",
    "onb.ask_mode": "{cat}\n\n3/5 — Comment travaillez-vous ?",
    "onb.ask_address": "4/5 — Adresse de votre établissement (ou partagez la position) :",
    "onb.ask_base": "4/5 — Ville ou adresse de départ de vos interventions (ou partagez la position) :",
    "onb.ask_radius": "Jusqu'à quelle distance vous déplacez-vous ?",
    "onb.ask_description": "5/5 — Présentez votre activité en quelques lignes (expérience, spécialités, garanties) :",
    "onb.done_active": "🎉 Votre fiche est en ligne ! Ajoutez maintenant vos prestations et tarifs.",
    "onb.done_pending": "🎉 Compte créé ! Notre équipe vérifie votre profil (badge « vérifié » après contrôle). "
                        "Ajoutez dès maintenant vos prestations et horaires.",
    "mode.on_site": "🏢 Les clients viennent dans mon établissement", "mode.mobile": "🚗 Je me déplace chez les clients",
    "mode.both": "🔁 Les deux",
    "psv.ask_name": "Nom de la prestation (ex : <i>Coupe homme</i>, <i>Recherche de fuite</i>) :",
    "psv.ask_duration": "⏱ Durée de la prestation ? (boutons ou ex : 1h30)",
    "psv.invalid_duration": "Durée invalide (entre 5 min et 24 h).",
    "psv.ask_price": "💶 Prix en € (ex : 35 ou 49,90) ou « Sur devis » :", "psv.on_quote": "Sur devis",
    "psv.invalid_price": "Prix invalide.", "psv.added": "✅ Prestation ajoutée.",
    "ph.title": "🕒 <b>Horaires d'ouverture</b>\nTouchez un jour pour le modifier.",
    "ph.ask": "Horaires du <b>{day}</b> ?\nEx : <code>9-12, 14-18</code> (pause incluse) ou <code>fermé</code>",
    "ph.invalid": "Format invalide. Ex : <code>9h-12h30, 14h-19h</code> ou <code>fermé</code>",
    "ph.saved": "✅ Horaires enregistrés.", "ph.copy_monday": "📋 Copier le lundi sur mar.–ven.",
    "pcl.title": "🏖 <b>Fermetures & congés</b> (touchez pour supprimer)", "pcl.add": "➕ Ajouter une fermeture",
    "pcl.holidays_on": "Jours fériés : fermé automatiquement.", "pcl.holidays_off": "Jours fériés : ouvert.",
    "pcl.ask": "Dates de fermeture : <code>24/12/2026</code> ou <code>24/12/2026-02/01/2027</code>",
    "pcl.invalid": "Format invalide. Ex : <code>24/12/2026-02/01/2027</code>",
    "pcl.saved": "✅ Fermeture enregistrée : plus aucun créneau proposé sur cette période.",
    "pcl.conflicts": "{n} rendez-vous déjà pris sur cette période : pensez à les déplacer ou les annuler.",
    "pf.title": "🪪 <b>{name}</b>\n\n📝 {desc}\n📞 {phone}\n📍 {address}\n🌐 {website}\n🏷 {specialties}\n"
                "🖼 {photos} photo(s)",
    "pf.description": "📝 Description", "pf.phone": "📞 Téléphone", "pf.address": "📍 Adresse",
    "pf.website": "🌐 Site web", "pf.specialties": "🏷 Spécialités", "pf.logo": "🖼 Logo / photo",
    "pf.photos": "📸 Réalisations", "pf.share": "🔗 Partager ma fiche",
    "pf.ask_description": "Nouvelle description :", "pf.ask_phone": "Téléphone professionnel :",
    "pf.ask_address": "Adresse :", "pf.ask_website": "Site web :",
    "pf.ask_specialties": "Spécialités séparées par des virgules :",
    "pf.ask_logo": "Envoyez votre logo ou photo de profil :",
    "pf.ask_photos": "Envoyez des photos de vos réalisations (légende facultative) :",
    "pf.invalid_phone": "Numéro invalide.", "pf.saved": "✅ Enregistré.", "pf.photo_added": "📸 Photo ajoutée.",
    "pst.title": "⚙️ <b>Réglages</b>\nMode : {mode}\nRayon : {radius} km · Battement entre interventions : "
                 "{buffer} min\nPas des créneaux : {step} min · Délai de prévenance : {notice} min",
    "pst.auto_confirm": "Confirmation automatique", "pst.accepts_quotes": "Accepter les demandes de devis",
    "pst.holidays": "Fermé les jours fériés", "pst.urgent": "Accepter les urgences",
    "duty.ask": "🚨 Pendant combien de temps êtes-vous disponible pour des interventions urgentes ?",

    # --- Notifications ----------------------------------------------------------
    "notif.summary": "<code>{ref}</code>\n💼 {service}\n🏷 {pro}\n🗓 {when}",
    "notif.price": "💶 {price}", "notif.address": "📍 {address}",
    "notif.client": "👤 {name}", "notif.note": "📝 {note}",
    "notif.client.confirmed": "✅ <b>Rendez-vous confirmé !</b>",
    "notif.client.pending": "⏳ <b>Demande envoyée.</b> Le professionnel va la valider.",
    "notif.client.pending_urgent": "🚨 <b>Demande d'intervention urgente envoyée.</b> Le professionnel vous répond "
                                   "au plus vite.",
    "notif.client.refused": "🚫 <b>Demande refusée</b> par le professionnel.\nMotif : {reason}",
    "notif.client.cancelled_by_pro": "❌ <b>Votre rendez-vous a été annulé</b> par le professionnel.",
    "notif.pro.new_confirmed": "🆕 <b>Nouvelle réservation confirmée</b>",
    "notif.pro.new_request": "🔔 <b>Nouvelle demande de rendez-vous</b> à valider",
    "notif.pro.new_urgent": "🚨 <b>Demande d'intervention URGENTE</b>",
    "notif.pro.cancelled": "❌ <b>Rendez-vous annulé</b> par le client",
    "notif.rescheduled": "🔁 <b>Rendez-vous déplacé</b> (initialement {old})",
    "notif.reminder.24h": "⏰ <b>Rappel :</b> votre rendez-vous est demain.",
    "notif.reminder.1h": "⏰ <b>Rappel :</b> votre rendez-vous est dans 1 heure.",
    "notif.review_request": "🙏 Comment s'est passée votre prestation chez <b>{pro}</b> ? Notez-la :",
    "notif.pro.tomorrow": "📅 <b>Vos {count} rendez-vous de demain :</b>",
    "notif.new_message": "💬 <b>Nouveau message de {sender}</b>\n\n{body}",
    "notif.pro.quote_request": "📝 <b>Nouvelle demande de devis</b>\n\n<i>{desc}</i>\n\n📍 {city} · 💶 {budget} · "
                               "{urgency}",
    "notif.client.quote": "💶 <b>Nouveau devis</b> de {pro} : <b>{amount}</b>\n<i>{msg}</i>",
    "notif.pro.quote_accepted": "🤝 <b>{client} a accepté votre devis</b> ({amount}) !",
    "notif.pro.status.active": "🎉 Votre profil professionnel est validé et visible des clients !",
    "notif.pro.status.suspended": "⛔ Votre profil professionnel a été suspendu. Contactez le support.",
    "notif.pro.status.rejected": "🚫 Votre profil professionnel n'a pas été validé. Contactez le support.",
    "notif.pro.status.pending": "🕵️ Votre profil est repassé en vérification.",

    # --- Admin ------------------------------------------------------------------
    "adm.home": "🛡 Admin",
    "adm.stats": "🛡 <b>Administration</b> (30 j)\n\n👥 Utilisateurs : {users} (+{new})\n💼 Pros actifs : {active} · "
                 "en attente : {pending}\n📅 Réservations : {bookings} · Volume : {gmv}\n⭐ Avis à modérer : {reviews}\n"
                 "🚩 Signalements : {reports}\n📝 Demandes de devis : {quotes}",
    "adm.pending_pros": "🕵️ Pros à valider", "adm.reviews": "⭐ Avis", "adm.reports": "🚩 Signalements",
    "adm.none": "Rien à traiter 🎉", "adm.approve": "✅ Valider", "adm.approve_verify": "✅ Valider + badge vérifié",
    "adm.reject": "🚫 Refuser", "adm.publish": "✅ Publier", "adm.resolve": "✅ Traité", "adm.dismiss": "Ignorer",
    "adm.suspend": "⛔ Suspendre",
}
