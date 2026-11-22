"""DOMOVA — génère tous les logos (SVG, PNG transparent, PDF vectoriel).

Usage :  python3 build_logos.py
Sorties : ../logos/{svg,png,pdf}/  et  ../icons/
"""
import os
import sys
import cairosvg

sys.path.insert(0, os.path.dirname(__file__))
from geom import to_d  # noqa: E402
from marks import symbol_A, wordmark, Typesetter, tagline, FONT_DIR  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

INK = "#111111"
ANTHRACITE = "#252525"
OFFWHITE = "#F5F4F0"
COPPER = "#B87345"
WHITE = "#FFFFFF"

VARIANTS = {
    # name: (symbol, accent, wordmark, tagline, dots)
    "couleur-fond-clair": (INK, COPPER, INK, ANTHRACITE, COPPER),
    "couleur-fond-sombre": (OFFWHITE, COPPER, OFFWHITE, OFFWHITE, COPPER),
    "monochrome-noir": (INK, INK, INK, INK, INK),
    "monochrome-blanc": (WHITE, WHITE, WHITE, WHITE, WHITE),
}

SYM_MARK, SYM_DIAG = symbol_A(parts=True)
SYM_REST = SYM_MARK.difference(SYM_DIAG).buffer(0)
SYM_W, SYM_H = 120.0, 112.0
WM, WM_W = wordmark()
CAP = 100.0
TS = Typesetter(os.path.join(FONT_DIR, "jost-latin-500-normal.woff"))


def g_symbol(x, y, h, col, acc):
    k = h / SYM_H
    if col == acc:
        return f'<path fill="{col}" d="{to_d(SYM_MARK, k, x, y)}"/>'
    return (f'<path fill="{col}" d="{to_d(SYM_REST, k, x, y)}"/>'
            f'<path fill="{acc}" d="{to_d(SYM_DIAG, k, x, y)}"/>')


def g_wordmark(x, y, cap, col):
    k = cap / CAP
    return f'<path fill="{col}" d="{to_d(WM, k, x, y)}"/>'


def g_tagline(x, y_base, cap, width, col, dotcol):
    t = tagline(TS, cap, total_width=width)
    out = f'<path fill="{col}" transform="translate({x:.3f} {y_base:.3f})" d="{t["text"]}"/>'
    for (cx, cy, r) in t["dots"]:
        s = r * 1.15  # small square: an architectural full stop
        out += (f'<rect fill="{dotcol}" x="{x + cx - s / 2:.3f}" y="{y_base + cy - s / 2:.3f}" '
                f'width="{s:.3f}" height="{s:.3f}"/>')
    return out


# ---------------------------------------------------------------- lockups
# All dimensions in wordmark units (cap height = 100). Each returns (body, w, h).

TAG_CAP = 21.0


def lockup_principal(v):
    col, acc, wcol, tcol, dcol = VARIANTS[v]
    sym_h = 176.0
    sym_w = SYM_W * sym_h / SYM_H
    gap1, gap2 = 74.0, 46.0
    w = WM_W
    body = g_symbol((w - sym_w) / 2, 0, sym_h, col, acc)
    y = sym_h + gap1
    body += g_wordmark(0, y, CAP, wcol)
    yb = y + CAP + gap2 + TAG_CAP
    body += g_tagline(0, yb, TAG_CAP, w, tcol, dcol)
    return body, w, yb


def lockup_horizontal(v):
    col, acc, wcol, tcol, dcol = VARIANTS[v]
    gap2 = 40.0
    sym_h = CAP + gap2 + TAG_CAP
    sym_w = SYM_W * sym_h / SYM_H
    gx = 78.0
    body = g_symbol(0, 0, sym_h, col, acc)
    x = sym_w + gx
    body += g_wordmark(x, 0, CAP, wcol)
    body += g_tagline(x, CAP + gap2 + TAG_CAP, TAG_CAP, WM_W, tcol, dcol)
    return body, x + WM_W, sym_h


def lockup_compact(v):
    col, acc, wcol, tcol, dcol = VARIANTS[v]
    sym_h = 128.0
    sym_w = SYM_W * sym_h / SYM_H
    gx = 58.0
    body = g_symbol(0, 0, sym_h, col, acc)
    body += g_wordmark(sym_w + gx, (sym_h - CAP) / 2, CAP, wcol)
    return body, sym_w + gx + WM_W, sym_h


def lockup_symbole(v):
    col, acc, *_ = VARIANTS[v]
    return g_symbol(0, 0, SYM_H, col, acc), SYM_W, SYM_H


def lockup_nom(v):
    col, acc, wcol, tcol, dcol = VARIANTS[v]
    gap2 = 46.0
    body = g_wordmark(0, 0, CAP, wcol)
    yb = CAP + gap2 + TAG_CAP
    body += g_tagline(0, yb, TAG_CAP, WM_W, tcol, dcol)
    return body, WM_W, yb


def lockup_monogramme(v):
    """Official icon: the D+M monogram set in a square tile."""
    col, acc, wcol, tcol, dcol = VARIANTS[v]
    S = 240.0
    if v == "couleur-fond-clair":
        tile, mcol, macc = INK, OFFWHITE, COPPER
    elif v == "couleur-fond-sombre":
        tile, mcol, macc = OFFWHITE, INK, COPPER
    elif v == "monochrome-noir":
        tile, mcol, macc = INK, None, None
    else:
        tile, mcol, macc = WHITE, None, None
    h = 104.0
    w = SYM_W * h / SYM_H
    x, y = (S - w) / 2 + 2.0, (S - h) / 2  # optical centring (bowl is heavier)
    body = f'<rect fill="{tile}" width="{S}" height="{S}"/>'
    if mcol is None:
        # monochrome: monogram knocked out of the tile
        k = h / SYM_H
        body = (f'<path fill="{tile}" fill-rule="evenodd" d="M0 0H{S}V{S}H0Z'
                f'{to_d(SYM_MARK, k, x, y)}"/>')
    else:
        body += g_symbol(x, y, h, mcol, macc)
    return body, S, S


LOCKUPS = {
    "principal": lockup_principal,
    "horizontal": lockup_horizontal,
    "compact": lockup_compact,
    "symbole": lockup_symbole,
    "monogramme": lockup_monogramme,
    "nom-signature": lockup_nom,
}

TITLES = {
    "principal": "DOMOVA — logo principal (symbole au-dessus du nom)",
    "horizontal": "DOMOVA — logo horizontal",
    "compact": "DOMOVA — logo compact",
    "symbole": "DOMOVA — symbole D+M seul",
    "monogramme": "DOMOVA — monogramme officiel (icône)",
    "nom-signature": "DOMOVA — nom et signature",
}


def make_svg(body, w, h, title, pad_ratio=0.0):
    pad = pad_ratio * h
    vb = f"{-pad:.3f} {-pad:.3f} {w + 2 * pad:.3f} {h + 2 * pad:.3f}"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" '
            f'width="{w + 2 * pad:.2f}" height="{h + 2 * pad:.2f}">'
            f'<title>{title}</title>{body}</svg>\n')


def export(name, svg, png_width, root=None):
    root = root or os.path.join(ROOT, "logos")
    for sub in ("svg", "png", "pdf"):
        os.makedirs(os.path.join(root, sub), exist_ok=True)
    with open(os.path.join(root, "svg", name + ".svg"), "w") as f:
        f.write(svg)
    cairosvg.svg2png(bytestring=svg.encode(), write_to=os.path.join(root, "png", name + ".png"),
                     output_width=png_width)
    cairosvg.svg2pdf(bytestring=svg.encode(), write_to=os.path.join(root, "pdf", name + ".pdf"))


def build():
    count = 0
    for lk, fn in LOCKUPS.items():
        for v in VARIANTS:
            body, w, h = fn(v)
            pad = 0.0 if lk == "monogramme" else 0.12
            svg = make_svg(body, w, h, TITLES[lk], pad)
            pw = 2048 if lk in ("symbole", "monogramme") else 3200
            export(f"domova_{lk}_{v}", svg, pw)
            count += 1
    # icons
    icons = os.path.join(ROOT, "icons")
    os.makedirs(icons, exist_ok=True)
    body, w, h = lockup_monogramme("couleur-fond-clair")
    svg = make_svg(body, w, h, "DOMOVA — icône")
    with open(os.path.join(icons, "domova_icone.svg"), "w") as f:
        f.write(svg)
    for px in (16, 32, 48, 64, 180, 192, 512, 1024):
        cairosvg.svg2png(bytestring=svg.encode(), write_to=os.path.join(icons, f"domova_icone_{px}.png"),
                         output_width=px)
    # social avatar: circular crop safe — monogram smaller, centred on black
    S = 1080.0
    h = 430.0
    w = SYM_W * h / SYM_H
    body = f'<rect fill="{INK}" width="{S}" height="{S}"/>' + g_symbol((S - w) / 2 + 8, (S - h) / 2, h, OFFWHITE, COPPER)
    svg = make_svg(body, S, S, "DOMOVA — photo de profil réseaux sociaux")
    with open(os.path.join(icons, "domova_avatar_reseaux.svg"), "w") as f:
        f.write(svg)
    cairosvg.svg2png(bytestring=svg.encode(), write_to=os.path.join(icons, "domova_avatar_reseaux_1080.png"),
                     output_width=1080)
    print(f"{count} logo files x 3 formats written")


if __name__ == "__main__":
    build()
