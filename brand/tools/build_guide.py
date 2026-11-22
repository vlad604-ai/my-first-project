"""DOMOVA — charte graphique : page HTML + PDF.

Génère  ../guide/index.html  (page autonome, logos en SVG inline)
        ../guide/assets/*.jpg  (versions web des planches et mises en situation)
        ../guide/DOMOVA_charte-graphique.pdf
"""
import os
import re
import sys
import subprocess
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from geom import to_d  # noqa: E402
from build_logos import (SYM_MARK, SYM_DIAG, SYM_REST, SYM_W, SYM_H, SYM_MARK as _M,  # noqa: E402
                         INK, ANTHRACITE, OFFWHITE, COPPER, ROOT, LOCKUPS)
from marks import SYM  # noqa: E402

G = os.path.join(ROOT, "guide")
A = os.path.join(G, "assets")


def inline(name):
    s = open(os.path.join(ROOT, "logos", "svg", name + ".svg")).read().strip()
    s = re.sub(r' width="[^"]+" height="[^"]+"', ' role="img"', s, count=1)
    return s


def web_images():
    os.makedirs(A, exist_ok=True)
    out = {}
    srcs = [os.path.join(ROOT, "directions", f) for f in sorted(os.listdir(os.path.join(ROOT, "directions"))) if f.endswith(".png")]
    srcs += [os.path.join(ROOT, "mockups", f) for f in sorted(os.listdir(os.path.join(ROOT, "mockups"))) if f.endswith(".png")]
    for p in srcs:
        im = Image.open(p).convert("RGB")
        im.thumbnail((1800, 1800))
        name = os.path.splitext(os.path.basename(p))[0] + ".jpg"
        im.save(os.path.join(A, name), quality=86, optimize=True, progressive=True)
        out[os.path.basename(p)] = "assets/" + name
    return out


def construction_svg():
    """Symbol on its construction grid, with the key measures."""
    s, H, flat = SYM["s"], SYM["H"], SYM["flat"]
    R = H / 2
    pad = 40
    W = SYM_W
    k = 3.2
    vw, vh = (W + 2 * pad) * k, (H + 2 * pad) * k
    o = pad * k
    L = []
    L.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vw:.0f} {vh:.0f}" role="img" aria-label="Construction du symbole">')
    L.append(f'<rect width="{vw:.0f}" height="{vh:.0f}" fill="{ANTHRACITE}"/>')
    # 4-unit grid
    for i in range(0, int(W) + 1, 4):
        op = 0.16 if i % 20 == 0 else 0.06
        L.append(f'<line x1="{o + i * k:.1f}" y1="{o - 12:.1f}" x2="{o + i * k:.1f}" y2="{o + H * k + 12:.1f}" stroke="#F5F4F0" stroke-opacity="{op}" stroke-width="1"/>')
    for j in range(0, int(H) + 1, 4):
        op = 0.16 if j % 20 == 0 else 0.06
        L.append(f'<line x1="{o - 12:.1f}" y1="{o + j * k:.1f}" x2="{o + W * k + 12:.1f}" y2="{o + j * k:.1f}" stroke="#F5F4F0" stroke-opacity="{op}" stroke-width="1"/>')
    L.append(f'<path fill="{OFFWHITE}" fill-opacity="0.92" d="{to_d(SYM_REST, k, o, o)}"/>')
    L.append(f'<path fill="{COPPER}" d="{to_d(SYM_DIAG, k, o, o)}"/>')
    # construction circles
    cx, cy = o + flat * k, o + R * k
    for r in (R, R - s):
        L.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * k:.1f}" fill="none" stroke="{COPPER}" stroke-width="1.2" stroke-dasharray="5 5"/>')
    L.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" fill="{COPPER}"/>')
    # V guide lines
    nl, nr = SYM["nl"], SYM["nr"]
    L.append(f'<line x1="{o + nl * k:.1f}" y1="{o:.1f}" x2="{o + (nl + nr) / 2 * k:.1f}" y2="{o + (H - s) * k:.1f}" stroke="{COPPER}" stroke-width="1" stroke-opacity="0.8"/>')
    # dimension labels
    def dim(x1, y1, x2, y2, label, lx, ly):
        L.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#F5F4F0" stroke-width="1"/>')
        L.append(f'<text x="{lx:.1f}" y="{ly:.1f}" fill="#F5F4F0" font-family="Jost, sans-serif" font-size="15" letter-spacing="1.5">{label}</text>')
    dim(o, o + H * k + 26, o + s * k, o + H * k + 26, "20 u", o, o + H * k + 50)
    dim(o - 26, o, o - 26, o + H * k, "", 0, 0)
    L.append(f'<text x="{o - 34:.1f}" y="{o + H * k / 2:.1f}" fill="#F5F4F0" font-family="Jost, sans-serif" font-size="15" letter-spacing="1.5" text-anchor="middle" transform="rotate(-90 {o - 34:.1f} {o + H * k / 2:.1f})">112 u</text>')
    dim(o, o - 26, o + W * k, o - 26, "120 u", o + W * k / 2 - 22, o - 36)
    L.append(f'<text x="{o + W * k + 14:.1f}" y="{cy + 5:.1f}" fill="{COPPER}" font-family="Jost, sans-serif" font-size="14" letter-spacing="1">R 56 / R 36</text>')
    L.append('</svg>')
    return "".join(L)


def clearspace_svg():
    body, w, h = LOCKUPS["horizontal"]("couleur-fond-clair")
    x = 100 * 0.5  # X = half the cap height of DOMOVA
    m = x
    vw, vh = w + 2 * m + 40, h + 2 * m + 40
    o = 20
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vw:.0f} {vh:.0f}" role="img" aria-label="Zone de protection">']
    s.append(f'<rect width="{vw:.0f}" height="{vh:.0f}" fill="{OFFWHITE}"/>')
    s.append(f'<rect x="{o}" y="{o}" width="{w + 2 * m:.1f}" height="{h + 2 * m:.1f}" fill="{COPPER}" fill-opacity="0.12" stroke="{COPPER}" stroke-dasharray="6 6" stroke-width="1.5"/>')
    s.append(f'<rect x="{o + m}" y="{o + m}" width="{w:.1f}" height="{h:.1f}" fill="none" stroke="{COPPER}" stroke-width="1"/>')
    s.append(f'<g transform="translate({o + m} {o + m})">{body}</g>')
    for (xx, yy) in ((o, o + m + h / 2 - 12), (o + m + w, o + m + h / 2 - 12)):
        s.append(f'<text x="{xx + m / 2:.1f}" y="{yy:.1f}" text-anchor="middle" fill="{COPPER}" font-family="Jost, sans-serif" font-size="22" font-weight="600">X</text>')
    s.append(f'<text x="{o + m + w / 2:.1f}" y="{o + m / 2 + 8:.1f}" text-anchor="middle" fill="{COPPER}" font-family="Jost, sans-serif" font-size="22" font-weight="600">X</text>')
    s.append('</svg>')
    return "".join(s)


def small_sizes_svg():
    """Symbol at decreasing pixel sizes, pixel-true."""
    sizes = (64, 48, 32, 24, 16)
    x = 0
    parts = []
    for px in sizes:
        k = px / SYM_H
        parts.append(f'<path fill="{OFFWHITE}" d="{to_d(SYM_REST, k, x, 64 - px)}"/><path fill="{COPPER}" d="{to_d(SYM_DIAG, k, x, 64 - px)}"/>')
        parts.append(f'<text x="{x + px * SYM_W / SYM_H / 2:.1f}" y="88" text-anchor="middle" fill="#9C9890" font-family="Jost, sans-serif" font-size="11">{px} px</text>')
        x += px * SYM_W / SYM_H + 34
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {x:.0f} 94" style="max-width:{x:.0f}px" role="img" aria-label="Lisibilité en petit format">{"".join(parts)}</svg>'


CSS = """
<title>DOMOVA Identité</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Jost:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
/* Layout: alternating full-bleed bands (ink / off-white), 12-col content at 1180px, plates sized like print boards */
:root{
  --ink:#111111; --anth:#252525; --paper:#F5F4F0; --copper:#B87345;
  --muted-d:#9C9890; --muted-l:#5D5B57; --line-d:rgba(245,244,240,.14); --line-l:rgba(17,17,17,.14);
  --f-display:"Jost","Futura","Century Gothic",system-ui,sans-serif;
  --f-body:"Jost","Futura","Century Gothic",system-ui,sans-serif;
  --f-mono:"JetBrains Mono",ui-monospace,"SFMono-Regular",Menlo,monospace;
  color-scheme:dark;
}
*{box-sizing:border-box}
body{margin:0;background:var(--ink);color:var(--paper);font-family:var(--f-body);font-size:17px;line-height:1.6;-webkit-font-smoothing:antialiased}
.band{padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:clamp(56px,9vw,120px)}
.band.light{background:var(--paper);color:var(--ink)}
.band.anth{background:var(--anth)}
.wrap{max-width:1180px;margin:0 auto;display:grid;gap:40px}
.eyebrow{font-family:var(--f-mono);font-size:12px;letter-spacing:.22em;text-transform:uppercase;color:var(--copper)}
h1,h2,h3{font-family:var(--f-display);font-weight:600;line-height:1.12;text-wrap:balance;margin:0}
h2{font-size:clamp(28px,4vw,44px);letter-spacing:.01em}
h3{font-size:20px;letter-spacing:.02em}
p{margin:0;max-width:64ch}
.lede{font-size:clamp(18px,2vw,21px);color:var(--muted-d)}
.light .lede,.light .muted{color:var(--muted-l)}
.muted{color:var(--muted-d)}
.head{display:grid;gap:14px}
.hero{margin-top:calc(-1*env(safe-area-inset-top,0px));padding-top:calc(env(safe-area-inset-top,0px) + clamp(56px,9vw,120px))}
.hero .logo{max-width:560px;width:100%;margin:0 auto}
.hero .wrap{justify-items:center;text-align:center;gap:48px}
.hero p{margin:0 auto}
.meta{display:flex;flex-wrap:wrap;gap:10px 28px;justify-content:center;font-family:var(--f-mono);font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted-d)}
.dirs{display:grid;gap:56px}
.dir{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(0,1fr);gap:32px;align-items:start}
.dir img{width:100%;display:block;border:1px solid var(--line-l)}
.dir .txt{display:grid;gap:12px}
.tag{display:inline-block;font-family:var(--f-mono);font-size:11px;letter-spacing:.16em;text-transform:uppercase;padding:4px 10px;border:1px solid currentColor;justify-self:start}
.tag.win{color:var(--paper);background:var(--copper);border-color:var(--copper)}
.dir ul{margin:0;padding-left:18px;color:var(--muted-l);font-size:15px}
.split{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:48px;align-items:center}
.split svg{width:100%;height:auto;display:block}
.facts{display:grid;gap:18px;margin:0;padding:0;list-style:none}
.facts li{display:grid;grid-template-columns:120px minmax(0,1fr);gap:16px;padding-top:16px;border-top:1px solid var(--line-d)}
.facts b{font-family:var(--f-mono);font-weight:500;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--copper);padding-top:3px}
.grid-logos{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:2px;background:var(--line-l)}
.plate{display:grid;place-items:center;padding:clamp(28px,5vw,64px);min-height:240px;position:relative}
.plate svg{width:100%;height:auto;max-height:220px}
.plate.sq svg{max-width:150px}
.plate.sym svg{max-width:130px}
.plate .cap{position:absolute;left:16px;bottom:12px;font-family:var(--f-mono);font-size:11px;letter-spacing:.12em;text-transform:uppercase;opacity:.6}
.p-ink{background:var(--ink);color:var(--paper)}.p-paper{background:var(--paper);color:var(--ink)}
.p-anth{background:var(--anth);color:var(--paper)}.p-copper{background:var(--copper);color:var(--ink)}
.swatches{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}
.sw{display:grid;grid-template-rows:180px auto;border:1px solid var(--line-l)}
.sw .chip{display:flex;align-items:flex-end;padding:14px;font-family:var(--f-mono);font-size:12px;letter-spacing:.1em}
.sw .info{padding:16px;display:grid;gap:4px;font-size:14px;background:#fff;color:var(--ink)}
.sw .info b{font-size:16px;font-weight:600}
.sw code{font-family:var(--f-mono);font-size:12.5px;color:var(--muted-l);font-variant-numeric:tabular-nums}
.ratio{display:flex;height:22px;border:1px solid var(--line-l)}
.ratio span{display:block}
.type{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:48px}
.spec{display:grid;gap:14px;padding-top:20px;border-top:1px solid var(--line-d)}
.spec .big{font-family:var(--f-display);font-weight:600;font-size:clamp(40px,6vw,72px);letter-spacing:.14em;line-height:1}
.spec .alpha{font-family:var(--f-display);font-weight:500;font-size:22px;letter-spacing:.12em;word-break:break-word}
.rules{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:24px}
.rule{display:grid;gap:10px;align-content:start}
.rule .box{background:var(--paper);display:grid;place-items:center;aspect-ratio:4/3;padding:22px;position:relative;max-width:100%}
.rule .box svg{width:100%;height:auto;max-height:100%}
.rule .x{position:absolute;top:10px;right:12px;font-family:var(--f-mono);font-size:12px;color:#B23A2A;letter-spacing:.1em}
.rule p{font-size:15px}
.mocks{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}
.mock{margin:0;display:grid;gap:10px}
.mock img{width:100%;display:block}
.mock.wide{grid-column:1/-1}
.mock figcaption{font-size:14px;color:var(--muted-d)}
.mock figcaption b{color:var(--paper);font-weight:500;margin-right:6px}
.files{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:2px;background:var(--line-d)}
.file{background:var(--ink);padding:22px;display:grid;gap:8px;align-content:start}
.file code{font-family:var(--f-mono);font-size:12.5px;color:var(--copper);word-break:break-all}
.file p{font-size:14.5px;color:var(--muted-d)}
.small{overflow-x:auto}
footer .wrap{grid-template-columns:auto 1fr;align-items:center;gap:24px}
footer svg{width:44px;height:auto}
@media (max-width:860px){
  .dir,.split,.type{grid-template-columns:minmax(0,1fr)}
  .swatches{grid-template-columns:repeat(2,minmax(0,1fr))}
  .rules,.files{grid-template-columns:minmax(0,1fr)}
  .mocks,.grid-logos{grid-template-columns:minmax(0,1fr)}
  .facts li{grid-template-columns:minmax(0,1fr);gap:4px}
}
@media print{.band{padding-block:48px;break-inside:avoid}.mock,.dir,.plate{break-inside:avoid}}
</style>
"""


def page(img):
    sym_dark = inline("domova_symbole_couleur-fond-sombre")
    P = []
    P.append(CSS)
    # HERO
    P.append(f"""
<section class="band hero" aria-labelledby="t-hero"><div class="wrap">
  <div class="eyebrow">Identité visuelle · Charte v1.0 · Novembre 2026</div>
  <div class="logo">{inline("domova_principal_couleur-fond-sombre")}</div>
  <h1 id="t-hero" style="position:absolute;left:-9999px">DOMOVA, identité visuelle</h1>
  <p class="lede">Entreprise générale de construction, de rénovation et d’aménagement. Une marque bâtie comme un ouvrage : une trame, des pleins, des vides, et une seule note de cuivre.</p>
  <div class="meta"><span>Gros œuvre</span><span>Rénovation int. &amp; ext.</span><span>Électricité · Plomberie</span><span>Menuiserie</span><span>Bureaux sur mesure</span><span>Façades</span><span>Tous corps d’état</span></div>
</div></section>""")
    # DIRECTIONS
    P.append(f"""
<section class="band light" aria-labelledby="t-dir"><div class="wrap">
  <div class="head"><div class="eyebrow">Étape 1 · Recherche</div><h2 id="t-dir">Trois directions artistiques</h2>
  <p class="lede">Trois réponses réellement différentes au même brief : un monogramme plié, un volume en perspective, un assemblage de pièces. Aucune ne recourt aux outils, maisons ou grues.</p></div>
  <div class="dirs">
    <article class="dir"><img src="{img['direction-01_le-pli.png']}" alt="Direction 01, Le Pli : monogramme D+M blanc et cuivre sur noir" loading="lazy">
      <div class="txt"><span class="tag win">Retenue</span><h3>01 · Le Pli</h3>
      <p>Un D dont le sommet se plie en M. La jambe du D et sa panse deviennent les deux montants du M ; le V descend jusqu’à la lisse basse. Deux contre-formes apparaissent : un triangle (le plan) et un segment de cercle (le volume).</p>
      <ul><li>D et M lisibles dans une seule forme pleine</li><li>Silhouette identifiable même à 16 px</li><li>Le cuivre souligne le second trait du M : le pli</li></ul></div></article>
    <article class="dir"><img src="{img['direction-02_perspective.png']}" alt="Direction 02, Perspective : un M formé de deux façades pliées" loading="lazy">
      <div class="txt"><span class="tag">Alternative</span><h3>02 · Perspective</h3>
      <p>Deux façades pliées, vues en perspective, dessinent un M en volume. Typographie technique très espacée, filet cuivre sous le nom.</p>
      <ul><li>Très architectural, lecture 3D immédiate</li><li>Repose sur trois tons : fragile en monochrome et en broderie</li><li>Le D disparaît du symbole</li></ul></div></article>
    <article class="dir"><img src="{img['direction-03_fondation.png']}" alt="Direction 03, Fondation : un pilier et un demi-cylindre assemblés" loading="lazy">
      <div class="txt"><span class="tag">Alternative</span><h3>03 · Fondation</h3>
      <p>Un pilier et un demi-cylindre posés avec un joint : la logique de l’assemblage. Une clé cuivre au centre, une composition éditoriale aérée.</p>
      <ul><li>Calme, très haut de gamme</li><li>Le M n’apparaît pas ; le signe reste proche d’un simple D</li><li>Moins distinctif face aux marques existantes</li></ul></div></article>
  </div>
  <p><strong>Pourquoi Le Pli.</strong> C’est la seule piste qui unit réellement D et M dans un signe unique, fonctionne en une couleur (broderie, gravure, tampon, vinyle) et garde sa silhouette en très petit. Elle est développée ci-dessous.</p>
</div></section>""")
    # SYMBOL
    P.append(f"""
<section class="band anth" aria-labelledby="t-sym"><div class="wrap">
  <div class="head"><div class="eyebrow">Étape 2 · Le symbole</div><h2 id="t-sym">Un monogramme construit, pas dessiné à main levée</h2></div>
  <div class="split">
    <div>{construction_svg()}</div>
    <ul class="facts">
      <li><b>Trame</b><span>Module de 4 unités. Hauteur 112 u, largeur 120 u : le signe tient dans un carré presque parfait, idéal pour les avatars et l’icône.</span></li>
      <li><b>Épaisseur</b><span>Fût de 20 u ; diagonales à 18 u, corrigées optiquement pour paraître égales.</span></li>
      <li><b>Panse</b><span>Deux cercles concentriques, R 56 et R 36, centrés sur l’axe médian.</span></li>
      <li><b>Le pli</b><span>Le V naît au nu intérieur du fût et touche exactement la lisse basse : il partage l’espace en plan et en volume.</span></li>
      <li><b>Cuivre</b><span>Une seule pièce en cuivre, le second trait du M. Elle peut passer en noir ou en blanc sans que le signe perde son sens.</span></li>
    </ul>
  </div>
  <div class="small">{small_sizes_svg()}</div>
  <p class="muted">Rendu réel du symbole de 64 à 16 px : la silhouette D, le V et les deux contre-formes restent distincts.</p>
</div></section>""")
    # LOCKUPS
    P.append(f"""
<section class="band light" aria-labelledby="t-lock"><div class="wrap">
  <div class="head"><div class="eyebrow">Étape 3 · Déclinaisons</div><h2 id="t-lock">Logo principal, horizontal, compact, monogramme</h2>
  <p class="lede">Chaque version existe en couleur sur fond clair, couleur sur fond sombre, monochrome noir et monochrome blanc. Tous les textes sont vectorisés : aucun fichier ne dépend d’une police installée.</p></div>
  <div class="grid-logos">
    <div class="plate p-paper"><span class="cap">A · Principal · fond clair</span>{inline("domova_principal_couleur-fond-clair")}</div>
    <div class="plate p-ink"><span class="cap">A · Principal · fond sombre</span>{inline("domova_principal_couleur-fond-sombre")}</div>
    <div class="plate p-ink"><span class="cap">B · Horizontal · fond sombre</span>{inline("domova_horizontal_couleur-fond-sombre")}</div>
    <div class="plate p-paper"><span class="cap">B · Horizontal · fond clair</span>{inline("domova_horizontal_couleur-fond-clair")}</div>
    <div class="plate p-paper"><span class="cap">Compact · sans signature</span>{inline("domova_compact_couleur-fond-clair")}</div>
    <div class="plate p-anth"><span class="cap">Compact · anthracite</span>{inline("domova_compact_couleur-fond-sombre")}</div>
    <div class="plate p-paper sq"><span class="cap">C · Monogramme officiel</span>{inline("domova_monogramme_couleur-fond-clair")}</div>
    <div class="plate p-ink sq"><span class="cap">C · Monogramme inversé</span>{inline("domova_monogramme_couleur-fond-sombre")}</div>
    <div class="plate p-paper sym"><span class="cap">Symbole · monochrome noir</span>{inline("domova_symbole_monochrome-noir")}</div>
    <div class="plate p-copper sym"><span class="cap">Symbole · noir sur cuivre</span>{inline("domova_symbole_monochrome-noir")}</div>
    <div class="plate p-anth"><span class="cap">Monochrome blanc</span>{inline("domova_horizontal_monochrome-blanc")}</div>
    <div class="plate p-paper"><span class="cap">Monochrome noir</span>{inline("domova_principal_monochrome-noir")}</div>
  </div>
</div></section>""")
    # COLOURS
    sw = [("Noir profond", "#111111", "17 · 17 · 17", "60 · 50 · 40 · 100 (noir riche)", "Fond principal, texte", INK, OFFWHITE),
          ("Anthracite", "#252525", "37 · 37 · 37", "0 · 0 · 0 · 85", "Fonds secondaires, aplats", ANTHRACITE, OFFWHITE),
          ("Blanc cassé", "#F5F4F0", "245 · 244 · 240", "0 · 0 · 2 · 4", "Papier, textes sur noir", OFFWHITE, INK),
          ("Cuivre", "#B87345", "184 · 115 · 69", "0 · 38 · 63 · 28", "Accent : 5 % de la surface au plus", COPPER, INK)]
    cards = "".join(f'<div class="sw"><div class="chip" style="background:{c};color:{t}">{h}</div><div class="info"><b>{n}</b><code>HEX {h}</code><code>RVB {r}</code><code>CMJN {k}</code><span>{u}</span></div></div>' for n, h, r, k, u, c, t in sw)
    P.append(f"""
<section class="band light" style="padding-top:0" aria-labelledby="t-col"><div class="wrap">
  <div class="head"><div class="eyebrow">Couleurs</div><h2 id="t-col">Le noir domine, le cuivre signe</h2></div>
  <div class="swatches">{cards}</div>
  <div class="ratio" aria-label="Proportions d’usage : noir 55 %, anthracite 20 %, blanc cassé 20 %, cuivre 5 %"><span style="flex:55;background:var(--ink)"></span><span style="flex:20;background:var(--anth)"></span><span style="flex:20;background:var(--paper)"></span><span style="flex:5;background:var(--copper)"></span></div>
  <p class="muted">Proportions d’usage : noir 55 %, anthracite 20 %, blanc cassé 20 %, cuivre 5 %. Valeurs CMJN indicatives, à caler avec l’imprimeur. En marquage véhicule ou en enseigne, le cuivre peut être réalisé en vinyle ou en métal cuivré brossé ; en broderie, choisir un fil cuivre mat.</p>
</div></section>""")
    # TYPE
    P.append(f"""
<section class="band" aria-labelledby="t-type"><div class="wrap">
  <div class="head"><div class="eyebrow">Typographie</div><h2 id="t-type">Un lettrage sur mesure, une famille d’accompagnement</h2></div>
  <div class="type">
    <div class="spec"><span class="eyebrow">Nom · lettrage DOMOVA</span>
      <div style="max-width:440px">{inline("domova_nom-signature_couleur-fond-sombre")}</div>
      <p class="muted">Capitales géométriques dessinées pour la marque : O parfaitement circulaires, D qui reprend la panse du symbole, M à fûts verticaux dont le V touche la ligne de base. Graisse soutenue (fût = 21 % de la hauteur de capitale), approche élargie et crénage optique paire par paire (DO, OV, VA).</p></div>
    <div class="spec"><span class="eyebrow">Supports · Jost (SIL Open Font License)</span>
      <div class="big">Aa</div>
      <div class="alpha">ABCDEFGHIJKLMNOPQRSTUVWXYZ<br>0123456789 · € · m² · n°</div>
      <p class="muted">Jost Medium pour la signature et les titres, Jost Regular pour le texte courant. Gratuite, utilisable commercialement, disponible sur Google Fonts. Capitales espacées (+20 à +30 %) pour les intitulés.</p></div>
  </div>
</div></section>""")
    # RULES
    def bad(tf, note, extra=""):
        s = inline("domova_horizontal_couleur-fond-clair")
        s = s.replace("<title>", f'<g transform="{tf}" {extra}><title>', 1).replace("</svg>", "</g></svg>")
        return s
    P.append(f"""
<section class="band anth" aria-labelledby="t-rules"><div class="wrap">
  <div class="head"><div class="eyebrow">Règles d’usage</div><h2 id="t-rules">Protection, tailles minimales, interdits</h2></div>
  <div class="split">
    <div>{clearspace_svg()}</div>
    <ul class="facts">
      <li><b>Zone libre</b><span>X = la moitié de la hauteur des capitales de DOMOVA, sur les quatre côtés. Rien ne pénètre dans cette zone.</span></li>
      <li><b>Principal</b><span>40 mm de large minimum en impression, 220 px à l’écran.</span></li>
      <li><b>Horizontal</b><span>35 mm / 200 px. En dessous, passer au logo compact : la signature disparaît.</span></li>
      <li><b>Compact</b><span>20 mm / 110 px.</span></li>
      <li><b>Symbole</b><span>5 mm / 16 px. Broderie : 12 mm minimum pour le symbole, 45 mm pour le logo avec signature.</span></li>
    </ul>
  </div>
  <div class="rules">
    <div class="rule"><div class="box"><span class="x">Interdit</span>{inline("domova_horizontal_couleur-fond-clair").replace("<svg ", '<svg style="transform:scale(1.18,.62)" ', 1)}</div><p>Ne pas déformer ni étirer le logo.</p></div>
    <div class="rule"><div class="box" style="background:#8a8a8a"><span class="x">Interdit</span>{inline("domova_horizontal_couleur-fond-clair")}</div><p>Pas de version couleur sur fond moyen ou photo chargée : utiliser le monochrome blanc ou noir.</p></div>
    <div class="rule"><div class="box"><span class="x">Interdit</span>{inline("domova_horizontal_couleur-fond-clair").replace(INK, "#1F4E8C").replace(COPPER, "#E0B000")}</div><p>Ne pas changer les couleurs ni ajouter d’ombre, de dégradé ou de contour.</p></div>
  </div>
</div></section>""")
    # MOCKUPS
    m = [("domova_mockup_01_camionnette.png", "Véhicule", "Utilitaire noir, logo horizontal blanc et cuivre, filet cuivre bas de caisse, symbole sur la portière cabine.", True),
         ("domova_mockup_02_textile-polo-sweat.png", "Textile", "Polo noir brodé cœur (symbole + nom), sweat de travail avec logo principal au dos.", True),
         ("domova_mockup_03_cartes-de-visite.png", "Carte de visite", "85 × 55 mm. Recto noir, monogramme en dorure à chaud cuivre ; verso blanc cassé, coordonnées en Jost.", False),
         ("domova_mockup_04_panneau-de-chantier.png", "Panneau de chantier", "Bandeau noir avec logo horizontal, informations réglementaires sur fond blanc cassé.", False),
         ("domova_mockup_05_devis.png", "Devis", "A4. En-tête horizontal, tableau à bandeau noir, total TTC mis en avant, mentions légales en pied.", False),
         ("domova_mockup_06_reseaux-sociaux.png", "Instagram · TikTok", "Avatar circulaire (monogramme sur noir), profils clair et sombre, test de lisibilité de 180 à 28 px.", False)]
    figs = "".join(f'<figure class="mock{" wide" if w else ""}"><img src="{img[f]}" alt="Mise en situation : {t}" loading="lazy"><figcaption><b>{t}</b>{c}</figcaption></figure>' for f, t, c, w in m)
    P.append(f"""
<section class="band" aria-labelledby="t-mock"><div class="wrap">
  <div class="head"><div class="eyebrow">Étape 4 · Mises en situation</div><h2 id="t-mock">DOMOVA sur le terrain</h2>
  <p class="lede">Illustrations vectorielles fidèles aux proportions réelles des supports. Noms, adresses et numéros sont des exemples à remplacer.</p></div>
  <div class="mocks">{figs}</div>
</div></section>""")
    # FILES
    files = [("logos/svg/", "Vectoriel", "24 fichiers SVG : 6 compositions × 4 versions couleur. Pour le web, la signalétique, le découpe vinyle."),
             ("logos/pdf/", "PDF vectoriel", "Les mêmes 24 logos en PDF, pour l’imprimeur, le brodeur et le marquage véhicule."),
             ("logos/png/", "PNG transparent", "3200 px de large (2048 px pour symbole et monogramme), fond transparent."),
             ("icons/", "Icônes", "Favicon et icône d’application de 16 à 1024 px, avatar réseaux sociaux 1080 × 1080."),
             ("mockups/", "Mises en situation", "6 scènes en SVG et PNG 2400 px."),
             ("tools/", "Sources", "Scripts de construction : tout se régénère en une commande, à l’identique.")]
    fl = "".join(f'<div class="file"><code>{p}</code><h3>{t}</h3><p>{d}</p></div>' for p, t, d in files)
    P.append(f"""
<section class="band anth" aria-labelledby="t-files"><div class="wrap">
  <div class="head"><div class="eyebrow">Livrables</div><h2 id="t-files">Fichiers prêts à l’emploi</h2>
  <p class="lede">Nommage : <code style="font-family:var(--f-mono);color:var(--copper)">domova_[composition]_[version]</code>. Compositions : principal, horizontal, compact, symbole, monogramme, nom-signature. Versions : couleur-fond-clair, couleur-fond-sombre, monochrome-noir, monochrome-blanc.</p></div>
  <div class="files">{fl}</div>
</div></section>
<footer class="band" style="padding-block:40px"><div class="wrap"><div>{sym_dark}</div><p class="muted" style="font-size:14px">DOMOVA · Construction · Rénovation · Aménagement. Charte graphique v1.0. Lettrage et symbole originaux ; police d’accompagnement Jost sous licence SIL OFL 1.1.</p></div></footer>
""")
    return "".join(P)


def build():
    os.makedirs(G, exist_ok=True)
    img = web_images()
    html = page(img)
    open(os.path.join(G, "index.html"), "w").write(html)
    # standalone copy for local viewing / PDF
    full = "<!doctype html><html lang=\"fr\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"></head><body>" + html + "</body></html>"
    open(os.path.join(G, "_print.html"), "w").write(full)
    subprocess.run(["node", "-e", f"""
const {{chromium}}=require('playwright');
(async()=>{{const b=await chromium.launch();const p=await b.newPage({{viewport:{{width:1280,height:900}}}});
await p.goto('file://{os.path.join(G, "_print.html")}',{{waitUntil:'networkidle'}});
await p.emulateMedia({{media:'screen'}});
await p.pdf({{path:'{os.path.join(G, "DOMOVA_charte-graphique.pdf")}',width:'1280px',height:'1810px',printBackground:true,margin:{{top:'0',bottom:'0',left:'0',right:'0'}}}});
await p.setViewportSize({{width:1280,height:900}});
await p.screenshot({{path:'{os.path.join(G, "_preview.png")}',fullPage:true}});
await b.close();}})();"""], check=True)
    os.remove(os.path.join(G, "_print.html"))
    print("guide ok")


if __name__ == "__main__":
    build()
