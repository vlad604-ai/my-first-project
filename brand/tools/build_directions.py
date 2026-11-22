"""DOMOVA — planches de présentation des trois directions artistiques."""
import os
import sys
import cairosvg

sys.path.insert(0, os.path.dirname(__file__))
from geom import to_d  # noqa: E402
from marks import symbol_B, symbol_C, Typesetter, FONT_DIR  # noqa: E402
from build_logos import (g_symbol, g_wordmark, g_tagline, WM_W, SYM_W, SYM_H,  # noqa: E402
                         INK, ANTHRACITE, OFFWHITE, COPPER, ROOT)

OUT = os.path.join(ROOT, "directions")
J600 = Typesetter(os.path.join(FONT_DIR, "jost-latin-600-normal.woff"))
J400 = Typesetter(os.path.join(FONT_DIR, "jost-latin-400-normal.woff"))
J500 = Typesetter(os.path.join(FONT_DIR, "jost-latin-500-normal.woff"))

W, H = 1600, 1000


def label(ts, s, x, y, cap, col, tr=0.12, anchor="start"):
    d, w = ts.text(s, cap, tr)
    if anchor == "middle":
        x -= w / 2
    return f'<path fill="{col}" transform="translate({x:.2f} {y:.2f})" d="{d}"/>'


def frame(num, name, pitch, panels):
    s = f'<rect width="{W}" height="{H}" fill="{OFFWHITE}"/>'
    s += panels
    s += label(J500, f"DIRECTION {num}", 80, 900, 13, COPPER, 0.3)
    s += label(J600, name, 80, 940, 26, INK, 0.08)
    for i, line in enumerate(pitch.split("|")):
        s += label(J400, line.strip(), 780, 912 + i * 28, 14, ANTHRACITE, 0.03)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
            f'<title>DOMOVA — direction {num} : {name}</title>{s}</svg>')


def dir_A():
    p = f'<rect x="0" y="0" width="1000" height="840" fill="{INK}"/>'
    sym_h = 150
    sw = SYM_W * sym_h / SYM_H
    k = 0.72
    wm_w = WM_W * k
    x0 = (1000 - wm_w) / 2
    p += g_symbol((1000 - sw) / 2, 230, sym_h, OFFWHITE, COPPER)
    p += g_wordmark(x0, 450, 100 * k, OFFWHITE)
    p += g_tagline(x0, 450 + 72 + 34 + 15, 15, wm_w, OFFWHITE, COPPER)
    p += f'<rect x="1000" y="0" width="600" height="420" fill="{OFFWHITE}"/>'
    p += g_symbol(1300 - 75, 135, 140, INK, COPPER)
    p += f'<rect x="1000" y="420" width="300" height="420" fill="{COPPER}"/>'
    p += g_symbol(1150 - 54, 580, 100, INK, INK)
    p += f'<rect x="1300" y="420" width="300" height="420" fill="{ANTHRACITE}"/>'
    p += g_symbol(1450 - 54, 580, 100, OFFWHITE, COPPER)
    return frame("01", "LE PLI — monogramme D+M",
                 "Un D dont le sommet se plie en M : la jambe du D et la panse deviennent les montants. | "
                 "Deux contre-formes : le plan (triangle) et le volume (panse).", p)


def dir_B():
    dark, light, acc = symbol_B()
    p = f'<rect x="0" y="0" width="1600" height="840" fill="{ANTHRACITE}"/>'

    def sym(x, y, h, cdark, clight, cacc):
        k = h / 112
        return (''.join(f'<path fill="{cdark}" d="{to_d(g, k, x, y)}"/>' for g in dark) +
                ''.join(f'<path fill="{clight}" d="{to_d(g, k, x, y)}"/>' for g in light) +
                ''.join(f'<path fill="{cacc}" d="{to_d(g, k, x, y)}"/>' for g in acc))
    # horizontal lockup, technical typography
    p += sym(250, 330, 160, OFFWHITE, "#8A8780", COPPER)
    d, w = J600.text("DOMOVA", 72, 0.42)
    p += f'<path fill="{OFFWHITE}" transform="translate(470 452)" d="{d}"/>'
    p += f'<rect x="472" y="478" width="{w:.1f}" height="2" fill="{COPPER}"/>'
    p += label(J400, "BÂTIR · RÉNOVER · AMÉNAGER", 472, 518, 15, "#BDBAB2", 0.42)
    p += f'<rect x="1220" y="560" width="300" height="220" fill="{OFFWHITE}"/>'
    p += sym(1316, 610, 120, INK, "#7A776F", COPPER)
    return frame("02", "PERSPECTIVE — l’M en volume",
                 "Deux façades pliées vues en perspective dessinent un M. | "
                 "Lecture tridimensionnelle, typographie technique très espacée, filet cuivre.", p)


def dir_C():
    pillar, bowl, key = symbol_C()
    p = f'<rect x="0" y="0" width="1600" height="840" fill="{OFFWHITE}"/>'
    p += f'<rect x="1040" y="0" width="560" height="840" fill="{INK}"/>'

    def sym(x, y, h, c1, c2, c3):
        k = h / 112
        return (f'<path fill="{c1}" d="{to_d(pillar, k, x, y)}"/>'
                f'<path fill="{c2}" d="{to_d(bowl, k, x, y)}"/>'
                f'<path fill="{c3}" d="{to_d(key, k, x, y)}"/>')
    p += sym(470, 200, 180, INK, INK, COPPER)
    d, w = J500.text("DOMOVA", 64, 0.62)
    p += f'<path fill="{INK}" transform="translate({520 - w / 2 + 0:.1f} 520)" d="{d}"/>'
    p += f'<rect x="{520 - w / 2:.1f}" y="560" width="{w:.1f}" height="1.5" fill="{INK}"/>'
    p += label(J400, "ENTREPRISE GÉNÉRALE DE BÂTIMENT", 520, 600, 13, ANTHRACITE, 0.5, "middle")
    p += sym(1250, 340, 160, OFFWHITE, OFFWHITE, COPPER)
    return frame("03", "FONDATION — D assemblé",
                 "Un pilier et un demi-cylindre, posés avec un joint : la logique de l’assemblage. | "
                 "Clé cuivre au centre, composition éditoriale aérée.", p)


def build():
    os.makedirs(OUT, exist_ok=True)
    for name, fn in (("direction-01_le-pli", dir_A), ("direction-02_perspective", dir_B),
                     ("direction-03_fondation", dir_C)):
        svg = fn()
        open(os.path.join(OUT, name + ".svg"), "w").write(svg)
        cairosvg.svg2png(bytestring=svg.encode(), write_to=os.path.join(OUT, name + ".png"), output_width=1600)
    print("directions ok")


if __name__ == "__main__":
    build()
