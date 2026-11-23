"""DOMOVA — dossiers prêts à publier (un visuel + sa légende par publication)."""
import os
import shutil
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import brand_arche as B  # noqa: E402
from content import INSTAGRAM_BIOS, INSTAGRAM_CAPTIONS, INSTAGRAM_STORIES, TIKTOK_BIOS, TIKTOK_VIDEOS  # noqa: E402

OUT = os.path.join(B.ROOT, "a-publier")
NAMES = {"01_bienvenue": "Bienvenue", "02_matiere": "La-matiere", "03_chantier": "Sur-le-chantier", "04_conseil": "Conseil-3-erreurs",
         "05_realisation": "Realisation-appartement", "06_engagements": "Nos-engagements", "07_sur-mesure": "Bureau-sur-mesure",
         "08_metiers": "Nos-metiers", "09_avant-apres": "Avant-apres", "10_citation": "Citation", "11_facade": "Facade-renovee",
         "12_devis": "Devis-gratuit"}


def jpg(src, dst):
    Image.open(src).convert("RGB").save(dst, quality=95, optimize=True)


def build():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    ig = os.path.join(OUT, "instagram")
    tt = os.path.join(OUT, "tiktok")
    os.makedirs(ig)
    os.makedirs(tt)
    posts = os.path.join(B.ROOT, "instagram", "posts")
    for slug, cap in INSTAGRAM_CAPTIONS.items():
        n = slug[:2]
        base = f"Post-{n}_{NAMES[slug]}"
        jpg(os.path.join(posts, slug + ".png"), os.path.join(ig, base + ".jpg"))
        open(os.path.join(ig, base + "_legende.txt"), "w").write(cap + "\n")
    # carousel: cover + 4 inner pages, numbered for upload order
    base = f"Post-04_{NAMES['04_conseil']}"
    os.replace(os.path.join(ig, base + ".jpg"), os.path.join(ig, base + "_page-1.jpg"))
    for k in range(2, 6):
        jpg(os.path.join(posts, f"04_conseil_page-{k}.png"), os.path.join(ig, f"{base}_page-{k}.jpg"))
    for i, (slug, note) in enumerate(INSTAGRAM_STORIES.items()):
        base = f"Story-{'AB'[i]}_{slug.split('_')[1].capitalize()}"
        jpg(os.path.join(posts, slug + ".png"), os.path.join(ig, base + ".jpg"))
        open(os.path.join(ig, base + "_mode-emploi.txt"), "w").write(note + "\n")
    with open(os.path.join(ig, "00_BIO-instagram.txt"), "w") as f:
        for b in INSTAGRAM_BIOS:
            f.write(f"--- {b['nom']} ({len(b['texte'])}/150) ---\n{b['texte']}\n\n")
    covers = os.path.join(B.ROOT, "tiktok", "covers")
    for v in TIKTOK_VIDEOS:
        base = f"Video-{v['num']:02d}_{v['slug']}"
        jpg(os.path.join(covers, v["fichier"] + ".png"), os.path.join(tt, base + "_couverture.jpg"))
        open(os.path.join(tt, base + "_legende.txt"), "w").write(
            f"{v['legende']}\n\n--- Idée de tournage ({v['format']}, {v['duree']}) ---\n{v['idee']}\n")
    with open(os.path.join(tt, "00_BIO-tiktok.txt"), "w") as f:
        for b in TIKTOK_BIOS:
            f.write(f"--- {b['nom']} ({len(b['texte'])}/80) ---\n{b['texte']}\n\n")
    open(os.path.join(OUT, "LISEZ-MOI.txt"), "w").write("""DOMOVA — publications prêtes à poster

INSTAGRAM (dossier instagram/)
- Publiez dans l’ordre : Post-01 en premier, Post-12 en dernier. Le profil affichera alors la grille prévue.
- Chaque image (1080 x 1350, format portrait 4:5) a sa légende dans le fichier _legende.txt du même numéro : copiez-collez.
- Post-04 (Conseil) est un carrousel : sélectionnez les 5 images page-1 à page-5 dans l’ordre, en une seule publication.
- Les stories (1080 x 1920) se publient quand vous voulez, avec les stickers indiqués.
- La bio : choisissez une des propositions de 00_BIO-instagram.txt.

TIKTOK (dossier tiktok/)
- Les images sont des COUVERTURES : filmez la vidéo (idée de tournage dans le fichier texte), puis choisissez l’image comme couverture lors de la publication (« Modifier la couverture » > « Importer »).
- Légendes et hashtags dans les fichiers _legende.txt.
- Épinglez les vidéos 01, 03 et 04.

Les villes, surfaces, durées et projets cités sont des exemples : adaptez-les à vos vrais chantiers.
""")
    print("a-publier ok", OUT)


if __name__ == "__main__":
    build()
