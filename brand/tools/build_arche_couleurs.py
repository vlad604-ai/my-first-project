"""DOMOVA — logo « L'Arche » décliné en plusieurs palettes.

Sorties : ../arche-couleurs/
  palette-XX_nom.svg/.png/.jpg   planche par palette
  cartes_toutes-palettes.*       comparatif cartes de visite
  logos/                         logo principal SVG + PNG par palette (fond foncé / fond clair)
"""
import os
import subprocess
import sys

import cairosvg

sys.path.insert(0, os.path.dirname(__file__))
from build_propositions import arch, text, centered_glyph, J4, J5, J6  # noqa: E402
from build_logos import g_tagline  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "arche-couleurs")
OUT = os.path.abspath(OUT)

# (slug, nom, description, foncé, texte sur foncé, accent sur foncé, clair, texte sur clair, accent sur clair)
PALETTES = [
    ("noir-cuivre", "Noir & cuivre", "La palette d’origine, pour comparer.",
     "#111111", "#F5F4F0", "#B87345", "#F5F4F0", "#111111", "#B87345"),
    ("bordeaux-champagne", "Bordeaux & champagne", "Un bordeaux profond, une crème chaude et un filet champagne. Le classicisme d’une maison de vins.",
     "#4A1420", "#F3E9DC", "#C9A46A", "#F3E9DC", "#4A1420", "#A8834A"),
    ("bordeaux-terracotta", "Bordeaux & terracotta", "Le bordeaux en fond, la terracotta en accent : chaleureux, sans perdre en tenue.",
     "#4A1420", "#F3E9DC", "#D06A3E", "#F3E9DC", "#4A1420", "#C25F35"),
    ("terracotta-creme", "Terracotta & crème", "Une terre cuite orangée, une crème et un brun expresso. La matière, le Sud, l’artisanat.",
     "#B4532A", "#F6EEE3", "#3A1F14", "#F6EEE3", "#B4532A", "#3A1F14"),
    ("vert-anglais-laiton", "Vert anglais & laiton", "Un vert très sombre et un laiton patiné, comme une boiserie de bibliothèque.",
     "#1E3329", "#EFE8DA", "#B89A5E", "#EFE8DA", "#1E3329", "#9C7F45"),
    ("bleu-nuit-or", "Bleu nuit & or pâle", "Un bleu presque noir et un or doux. Sobre, institutionnel, très chic.",
     "#141C2E", "#F1ECE2", "#CDB27C", "#F1ECE2", "#141C2E", "#A88D55"),
    ("noir-or", "Noir & or", "Le grand classique du luxe : noir absolu, ivoire et or satiné.",
     "#0D0D0D", "#F2EDE4", "#C6A15B", "#F2EDE4", "#0D0D0D", "#A9853F"),
    ("expresso-greige", "Expresso & grège", "Un brun expresso, une grège minérale et un bronze. Doux, naturel, très intérieur.",
     "#2E2420", "#E9E2D6", "#A27B4F", "#E9E2D6", "#2E2420", "#8E6A42"),
]

PAGE = "#F4F2EE"
TXT = "#1A1A1A"
MUTED = "#6A665F"


def lockup(fg, acc):
    wm, ww = text(J4, "DOMOVA", 92, 0.42, fill=fg)
    W = ww
    aw, ah = 120, 168
    body = arch((W - aw) / 2, 0, aw, ah, fg, acc, 4.5)
    y = ah + 92
    body += f'<g transform="translate(0 {y + 92})">{wm}</g>'
    yb = y + 92 + 44 + 18
    body += g_tagline(0, yb, 18, W, fg, acc)
    return body, W, yb


def horizontal(fg, acc):
    wm, ww = text(J4, "DOMOVA", 92, 0.42, fill=fg)
    ah = 92 + 40 + 18
    aw = ah * 120 / 168
    body = arch(aw * 0.28, 0, aw, ah, fg, acc, 3.6)
    x = aw * 1.56 + 56
    body += f'<g transform="translate({x:.2f} 92)">{wm}</g>'
    body += g_tagline(x, ah, 18, ww, fg, acc)
    return body, x + ww, ah


def icon(fg, acc):
    s = arch(78, 40, 84, 150, fg, acc, 4)
    s += centered_glyph(J4, "D", 40, 120, 136, fg)
    return s


def place(body, w, h, bx, by, bw, bh, pad=0.16):
    k = min(bw * (1 - 2 * pad) / w, bh * (1 - 2 * pad) / h)
    return (f'<g transform="translate({bx + (bw - w * k) / 2:.2f} {by + (bh - h * k) / 2:.2f}) '
            f'scale({k:.5f})">{body}</g>')


def board(i, p):
    slug, name, desc, dk, fd, ad, lt, fl, al = p
    W, H = 1600, 1000
    s = f'<rect width="{W}" height="{H}" fill="{PAGE}"/>'
    s += f'<rect width="1000" height="760" fill="{dk}"/>'
    s += place(*lockup(fd, ad), 0, 0, 1000, 760, 0.2)
    s += f'<rect x="1000" width="600" height="380" fill="{lt}"/>'
    s += place(*horizontal(fl, al), 1000, 0, 600, 380, 0.12)
    s += f'<rect x="1000" y="380" width="300" height="380" fill="{dk}"/>'
    s += (f'<g transform="translate(1070 490) scale({160 / 240:.4f})">'
          f'<rect width="240" height="240" fill="{dk}" stroke="{ad}" stroke-opacity=".35" stroke-width="2"/>{icon(fd, ad)}</g>')
    s += f'<rect x="1300" y="380" width="300" height="380" fill="{ad}"/>'
    s += (f'<defs><clipPath id="c{i}"><circle cx="120" cy="120" r="120"/></clipPath></defs>'
          f'<g transform="translate(1370 490) scale({160 / 240:.4f})"><g clip-path="url(#c{i})">'
          f'<rect width="240" height="240" fill="{lt}"/>{icon(fl, al)}</g></g>')
    s += text(J5, f"PALETTE {i:02d}", 13, 0.3, 80, 826, fill=al)[0]
    s += text(J6, name.upper(), 26, 0.08, 80, 868, fill=TXT)[0]
    s += text(J4, desc, 14.5, 0.02, 80, 912, fill=MUTED)[0]
    # swatches
    sw = [(dk, "Fond"), (fd if fd != lt else lt, "Clair"), (ad, "Accent"), (fl, "Texte clair")]
    seen = []
    sw = [x for x in sw if not (x[0] in seen or seen.append(x[0]))]
    x = 1600 - 80 - len(sw) * 132 + 12
    for col, lab in sw:
        s += f'<rect x="{x}" y="800" width="120" height="80" fill="{col}" stroke="#000" stroke-opacity=".08"/>'
        s += text(J5, col.upper(), 12, 0.1, x, 908, fill=TXT)[0]
        s += text(J4, lab, 11, 0.05, x, 928, fill=MUTED)[0]
        x += 132
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
            f'<title>DOMOVA — L’Arche — {name.replace("&", "&amp;")}</title>{s}</svg>')


def cards_sheet():
    W, H = 1600, 1180
    defs = ('<filter id="sh" x="-20%" y="-20%" width="140%" height="160%"><feGaussianBlur stdDeviation="10"/></filter>'
            '<filter id="grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="3"/>'
            '<feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.10 0"/></filter>')
    s = f'<rect width="{W}" height="{H}" fill="#D9D5CD"/><rect width="{W}" height="{H}" filter="url(#grain)"/>'
    cw, ch = 300, 194  # 85 x 55
    gx, gy = 70, 70
    colw = (W - 2 * gx) / 4
    for i, p in enumerate(PALETTES):
        slug, name, desc, dk, fd, ad, lt, fl, al = p
        c, r = i % 4, i // 4
        cx = gx + c * colw + (colw - cw) / 2
        cy = gy + r * 540
        # back card (light, contact side) offset
        bx, by = cx + 22, cy + 222
        s += f'<rect x="{bx + 6}" y="{by + 12}" width="{cw}" height="{ch}" fill="#000" opacity=".35" filter="url(#sh)"/>'
        s += f'<rect x="{bx}" y="{by}" width="{cw}" height="{ch}" fill="{lt}"/>'
        s += place(*horizontal(fl, al), bx, by, cw, 90, 0.18)
        s += text(J6, "Alexandre Martin", 12.5, 0.01, bx + 24, by + 116, fill=fl)[0]
        s += text(J5, "GÉRANT", 7.5, 0.25, bx + 24, by + 132, fill=al)[0]
        s += text(J4, "+33 (0)6 00 00 00 00  ·  domova.fr", 8.5, 0.02, bx + 24, by + 166, fill=fl)[0]
        # front card (dark)
        s += f'<rect x="{cx + 6}" y="{cy + 12}" width="{cw}" height="{ch}" fill="#000" opacity=".4" filter="url(#sh)"/>'
        s += f'<rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" fill="{dk}"/>'
        s += place(*lockup(fd, ad), cx, cy, cw, ch, 0.14)
        s += text(J6, f"{i + 1:02d} · {name.upper()}", 11, 0.18, cx + cw / 2 + 11, cy + 470, anchor="middle", fill=TXT)[0]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
            f'<title>DOMOVA — L’Arche — cartes de visite, toutes palettes</title><defs>{defs}</defs>{s}</svg>')


def logo_file(body, w, h, title):
    p = 0.1 * h
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-p:.2f} {-p:.2f} {w + 2 * p:.2f} {h + 2 * p:.2f}" '
            f'width="{w + 2 * p:.2f}" height="{h + 2 * p:.2f}"><title>{title.replace("&", "&amp;")}</title>{body}</svg>')


def build():
    os.makedirs(os.path.join(OUT, "logos"), exist_ok=True)
    pairs = []
    for i, p in enumerate(PALETTES, 1):
        f = os.path.join(OUT, f"palette-{i:02d}_{p[0]}")
        open(f + ".svg", "w").write(board(i, p))
        pairs += [f + ".svg", f + ".png"]
        slug, name, desc, dk, fd, ad, lt, fl, al = p
        for tag_, (fg, acc) in (("fond-fonce", (fd, ad)), ("fond-clair", (fl, al))):
            b, w, h = lockup(fg, acc)
            svg = logo_file(b, w, h, f"DOMOVA — L’Arche — {name} — {tag_}")
            lp = os.path.join(OUT, "logos", f"domova_arche_{slug}_{tag_}")
            open(lp + ".svg", "w").write(svg)
            cairosvg.svg2png(bytestring=svg.encode(), write_to=lp + ".png", output_width=2400)
    f = os.path.join(OUT, "cartes_toutes-palettes")
    open(f + ".svg", "w").write(cards_sheet())
    pairs += [f + ".svg", f + ".png"]
    subprocess.run(["node", os.path.join(os.path.dirname(__file__), "render_svg.js"), "1600"] + pairs, check=True)
    from PIL import Image
    for k in range(1, len(pairs), 2):
        Image.open(pairs[k]).convert("RGB").save(pairs[k][:-4] + ".jpg", quality=88, optimize=True, progressive=True)
    print("ok", len(PALETTES), "palettes")


if __name__ == "__main__":
    build()
