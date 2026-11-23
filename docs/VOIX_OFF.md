# Voix off DOMOVA — votre voix clonée par l'IA

## 1. Enregistrer un échantillon de votre voix (10 minutes)

L'IA apprend votre timbre à partir d'un enregistrement propre.

- **Durée :** 2 à 3 minutes de parole, d'un seul tenant (1 minute minimum).
- **Lieu :** une pièce calme, si possible avec des meubles, des rideaux ou un tapis (pas une pièce vide qui résonne). Pas de musique, pas de télé, fenêtres fermées.
- **Matériel :** votre téléphone suffit. Tenez-le à 15–20 cm de la bouche, un peu sur le côté pour éviter les souffles. Application Dictaphone (iPhone) ou Enregistreur (Android).
- **Ton :** celui que vous voulez entendre dans la pub : posé, confiant, souriant. Parlez naturellement, sans lire trop vite.
- **Quoi lire :** le texte de la pub ci-dessous, deux fois, puis 30 secondes où vous présentez librement DOMOVA et votre métier.

Exportez le fichier tel quel (.m4a, .wav ou .mp3).

## 2. Cloner votre voix (ElevenLabs, recommandé pour le français)

1. Créez un compte sur **elevenlabs.io**. Le clonage instantané demande un abonnement payant, en général l'offre d'entrée de gamme (vérifiez les tarifs actuels sur le site).
2. Ouvrez **Voices → Add a new voice → Instant Voice Clone**.
3. Importez votre enregistrement, nommez la voix « DOMOVA — [votre prénom] » et cochez la case qui confirme que c'est votre propre voix.
4. Allez dans **Text to Speech** et choisissez votre voix clonée, avec le modèle **Eleven Multilingual v2** (le meilleur en français).
5. Réglages conseillés : *Stability* 45–55 %, *Similarity* 75–85 %, *Style* 0–15 %.
6. Collez le texte d'**une scène à la fois** (tableau ci-dessous), générez, écoutez, régénérez si besoin, puis téléchargez en MP3.

Pour un résultat encore plus fidèle, il existe le *Professional Voice Clone*, qui demande au moins 30 minutes d'enregistrement et une offre supérieure.

## 3. Nommer et déposer les fichiers

Un fichier par scène, dans `assets/audio/vo/` :

| Fichier | Scène | Durée visée | Texte |
|---|---|---|---|
| `s1.mp3` | Paris | ≤ 7 s | À Paris, chaque espace possède un potentiel. Chez DOMOVA, nous transformons vos idées en réalisations uniques, entièrement pensées pour vous. |
| `s2.mp3` | La rencontre | ≤ 7,5 s | Tout commence par une rencontre. Vous avez un projet, une envie, un espace à aménager ? Nous venons à votre rencontre pour comprendre vos besoins. |
| `s3.mp3` | L'étude | ≤ 8 s | Nous étudions votre espace, prenons les mesures et imaginons avec vous un aménagement qui correspond parfaitement à vos attentes. |
| `s4.mp3` | La conception | ≤ 12,5 s | Nous concevons votre bureau selon vos dimensions, vos envies et votre utilisation. Chaque détail est étudié pour créer un espace fonctionnel, esthétique et parfaitement adapté à votre intérieur. |
| `s5.mp3` | Les matériaux | ≤ 18 s | Du mélaminé de qualité aux finitions bois naturel, en passant par les décors noyer, le stratifié et les matériaux haut de gamme, nous vous proposons de nombreuses possibilités. Chaque matériau possède ses caractéristiques et son prix. Nous adaptons votre projet à vos envies et à votre budget, sans négliger la qualité. |
| `s5b.mp3` | Vos inspirations | ≤ 7 s | Pas encore d'idée précise ? Nous imaginons votre projet pour vous, ou vous nous envoyez vos inspirations, et nous les transformons en plan sur mesure. |
| `s6.mp3` | Avant / Après | ≤ 9,5 s | Voici ce que nous pouvons réaliser. D'un espace inutilisé à un véritable bureau sur mesure, chaque centimètre est optimisé pour créer un aménagement unique. |
| `s7.mp3` | La livraison | ≤ 8,5 s | Notre objectif est simple : transformer votre espace en un lieu qui vous ressemble, avec des matériaux de qualité et une réalisation soignée jusque dans les moindres détails. |
| `s8.mp3` | Conclusion | ≤ 7 s | Vous imaginez votre bureau. Nous le concevons et nous le réalisons. DOMOVA, l'art de rénover. Contactez-nous et imaginons ensemble votre futur bureau. |

Si une phrase dépasse sa durée, ce n'est pas grave : le montage peut s'adapter automatiquement à la longueur réelle de votre voix.

Musique (optionnelle) : `assets/audio/music/musique.mp3`, sous licence pour les réseaux sociaux. Elle baisse automatiquement sous la voix.

## 4. Ensuite

Une fois les fichiers déposés, le montage les cale au début de chaque scène et les sous-titres restent synchronisés.
