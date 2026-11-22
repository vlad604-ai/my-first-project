# DOMOVA — Publicité « Bureaux sur mesure »

Film publicitaire vertical **9:16 · 1080 × 1920 · 30 i/s · 90 s**, pour TikTok, Instagram Reels et Stories, YouTube Shorts et Facebook Reels.

> *Vous imaginez votre bureau. Nous le concevons et nous le réalisons.*

## Contenu du dépôt

```
docs/STORYBOARD.md        Storyboard complet, plan par plan (cadrage vertical, timing, voix off, son)
prompts/PROMPTS_IA.md     Prompts IA par plan + fiche personnage (cohérence du dirigeant DOMOVA)
assets/                   Vos médias (chaque dossier contient un LISEZMOI)
  logo/  videos/avant/  videos/apres/  videos/sequences/  images/  materials/  audio/  social/
video/                    Projet de montage (Remotion / React), rendu en MP4 H.264
  src/content/domova.json   ← TOUS les textes, durées, coordonnées, matériaux, réglages avant/après
  src/scenes/               Une scène par fichier (S1Paris … S8Conclusion)
  src/components/           Sous-titres, logo, cotes, carte, plans 2D, présentation des bureaux détourés, matériaux
```

## Ce que le projet produit déjà
- Montage complet de 90 s, rendu en MP4.
- Sous-titres intégrés dans la zone sûre.
- Signature DOMOVA et titres de chapitres.
- Carte animée de Paris avec repère 14e.
- Cotes architecturales animées.
- Transition pièce → plan 2D.
- **Vos réalisations détourées** sur fond studio : passage du plan au comptoir réel avec ses personnalisations, puis vos 3 autres comptoirs présentés un par un, avec annotations et zooms.
- Présentation des 10 matériaux avec indicateur de gamme de € à €€€€.
- Carte « le prix varie selon… ».
- Avant/après avec transition architecturale et rapprochements.
- Gros plans de détails.
- Conclusion avec logo, CTA et 4 emplacements de contact.

Chaque média manquant est remplacé par un **écran de repère** qui indique le fichier attendu et son emplacement. Dès que vous déposez le fichier dans `assets/`, il prend sa place au rendu suivant.

## Ce qui doit venir de l'extérieur
| Élément | Où le déposer | Comment l'obtenir |
|---|---|---|
| Vos vidéos AVANT / APRÈS | `assets/videos/avant/avant.mp4`, `assets/videos/apres/apres.mp4` | Vos fichiers |
| 7 plans réalistes (Paris, personnages) | `assets/videos/sequences/S1-A.mp4` … | IA vidéo (prompts fournis), banque d'images ou tournage |
| Voix off FR (8 fichiers) | `assets/audio/vo/s1.mp3` … | Comédien ou ElevenLabs |
| Musique | `assets/audio/music/musique.mp3` | Artlist, Musicbed, Epidemic Sound… |
| Logo | `assets/logo/logo.png` | Votre fichier |
| Photos matériaux et détails | `assets/materials/`, `assets/images/details/` | Vos photos |
| Coordonnées | `video/src/content/domova.json` → `contacts` | À compléter |

## Rendu de la vidéo

Prérequis : Node.js 18 ou plus récent.

```bash
cd video
npm install
npm run studio            # aperçu interactif dans le navigateur (chaque scène existe aussi seule)
npm run render            # → out/domova_9x16_1080x1920.mp4 (H.264, yuv420p, AAC)
npm run render:safezones  # même vidéo avec les zones de sécurité TikTok/Reels en surimpression
```

Licence : Remotion est gratuit pour les particuliers et les entreprises de 3 salariés au plus. Au-delà, une licence entreprise est nécessaire (remotion.pro).
