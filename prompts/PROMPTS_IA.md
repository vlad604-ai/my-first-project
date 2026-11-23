# Prompts IA — plans à générer (format vertical 9:16)

> **Optionnel depuis la version 9 :** chaque plan ci-dessous est déjà couvert par une animation au trait aux couleurs DOMOVA. Générer ou tourner ces plans n'est utile que pour remplacer l'animation par de vraies images.

Ce fichier contient **uniquement** les plans que le code ne peut pas fabriquer : prises de vue réalistes de Paris et de personnages.
Le reste (carte, cotes, plan 2D, configurateur 3D, matériaux, avant/après, logo, CTA) est déjà animé dans le projet.

Les prompts sont en anglais, langue sur laquelle les modèles vidéo sont les plus fiables. Chaque prompt :
- impose le **9:16 vertical natif** (ne jamais générer en 16:9 pour recadrer ensuite) ;
- reprend **mot pour mot** le bloc personnage, pour garder la même apparence d'un plan à l'autre ;
- vise 5 s (ou 8 s), d'où l'on extrait la durée utile.

Une fois généré, chaque fichier se dépose dans `/assets/videos/sequences/` sous le nom indiqué (`S1-A.mp4`, etc.). Il apparaît automatiquement dans le montage.

---

## 0. Méthode pour garder le même personnage d'un plan à l'autre

1. **Si le dirigeant de DOMOVA existe réellement** (grand, blond, tout en noir, lunettes), la meilleure option est d'utiliser **ses propres photos** comme référence, ou mieux, de **le filmer** pour S2 et S7. C'est plus crédible et cela évite tout effet « personnage IA ». N'utilisez l'image d'une personne réelle qu'avec son accord.
2. Sinon, générez d'abord une **planche personnage** (image fixe) : face, trois quarts, profil, en pied. Choisissez une version et gardez-la.
3. Générez chaque plan vidéo en **image → vidéo** (*image-to-video* / *reference-to-video*) à partir de cette planche, avec le bloc personnage ci-dessous dans chaque prompt.
4. Gardez la même graine (*seed*) et les mêmes réglages de style pour tous les plans.
5. Générez **4 à 8 variantes** par plan et gardez la meilleure. Les mains (poignée de main) sont le point faible des IA : vérifiez les doigts image par image.

### Bloc personnage — LE DIRIGEANT DOMOVA (à coller tel quel)
```
DOMOVA FOUNDER: a tall man (about 1.90 m), early-to-mid thirties, short neatly styled blond hair
side-parted with natural texture, light stubble, thin rectangular black-framed glasses,
entirely dressed in black: tailored knee-length black wool overcoat, black fine-knit turtleneck,
slim black trousers, black leather derby shoes. No logos, no accessories except a black watch.
Confident, warm, natural posture, calm smile.
```

### Bloc personnage — LE CLIENT (à coller tel quel)
```
CLIENT: a woman around 40, shoulder-length chestnut hair loosely tied back, natural make-up,
camel wool coat over a cream knit sweater, charcoal grey straight trousers, white leather sneakers.
Elegant, natural, friendly.
```
*(Vous pouvez remplacer la cliente par un client : gardez alors ce même bloc modifié dans tous les plans.)*

### Bloc style — à ajouter à la fin de chaque prompt
```
Vertical 9:16 native framing, 1080x1920, cinematic luxury real-estate commercial, shot on ARRI Alexa
with anamorphic-look lenses, shallow depth of field, soft natural light, warm golden-hour tones,
muted palette of black, charcoal, off-white, beige and natural wood, subtle film grain,
smooth stabilized camera, photorealistic, 24-30 fps.
```

### Négatif (si l'outil l'accepte)
```
horizontal framing, letterbox, black bars, text, watermark, logo, distorted hands, extra fingers,
warped faces, morphing clothes, cartoon, CGI look, oversaturated, fisheye, shaky camera
```

---

## Outils possibles (à vérifier au moment de la production : les versions évoluent vite)

| Besoin | Options | Remarques |
|---|---|---|
| Planche personnage (image) | Midjourney (référence de personnage), Flux Kontext, générateurs d'images Google / OpenAI | Exportez en 9:16 ou en carré haute définition. |
| Vidéo réaliste 9:16 | Google **Veo**, **Kling**, **Runway** (références de personnage), **Sora**, **Luma** | Choisissez un outil qui accepte une image de référence et le format 9:16 natif. Vérifiez les droits d'usage commercial de votre abonnement. |
| Plans de Paris | Banques d'images sous licence (Artgrid, Storyblocks, Getty, Shutterstock) ou IA | ⚠️ Le survol de Paris en drone est interdit sans autorisation préfectorale : un tournage drone « maison » n'est pas une option. |
| Voix off française | Comédien voix off (idéal pour le haut de gamme) ou **ElevenLabs** (voix FR) | Exporter un fichier par scène : `/assets/audio/vo/s1.mp3` … `s8.mp3`. |
| Musique | Artlist, Musicbed, Epidemic Sound (licence publicité réseaux sociaux) | Piano + cordes feutrées, 90–100 BPM, montée vers 1:00. → `/assets/audio/music/musique.mp3` |
| Sous-titres calés au mot près | Whisper (transcription de la voix finale) | Reportez les temps de début dans `subtitleTimes` si besoin. |

---

## S1-A — Vue aérienne de Paris → 14e (5 s)
**Fichier :** `assets/videos/sequences/S1-A.mp4`
```
Aerial top-down view of Paris at golden hour, vertical frame, the Seine crossing the upper part of
the frame, zinc rooftops and Haussmann boulevards radiating from a star-shaped square. The camera
descends steadily and smoothly while tilting from a straight top-down view to a 40-degree oblique view,
converging on the residential 14th arrondissement south of Montparnasse, Haussmann buildings and
tree-lined avenues becoming larger. Majestic, slow, seamless motion. No text.
+ [bloc style]
```
*Option banque d'images : cherchez « Paris aerial vertical golden hour » et prenez de préférence une source 4K, pour garder de la marge au recadrage vertical.*

## S1-B — Rue haussmannienne du 14e (5 s)
**Fichier :** `assets/videos/sequences/S1-B.mp4`
```
Vertical low-angle shot of a quiet Parisian street in the 14th arrondissement: cream limestone
Haussmann facades rising to the top of the frame, wrought-iron balconies, tall wooden carriage door,
sidewalk with a few passers-by out of focus. Slow crane-down movement from the cornice to the sidewalk.
Warm late-afternoon sun raking the facades. No text, no readable shop signs.
+ [bloc style]
```

## S2-A — Le dirigeant marche dans la rue (5 s)
**Fichier :** `assets/videos/sequences/S2-A.mp4`
```
[bloc DOMOVA FOUNDER]
Full-body vertical shot: the DOMOVA FOUNDER walks confidently toward the camera along a Haussmann
street sidewalk in Paris 14th arrondissement, coat moving naturally, he adjusts his glasses with one
hand and gives a subtle smile. Smooth backward tracking shot at chest height, his head in the upper
third of the frame, his full body visible down to the shoes. Background softly blurred limestone
facades and trees.
+ [bloc style]
```

## S2-B — La poignée de main (5 s)
**Fichier :** `assets/videos/sequences/S2-B.mp4`
```
[bloc DOMOVA FOUNDER] [bloc CLIENT]
Vertical medium shot in profile in front of a tall Parisian carriage door: the CLIENT waits, the
DOMOVA FOUNDER arrives from the left, they smile and shake hands firmly and naturally, eye contact,
realistic hand anatomy, the joined hands exactly at the centre of the frame. Slight slow push-in
that stops on the handshake. Natural facial expressions, friendly and professional.
+ [bloc style]
```
*Conseil : c'est le plan le plus difficile pour une IA. Un tournage réel de 5 s au smartphone (4K, vertical) est souvent plus rapide et plus crédible.*

## S3-A — Pièce vide, observation et mesures (8 s)
**Fichier :** `assets/videos/sequences/S3-A.mp4`
```
[bloc DOMOVA FOUNDER] [bloc CLIENT]
Vertical one-point-perspective shot of an empty Parisian Haussmann room: high ceiling with
moulding at the top of the frame, herringbone oak parquet converging toward the back wall at the
bottom, tall window on the left wall with soft daylight. The CLIENT gestures toward the back wall
explaining her project; the DOMOVA FOUNDER measures the wall with a laser distance meter, a thin red
dot on the wall, then looks around observing the space. Slow dolly-in along the axis of the room.
Calm, precise, professional mood.
+ [bloc style]
```
*Après génération, ajustez les coordonnées des cotes (`scenes.s3.dimensions` dans `domova.json`) pour qu'elles tombent sur les murs réels de votre plan.*

## S4-A — Le concepteur à l'ordinateur (5 s)
**Fichier :** `assets/videos/sequences/S4-A.mp4`
```
Vertical over-the-shoulder shot of an interior designer at a minimalist dark desk, a large monitor
in the upper part of the frame shows a 3D model of a custom wooden desk with drawers and shelves
(architectural software interface, no readable brand), hands on keyboard and mouse in the lower part.
Slow lateral slide. Evening ambience, warm desk lamp, monitor glow on the face.
+ [bloc style]
```
*Option : utiliser le dirigeant DOMOVA comme concepteur (ajoutez alors le bloc personnage, vu de dos ou de trois quarts).*

## S7-A — Le client découvre son bureau (5 s) · ⚠️ voir la note
**Fichier :** `assets/videos/sequences/S7-A.mp4`

**Recommandation : tournage réel** dans la pièce réalisée (le bureau doit rester le vôtre). Plan vertical, téléphone stabilisé à hauteur de poitrine : le client entre dans le cadre, passe la main sur le plateau, ouvre un tiroir, sourit. Le dirigeant est en retrait, à gauche du cadre (la droite est masquée par les boutons TikTok/Instagram).

Si vous passez quand même par l'IA, ne générez que des plans **où le bureau n'est pas identifiable** :
```
[bloc DOMOVA FOUNDER] [bloc CLIENT]
Vertical close-up: the CLIENT's face lit by warm light, she looks down at something in front of her
and smiles with genuine delight; the DOMOVA FOUNDER stands slightly behind her, softly out of focus,
nodding with a proud smile. Very shallow depth of field, warm evening light, no furniture visible.
+ [bloc style]
```

---

## Plans à NE PAS générer par IA
- **S6 (avant/après) :** uniquement vos deux vidéos réelles → `/assets/videos/avant/avant.mp4` et `/assets/videos/apres/apres.mp4`.
- **S7 gros plans :** photos ou vidéos réelles de votre bureau → `/assets/images/details/` (assemblages, tiroirs, poignées, éclairage, plateau).
- **S5 matériaux :** vos photos macro ou les visuels de vos fournisseurs → `/assets/materials/<id>.jpg` (identifiants listés dans `domova.json`).
