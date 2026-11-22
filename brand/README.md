# DOMOVA — Identité visuelle

Construction · Rénovation · Aménagement

Charte complète : `guide/DOMOVA_charte-graphique.pdf` (et `guide/index.html`).

## Arborescence

| Dossier | Contenu |
|---|---|
| `logos/svg/` | 24 logos vectoriels (textes vectorisés, aucune police requise) |
| `logos/pdf/` | les mêmes 24 logos en PDF vectoriel (imprimeur, brodeur, marquage) |
| `logos/png/` | PNG à fond transparent, 3200 px (2048 px pour symbole et monogramme) |
| `icons/` | favicon / icône d’app 16 → 1024 px, avatar réseaux sociaux 1080 px |
| `directions/` | planches des 3 directions artistiques |
| `mockups/` | 6 mises en situation (SVG + PNG 2400 px) |
| `guide/` | charte graphique HTML + PDF |
| `tools/` | sources : tout se régénère à l’identique |

Nommage : `domova_[composition]_[version].[svg|pdf|png]`

- compositions : `principal` (symbole au-dessus du nom), `horizontal`, `compact` (sans signature), `symbole`, `monogramme` (icône carrée), `nom-signature`
- versions : `couleur-fond-clair`, `couleur-fond-sombre`, `monochrome-noir`, `monochrome-blanc`

## Couleurs

| | HEX | RVB | CMJN (indicatif) |
|---|---|---|---|
| Noir profond | `#111111` | 17 17 17 | 60 50 40 100 (noir riche) |
| Anthracite | `#252525` | 37 37 37 | 0 0 0 85 |
| Blanc cassé | `#F5F4F0` | 245 244 240 | 0 0 2 4 |
| Cuivre | `#B87345` | 184 115 69 | 0 38 63 28 |

## Régénérer

```bash
pip install shapely cairosvg fonttools brotli pillow   # + Node avec playwright pour les PNG des mises en situation
cd tools
python3 build_logos.py && python3 build_directions.py && python3 build_mockups.py && python3 build_guide.py
```

Typographie d’accompagnement : Jost (SIL Open Font License 1.1, usage commercial autorisé), incluse dans `tools/fonts/`.
Les coordonnées visibles dans les mises en situation (nom, téléphone, SIRET…) sont des exemples.
