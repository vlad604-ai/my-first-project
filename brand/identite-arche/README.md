# DOMOVA — Identité « L'Arche » · Bordeaux & champagne

Fiche logo : `guide/DOMOVA_fiche-logo.pdf` (et `guide/index.html`).

| Dossier | Contenu |
|---|---|
| `logos/svg/` | 35 logos vectoriels (7 compositions × 5 versions), textes vectorisés |
| `logos/pdf/` | les mêmes en PDF vectoriel |
| `logos/png/` | PNG transparent, 3200 px (2048 px symboles / monogramme) |
| `icons/` | favicon et icône d'app 16 → 1024 px, avatar réseaux 1080 px |
| `mockups/` | 6 mises en situation (SVG + PNG) |

Compositions : `principal`, `horizontal`, `compact`, `symbole`, `symbole-renforce`, `monogramme`, `nom-signature`.
Versions : `couleur-fond-clair`, `couleur-fond-sombre`, `monochrome-champagne`, `monochrome-noir`, `monochrome-blanc`.

| Couleur | HEX | RVB | CMJN (indicatif) |
|---|---|---|---|
| Bordeaux | `#4A1420` | 74 20 32 | 30 100 70 45 |
| Bordeaux profond | `#2E0B14` | 46 11 20 | 40 100 70 65 |
| Crème | `#F3E9DC` | 243 233 220 | 0 4 9 5 |
| Champagne | `#C9A46A` | 201 164 106 | 0 18 47 21 |
| Champagne foncé (sur crème) | `#A8834A` | 168 131 74 | 0 22 56 34 |

Régénérer (depuis `brand/tools/`) :
```bash
python3 brand_arche.py && DOMOVA_BRAND=brand_arche python3 build_mockups.py && python3 build_guide_arche.py
```
