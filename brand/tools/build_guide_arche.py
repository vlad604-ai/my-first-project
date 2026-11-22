"""DOMOVA — fiche logo « L'Arche » (bordeaux & champagne) : page HTML + PDF.

Sorties : ../identite-arche/guide/{index.html, assets/, DOMOVA_fiche-logo.pdf}
"""
import os
import re
import subprocess
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import brand_arche as B  # noqa: E402
from build_guide import CSS as BASE_CSS  # noqa: E402
from geom import to_d  # noqa: E402

G = os.path.join(B.ROOT, "guide")
A = os.path.join(G, "assets")


def inline(name):
    s = open(os.path.join(B.ROOT, "logos", "svg", name + ".svg")).read().strip()
    return re.sub(r' width="[^"]+" height="[^"]+"', ' role="img"', s, count=1)


def css():
    c = BASE_CSS.replace("<title>DOMOVA Identité</title>", "<title>DOMOVA Fiche logo</title>")
    c = (c.replace("--ink:#111111", f"--ink:{B.BORDEAUX}").replace("--anth:#252525", f"--anth:{B.BORDEAUX_PROFOND}")
          .replace("--paper:#F5F4F0", f"--paper:{B.CREME}").replace("--copper:#B87345", f"--copper:{B.CHAMPAGNE}")
          .replace("--muted-d:#9C9890", "--muted-d:#D2BFB2").replace("--muted-l:#5D5B57", "--muted-l:#6B4F4A")
          .replace("JetBrains+Mono:wght@400;500&", "JetBrains+Mono:wght@400;500&family=Jost:wght@300&"))
    extra = f"""
.light .eyebrow,.light .num{{color:{B.CHAMPAGNE_FONCE}}}
.light .tag.win{{color:{B.CREME}}}
.weights{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:2px;background:var(--line-d)}}
.weights .plate{{min-height:300px}}
.plate.sym svg{{max-width:170px}}
.wm-sample{{max-width:520px}}
"""
    return c.replace("</style>", extra + "</style>")


def web_images():
    os.makedirs(A, exist_ok=True)
    out = {}
    src = os.path.join(B.ROOT, "mockups")
    for f in sorted(os.listdir(src)):
        if f.endswith(".png"):
            im = Image.open(os.path.join(src, f)).convert("RGB")
            im.thumbnail((1800, 1800))
            name = f[:-4] + ".jpg"
            im.save(os.path.join(A, name), quality=86, optimize=True, progressive=True)
            out[f] = "assets/" + name
    return out


def construction_svg():
    s, t, i = B.WEIGHTS["fin"]
    k = 2.6
    pad = 46
    W, H = B.SYM_W, B.SYM_H
    vw, vh = (W + 2 * pad) * k, (H + 2 * pad) * k
    o = pad * k
    ox = o + B.SILL_OVER * k
    L = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vw:.0f} {vh:.0f}" role="img" aria-label="Construction de l’Arche">',
         f'<rect width="{vw:.0f}" height="{vh:.0f}" fill="{B.BORDEAUX_PROFOND}"/>']
    for gx in range(0, int(W) + 1, 6):
        L.append(f'<line x1="{o + gx * k:.1f}" y1="{o - 10:.1f}" x2="{o + gx * k:.1f}" y2="{o + H * k + 10:.1f}" stroke="{B.CREME}" stroke-opacity="{0.14 if gx % 30 == 0 else 0.05}"/>')
    for gy in range(0, int(H) + 1, 6):
        L.append(f'<line x1="{o - 10:.1f}" y1="{o + gy * k:.1f}" x2="{o + W * k + 10:.1f}" y2="{o + gy * k:.1f}" stroke="{B.CREME}" stroke-opacity="{0.14 if gy % 30 == 0 else 0.05}"/>')
    main, acc = B.GEOMS["fin"]
    L.append(f'<path fill="{B.CREME}" d="{to_d(main, k, ox, o)}"/><path fill="{B.CHAMPAGNE}" d="{to_d(acc, k, ox, o)}"/>')
    cx, cy = ox + B.AW / 2 * k, o + B.AW / 2 * k
    L.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{B.AW / 2 * k:.1f}" fill="none" stroke="{B.CHAMPAGNE}" stroke-dasharray="5 5"/>')
    L.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" fill="{B.CHAMPAGNE}"/>')
    L.append(f'<line x1="{ox - 30:.1f}" y1="{cy:.1f}" x2="{ox + B.AW * k + 30:.1f}" y2="{cy:.1f}" stroke="{B.CHAMPAGNE}" stroke-opacity=".6"/>')

    def lab(x, y, txt, anchor="middle", rot=None, col=B.CREME):
        tr = f' transform="rotate({rot} {x:.1f} {y:.1f})"' if rot else ""
        L.append(f'<text x="{x:.1f}" y="{y:.1f}" fill="{col}" font-family="Jost, sans-serif" font-size="15" letter-spacing="1.5" text-anchor="{anchor}"{tr}>{txt}</text>')
    L.append(f'<line x1="{ox:.1f}" y1="{o - 24:.1f}" x2="{ox + B.AW * k:.1f}" y2="{o - 24:.1f}" stroke="{B.CREME}"/>')
    lab(ox + B.AW * k / 2, o - 34, "120 u")
    L.append(f'<line x1="{o - 24:.1f}" y1="{o:.1f}" x2="{o - 24:.1f}" y2="{o + B.AH * k:.1f}" stroke="{B.CREME}"/>')
    lab(o - 34, o + B.AH * k / 2, "168 u", rot=-90)
    L.append(f'<line x1="{o:.1f}" y1="{o + H * k + 24:.1f}" x2="{o + W * k:.1f}" y2="{o + H * k + 24:.1f}" stroke="{B.CREME}"/>')
    lab(o + W * k / 2, o + H * k + 46, "seuil : 1,56 × la largeur de l’arche")
    lab(cx + 8, cy - 12, "R 60", "start", col=B.CHAMPAGNE)
    L.append("</svg>")
    return "".join(L)


def clearspace_svg():
    body, w, h = B.LOCKUPS["horizontal"]("couleur-fond-clair")
    m = B.CAP / 2
    o = 20
    vw, vh = w + 2 * m + 2 * o, h + 2 * m + 2 * o
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vw:.0f} {vh:.0f}" role="img" aria-label="Zone de protection">',
         f'<rect width="{vw:.0f}" height="{vh:.0f}" fill="{B.CREME}"/>',
         f'<rect x="{o}" y="{o}" width="{w + 2 * m:.1f}" height="{h + 2 * m:.1f}" fill="{B.CHAMPAGNE}" fill-opacity=".14" stroke="{B.CHAMPAGNE_FONCE}" stroke-dasharray="6 6" stroke-width="1.5"/>',
         f'<g transform="translate({o + m} {o + m})">{body}</g>']
    for xx in (o + m / 2, o + m + w + m / 2):
        s.append(f'<text x="{xx:.1f}" y="{o + m + h / 2 + 8:.1f}" text-anchor="middle" fill="{B.CHAMPAGNE_FONCE}" font-family="Jost, sans-serif" font-size="22" font-weight="600">X</text>')
    s.append(f'<text x="{o + m + w / 2:.1f}" y="{o + m / 2 + 8:.1f}" text-anchor="middle" fill="{B.CHAMPAGNE_FONCE}" font-family="Jost, sans-serif" font-size="22" font-weight="600">X</text>')
    s.append("</svg>")
    return "".join(s)


def small_sizes_svg():
    x, parts = 0, []
    for px in (64, 48, 32, 24, 16):
        W, H = B.sym_box("renforce")
        w = W * px / H
        parts.append(B.g_symbol(x, 64 - px, px, B.CREME, B.CHAMPAGNE, weight="renforce"))
        parts.append(f'<text x="{x + w / 2:.1f}" y="88" text-anchor="middle" fill="#D2BFB2" font-family="Jost, sans-serif" font-size="11">{px} px</text>')
        x += w + 34
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {x:.0f} 94" style="max-width:{x:.0f}px" role="img" aria-label="Lisibilité en petit format">{"".join(parts)}</svg>'


def page(img):
    P = [css()]
    P.append(f"""
<section class="band hero" aria-labelledby="t-hero"><div class="wrap">
  <div class="eyebrow">Fiche logo · Version 1.0 · Novembre 2026</div>
  <div class="logo" style="max-width:520px">{inline("domova_principal_couleur-fond-sombre")}</div>
  <h1 id="t-hero" style="position:absolute;left:-9999px">DOMOVA, fiche logo</h1>
  <p class="lede">Une voûte tracée d’un trait, posée sur un seuil. L’Arche dit l’entrée, le passage et l’ouvrage bien fait : ce que DOMOVA construit, rénove et aménage.</p>
  <div class="meta"><span>Construction</span><span>Rénovation</span><span>Aménagement</span><span>Tous corps d’état</span></div>
</div></section>""")
    P.append(f"""
<section class="band anth" aria-labelledby="t-sym"><div class="wrap">
  <div class="head"><div class="eyebrow">Le symbole</div><h2 id="t-sym">Une arche, un seuil, un filet champagne</h2></div>
  <div class="split">
    <div>{construction_svg()}</div>
    <ul class="facts">
      <li><b>Arche</b><span>Plein cintre de rayon 60 u sur une largeur de 120 u. Hauteur jusqu’à l’axe du seuil : 168 u, soit 1,4 fois la largeur.</span></li>
      <li><b>Seuil</b><span>Il déborde de 28 % de chaque côté. C’est lui qui pose le signe et le rend stable.</span></li>
      <li><b>Filet</b><span>Une seconde arche intérieure, plus fine, en champagne. C’est la seule touche dorée du logo.</span></li>
      <li><b>Nom</b><span>DOMOVA en Jost Regular, capitales espacées de 42 % : l’arche et le nom partagent le même trait fin.</span></li>
    </ul>
  </div>
  <div class="weights">
    <div class="plate p-anth sym"><span class="cap">Graisse fine · grands formats</span>{inline("domova_symbole_couleur-fond-sombre")}</div>
    <div class="plate p-anth sym"><span class="cap">Graisse renforcée · sous 25 mm / 90 px</span>{inline("domova_symbole-renforce_couleur-fond-sombre")}</div>
  </div>
  <div class="small">{small_sizes_svg()}</div>
  <p class="muted">Sous 25 mm ou 90 px, utilisez toujours la graisse renforcée : le trait fin disparaîtrait. Ci-dessus, le rendu réel de 64 à 16 px.</p>
</div></section>""")
    plates = [("principal", "couleur-fond-clair", "p-paper", "Principal · fond clair"),
              ("principal", "couleur-fond-sombre", "p-ink", "Principal · fond bordeaux"),
              ("horizontal", "couleur-fond-sombre", "p-ink", "Horizontal · fond bordeaux"),
              ("horizontal", "couleur-fond-clair", "p-paper", "Horizontal · fond clair"),
              ("compact", "couleur-fond-clair", "p-paper", "Compact · sans signature"),
              ("compact", "couleur-fond-sombre", "p-anth", "Compact · bordeaux profond"),
              ("monogramme", "couleur-fond-clair", "p-paper sq", "Monogramme · icône officielle"),
              ("monogramme", "couleur-fond-sombre", "p-ink sq", "Monogramme · inversé"),
              ("principal", "monochrome-champagne", "p-anth", "Champagne · dorure, broderie"),
              ("nom-signature", "couleur-fond-clair", "p-paper", "Nom et signature seuls"),
              ("horizontal", "monochrome-blanc", "p-ink", "Monochrome blanc"),
              ("principal", "monochrome-noir", "p-paper", "Monochrome noir")]
    grid = "".join(f'<div class="plate {c}"><span class="cap">{cap}</span>{inline(f"domova_{lk}_{v}")}</div>' for lk, v, c, cap in plates)
    P.append(f"""
<section class="band light" aria-labelledby="t-lock"><div class="wrap">
  <div class="head"><div class="eyebrow">Déclinaisons</div><h2 id="t-lock">Principal, horizontal, compact, monogramme</h2>
  <p class="lede">Chaque composition existe en cinq versions : couleur sur fond clair, couleur sur fond bordeaux, champagne, noir et blanc. Tous les textes sont vectorisés.</p></div>
  <div class="grid-logos">{grid}</div>
</div></section>""")
    sw = [("Bordeaux", B.BORDEAUX, "74 · 20 · 32", "30 · 100 · 70 · 45", "Couleur principale", B.CREME),
          ("Bordeaux profond", B.BORDEAUX_PROFOND, "46 · 11 · 20", "40 · 100 · 70 · 65", "Fonds, aplats, textile", B.CREME),
          ("Crème", B.CREME, "243 · 233 · 220", "0 · 4 · 9 · 5", "Papier, textes sur bordeaux", B.BORDEAUX),
          ("Champagne", B.CHAMPAGNE, "201 · 164 · 106", "0 · 18 · 47 · 21", "Accent sur bordeaux, dorure", B.BORDEAUX),
          ]
    cards = "".join(f'<div class="sw"><div class="chip" style="background:{c};color:{t}">{h}</div><div class="info"><b>{n}</b><code>HEX {h}</code><code>RVB {r}</code><code>CMJN {k}</code><span>{u}</span></div></div>' for n, h, r, k, u, t in [(a, b, c, d, e, f) for a, b, c, d, e, f in sw for _ in [0]] for c in [h])
    P.append(f"""
<section class="band light" style="padding-top:0" aria-labelledby="t-col"><div class="wrap">
  <div class="head"><div class="eyebrow">Couleurs</div><h2 id="t-col">Bordeaux et champagne</h2></div>
  <div class="swatches">{cards}</div>
  <div class="ratio" aria-label="Proportions : bordeaux 50 %, crème 30 %, bordeaux profond 15 %, champagne 5 %"><span style="flex:50;background:{B.BORDEAUX}"></span><span style="flex:30;background:{B.CREME}"></span><span style="flex:15;background:{B.BORDEAUX_PROFOND}"></span><span style="flex:5;background:{B.CHAMPAGNE}"></span></div>
  <p class="muted">Proportions : bordeaux 50 %, crème 30 %, bordeaux profond 15 %, champagne 5 %. Sur fond crème, le champagne passe en version foncée ({B.CHAMPAGNE_FONCE}) pour rester lisible. En impression, le champagne peut être remplacé par une dorure à chaud or pâle ; en broderie, par un fil or mat. Valeurs CMJN indicatives, à valider avec l’imprimeur.</p>
</div></section>""")
    P.append(f"""
<section class="band" aria-labelledby="t-type"><div class="wrap">
  <div class="head"><div class="eyebrow">Typographie</div><h2 id="t-type">Une seule famille : Jost</h2></div>
  <div class="type">
    <div class="spec"><span class="eyebrow">Nom · Jost Regular, interlettrage + 42 %</span>
      <div class="wm-sample">{inline("domova_nom-signature_couleur-fond-sombre")}</div>
      <p class="muted">Le nom est vectorisé dans les fichiers logo : ne le recomposez jamais au clavier. La signature est en Jost Medium, avec des petits carrés champagne entre les métiers.</p></div>
    <div class="spec"><span class="eyebrow">Supports · Jost (SIL Open Font License)</span>
      <div class="big" style="font-weight:400">Aa</div>
      <div class="alpha">ABCDEFGHIJKLMNOPQRSTUVWXYZ<br>0123456789 · € · m² · n°</div>
      <p class="muted">Titres en Jost Medium, capitales espacées ; texte courant en Jost Regular. Gratuite, utilisable commercialement, disponible sur Google Fonts.</p></div>
  </div>
</div></section>""")
    hz = inline("domova_horizontal_couleur-fond-clair")
    P.append(f"""
<section class="band anth" aria-labelledby="t-rules"><div class="wrap">
  <div class="head"><div class="eyebrow">Règles d’usage</div><h2 id="t-rules">Protection, tailles minimales, interdits</h2></div>
  <div class="split">
    <div>{clearspace_svg()}</div>
    <ul class="facts">
      <li><b>Zone libre</b><span>X = la moitié de la hauteur des capitales de DOMOVA, sur les quatre côtés.</span></li>
      <li><b>Principal</b><span>45 mm de large minimum en impression, 240 px à l’écran.</span></li>
      <li><b>Horizontal</b><span>40 mm / 220 px. En dessous, passez au logo compact : la signature disparaît.</span></li>
      <li><b>Compact</b><span>25 mm / 130 px.</span></li>
      <li><b>Symbole</b><span>Graisse fine au-dessus de 25 mm / 90 px, graisse renforcée en dessous, jusqu’à 6 mm / 16 px. Broderie : 15 mm minimum, toujours en graisse renforcée.</span></li>
    </ul>
  </div>
  <div class="rules">
    <div class="rule"><div class="box"><span class="x">Interdit</span>{hz.replace("<svg ", '<svg style="transform:scale(1.18,.62)" ', 1)}</div><p>Ne pas déformer ni étirer le logo.</p></div>
    <div class="rule"><div class="box" style="background:#9a7f78"><span class="x">Interdit</span>{hz}</div><p>Pas de version couleur sur un fond moyen ou une photo chargée : prenez la version blanche ou champagne.</p></div>
    <div class="rule"><div class="box"><span class="x">Interdit</span>{hz.replace(B.BORDEAUX, "#1F4E8C").replace(B.CHAMPAGNE_FONCE, "#3BAF6B")}</div><p>Ne pas changer les couleurs ni ajouter d’ombre, de dégradé ou de contour.</p></div>
  </div>
</div></section>""")
    m = [("domova_mockup_01_camionnette.png", "Véhicule", "Utilitaire bordeaux, logo horizontal crème et champagne, filet champagne en bas de caisse, arche sur la portière.", True),
         ("domova_mockup_02_textile-polo-sweat.png", "Textile", "Polo bordeaux brodé au cœur, sweat avec le logo principal au dos.", True),
         ("domova_mockup_03_cartes-de-visite.png", "Carte de visite", "85 × 55 mm. Recto bordeaux, arche en dorure à chaud ; verso crème.", False),
         ("domova_mockup_04_panneau-de-chantier.png", "Panneau de chantier", "Bandeau bordeaux, informations réglementaires sur fond crème.", False),
         ("domova_mockup_05_devis.png", "Devis", "A4 : en-tête horizontal, tableau à bandeau bordeaux, total TTC mis en avant.", False),
         ("domova_mockup_06_reseaux-sociaux.png", "Instagram · TikTok", "Avatar : l’arche renforcée avec le D, crème sur bordeaux. Lisible jusqu’à 28 px.", False)]
    figs = "".join(f'<figure class="mock{" wide" if w else ""}"><img src="{img[f]}" alt="Mise en situation : {t}" loading="lazy"><figcaption><b>{t}</b>{c}</figcaption></figure>' for f, t, c, w in m)
    P.append(f"""
<section class="band" aria-labelledby="t-mock"><div class="wrap">
  <div class="head"><div class="eyebrow">Mises en situation</div><h2 id="t-mock">DOMOVA sur le terrain</h2>
  <p class="lede">Illustrations vectorielles aux proportions réelles des supports. Noms, adresses et numéros sont des exemples à remplacer.</p></div>
  <div class="mocks">{figs}</div>
</div></section>""")
    files = [("logos/svg/", "Vectoriel", "35 fichiers SVG : 7 compositions × 5 versions couleur."),
             ("logos/pdf/", "PDF vectoriel", "Les mêmes 35 logos pour l’imprimeur, le brodeur et le marquage véhicule."),
             ("logos/png/", "PNG transparent", "3200 px de large (2048 px pour symboles et monogramme)."),
             ("icons/", "Icônes", "Favicon et icône d’application de 16 à 1024 px, avatar réseaux sociaux 1080 × 1080."),
             ("mockups/", "Mises en situation", "6 scènes en SVG et PNG 2400 px."),
             ("guide/", "Cette fiche", "En page web et en PDF (DOMOVA_fiche-logo.pdf).")]
    fl = "".join(f'<div class="file"><code>{p}</code><h3>{t}</h3><p>{d}</p></div>' for p, t, d in files)
    P.append(f"""
<section class="band anth" aria-labelledby="t-files"><div class="wrap">
  <div class="head"><div class="eyebrow">Fichiers</div><h2 id="t-files">Prêts à l’emploi</h2>
  <p class="lede">Nommage : <code style="font-family:var(--f-mono);color:var(--copper)">domova_[composition]_[version]</code>. Compositions : principal, horizontal, compact, symbole, symbole-renforce, monogramme, nom-signature. Versions : couleur-fond-clair, couleur-fond-sombre, monochrome-champagne, monochrome-noir, monochrome-blanc.</p></div>
  <div class="files">{fl}</div>
</div></section>
<footer class="band" style="padding-block:40px"><div class="wrap"><div>{inline("domova_symbole-renforce_couleur-fond-sombre")}</div><p class="muted" style="font-size:14px">DOMOVA · Construction · Rénovation · Aménagement. Fiche logo v1.0. Symbole original ; typographie Jost sous licence SIL OFL 1.1.</p></div></footer>
""")
    return "".join(P)


def build():
    os.makedirs(G, exist_ok=True)
    html = page(web_images())
    open(os.path.join(G, "index.html"), "w").write(html)
    tmp = os.path.join(G, "_print.html")
    open(tmp, "w").write('<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>' + html + "</body></html>")
    pdf = os.path.join(G, "DOMOVA_fiche-logo.pdf")
    prev = os.environ.get("PREVIEW_PNG", "/tmp/_arche_preview.png")
    subprocess.run(["node", "-e", f"""
const {{chromium}}=require('playwright');
(async()=>{{const b=await chromium.launch();const p=await b.newPage({{viewport:{{width:1280,height:900}}}});
await p.goto('file://{tmp}',{{waitUntil:'networkidle'}});await p.emulateMedia({{media:'screen'}});
await p.pdf({{path:'{pdf}',width:'1280px',height:'1810px',printBackground:true}});
await p.screenshot({{path:'{os.path.abspath(prev)}',fullPage:true}});await b.close();}})();"""], check=True)
    os.remove(tmp)
    print("fiche ok", os.path.abspath(prev))


if __name__ == "__main__":
    build()
