"""DOMOVA — direction artistique TikTok (identité L'Arche, bordeaux & champagne).

Sorties : ../identite-arche/tiktok/
  covers/   9 couvertures de vidéos 1080 x 1920 (SVG + PNG + JPG)
  index.html  page de présentation (profil, couvertures, formats, bios, légendes, planning)
"""
import os
import re
import subprocess
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import brand_arche as B  # noqa: E402
from build_instagram import (DEFS, J3, J5, J6, T, arch_path, mini_logo, interior, facade, desk, materials,  # noqa: E402
                             BX, BXP, CR, CH, CHF)
from content import TIKTOK_BIOS, TIKTOK_VIDEOS  # noqa: E402

OUT = os.path.join(B.ROOT, "tiktok")
C = os.path.join(OUT, "covers")
W, H = 1080, 1920


def doc(body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
            f'<title>{title}</title><defs>{DEFS}</defs>{body}'
            f'<rect width="{W}" height="{H}" filter="url(#grain)"/></svg>')


def full_scene(scene_svg):
    """Scale a 1080x1350 scene to cover 1080x1920 (centre crop)."""
    k = H / 1350
    dx = (W - 1080 * k) / 2
    return f'<g transform="translate({dx:.1f} 0) scale({k:.4f})">{scene_svg}</g>'


def blocks(rows, cap, cx, y, bg, fg, ts=None, lh=None, pad=26):
    """TikTok-style text: each line on its own solid block, centred."""
    ts = ts or J6
    lh = lh or cap * 2.15
    s = ""
    for i, r in enumerate(rows):
        w = ts.text(r, cap, 0.01)[1]
        bh = cap * 1.95
        top = y + i * lh
        s += f'<rect x="{cx - w / 2 - pad:.1f}" y="{top:.1f}" width="{w + 2 * pad:.1f}" height="{bh:.1f}" fill="{bg}"/>'
        s += T(ts, r, cap, cx, top + bh / 2 + cap / 2, fg, 0.01, "middle")
    return s


def tag(txt, y, bg=CH, fg=BX):
    w = J5.text(txt, 20, 0.3)[1]
    return (f'<rect x="{W / 2 - w / 2 - 26:.1f}" y="{y}" width="{w + 52:.1f}" height="56" fill="{bg}"/>'
            + T(J5, txt, 20, W / 2, y + 38, fg, 0.3, "middle"))


def signature(dark_bg=True):
    col = CR if dark_bg else BX
    acc = CH if dark_bg else CHF
    s = mini_logo(W / 2 - 50, 1500, 80, col, acc)
    s += T(J5, "DOMOVA", 20, W / 2, 1640, col, 0.45, "middle")
    return s


def shade_top_bottom():
    return ('<linearGradient id="tb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2E0B14" stop-opacity=".75"/>'
            '<stop offset=".35" stop-color="#2E0B14" stop-opacity="0"/><stop offset=".62" stop-color="#2E0B14" stop-opacity="0"/>'
            '<stop offset="1" stop-color="#2E0B14" stop-opacity=".9"/></linearGradient>'
            f'<rect width="{W}" height="{H}" fill="url(#tb)"/>')


# ------------------------------------------------------------------ covers
def c_qui():
    s = f'<rect width="{W}" height="{H}" fill="{BX}"/>'
    s += f'<path d="{arch_path(190, 700, 330, 1380)}" fill="none" stroke="{CH}" stroke-opacity=".25" stroke-width="4"/>'
    s += f'<rect x="90" y="1376" width="900" height="8" fill="{CH}" opacity=".35"/>'
    s += tag("ÉPISODE 1", 420)
    s += T(J3, "Qui est", 92, W / 2, 680, CR, 0.0, "middle")
    s += T(J3, "DOMOVA ?", 92, W / 2, 820, CR, 0.06, "middle")
    s += T(J3, "Construction · Rénovation · Aménagement", 30, W / 2, 940, CH, 0.04, "middle")
    s += signature()
    return s


def c_avant_apres():
    s = '<defs><clipPath id="L"><rect width="540" height="1920"/></clipPath><clipPath id="R"><rect x="540" width="540" height="1920"/></clipPath></defs>'
    s += f'<g clip-path="url(#L)">{full_scene(interior(False))}</g><g clip-path="url(#R)">{full_scene(interior(True))}</g>'
    s += shade_top_bottom()
    s += f'<rect x="537" width="6" height="{H}" fill="{CR}"/>'
    s += blocks(["AVANT / APRÈS", "un salon", "méconnaissable"], 54, W / 2, 380, CR, BX)
    s += signature()
    return s


def c_chantier():
    s = full_scene(facade(True)) + shade_top_bottom()
    s += tag("VISITE DE CHANTIER", 330, BX, CR)
    s += blocks(["Ravalement", "semaine 3 sur 8"], 58, W / 2, 440, CR, BX)
    s += signature()
    return s


def c_prix():
    s = f'<rect width="{W}" height="{H}" fill="{CR}"/>'
    s += tag("ON RÉPOND", 380, BX, CR)
    s += T(J3, "Combien coûte", 84, W / 2, 620, BX, 0.0, "middle")
    s += T(J3, "une rénovation", 84, W / 2, 740, BX, 0.0, "middle")
    s += T(J3, "au m² ?", 84, W / 2, 860, BX, 0.0, "middle")
    s += f'<rect x="{W / 2 - 40}" y="930" width="80" height="4" fill="{CHF}"/>'
    s += T(J5, "LES VRAIS CHIFFRES", 24, W / 2, 1010, CHF, 0.3, "middle")
    s += f'<path d="{arch_path(390, 300, 1080, 1420)}" fill="none" stroke="{BX}" stroke-width="5"/>'
    s += f'<rect x="300" y="1417" width="480" height="7" fill="{BX}"/>'
    s += signature(False).replace(f'translate({W / 2 - 50}', f'translate({W / 2 - 50}')
    return s


def c_pov():
    s = full_scene(interior(True)) + shade_top_bottom()
    s += blocks(["POV : on retrouve", "une arche cachée", "derrière un mur"], 52, W / 2, 360, BX, CR)
    s += signature()
    return s


def c_bureau():
    s = full_scene(desk()) + shade_top_bottom()
    s += tag("SUR MESURE", 330)
    s += blocks(["Un bureau en chêne,", "de l’esquisse", "à la pose"], 54, W / 2, 440, CR, BX)
    s += signature()
    return s


def c_erreurs():
    s = f'<rect width="{W}" height="{H}" fill="{BX}"/>'
    s += tag("CONSEIL", 330)
    s += T(J3, "3", 520, W / 2, 980, CH, 0.0, "middle")
    s += T(J3, "erreurs à éviter", 70, W / 2, 1140, CR, 0.0, "middle")
    s += T(J3, "avant de rénover", 70, W / 2, 1240, CR, 0.0, "middle")
    s += signature()
    return s


def c_matiere():
    s = full_scene(materials()) + shade_top_bottom()
    s += blocks(["On choisit", "les finitions", "avec vous"], 58, W / 2, 380, BX, CR)
    s += signature()
    return s


def c_timelapse():
    s = full_scene(facade(False)) + shade_top_bottom()
    s += tag("TIMELAPSE", 330, BX, CR)
    s += blocks(["8 semaines", "de façade", "en 30 secondes"], 58, W / 2, 440, CR, BX)
    s += signature()
    return s


COVERS = {
    "qui-sommes-nous": c_qui, "avant-apres-salon": c_avant_apres, "visite-chantier": c_chantier,
    "prix-renovation": c_prix, "pov-arche-cachee": c_pov, "bureau-sur-mesure": c_bureau,
    "3-erreurs": c_erreurs, "finitions": c_matiere, "timelapse-facade": c_timelapse,
}


# ------------------------------------------------------------------ page
def page():
    avatar = open(os.path.join(B.ROOT, "icons", "reseaux-sociaux", "domova_cercle-symbole-bordeaux.svg")).read()
    avatar = re.sub(r' width="[^"]+" height="[^"]+"', ' role="img"', avatar, count=1)
    bio = TIKTOK_BIOS[0]["texte"].replace("\n", "<br>")
    # profile grid: newest first, 3 pinned
    order = list(reversed(TIKTOK_VIDEOS))
    pinned = {"avant-apres-salon", "prix-renovation", "qui-sommes-nous"}
    pins = [v for v in TIKTOK_VIDEOS if v["slug"] in pinned]
    rest = [v for v in order if v["slug"] not in pinned]
    grid = ""
    for v in pins + rest:
        badge = '<em class="pin">Épinglé</em>' if v["slug"] in pinned else ""
        grid += f'<div class="cell"><img src="covers/{v["fichier"]}.jpg" alt="Vidéo : {v["titre"]}" loading="lazy">{badge}<span class="views">▷ {v["vues"]}</span></div>'
    cards = "".join(
        f'<figure><img src="covers/{v["fichier"]}.jpg" alt="{v["titre"]}" loading="lazy"><figcaption><b>{v["num"]:02d} · {v["titre"]}</b>'
        f'<span class="fmt">{v["format"]} · {v["duree"]}</span>{v["idee"]}</figcaption></figure>' for v in TIKTOK_VIDEOS)
    bios = "".join(
        f'<div class="bio-card"><span class="tag">{b["nom"]}</span><p class="bio-text">{b["texte"].replace(chr(10), "<br>")}</p>'
        f'<span class="count">{len(b["texte"].replace(chr(10), " "))} / 80 caractères</span></div>' for b in TIKTOK_BIOS)
    caps = "".join(
        f'<div class="cap"><span class="tag">Vidéo {v["num"]:02d} · {v["titre"]}</span>{v["legende"]}</div>'
        for v in TIKTOK_VIDEOS[:3])
    return f"""<title>DOMOVA TikTok</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Jost:wght@400;500;600&family=JetBrains+Mono:wght@400&display=swap">
<style>
/* Layout: phone profile beside the strategy, then covers, video formats, bios, captions, rhythm */
:root{{--bx:{BX};--bxp:{BXP};--cr:{CR};--ch:{CH};--chf:{CHF};--ink:#24161A;--muted:#7A645E;--line:rgba(74,20,32,.14);
--f:"Jost","Futura","Century Gothic",system-ui,sans-serif;--m:"JetBrains Mono",ui-monospace,Menlo,monospace;color-scheme:light}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--cr);color:var(--ink);font-family:var(--f);font-size:17px;line-height:1.6}}
.band{{padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:clamp(48px,8vw,104px)}}
.dark{{background:var(--bx);color:var(--cr)}}
.wrap{{max-width:1200px;margin:0 auto;display:grid;gap:40px}}
.eyebrow{{font-family:var(--m);font-size:12px;letter-spacing:.2em;text-transform:uppercase;color:var(--chf)}}
.dark .eyebrow{{color:var(--ch)}}
h1,h2,h3{{margin:0;font-weight:500;line-height:1.12;text-wrap:balance}}
h1{{font-size:clamp(32px,5vw,56px)}} h2{{font-size:clamp(26px,3.6vw,40px)}} h3{{font-size:19px;font-weight:600}}
p{{margin:0;max-width:62ch}}
.lede{{font-size:19px;color:var(--muted)}} .dark .lede{{color:#E3CFC2}}
.hero{{display:grid;grid-template-columns:minmax(0,420px) minmax(0,1fr);gap:64px;align-items:start}}
.phone{{background:#151012;border-radius:48px;padding:12px;box-shadow:0 30px 60px rgba(46,11,20,.35);max-width:420px;width:100%}}
.screen{{background:#fff;border-radius:38px;overflow:hidden;color:#141414;font-size:13px;line-height:1.4;text-align:center}}
.bar{{display:flex;justify-content:space-between;padding:18px 20px 6px;font-weight:600;font-size:15px}}
.av svg{{width:96px;height:96px;display:block;margin:6px auto 8px;border-radius:50%}}
.handle{{font-weight:600;font-size:15px}}
.stats{{display:flex;justify-content:center;gap:26px;margin:12px 0}}
.stats b{{display:block;font-size:16px}} .stats span{{color:#777;font-size:12px}}
.btns{{display:flex;justify-content:center;gap:6px;margin:4px 0 10px}}
.btns span{{background:#F1F1F2;border-radius:6px;padding:8px 22px;font-weight:600}}
.btns span:first-child{{background:var(--bx);color:var(--cr);padding:8px 40px}}
.bio{{padding:0 28px 6px;font-size:13px}}
.bio a{{display:block;font-weight:600;color:#141414;margin-top:4px}}
.tabs{{display:flex;justify-content:space-around;border-bottom:1px solid #eee;padding:10px 0 8px;color:#999;font-size:12px;margin-top:8px}}
.tabs span:first-child{{color:#141414;border-bottom:2px solid #141414;padding-bottom:6px}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:2px}}
.cell{{position:relative}}
.cell img{{width:100%;aspect-ratio:3/4;object-fit:cover;display:block}}
.pin{{position:absolute;top:6px;left:6px;background:#FE2C55;color:#fff;font-style:normal;font-size:10px;font-weight:600;padding:2px 6px;border-radius:3px}}
.views{{position:absolute;left:6px;bottom:5px;color:#fff;font-size:11px;font-weight:600;text-shadow:0 1px 3px rgba(0,0,0,.6)}}
.strat{{display:grid;gap:26px}}
.pillars{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:2px;background:var(--line)}}
.pillars div{{background:var(--cr);padding:20px;display:grid;gap:6px}}
.pillars b{{font-family:var(--m);font-size:12px;letter-spacing:.14em;color:var(--chf);text-transform:uppercase;font-weight:400}}
.covers{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:28px}}
.covers figure{{margin:0;display:grid;gap:12px;align-content:start}}
.covers img{{width:100%;display:block;border-radius:14px;box-shadow:0 12px 30px rgba(0,0,0,.3)}}
.covers figcaption{{font-size:14.5px;color:#E3CFC2;display:grid;gap:4px}}
.covers b{{color:var(--cr);font-weight:500;font-size:16px}}
.fmt{{font-family:var(--m);font-size:11.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--ch)}}
.rules{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:32px}}
.rule{{display:grid;gap:10px;align-content:start;padding-top:18px;border-top:2px solid var(--bx)}}
.rule ul{{margin:0;padding-left:18px;color:var(--muted)}}
.bios{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:24px}}
.bio-card{{background:#fff;border:1px solid var(--line);padding:22px;display:grid;gap:12px;align-content:start}}
.bio-text{{font-size:16px;line-height:1.5}}
.tag{{font-family:var(--m);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--chf)}}
.count{{font-family:var(--m);font-size:12px;color:var(--muted)}}
.caps{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:24px}}
.cap{{background:#fff;color:var(--ink);padding:22px;display:grid;gap:10px;align-content:start;border:1px solid var(--line);font-size:15px;white-space:pre-line}}
.week{{width:100%;border-collapse:collapse;font-size:15px;min-width:640px}}
.week th,.week td{{text-align:left;padding:14px 12px;border-bottom:1px solid var(--line);vertical-align:top}}
.week th{{font-family:var(--m);font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--chf);font-weight:400}}
.scroll{{overflow-x:auto}} .note{{font-size:14px;color:var(--muted)}}
@media (max-width:900px){{.hero{{grid-template-columns:minmax(0,1fr)}}.phone{{margin:0 auto}}.covers{{grid-template-columns:repeat(2,minmax(0,1fr))}}.rules,.bios,.caps{{grid-template-columns:minmax(0,1fr)}}}}
</style>

<section class="band"><div class="wrap"><div class="hero">
 <div class="phone"><div class="screen">
  <div class="bar"><span>＋</span><span>DOMOVA ▾</span><span>☰</span></div>
  <div class="av">{avatar}</div>
  <div class="handle">@domova.btp</div>
  <div class="stats"><div><b>48</b><span>Abonnements</span></div><div><b>2 310</b><span>Abonnés</span></div><div><b>24,9 k</b><span>J’aime</span></div></div>
  <div class="btns"><span>Suivre</span><span>Message</span></div>
  <div class="bio">{bio}<a>domova.fr</a></div>
  <div class="tabs"><span>Vidéos</span><span>Repost</span><span>Favoris</span></div>
  <div class="grid">{grid}</div>
 </div></div>
 <div class="strat">
  <span class="eyebrow">DOMOVA · Direction artistique TikTok</span>
  <h1>Les coulisses d’une maison d’architecture</h1>
  <p class="lede">Instagram montre le résultat ; TikTok montre comment on y arrive. Des vidéos verticales courtes, filmées sur le chantier, avec des couvertures à la même charte pour que le profil reste haut de gamme.</p>
  <div class="pillars">
   <div><b>Transformer</b><span>Avant / après et timelapses : le format qui fait le plus de vues.</span></div>
   <div><b>Montrer</b><span>Visites de chantier, gestes d’artisans, détails de finition.</span></div>
   <div><b>Expliquer</b><span>Prix, étapes, erreurs à éviter : face caméra, 30 à 60 s.</span></div>
   <div><b>Incarner</b><span>L’équipe, le gérant, les coulisses. On suit des personnes, pas un logo.</span></div>
  </div>
  <p class="note">Épinglez trois vidéos en haut du profil : la présentation, l’avant/après le plus fort et la vidéo sur les prix. Nombres de vues, ville et projets : exemples.</p>
 </div>
</div></div></section>

<section class="band dark"><div class="wrap">
 <div><span class="eyebrow">Les 9 premières vidéos</span><h2>Couvertures et idées de tournage</h2></div>
 <p class="lede">Couvertures 1080 × 1920 px. Le titre est placé dans le tiers haut, au centre : il reste visible dans la grille (recadrage 3:4) et hors des boutons TikTok à droite et en bas.</p>
 <div class="covers">{cards}</div>
</div></section>

<section class="band"><div class="wrap">
 <div><span class="eyebrow">Les règles</span><h2>Tourner et monter dans la charte</h2></div>
 <div class="rules">
  <div class="rule"><h3>Tournage</h3><ul><li>Vertical 9:16, en 4K si possible, téléphone stabilisé</li><li>Lumière du jour ; avant et après filmés du même point</li><li>L’accroche dans les 2 premières secondes</li><li>Son du chantier conservé (ponceuse, pose, découpe) : il fait regarder</li></ul></div>
  <div class="rule"><h3>Texte à l’écran</h3><ul><li>Police proche de Jost (TikTok : « Classic » ou « Modern »)</li><li>Texte crème sur bloc bordeaux, ou bordeaux sur bloc crème</li><li>3 lignes maximum, dans le tiers haut</li><li>Sous-titres activés : beaucoup regardent sans le son</li></ul></div>
  <div class="rule"><h3>Profil</h3><ul><li>Même photo de profil que sur Instagram</li><li>Une couverture à la charte pour chaque vidéo</li><li>Musique tendance discrète, jamais par-dessus la voix</li><li>Répondre aux commentaires en vidéo : ça fait de nouveaux sujets</li></ul></div>
 </div>
</div></section>

<section class="band" style="padding-top:0"><div class="wrap">
 <div><span class="eyebrow">Bio TikTok</span><h2>Trois bios (80 caractères maximum)</h2></div>
 <div class="bios">{bios}</div>
</div></section>

<section class="band dark"><div class="wrap">
 <div><span class="eyebrow">Légendes</span><h2>Exemples de légendes</h2></div>
 <div class="caps">{caps}</div>
 <p class="lede">Les légendes des 9 vidéos sont dans le dossier à publier, un fichier texte par vidéo.</p>
</div></section>

<section class="band"><div class="wrap">
 <div><span class="eyebrow">Planning</span><h2>Une semaine type</h2></div>
 <div class="scroll"><table class="week"><thead><tr><th>Jour</th><th>Vidéo</th><th>Durée</th></tr></thead><tbody>
  <tr><td>Mardi</td><td>Visite de chantier ou geste d’artisan</td><td>15 à 30 s</td></tr>
  <tr><td>Jeudi</td><td>Conseil face caméra (prix, étapes, erreurs)</td><td>30 à 60 s</td></tr>
  <tr><td>Samedi</td><td>Avant / après ou timelapse</td><td>10 à 20 s</td></tr>
 </tbody></table></div>
 <p class="note">Publiez entre 18 h et 21 h en semaine, et le samedi matin. Trois vidéos par semaine, sur la durée.</p>
</div></section>
"""


def build():
    os.makedirs(C, exist_ok=True)
    pairs = []
    for v in TIKTOK_VIDEOS:
        f = os.path.join(C, v["fichier"])
        open(f + ".svg", "w").write(doc(COVERS[v["slug"]](), f"DOMOVA — TikTok — {v['titre']}"))
        pairs += [f + ".svg", f + ".png"]
    subprocess.run(["node", os.path.join(os.path.dirname(__file__), "render_svg.js"), "1080"] + pairs, check=True)
    for k in range(1, len(pairs), 2):
        Image.open(pairs[k]).convert("RGB").save(pairs[k][:-4] + ".jpg", quality=88, optimize=True, progressive=True)
    open(os.path.join(OUT, "index.html"), "w").write(page())
    print("tiktok ok")


if __name__ == "__main__":
    build()
