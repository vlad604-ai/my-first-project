# DOMOVA : bible du personnage officiel

> Document de référence pour créer et réutiliser l'avatar virtuel de DOMOVA.
> Toute nouvelle image ou vidéo doit respecter **l'ADN visuel verrouillé** (section 2) mot pour mot.

---

## 1. Fiche d'identité

| Élément | Valeur |
|---|---|
| Nom de travail | **Le Fondateur DOMOVA** (à remplacer par votre prénom si vous le souhaitez) |
| Rôle | Visage et porte-parole de DOMOVA : rénovation, travaux, bureaux sur mesure |
| Âge apparent | 30–35 ans |
| Taille / silhouette | Grand (environ 1,88 m), élancé, épaules droites, posture verticale et ouverte |
| Personnalité | Charismatique, sérieux mais chaleureux, sûr de lui, accessible, moderne |
| Ton de voix (vidéo) | Posé, clair, rythme moyen, phrases courtes, sourire dans la voix |
| Gestuelle | Mains calmes et ouvertes, gestes de présentation vers le décor, aucun geste nerveux |
| Signature visuelle | Total look noir + cheveux blonds + lunettes fines = silhouette reconnaissable instantanément |

---

## 2. ADN visuel verrouillé (à ne jamais modifier)

C'est ce bloc qui garantit la cohérence. **Copiez-le tel quel dans chaque prompt.**

### Bloc personnage (EN, pour les générateurs d'images)

```
DOMOVA brand ambassador: a tall slender Caucasian man in his early thirties, fair natural skin with subtle realistic texture and light freckles on the nose, oval face with a defined jawline, straight nose, light-grey-blue eyes, clean-shaven with a faint natural stubble shadow, medium-length honey-blond hair styled in a modern textured side-part swept back, short tapered sides, neat and elegant; thin rectangular eyeglasses with a matte black metal frame and slightly rounded corners; wearing an all-black outfit: slim-fit black wool blazer with notch lapels, black fine-knit merino turtleneck, tailored slim black trousers, polished black leather Chelsea boots; no logos, no colour, no accessories except a minimal black steel watch on the left wrist
```

### Bloc rendu (EN)

```
hyper-realistic 3D digital human, cinematic CGI render, premium luxury tech commercial aesthetic, physically based skin shading with subsurface scattering and visible pores, individual hair strands, detailed fabric weave on wool and knit, soft professional three-point studio lighting with large softbox key light, gentle rim light, shallow depth of field, 85mm lens, neutral warm-grey seamless studio background, 8K, sharp focus, realistic human proportions
```

### Prompt négatif (pour les outils qui l'acceptent)

```
cartoon, anime, manga, illustration, video game, plastic skin, doll, uncanny, exaggerated features, colorful clothing, pattern, logo, text, watermark, tie, beard, long hair, dark hair, round glasses, thick frames, sunglasses, deformed hands, extra fingers, distorted face, low resolution, oversaturated
```

### Règles de cohérence

- **Lunettes** : toujours fines, rectangulaires, métal noir mat. Jamais d'autre modèle.
- **Coiffure** : raie sur le côté gauche, mèche balayée en arrière. Toujours la même longueur.
- **Tenue** : col roulé noir par défaut. Variante chemise noire autorisée **uniquement** pour une déclinaison clairement définie (voir section 5).
- **Montre** : toujours poignet gauche. C'est un repère de continuité.
- **Palette** : noir, peau, blond, gris chaud. Aucune autre couleur sur le personnage.

---

## 3. Les 7 livrables : prompts prêts à l'emploi

Structure de chaque prompt : `[cadrage] + [BLOC PERSONNAGE] + [expression/pose] + [BLOC RENDU]`.
Remplacez `{PERSONNAGE}` et `{RENDU}` par les blocs de la section 2.

### 01 : Vue de face (image de référence maîtresse)
```
Front view, head-and-shoulders to mid-chest portrait, perfectly centered, looking straight into the camera, {PERSONNAGE}, neutral relaxed expression with closed lips, symmetrical even lighting, {RENDU}
```
> ⭐ **Générez celle-ci en premier.** Choisissez la meilleure : elle devient la référence de visage pour toutes les autres.

### 02 : Vue de trois quarts
```
Three-quarter view, body turned 45 degrees to the left, head turned slightly toward the camera, waist-up framing, {PERSONNAGE}, calm confident expression, {RENDU}
```

### 03 : Vue de profil
```
Strict side profile view facing left, head-and-shoulders framing, {PERSONNAGE}, neutral expression, clear silhouette of nose, jaw and glasses arm, hair swept back visible, {RENDU}
```

### 04 : Vue en pied
```
Full-body shot, head to toe, standing straight in a relaxed confident pose, hands loosely at sides, feet slightly apart, camera at chest height, {PERSONNAGE}, entire outfit clearly visible including trousers break and black Chelsea boots, {RENDU}, 50mm lens
```

### 05 : Portrait rapproché du visage
```
Extreme close-up beauty portrait, face filling the frame from forehead to chin, {PERSONNAGE}, soft focused gaze into the lens, ultra-detailed skin pores, eyelashes, iris detail and reflections in the eyeglass lenses, {RENDU}, 100mm macro lens
```

### 06 : Sourire naturel
```
Front view, chest-up portrait, {PERSONNAGE}, warm genuine natural smile showing a hint of teeth, slight crinkles at the corners of the eyes, approachable and friendly, {RENDU}
```

### 07 : Expression sérieuse et professionnelle
```
Front view, chest-up portrait, {PERSONNAGE}, serious focused professional expression, lips closed, slight determined look, chin level, arms crossed, {RENDU}
```

---

## 4. Méthode pour garder exactement le même visage

Un générateur d'images ne garantit pas la cohérence d'un prompt à l'autre. Voici la méthode qui marche :

1. **Partir de votre vrai visage (recommandé).** Le personnage vous représente : fournissez 10 à 20 photos de vous (face, 3/4, profil, lumière douce, sans lunettes de soleil). Le résultat sera ressemblant *et* stable.
2. **Créer l'image maîtresse (livrable 01).** Générez une vingtaine de variantes, retenez-en **une seule**. C'est le « visage officiel ».
3. **Verrouiller l'identité** avec l'une de ces options :
   - **Référence personnage** : dans les outils qui proposent une fonction « character reference » ou « image reference », chargez l'image maîtresse à chaque génération, avec une influence élevée.
   - **Édition par référence** (modèles d'édition d'image) : partez de l'image maîtresse et demandez uniquement le changement d'angle ou d'expression.
   - **Entraîner un modèle dédié (LoRA)**, la solution la plus solide pour un usage récurrent : 15 à 30 images validées du personnage, mot-déclencheur unique, par exemple `domovaman`. Ensuite, chaque prompt commence par `photo of domovaman, ...`.
4. **Garder la même graine (seed)** et les mêmes réglages pour une même série.
5. **Contrôler chaque image** avec la checklist ci-dessous avant publication.

### Checklist de validation
- [ ] Même forme de visage, même couleur d'yeux
- [ ] Cheveux blond miel, raie à gauche, mèche en arrière
- [ ] Lunettes rectangulaires fines en métal noir mat
- [ ] Col roulé noir + blazer noir (ou variante validée)
- [ ] Montre noire au poignet gauche
- [ ] Aucune couleur, aucun logo sur la tenue
- [ ] Mains correctes (5 doigts, proportions naturelles)
- [ ] Rendu réaliste, ni plastique, ni dessin, ni jeu vidéo

---

## 5. Déclinaisons autorisées

| Contexte | Changement autorisé | Le reste ne bouge pas |
|---|---|---|
| Studio / portrait officiel | Fond gris chaud uni | ✔ |
| Présentation de chantier | Décor de rénovation en arrière-plan, lumière naturelle de fenêtre | ✔ (tenue identique, même sur chantier) |
| Bureaux sur mesure | Bureau design en bois et métal noir, lumière douce | ✔ |
| Version « chemise » | Chemise noire mate col classique, boutonnée jusqu'en haut, sans cravate, à la place du col roulé | ✔ |
| Réseaux sociaux (format 9:16) | Cadrage vertical, plan taille | ✔ |

Exemple, présentation de chantier :
```
Waist-up shot, standing in a bright apartment under renovation with exposed plaster walls and natural window light, gesturing with an open hand toward the room, {PERSONNAGE}, confident friendly expression, speaking to camera, {RENDU}, vertical 9:16 composition
```

---

## 6. Passer de l'image à la vidéo face caméra

Pour qu'il parle dans vos vidéos TikTok, Instagram et vos présentations de chantiers :

1. **Avatar parlant** : importez l'image maîtresse (01 ou 06) dans une plateforme d'avatars vidéo qui anime un portrait (synchronisation labiale à partir d'un texte ou d'un audio).
2. **Voix** : enregistrez votre propre voix (le plus authentique) ou créez un clone vocal à partir de vos enregistrements, avec votre consentement explicite.
3. **Plans en mouvement** : un générateur image-vers-vidéo, à partir des livrables 02 et 04, donne des plans de marche ou de présentation (3 à 8 secondes).
4. **Format** : 9:16 pour TikTok/Reels, 16:9 pour le site et YouTube, 1:1 ou 4:5 pour le fil Instagram.
5. **Transparence** : mentionnez « avatar virtuel » ou « contenu généré par IA » quand la plateforme ou la réglementation l'exige (l'AI Act européen impose cette transparence pour les contenus de synthèse réalistes).

### Exemple de script (15 s)
> « Bonjour, je suis [Prénom], fondateur de DOMOVA. Ici, on transforme vos espaces : rénovation complète, travaux sur mesure et bureaux pensés pour vous. Suivez-moi, je vous montre ce chantier. »

---

## 7. Arborescence conseillée des fichiers

```
domova-personnage/
├── BIBLE_PERSONNAGE.md        ← ce document
├── reference/
│   └── 00_visage_officiel.png ← image maîtresse validée
├── livrables/
│   ├── 01_face.png
│   ├── 02_trois-quarts.png
│   ├── 03_profil.png
│   ├── 04_pied.png
│   ├── 05_gros-plan.png
│   ├── 06_sourire.png
│   └── 07_serieux.png
└── lora/                      ← images d'entraînement, si vous en créez un
```
