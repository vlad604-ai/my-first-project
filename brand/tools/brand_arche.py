"""DOMOVA — identité finale « L'Arche », palette bordeaux & champagne.

Ce module expose la même interface que build_logos (LOCKUPS, g_symbol, couleurs,
ROOT…) pour que les mises en situation se génèrent avec :
    DOMOVA_BRAND=brand_arche python3 build_mockups.py
Usage direct :  python3 brand_arche.py   -> ../identite-arche/{logos,icons}
"""
import os
import sys

import cairosvg

sys.path.insert(0, os.path.dirname(__file__))
from geom import ellipse, box, union, to_d  # noqa: E402
from marks import Typesetter, FONT_DIR  # noqa: E402
from build_logos import g_tagline  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "identite-arche"))

# ---------------------------------------------------------------- palette
BORDEAUX = "#4A1420"
BORDEAUX_PROFOND = "#2E0B14"
CREME = "#F3E9DC"
CHAMPAGNE = "#C9A46A"
CHAMPAGNE_FONCE = "#A8834A"   # champagne lisible sur fond crème
NOIR = "#111111"
BLANC = "#FFFFFF"

# names used by the mock-up generator
INK, ANTHRACITE, OFFWHITE, COPPER = BORDEAUX, BORDEAUX_PROFOND, CREME, CHAMPAGNE
VAN_BODY = ["#6A2532", "#521825", "#45121D", "#370E17", "#3F111B"]
FABRIC = ["#33101A", "#4A1622", "#521A27", "#461521", "#300E17"]
FABRIC_TRIM = "#2A0A12"
PAPER_DARK = ["#56192A", "#3A0E19"]
FOIL = ["#E6CC95", "#C9A46A", "#EFDDB2", "#9E7C45"]

VARIANTS = {
    # name: (symbole, accent, nom, signature, points)
    "couleur-fond-clair": (BORDEAUX, CHAMPAGNE_FONCE, BORDEAUX, BORDEAUX, CHAMPAGNE_FONCE),
    "couleur-fond-sombre": (CREME, CHAMPAGNE, CREME, CREME, CHAMPAGNE),
    "monochrome-champagne": (CHAMPAGNE, CHAMPAGNE, CHAMPAGNE, CHAMPAGNE, CHAMPAGNE),
    "monochrome-noir": (NOIR, NOIR, NOIR, NOIR, NOIR),
    "monochrome-blanc": (BLANC, BLANC, BLANC, BLANC, BLANC),
}

J4 = Typesetter(os.path.join(FONT_DIR, "jost-latin-400-normal.woff"))
J5 = Typesetter(os.path.join(FONT_DIR, "jost-latin-500-normal.woff"))

# ---------------------------------------------------------------- symbol
AW, AH = 120.0, 168.0          # arch width / height (sill axis)
WEIGHTS = {
    # stroke, accent stroke, accent inset
    "fin": (4.5, 2.0, 19.0),
    "renforce": (10.0, 4.5, 23.0),
}
SILL_OVER = 0.28 * AW          # sill overhang on each side


def arch_geom(weight):
    s, t, i = WEIGHTS[weight]
    r = AW / 2
    outer = union(box(0, r, AW, AH), ellipse(r, r, r).intersection(box(0, 0, AW, r)))
    inner = union(box(s, r, AW - s, AH + 1), ellipse(r, r, r - s).intersection(box(0, 0, AW, r)))
    sill = box(-SILL_OVER, AH - s / 2, AW + SILL_OVER, AH + s / 2)
    main = union(outer.difference(inner), sill).buffer(0)
    r2 = r - i
    a_out = union(box(i, r, AW - i, AH - s / 2), ellipse(r, r, r2).intersection(box(0, 0, AW, r)))
    a_in = union(box(i + t, r, AW - i - t, AH), ellipse(r, r, r2 - t).intersection(box(0, 0, AW, r)))
    accent = a_out.difference(a_in).buffer(0)
    return main, accent


GEOMS = {w: arch_geom(w) for w in WEIGHTS}


def sym_box(weight="fin"):
    s = WEIGHTS[weight][0]
    return AW + 2 * SILL_OVER, AH + s / 2


SYM_W, SYM_H = sym_box("fin")


def g_symbol(x, y, h, col, acc, weight=None, with_d=False):
    """Arch symbol whose bounding box (sill included) is placed at x,y with height h.
    Small sizes automatically use the reinforced weight."""
    weight = weight or ("renforce" if h < 90 else "fin")
    W, H = sym_box(weight)
    k = h / H
    ox = x + SILL_OVER * k
    main, accent = GEOMS[weight]
    out = (f'<path fill="{col}" d="{to_d(main, k, ox, y)}"/>'
           f'<path fill="{acc}" d="{to_d(accent, k, ox, y)}"/>')
    if with_d:
        ts = J5 if weight == "renforce" else J4
        cap = AW * (0.36 if weight == "renforce" else 0.32) * k
        from build_propositions import centered_glyph
        out += centered_glyph(ts, "D", cap, ox + AW / 2 * k, y + AH * 0.62 * k, col)
    return out


def g_icon(x, y, h, col, acc):
    return g_symbol(x, y, h, col, acc, weight="renforce", with_d=True)


# ---------------------------------------------------------------- lockups
CAP = 92.0
TRACK = 0.42
TAG_CAP = 18.0


def wordmark(x, y_base, col, cap=CAP):
    d, w = J4.text("DOMOVA", cap, TRACK)
    return f'<path fill="{col}" transform="translate({x:.3f} {y_base:.3f})" d="{d}"/>', w


WM_W = J4.text("DOMOVA", CAP, TRACK)[1]


def lockup_principal(v):
    col, acc, wcol, tcol, dcol = VARIANTS[v]
    sh = 176.0
    sw = SYM_W * sh / SYM_H
    W = WM_W
    body = g_symbol((W - sw) / 2, 0, sh, col, acc, "fin")
    yb = sh + 86 + CAP
    body += wordmark(0, yb, wcol)[0]
    yt = yb + 44 + TAG_CAP
    body += g_tagline(0, yt, TAG_CAP, W, tcol, dcol)
    return body, W, yt


def lockup_horizontal(v):
    col, acc, wcol, tcol, dcol = VARIANTS[v]
    h = CAP + 40 + TAG_CAP
    sw = SYM_W * h / SYM_H
    body = g_symbol(0, 0, h, col, acc, "fin")
    x = sw + 52
    body += wordmark(x, CAP, wcol)[0]
    body += g_tagline(x, h, TAG_CAP, WM_W, tcol, dcol)
    return body, x + WM_W, h


def lockup_compact(v):
    col, acc, wcol, tcol, dcol = VARIANTS[v]
    h = CAP * 1.5
    sw = SYM_W * h / SYM_H
    body = g_symbol(0, 0, h, col, acc, "fin")
    x = sw + 44
    body += wordmark(x, h * AH / SYM_H, wcol)[0]  # text baseline on the sill axis
    return body, x + WM_W, h


def lockup_symbole(v):
    col, acc, *_ = VARIANTS[v]
    return g_symbol(0, 0, SYM_H, col, acc, "fin"), SYM_W, SYM_H


def lockup_symbole_renforce(v):
    col, acc, *_ = VARIANTS[v]
    W, H = sym_box("renforce")
    return g_symbol(0, 0, H, col, acc, "renforce"), W, H


def lockup_nom(v):
    col, acc, wcol, tcol, dcol = VARIANTS[v]
    body = wordmark(0, CAP, wcol)[0]
    yt = CAP + 44 + TAG_CAP
    body += g_tagline(0, yt, TAG_CAP, WM_W, tcol, dcol)
    return body, WM_W, yt


TILES = {
    "couleur-fond-clair": (BORDEAUX, CREME, CHAMPAGNE),
    "couleur-fond-sombre": (CREME, BORDEAUX, CHAMPAGNE_FONCE),
    "monochrome-champagne": (CHAMPAGNE, BORDEAUX, BORDEAUX),
    "monochrome-noir": (NOIR, BLANC, BLANC),
    "monochrome-blanc": (BLANC, NOIR, NOIR),
}


def lockup_monogramme(v):
    tile, col, acc = TILES[v]
    S = 240.0
    h = 150.0
    W, H = sym_box("renforce")
    w = W * h / H
    body = f'<rect fill="{tile}" width="{S}" height="{S}"/>'
    body += g_icon((S - w) / 2, (S - h) / 2 + 2, h, col, acc)
    return body, S, S


LOCKUPS = {
    "principal": lockup_principal,
    "horizontal": lockup_horizontal,
    "compact": lockup_compact,
    "symbole": lockup_symbole,
    "symbole-renforce": lockup_symbole_renforce,
    "monogramme": lockup_monogramme,
    "nom-signature": lockup_nom,
}

TITLES = {
    "principal": "DOMOVA — logo principal",
    "horizontal": "DOMOVA — logo horizontal",
    "compact": "DOMOVA — logo compact",
    "symbole": "DOMOVA — symbole l’Arche",
    "symbole-renforce": "DOMOVA — symbole l’Arche, graisse renforcée (petits formats)",
    "monogramme": "DOMOVA — monogramme (icône)",
    "nom-signature": "DOMOVA — nom et signature",
}


def make_svg(body, w, h, title, pad_ratio=0.0):
    pad = pad_ratio * h
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-pad:.3f} {-pad:.3f} {w + 2 * pad:.3f} {h + 2 * pad:.3f}" '
            f'width="{w + 2 * pad:.2f}" height="{h + 2 * pad:.2f}"><title>{title}</title>{body}</svg>\n')


def export(name, svg, png_width, root):
    for sub in ("svg", "png", "pdf"):
        os.makedirs(os.path.join(root, sub), exist_ok=True)
    open(os.path.join(root, "svg", name + ".svg"), "w").write(svg)
    cairosvg.svg2png(bytestring=svg.encode(), write_to=os.path.join(root, "png", name + ".png"), output_width=png_width)
    cairosvg.svg2pdf(bytestring=svg.encode(), write_to=os.path.join(root, "pdf", name + ".pdf"))


def build():
    n = 0
    for lk, fn in LOCKUPS.items():
        for v in VARIANTS:
            body, w, h = fn(v)
            pad = 0.0 if lk == "monogramme" else 0.12
            pw = 2048 if lk.startswith("symbole") or lk == "monogramme" else 3200
            export(f"domova_{lk}_{v}", make_svg(body, w, h, TITLES[lk], pad), pw, os.path.join(ROOT, "logos"))
            n += 1
    icons = os.path.join(ROOT, "icons")
    os.makedirs(icons, exist_ok=True)
    body, w, h = lockup_monogramme("couleur-fond-clair")
    svg = make_svg(body, w, h, "DOMOVA — icône")
    open(os.path.join(icons, "domova_icone.svg"), "w").write(svg)
    for px in (16, 32, 48, 64, 180, 192, 512, 1024):
        cairosvg.svg2png(bytestring=svg.encode(), write_to=os.path.join(icons, f"domova_icone_{px}.png"), output_width=px)
    S, h = 1080.0, 560.0
    W, H = sym_box("renforce")
    w = W * h / H
    body = f'<rect fill="{BORDEAUX}" width="{S}" height="{S}"/>' + g_icon((S - w) / 2, (S - h) / 2 + 10, h, CREME, CHAMPAGNE)
    svg = make_svg(body, S, S, "DOMOVA — photo de profil réseaux sociaux")
    open(os.path.join(icons, "domova_avatar_reseaux.svg"), "w").write(svg)
    cairosvg.svg2png(bytestring=svg.encode(), write_to=os.path.join(icons, "domova_avatar_reseaux_1080.png"), output_width=1080)
    print(f"{n} logos x 3 formats -> {ROOT}")


if __name__ == "__main__" and "--social" not in sys.argv:
    build()
    build_social()


# ---------------------------------------------------------------- réseaux sociaux : logos ronds
SOCIAL = {
    # name: (fond, symbole, accent, anneau, avec_nom)
    "cercle-symbole-bordeaux": (BORDEAUX, CREME, CHAMPAGNE, CHAMPAGNE, False),
    "cercle-symbole-creme": (CREME, BORDEAUX, CHAMPAGNE_FONCE, CHAMPAGNE_FONCE, False),
    "cercle-symbole-champagne": (CHAMPAGNE, BORDEAUX, BORDEAUX_PROFOND, BORDEAUX, False),
    "cercle-nom-bordeaux": (BORDEAUX, CREME, CHAMPAGNE, CHAMPAGNE, True),
    "cercle-nom-creme": (CREME, BORDEAUX, CHAMPAGNE_FONCE, CHAMPAGNE_FONCE, True),
}


def social_body(name, R=500.0):
    bg, col, acc, ring, with_name = SOCIAL[name]
    c = R
    body = f'<circle cx="{c}" cy="{c}" r="{R}" fill="{bg}"/>'
    rr = R * 0.90
    body += f'<circle cx="{c}" cy="{c}" r="{rr:.2f}" fill="none" stroke="{ring}" stroke-width="{R * 0.008:.2f}"/>'
    if not with_name:
        W, H = sym_box("renforce")
        h = R * 0.84
        w = W * h / H
        body += g_icon(c - w / 2, c - h / 2 + R * 0.02, h, col, acc)
    else:
        cap = R * 0.13
        d, ww = J4.text("DOMOVA", cap, TRACK)
        h = R * 0.62
        w = SYM_W * h / SYM_H
        top = c - (h + R * 0.13 + cap) / 2 - R * 0.02
        body += g_symbol(c - w / 2, top, h, col, acc, "fin")
        yb = top + h + R * 0.13 + cap
        body += f'<path fill="{col}" transform="translate({c - ww / 2:.3f} {yb:.3f})" d="{d}"/>'
        body += f'<rect x="{c - R * 0.06:.2f}" y="{yb + R * 0.08:.2f}" width="{R * 0.12:.2f}" height="{R * 0.008:.2f}" fill="{acc}"/>'
    return body, bg


def build_social():
    out = os.path.join(ROOT, "icons", "reseaux-sociaux")
    os.makedirs(out, exist_ok=True)
    for name in SOCIAL:
        body, bg = social_body(name)
        svg = make_svg(body, 1000, 1000, f"DOMOVA — logo rond réseaux sociaux ({name})")
        base = os.path.join(out, f"domova_{name}")
        open(base + ".svg", "w").write(svg)
        cairosvg.svg2pdf(bytestring=svg.encode(), write_to=base + ".pdf")
        cairosvg.svg2png(bytestring=svg.encode(), write_to=base + "_1080.png", output_width=1080)
        cairosvg.svg2png(bytestring=svg.encode(), write_to=base + "_400.png", output_width=400)
        sq = make_svg(f'<rect width="1000" height="1000" fill="{bg}"/>' + body, 1000, 1000,
                      f"DOMOVA — photo de profil carrée à téléverser ({name})")
        cairosvg.svg2png(bytestring=sq.encode(), write_to=base + "_carre-a-televerser_1080.png", output_width=1080)
    print(len(SOCIAL), "logos ronds ->", out)


if __name__ == "__main__" and "--social" in sys.argv:
    build_social()
