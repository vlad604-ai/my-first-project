"""DOMOVA — série 2 : six nouvelles pistes de logo (hors monogramme géométrique).

Sorties : ../propositions/  (une planche par piste + logos SVG/PNG de chaque piste)
"""
import math
import os
import subprocess
import sys

import cairosvg
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, os.path.dirname(__file__))
from geom import to_d, box, union  # noqa: E402
from marks import Typesetter, FONT_DIR, BUILDERS, PAIRS, TRACK, STEM, CAP, L_D  # noqa: E402
from build_logos import g_tagline, INK, ANTHRACITE, OFFWHITE, COPPER, ROOT  # noqa: E402

OUT = os.path.join(ROOT, "propositions")


def font(n):
    return Typesetter(os.path.join(FONT_DIR, n))


CINZEL = font("cinzel-latin-600-normal.woff")
BODONI = font("bodoni-moda-latin-500-normal.woff")
BODONI6 = font("bodoni-moda-latin-600-normal.woff")
CORM = font("cormorant-garamond-latin-600-normal.woff")
CORM7 = font("cormorant-garamond-latin-700-normal.woff")
J4 = font("jost-latin-400-normal.woff")
J5 = font("jost-latin-500-normal.woff")
J6 = font("jost-latin-600-normal.woff")

PAL = {  # variant -> (fg, accent, secondary, background)
    "sombre": (OFFWHITE, COPPER, OFFWHITE, INK),
    "clair": (INK, COPPER, ANTHRACITE, OFFWHITE),
}


def text(ts, s, cap, tr=0.0, x=0.0, y=0.0, anchor="start", fill="#000"):
    d, w = ts.text(s, cap, tr)
    if anchor == "middle":
        x -= w / 2
    elif anchor == "end":
        x -= w
    return f'<path fill="{fill}" transform="translate({x:.3f} {y:.3f})" d="{d}"/>', w


def glyph(ts, ch, cap):
    """Single glyph at origin (baseline y=0). Returns d, advance, (xmin, ymin, xmax, ymax)."""
    from fontTools.pens.svgPathPen import SVGPathPen
    k = cap / ts.cap
    g = ts.cmap[ord(ch)]
    pen = SVGPathPen(ts.gs)
    ts.gs[g].draw(TransformPen(pen, (k, 0, 0, -k, 0, 0)))
    bp = BoundsPen(ts.gs)
    ts.gs[g].draw(TransformPen(bp, (k, 0, 0, -k, 0, 0)))
    return pen.getCommands(), ts.hmtx[g][0] * k, bp.bounds


def centered_glyph(ts, ch, cap, cx, cy, fill, extra=""):
    d, adv, (x0, y0, x1, y1) = glyph(ts, ch, cap)
    tx, ty = cx - (x0 + x1) / 2, cy - (y0 + y1) / 2
    return f'<path fill="{fill}" {extra} transform="translate({tx:.3f} {ty:.3f})" d="{d}"/>'


def circle_text(ts, s, cap, cx, cy, r_base, fill):
    """Text set clockwise around a full circle, glyphs upright toward the outside."""
    size = ts.upm * cap / ts.cap
    advs = [glyph(ts, c, cap)[1] for c in s]
    total = sum(advs)
    tr = (2 * math.pi * r_base - total) / len(s)  # spread evenly
    out = []
    a = 0.0
    for c, adv in zip(s, advs):
        if c != " ":
            d = glyph(ts, c, cap)[0]
            mid = a + adv / 2
            deg = math.degrees(mid / r_base)
            out.append(f'<path fill="{fill}" transform="translate({cx:.3f} {cy:.3f}) rotate({deg:.3f}) '
                       f'translate({-adv / 2:.3f} {-r_base:.3f})" d="{d}"/>')
        a += adv + tr
    _ = size
    return "".join(out)


def tag(x, y_base, cap, width, col, acc):
    return g_tagline(x, y_base, cap, width, col, acc)


# ==========================================================================
# 1. PIERRE GRAVÉE — capitales romaines, cadre double
# ==========================================================================
def p1_symbol(x, y, h, fg, acc):
    w = h * 0.82
    s = f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="none" stroke="{fg}" stroke-width="{h * 0.022:.2f}"/>'
    i = h * 0.075
    s += (f'<rect x="{x + i:.2f}" y="{y + i:.2f}" width="{w - 2 * i:.2f}" height="{h - 2 * i:.2f}" fill="none" '
          f'stroke="{acc}" stroke-width="{h * 0.008:.2f}"/>')
    s += centered_glyph(CINZEL, "D", h * 0.46, x + w / 2, y + h * 0.47, fg)
    s += f'<rect x="{x + w / 2 - h * 0.09:.2f}" y="{y + h * 0.76:.2f}" width="{h * 0.18:.2f}" height="{h * 0.012:.2f}" fill="{acc}"/>'
    return s, w


def p1(v):
    fg, acc, sub, bg = PAL[v]
    sh = 190
    sym, sw = p1_symbol(0, 0, sh, fg, acc)
    wm, ww = text(CINZEL, "DOMOVA", 100, 0.30)
    W = ww
    body = f'<g transform="translate({(W - sw) / 2:.2f} 0)">{sym}</g>'
    y = sh + 80
    body += f'<g transform="translate(0 {y + 100})">{text(CINZEL, "DOMOVA", 100, 0.30, fill=fg)[0]}</g>'
    body += tag(0, y + 100 + 48 + 19, 19, W, sub, acc)
    return body, W, y + 100 + 48 + 19


def p1_icon(v):
    fg, acc, sub, bg = PAL[v]
    s, w = p1_symbol(0, 0, 150, fg, acc)
    return f'<g transform="translate({(240 - w) / 2:.2f} 45)">{s}</g>'


# ==========================================================================
# 2. LE SCEAU — emblème circulaire, D Didone
# ==========================================================================
def p2_seal(cx, cy, R, fg, acc, ring_text=True):
    s = f'<circle cx="{cx}" cy="{cy}" r="{R:.2f}" fill="none" stroke="{fg}" stroke-width="{R * 0.02:.2f}"/>'
    ri = R * 0.70 if ring_text else R * 0.86
    s += f'<circle cx="{cx}" cy="{cy}" r="{ri:.2f}" fill="none" stroke="{acc}" stroke-width="{R * 0.009:.2f}"/>'
    if ring_text:
        s += circle_text(J5, "CONSTRUCTION · RÉNOVATION · AMÉNAGEMENT · ", R * 0.095, cx, cy, R * 0.80, fg)
    s += centered_glyph(BODONI6, "D", ri * 0.95, cx, cy - ri * 0.04, fg)
    s += f'<rect x="{cx - ri * 0.22:.2f}" y="{cy + ri * 0.52:.2f}" width="{ri * 0.44:.2f}" height="{R * 0.012:.2f}" fill="{acc}"/>'
    return s


def p2(v):
    fg, acc, sub, bg = PAL[v]
    R = 150
    body = p2_seal(R, R, R, fg, acc)
    x = 2 * R + 80
    wm, ww = text(BODONI, "DOMOVA", 100, 0.22, x=x, y=R + 50, fill=fg)
    body += wm
    body += f'<rect x="{x}" y="{R + 50 + 34}" width="{ww:.2f}" height="2" fill="{acc}"/>'
    t, tw = text(J5, "ENTREPRISE GÉNÉRALE DU BÂTIMENT", 17, 0.32, x=x, y=R + 50 + 34 + 46, fill=sub)
    body += t
    return body, x + ww, 2 * R


def p2_icon(v):
    fg, acc, sub, bg = PAL[v]
    return p2_seal(120, 120, 92, fg, acc, ring_text=False)


# ==========================================================================
# 3. LA COTE — le lettrage DOMOVA sous une ligne de cote d'architecte
# ==========================================================================
WM_LETTERS = []


def wm_letters():
    if WM_LETTERS:
        return WM_LETTERS
    x, prev = 0.0, None
    for ch in "DOMOVA":
        if prev:
            x += TRACK + PAIRS.get(prev + ch, 0.0)
        g, w = BUILDERS[ch](x)
        WM_LETTERS.append((ch, x, w, g))
        x += w
        prev = ch
    return WM_LETTERS


def wm_width():
    L = wm_letters()
    return L[-1][1] + L[-1][2]


def cote(x0, x1, y, fg, acc, ext=22, sw=2.2, tick=11):
    s = f'<line x1="{x0:.2f}" y1="{y:.2f}" x2="{x1:.2f}" y2="{y:.2f}" stroke="{acc}" stroke-width="{sw}"/>'
    for x in (x0, x1):
        s += f'<line x1="{x:.2f}" y1="{y - ext:.2f}" x2="{x:.2f}" y2="{y + ext:.2f}" stroke="{fg}" stroke-width="{sw * 0.6:.2f}"/>'
        s += (f'<line x1="{x - tick:.2f}" y1="{y + tick:.2f}" x2="{x + tick:.2f}" y2="{y - tick:.2f}" '
              f'stroke="{acc}" stroke-width="{sw * 1.7:.2f}"/>')
    return s


def p3(v):
    fg, acc, sub, bg = PAL[v]
    from build_logos import WM
    W = wm_width()
    body = cote(0, W, 0, fg, acc, ext=20, sw=2.4, tick=12)
    y = 54
    body += f'<path fill="{fg}" d="{to_d(WM, 1, 0, y)}"/>'
    body += tag(0, y + 100 + 46 + 20, 20, W, sub, acc)
    return body, W, y + 100 + 46 + 20


def p3_icon(v):
    fg, acc, sub, bg = PAL[v]
    g, w = L_D(0)
    k = 1.05
    x, y = (240 - w * k) / 2 + 16, 80
    s = f'<path fill="{fg}" d="{to_d(g, k, x, y)}"/>'
    s += cote(x, x + w * k, y - 30, fg, acc, ext=12, sw=2.2, tick=8)
    s += cote(x - 30, x - 30 + 0.0001, y, fg, acc, ext=0, sw=0, tick=0)
    # vertical cote on the left
    s += f'<line x1="{x - 30:.2f}" y1="{y:.2f}" x2="{x - 30:.2f}" y2="{y + 100 * k:.2f}" stroke="{acc}" stroke-width="2.2"/>'
    for yy in (y, y + 100 * k):
        s += f'<line x1="{x - 42:.2f}" y1="{yy:.2f}" x2="{x - 18:.2f}" y2="{yy:.2f}" stroke="{fg}" stroke-width="1.3"/>'
        s += f'<line x1="{x - 38:.2f}" y1="{yy + 8:.2f}" x2="{x - 22:.2f}" y2="{yy - 8:.2f}" stroke="{acc}" stroke-width="3.6"/>'
    return s


# ==========================================================================
# 4. POCHOIR — le lettrage découpé comme un marquage de chantier
# ==========================================================================
def stencil_word():
    b = 7.5
    cuts = []
    for ch, x, w, g in wm_letters():
        if ch == "D":
            cuts.append(box(x + STEM, -5, x + STEM + b, 105))
        elif ch == "O":
            cx = x + w / 2
            cuts.append(box(cx - b / 2, -5, cx + b / 2, 105))
        elif ch == "M":
            cuts.append(box(x + STEM, -5, x + STEM + b, 50))
            cuts.append(box(x + w - STEM - b, -5, x + w - STEM, 50))
        elif ch == "V":
            cx = x + w / 2
            cuts.append(box(cx - b / 2, 60, cx + b / 2, 105))
        elif ch == "A":
            cx = x + w / 2
            cuts.append(box(cx - b / 2, -5, cx + b / 2, 45))
    from build_logos import WM
    return WM.difference(union(*cuts)).buffer(0)


STENCIL = None


def p4(v):
    global STENCIL
    fg, acc, sub, bg = PAL[v]
    STENCIL = STENCIL or stencil_word()
    W = wm_width()
    # copper plate with stencil D on the left
    ph = 100 + 46 + 20
    body = f'<rect x="0" y="0" width="{ph:.2f}" height="{ph:.2f}" fill="{acc}"/>'
    g, w = L_D(0)
    k = 0.92
    gd = g.difference(box(STEM, -5, STEM + 7.5, 105))
    body += f'<path fill="{INK}" d="{to_d(gd, k, (ph - w * k) / 2 + 3, (ph - 100 * k) / 2)}"/>'
    x = ph + 60
    body += f'<path fill="{fg}" d="{to_d(STENCIL, 1, x, 0)}"/>'
    body += tag(x, ph, 20, W, sub, acc)
    return body, x + W, ph


def p4_icon(v):
    fg, acc, sub, bg = PAL[v]
    g, w = L_D(0)
    gd = g.difference(box(STEM, -5, STEM + 7.5, 105))
    k = 1.2
    s = f'<path fill="{fg}" d="{to_d(gd, k, (240 - w * k) / 2 + 4, 52)}"/>'
    s += f'<rect x="{(240 - w * k) / 2 + 4:.2f}" y="{52 + 100 * k + 16:.2f}" width="{w * k:.2f}" height="7" fill="{acc}"/>'
    return s


# ==========================================================================
# 5. L'ARCHE — un seuil, une voûte, une ligne
# ==========================================================================
def arch(x, y, w, h, fg, acc, sw):
    r = w / 2
    d = f"M{x:.2f} {y + h:.2f}V{y + r:.2f}A{r:.2f} {r:.2f} 0 0 1 {x + w:.2f} {y + r:.2f}V{y + h:.2f}"
    s = f'<path d="{d}" fill="none" stroke="{fg}" stroke-width="{sw:.2f}"/>'
    i = w * 0.16
    r2 = r - i
    d2 = f"M{x + i:.2f} {y + h:.2f}V{y + r:.2f}A{r2:.2f} {r2:.2f} 0 0 1 {x + w - i:.2f} {y + r:.2f}V{y + h:.2f}"
    s += f'<path d="{d2}" fill="none" stroke="{acc}" stroke-width="{sw * 0.45:.2f}"/>'
    s += f'<rect x="{x - w * 0.28:.2f}" y="{y + h - sw / 2:.2f}" width="{w * 1.56:.2f}" height="{sw:.2f}" fill="{fg}"/>'
    return s


def p5(v):
    fg, acc, sub, bg = PAL[v]
    wm, ww = text(J4, "DOMOVA", 92, 0.42, fill=fg)
    W = ww
    aw, ah = 120, 168
    body = arch((W - aw) / 2, 0, aw, ah, fg, acc, 4.5)
    y = ah + 92
    body += f'<g transform="translate(0 {y + 92})">{wm}</g>'
    body += tag(0, y + 92 + 44 + 18, 18, W, sub, acc)
    return body, W, y + 92 + 44 + 18


def p5_icon(v):
    fg, acc, sub, bg = PAL[v]
    s = arch(78, 40, 84, 150, fg, acc, 4)
    s += centered_glyph(J4, "D", 40, 120, 136, fg)
    return s


# ==========================================================================
# 6. MONOGRAMME CLASSIQUE — D et M entrelacés, Garamond
# ==========================================================================
def p6_mono(cx, cy, h, fg, acc, bg):
    s = centered_glyph(CORM7, "M", h, cx + h * 0.16, cy, fg)
    s += centered_glyph(CORM7, "D", h * 1.02, cx - h * 0.22, cy, acc,
                        extra=f'stroke="{bg}" stroke-width="{h * 0.05:.2f}" paint-order="stroke" stroke-linejoin="round"')
    return s


def p6(v):
    fg, acc, sub, bg = PAL[v]
    wm, ww = text(CORM, "DOMOVA", 100, 0.30, fill=fg)
    W = ww
    mh = 170
    body = p6_mono(W / 2, mh / 2, mh, fg, acc, bg)
    y = mh + 70
    body += f'<g transform="translate(0 {y + 100})">{wm}</g>'
    body += tag(0, y + 100 + 46 + 19, 19, W, sub, acc)
    return body, W, y + 100 + 46 + 19


def p6_icon(v):
    fg, acc, sub, bg = PAL[v]
    return p6_mono(120, 120, 112, fg, acc, bg)


PROPS = [
    ("01", "pierre-gravee", "PIERRE GRAVÉE", p1, p1_icon,
     "Capitales romaines taillées comme une inscription sur un fronton. | Cadre double, D au centre : la plaque d’entreprise, solide et intemporelle."),
    ("02", "le-sceau", "LE SCEAU", p2, p2_icon,
     "Un emblème circulaire, comme un poinçon de compagnon ou un tampon d’architecte. | Le savoir-faire certifié, le D Didone au centre."),
    ("03", "la-cote", "LA COTE", p3, p3_icon,
     "Le nom DOMOVA posé sous une ligne de cote, le signe des plans d’architecte. | Pas de symbole ajouté : la précision devient la signature."),
    ("04", "pochoir", "POCHOIR", p4, p4_icon,
     "Le lettrage découpé comme un marquage de chantier, sur une plaque cuivre. | Industriel, franc, immédiatement lisible sur un véhicule ou une palissade."),
    ("05", "l-arche", "L’ARCHE", p5, p5_icon,
     "Une voûte tracée d’un trait, posée sur un seuil : l’entrée, le passage, l’ouvrage. | Fin, aérien, proche d’une agence d’architecture."),
    ("06", "monogramme-classique", "MONOGRAMME CLASSIQUE", p6, p6_icon,
     "D et M entrelacés en Garamond, le D en cuivre passant devant le M. | Héritage, artisanat, haut de gamme."),
]

W, H = 1600, 1000


def place(body, w, h, bx, by, bw, bh, pad=0.16):
    k = min(bw * (1 - 2 * pad) / w, bh * (1 - 2 * pad) / h)
    x = bx + (bw - w * k) / 2
    y = by + (bh - h * k) / 2
    return f'<g transform="translate({x:.2f} {y:.2f}) scale({k:.5f})">{body}</g>'


def board(num, slug, name, fn, icon, pitch):
    s = f'<rect width="{W}" height="{H}" fill="{OFFWHITE}"/>'
    s += f'<rect width="1000" height="840" fill="{INK}"/>'
    b, w, h = fn("sombre")
    s += place(b, w, h, 0, 0, 1000, 840, 0.17)
    s += f'<rect x="1000" width="600" height="420" fill="{OFFWHITE}"/>'
    b, w, h = fn("clair")
    s += place(b, w, h, 1000, 0, 600, 420, 0.14)
    # app icon tile + round avatar
    s += f'<rect x="1000" y="420" width="300" height="420" fill="{ANTHRACITE}"/>'
    s += (f'<g transform="translate({1150 - 80} {630 - 80}) scale({160 / 240:.4f})"><rect width="240" height="240" rx="0" fill="{INK}"/>'
          f'{icon("sombre")}</g>')
    s += f'<rect x="1300" y="420" width="300" height="420" fill="{COPPER}"/>'
    s += (f'<defs><clipPath id="c{num}"><circle cx="120" cy="120" r="120"/></clipPath></defs>'
          f'<g transform="translate({1450 - 80} {630 - 80}) scale({160 / 240:.4f})"><g clip-path="url(#c{num})">'
          f'<rect width="240" height="240" fill="{OFFWHITE}"/>{icon("clair")}</g></g>')
    s += text(J5, f"PROPOSITION {num}", 13, 0.3, 80, 900, fill=COPPER)[0]
    s += text(J6, name, 26, 0.08, 80, 940, fill=INK)[0]
    for i, line in enumerate(pitch.split("|")):
        s += text(J4, line.strip(), 14, 0.03, 760, 912 + i * 28, fill=ANTHRACITE)[0]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
            f'<title>DOMOVA — proposition {num} : {name}</title>{s}</svg>')


def logo_svg(body, w, h, title):
    p = 0.1 * h
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-p:.2f} {-p:.2f} {w + 2 * p:.2f} {h + 2 * p:.2f}" '
            f'width="{w + 2 * p:.2f}" height="{h + 2 * p:.2f}"><title>{title}</title>{body}</svg>')


def build():
    os.makedirs(os.path.join(OUT, "logos"), exist_ok=True)
    pairs = []
    for num, slug, name, fn, icon, pitch in PROPS:
        svg = board(num, slug, name, fn, icon, pitch)
        p = os.path.join(OUT, f"proposition-{num}_{slug}")
        open(p + ".svg", "w").write(svg)
        pairs += [p + ".svg", p + ".png"]
        for v in ("sombre", "clair"):
            b, w, h = fn(v)
            ls = logo_svg(b, w, h, f"DOMOVA — {name} — fond {v}")
            lp = os.path.join(OUT, "logos", f"domova_{num}-{slug}_fond-{v}")
            open(lp + ".svg", "w").write(ls)
            cairosvg.svg2png(bytestring=ls.encode(), write_to=lp + ".png", output_width=2400)
        print("ok", num, slug)
    subprocess.run(["node", os.path.join(os.path.dirname(__file__), "render_svg.js"), "1600"] + pairs, check=True)


if __name__ == "__main__":
    build()
