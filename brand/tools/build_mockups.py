"""DOMOVA — mises en situation (illustrations vectorielles réalistes).

Toutes les scènes sont en SVG pur (textes vectorisés), exportées aussi en PNG.
Les coordonnées (adresse, téléphone, SIRET…) sont des exemples à remplacer.
"""
import os
import sys
import cairosvg

sys.path.insert(0, os.path.dirname(__file__))
from build_logos import (LOCKUPS, g_symbol, INK, ANTHRACITE, OFFWHITE, COPPER, SYM_W, SYM_H, ROOT)  # noqa: E402
from marks import Typesetter, FONT_DIR  # noqa: E402

OUT = os.path.join(ROOT, "mockups")
J4 = Typesetter(os.path.join(FONT_DIR, "jost-latin-400-normal.woff"))
J5 = Typesetter(os.path.join(FONT_DIR, "jost-latin-500-normal.woff"))
J6 = Typesetter(os.path.join(FONT_DIR, "jost-latin-600-normal.woff"))


def T(s, x, y, cap, col, ts=J4, tr=0.0, anchor="start", opacity=None):
    d, w = ts.text(s, cap, tr)
    if anchor == "middle":
        x -= w / 2
    elif anchor == "end":
        x -= w
    op = f' opacity="{opacity}"' if opacity is not None else ""
    return f'<path fill="{col}"{op} transform="translate({x:.2f} {y:.2f})" d="{d}"/>'


def logo(kind, variant, x, y, width=None, height=None):
    body, w, h = LOCKUPS[kind](variant)
    k = width / w if width else height / h
    return f'<g transform="translate({x:.2f} {y:.2f}) scale({k:.5f})">{body}</g>', w * k, h * k


def svg_doc(w, h, body, title, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            f'<title>{title}</title><defs>{defs}</defs>{body}</svg>')


COMMON_DEFS = """
<filter id="soft" x="-20%" y="-20%" width="140%" height="160%"><feGaussianBlur stdDeviation="18"/></filter>
<filter id="soft2" x="-20%" y="-20%" width="140%" height="160%"><feGaussianBlur stdDeviation="6"/></filter>
<filter id="grain" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="4"/>
  <feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.16 0"/>
</filter>
"""


# =========================================================================
# 1. CAMIONNETTE NOIRE
# =========================================================================
def van():
    W, H = 1600, 1000
    defs = COMMON_DEFS + f"""
<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#D9D7D1"/><stop offset="0.72" stop-color="#C9C6BF"/><stop offset="0.72" stop-color="#A9A69F"/><stop offset="1" stop-color="#8E8B85"/></linearGradient>
<linearGradient id="body" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2E2E2E"/><stop offset="0.18" stop-color="#1A1A1A"/><stop offset="0.55" stop-color="#121212"/><stop offset="0.8" stop-color="#0C0C0C"/><stop offset="1" stop-color="#151515"/></linearGradient>
<linearGradient id="sheen" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.45" stop-color="#fff" stop-opacity="0.07"/><stop offset="0.55" stop-color="#fff" stop-opacity="0.02"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<linearGradient id="glass" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3B4247"/><stop offset="0.5" stop-color="#1C2023"/><stop offset="1" stop-color="#0E1012"/></linearGradient>
<radialGradient id="rim" cx="0.5" cy="0.45" r="0.6"><stop offset="0" stop-color="#7C7C7C"/><stop offset="0.6" stop-color="#3C3C3C"/><stop offset="1" stop-color="#1E1E1E"/></radialGradient>
"""
    b = f'<rect width="{W}" height="{H}" fill="url(#bg)"/>'
    # back wall joints (architecture)
    for x in range(0, W, 200):
        b += f'<rect x="{x}" y="0" width="1" height="{0.72 * H}" fill="#000" opacity="0.06"/>'
    ground = 850
    b += f'<ellipse cx="800" cy="{ground + 6}" rx="640" ry="30" fill="#000" opacity="0.45" filter="url(#soft)"/>'
    # body silhouette (facing left)
    body = ("M1412 812 L1412 300 Q1412 262 1374 262 L560 262 Q520 262 498 290 L352 470 "
            "Q340 486 318 492 L232 516 Q196 527 192 566 L188 770 Q188 812 226 812 Z")
    b += f'<path d="{body}" fill="url(#body)"/>'
    b += f'<path d="{body}" fill="url(#sheen)"/>'
    # roof highlight
    b += '<path d="M560 266 L1374 266 Q1404 266 1406 296" fill="none" stroke="#5a5a5a" stroke-width="2" opacity="0.6"/>'
    # windshield / side glass
    b += '<path d="M548 292 L690 292 L690 470 L380 470 Z" fill="url(#glass)"/>'
    b += '<path d="M560 300 L620 300 L470 462 L410 462 Z" fill="#fff" opacity="0.06"/>'
    # door seams
    b += '<path d="M705 280 L705 780 M1000 280 L1000 780 M1004 280 L1004 780" stroke="#000" stroke-width="2.4" opacity="0.8"/>'
    b += '<path d="M706 280 L706 780" stroke="#3a3a3a" stroke-width="1" opacity="0.7"/>'
    b += '<rect x="650" y="500" width="34" height="8" rx="4" fill="#2b2b2b"/>'
    b += '<rect x="1020" y="500" width="34" height="8" rx="4" fill="#2b2b2b"/>'
    # mirror
    b += '<path d="M372 450 L338 452 Q326 454 326 468 L328 500 Q330 510 342 508 L372 500 Z" fill="#141414"/>'
    # headlight, grille, rear light
    b += '<path d="M196 560 Q198 532 232 524 L292 508 L292 548 L196 572 Z" fill="#D8D6D0" opacity="0.9"/>'
    b += '<rect x="190" y="600" width="22" height="80" rx="4" fill="#090909"/>'
    b += '<rect x="1402" y="330" width="10" height="120" fill="#5C1A12"/>'
    # rocker / bumper
    b += '<path d="M188 740 L1412 740 L1412 812 L226 812 Q188 812 188 770 Z" fill="#0A0A0A"/>'
    # copper line
    b += f'<rect x="712" y="716" width="700" height="5" fill="{COPPER}"/>'
    # wheels
    for cx in (395, 1180):
        b += f'<path d="M{cx - 120} 812 A120 120 0 0 1 {cx + 120} 812 Z" fill="#050505"/>'
        b += f'<circle cx="{cx}" cy="812" r="92" fill="#0B0B0B"/>'
        b += f'<circle cx="{cx}" cy="812" r="88" fill="none" stroke="#1d1d1d" stroke-width="6"/>'
        b += f'<circle cx="{cx}" cy="812" r="56" fill="url(#rim)"/>'
        for a in range(5):
            b += (f'<rect x="{cx - 5}" y="{812 - 52}" width="10" height="40" rx="3" fill="#2a2a2a" '
                  f'transform="rotate({a * 72} {cx} 812)"/>')
        b += f'<circle cx="{cx}" cy="812" r="14" fill="#555"/>'
    # logo on side panel
    g, w, h = logo("horizontal", "couleur-fond-sombre", 0, 0, width=560)
    b += f'<g transform="translate({1060 - w / 2:.1f} 420)">{g}</g>'
    b += T("domova.fr", 1372, 690, 17, OFFWHITE, J5, 0.2, "end", opacity=0.85)
    b += T("TOUS CORPS D’ÉTAT", 740, 690, 13, COPPER, J6, 0.3)
    # cab door symbol
    b += g_symbol(560, 560, 70, OFFWHITE, COPPER)
    b += f'<rect width="{W}" height="{H}" fill="#fff" filter="url(#grain)"/>'
    return svg_doc(W, H, b, "DOMOVA — camionnette", defs)


# =========================================================================
# 2. TEXTILE : polo (devant) + sweat (dos)
# =========================================================================
def textile():
    W, H = 1600, 1000
    defs = COMMON_DEFS + """
<linearGradient id="bgT" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#E7E5DF"/><stop offset="1" stop-color="#D3D0C9"/></linearGradient>
<linearGradient id="fab" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#0E0E0E"/><stop offset="0.25" stop-color="#1D1D1D"/><stop offset="0.5" stop-color="#222"/><stop offset="0.75" stop-color="#1A1A1A"/><stop offset="1" stop-color="#0C0C0C"/></linearGradient>
<linearGradient id="fold" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.35"/></linearGradient>
<filter id="knit"><feTurbulence type="fractalNoise" baseFrequency="1.6" numOctaves="1" seed="2"/><feColorMatrix type="saturate" values="0"/><feComponentTransfer><feFuncA type="table" tableValues="0 0.10"/></feComponentTransfer><feComposite in2="SourceGraphic" operator="in"/></filter>
"""
    b = '<rect width="1600" height="1000" fill="url(#bgT)"/>'
    # ---- POLO (front), centred at x=430
    cx = 430
    polo = (f"M{cx - 92} 190 Q{cx} 214 {cx + 92} 190 L{cx + 200} 232 Q{cx + 262} 256 {cx + 292} 330 "
            f"L{cx + 330} 450 L{cx + 236} 486 L{cx + 210} 410 L{cx + 206} 860 Q{cx} 880 {cx - 206} 860 "
            f"L{cx - 210} 410 L{cx - 236} 486 L{cx - 330} 450 L{cx - 292} 330 Q{cx - 262} 256 {cx - 200} 232 Z")
    b += f'<ellipse cx="{cx}" cy="880" rx="250" ry="18" fill="#000" opacity="0.25" filter="url(#soft)"/>'
    b += f'<path d="{polo}" fill="url(#fab)"/><path d="{polo}" fill="#fff" filter="url(#knit)"/>'
    # collar
    b += (f'<path d="M{cx - 92} 190 L{cx - 70} 176 Q{cx} 196 {cx + 70} 176 L{cx + 92} 190 L{cx + 60} 262 '
          f'L{cx} 226 L{cx - 60} 262 Z" fill="#161616" stroke="#000" stroke-width="2"/>')
    b += f'<path d="M{cx - 14} 226 L{cx + 14} 226 L{cx + 14} 340 L{cx - 14} 340 Z" fill="#131313" stroke="#000" stroke-width="1.5"/>'
    for yy in (262, 300):
        b += f'<circle cx="{cx}" cy="{yy}" r="5" fill="#2a2a2a"/>'
    # sleeve hems, folds
    b += (f'<path d="M{cx + 330} 450 L{cx + 236} 486" stroke="{COPPER}" stroke-width="3"/>'
          f'<path d="M{cx - 330} 450 L{cx - 236} 486" stroke="{COPPER}" stroke-width="3"/>')
    b += f'<path d="M{cx - 120} 600 Q{cx - 80} 760 {cx - 110} 860" stroke="#000" stroke-width="10" opacity="0.25" fill="none" filter="url(#soft2)"/>'
    # chest logo (wearer's left = viewer's right)
    b += g_symbol(cx + 70, 340, 46, OFFWHITE, COPPER)
    g, w, h = logo("nom-signature", "couleur-fond-sombre", cx + 70, 400, width=118)
    b += g
    b += T("POLO", cx, 950, 14, ANTHRACITE, J6, 0.3, "middle")
    # ---- SWEAT (back), centred at x=1170
    cx = 1170
    sw = (f"M{cx - 96} 170 Q{cx} 186 {cx + 96} 170 L{cx + 220} 214 Q{cx + 280} 240 {cx + 300} 330 "
          f"L{cx + 352} 760 L{cx + 268} 776 L{cx + 222} 420 L{cx + 224} 860 Q{cx} 884 {cx - 224} 860 "
          f"L{cx - 222} 420 L{cx - 268} 776 L{cx - 352} 760 L{cx - 300} 330 Q{cx - 280} 240 {cx - 220} 214 Z")
    b += f'<ellipse cx="{cx}" cy="884" rx="270" ry="18" fill="#000" opacity="0.25" filter="url(#soft)"/>'
    b += f'<path d="{sw}" fill="url(#fab)"/><path d="{sw}" fill="#fff" filter="url(#knit)"/>'
    b += f'<path d="M{cx - 96} 170 Q{cx} 196 {cx + 96} 170 L{cx + 96} 182 Q{cx} 210 {cx - 96} 182 Z" fill="#0b0b0b"/>'
    b += f'<path d="M{cx - 224} 830 Q{cx} 852 {cx + 224} 830 L{cx + 224} 860 Q{cx} 884 {cx - 224} 860 Z" fill="#0b0b0b"/>'
    b += f'<path d="M{cx + 352} 760 L{cx + 268} 776 L{cx + 266} 750 L{cx + 348} 734 Z" fill="#0b0b0b"/>'
    b += f'<path d="M{cx - 352} 760 L{cx - 268} 776 L{cx - 266} 750 L{cx - 348} 734 Z" fill="#0b0b0b"/>'
    g, w, h = logo("principal", "couleur-fond-sombre", 0, 0, width=300)
    b += f'<g transform="translate({cx - w / 2:.1f} 300)">{g}</g>'
    b += f'<rect x="{cx - 150}" y="{300 + h + 50:.1f}" width="300" height="1.5" fill="{COPPER}" opacity="0.8"/>'
    b += T("domova.fr", cx, 300 + h + 90, 14, OFFWHITE, J5, 0.3, "middle", opacity=0.75)
    b += T("SWEAT — DOS", cx, 950, 14, ANTHRACITE, J6, 0.3, "middle")
    return svg_doc(W, H, b, "DOMOVA — textile", defs)


# =========================================================================
# 3. CARTES DE VISITE
# =========================================================================
def cards():
    W, H = 1600, 1000
    defs = COMMON_DEFS + """
<linearGradient id="desk" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3A3936"/><stop offset="1" stop-color="#1E1D1B"/></linearGradient>
<linearGradient id="paperL" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FAF9F6"/><stop offset="1" stop-color="#ECEAE4"/></linearGradient>
<linearGradient id="paperD" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1C1C1C"/><stop offset="1" stop-color="#0E0E0E"/></linearGradient>
<linearGradient id="foil" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#D79A6A"/><stop offset="0.45" stop-color="#B87345"/><stop offset="0.6" stop-color="#E2AE83"/><stop offset="1" stop-color="#9A5C35"/></linearGradient>
"""
    b = '<rect width="1600" height="1000" fill="url(#desk)"/>'
    b += '<rect width="1600" height="1000" fill="#fff" filter="url(#grain)"/>'
    cw, ch = 595, 385  # 85 x 55 mm
    # back card (dark, front face with foil monogram)
    x1, y1, r1 = 230, 250, -8
    b += f'<g transform="rotate({r1} {x1 + cw / 2} {y1 + ch / 2})">'
    b += f'<rect x="{x1 + 14}" y="{y1 + 26}" width="{cw}" height="{ch}" fill="#000" opacity="0.55" filter="url(#soft)"/>'
    b += f'<rect x="{x1}" y="{y1}" width="{cw}" height="{ch}" rx="4" fill="url(#paperD)"/>'
    sh = 120
    swd = SYM_W * sh / SYM_H
    from build_logos import SYM_MARK, SYM_DIAG, SYM_REST
    from geom import to_d
    k = sh / SYM_H
    sx, sy = x1 + (cw - swd) / 2, y1 + (ch - sh) / 2 - 18
    b += f'<path fill="{OFFWHITE}" d="{to_d(SYM_REST, k, sx, sy)}"/><path fill="url(#foil)" d="{to_d(SYM_DIAG, k, sx, sy)}"/>'
    b += T("DOMOVA", x1 + cw / 2, y1 + ch - 64, 15, OFFWHITE, J6, 0.55, "middle")
    b += '</g>'
    # front card (light, contact side)
    x2, y2, r2 = 760, 380, 6
    b += f'<g transform="rotate({r2} {x2 + cw / 2} {y2 + ch / 2})">'
    b += f'<rect x="{x2 + 12}" y="{y2 + 24}" width="{cw}" height="{ch}" fill="#000" opacity="0.5" filter="url(#soft)"/>'
    b += f'<rect x="{x2}" y="{y2}" width="{cw}" height="{ch}" rx="4" fill="url(#paperL)"/>'
    g, w, h = logo("compact", "couleur-fond-clair", x2 + 46, y2 + 46, height=34)
    b += g
    b += f'<rect x="{x2 + 46}" y="{y2 + 128}" width="28" height="3" fill="{COPPER}"/>'
    b += T("Alexandre Martin", x2 + 46, y2 + 182, 22, INK, J6, 0.01)
    b += T("GÉRANT — CONDUCTEUR DE TRAVAUX", x2 + 46, y2 + 214, 10.5, ANTHRACITE, J5, 0.22)
    ys = y2 + 268
    for i, (k1, v1) in enumerate((("T", "+33 (0)6 00 00 00 00"), ("E", "contact@domova.fr"), ("W", "domova.fr"))):
        b += T(k1, x2 + 46, ys + i * 30, 10.5, COPPER, J6, 0.1)
        b += T(v1, x2 + 72, ys + i * 30, 12.5, INK, J4, 0.04)
    b += T("CONSTRUCTION · RÉNOVATION", x2 + cw - 46, ys + 30, 9.5, ANTHRACITE, J5, 0.25, "end")
    b += T("AMÉNAGEMENT", x2 + cw - 46, ys + 60, 9.5, ANTHRACITE, J5, 0.25, "end")
    b += f'<rect x="{x2}" y="{y2 + ch - 10}" width="{cw}" height="10" fill="{INK}"/>'
    b += '</g>'
    return svg_doc(W, H, b, "DOMOVA — cartes de visite", defs)


# =========================================================================
# 4. PANNEAU DE CHANTIER
# =========================================================================
def site_panel():
    W, H = 1600, 1000
    defs = COMMON_DEFS + """
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9FB0BC"/><stop offset="0.7" stop-color="#D9DDDC"/></linearGradient>
<linearGradient id="hoard" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5E5D5A"/><stop offset="1" stop-color="#3E3D3B"/></linearGradient>
<linearGradient id="soil" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8C877E"/><stop offset="1" stop-color="#6E6A63"/></linearGradient>
<linearGradient id="post" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#1a1a1a"/><stop offset="0.5" stop-color="#3a3a3a"/><stop offset="1" stop-color="#121212"/></linearGradient>
"""
    b = '<rect width="1600" height="1000" fill="url(#sky)"/>'
    # building under construction behind (concrete frame)
    for i in range(5):
        y = 120 + i * 92
        b += f'<rect x="980" y="{y}" width="520" height="14" fill="#A8A6A0"/>'
    for x in (990, 1120, 1250, 1380, 1486):
        b += f'<rect x="{x}" y="120" width="14" height="470" fill="#B2B0AA"/>'
    b += '<rect x="80" y="260" width="420" height="330" fill="#B9B7B1"/>'
    for i in range(3):
        for j in range(4):
            b += f'<rect x="{110 + j * 98}" y="{290 + i * 96}" width="60" height="64" fill="#8F8D88"/>'
    # hoarding fence
    b += '<rect x="0" y="560" width="1600" height="300" fill="url(#hoard)"/>'
    for x in range(0, 1600, 120):
        b += f'<rect x="{x}" y="560" width="2" height="300" fill="#000" opacity="0.25"/>'
    b += f'<rect x="0" y="842" width="1600" height="6" fill="{COPPER}" opacity="0.9"/>'
    b += '<rect x="0" y="860" width="1600" height="140" fill="url(#soil)"/>'
    # posts
    for x in (420, 1150):
        b += f'<rect x="{x}" y="420" width="26" height="520" fill="url(#post)"/>'
    b += '<ellipse cx="800" cy="940" rx="520" ry="16" fill="#000" opacity="0.3" filter="url(#soft)"/>'
    # panel
    px, py, pw, ph = 330, 110, 940, 660
    b += f'<rect x="{px + 12}" y="{py + 18}" width="{pw}" height="{ph}" fill="#000" opacity="0.35" filter="url(#soft)"/>'
    b += f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" fill="{OFFWHITE}"/>'
    b += f'<rect x="{px}" y="{py}" width="{pw}" height="230" fill="{INK}"/>'
    g, w, h = logo("horizontal", "couleur-fond-sombre", 0, 0, height=104)
    b += f'<g transform="translate({px + (pw - w) / 2:.1f} {py + 63})">{g}</g>'
    b += f'<rect x="{px}" y="{py + 230}" width="{pw}" height="8" fill="{COPPER}"/>'
    y = py + 300
    b += T("RÉHABILITATION D’UN IMMEUBLE DE BUREAUX", px + 60, y, 22, INK, J6, 0.06)
    b += T("Rénovation de façade · Aménagement intérieur · Lots techniques", px + 60, y + 40, 16, ANTHRACITE, J4, 0.02)
    rows = (("MAÎTRE D’OUVRAGE", "SCI Exemple"), ("ARCHITECTE", "Atelier Exemple"),
            ("ENTREPRISE GÉNÉRALE", "DOMOVA — Tous corps d’état"),
            ("PERMIS DE CONSTRUIRE", "PC 000 000 00 X0000"), ("DÉBUT DES TRAVAUX", "Janvier 2027"),
            ("DURÉE", "9 mois"))
    for i, (k1, v1) in enumerate(rows):
        col = i % 2
        row = i // 2
        xx = px + 60 + col * 430
        yy = y + 112 + row * 70
        b += T(k1, xx, yy, 11, COPPER, J6, 0.22)
        b += T(v1, xx, yy + 28, 17, INK, J5, 0.02)
        b += f'<rect x="{xx}" y="{yy + 44}" width="380" height="1" fill="{INK}" opacity="0.15"/>'
    b += f'<rect x="{px}" y="{py + ph - 54}" width="{pw}" height="54" fill="{ANTHRACITE}"/>'
    b += T("domova.fr", px + 60, py + ph - 20, 15, OFFWHITE, J5, 0.2)
    b += T("CONSTRUCTION · RÉNOVATION · AMÉNAGEMENT", px + pw - 60, py + ph - 20, 12, OFFWHITE, J5, 0.25, "end", 0.75)
    return svg_doc(W, H, b, "DOMOVA — panneau de chantier", defs)


# =========================================================================
# 5. DEVIS (A4)
# =========================================================================
def quote():
    W, H = 1600, 1200
    defs = COMMON_DEFS + """
<linearGradient id="desk2" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#2B2A28"/><stop offset="1" stop-color="#161615"/></linearGradient>
"""
    b = '<rect width="1600" height="1200" fill="url(#desk2)"/>'
    b += '<rect width="1600" height="1200" fill="#fff" filter="url(#grain)"/>'
    pw, ph = 760, 1075  # A4 ratio
    px, py = (W - pw) / 2, 62
    b += f'<rect x="{px + 16}" y="{py + 26}" width="{pw}" height="{ph}" fill="#000" opacity="0.55" filter="url(#soft)"/>'
    b += f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" fill="#FBFAF7"/>'
    m = 58
    g, w, h = logo("horizontal", "couleur-fond-clair", px + m, py + 56, height=50)
    b += g
    b += T("DEVIS", px + pw - m, py + 82, 26, INK, J6, 0.18, "end")
    b += T("N° 2026-0142", px + pw - m, py + 106, 11, COPPER, J6, 0.2, "end")
    b += f'<rect x="{px + m}" y="{py + 146}" width="{pw - 2 * m}" height="1.2" fill="{INK}"/>'
    y = py + 190
    b += T("ÉMETTEUR", px + m, y, 8.5, COPPER, J6, 0.25)
    b += T("CLIENT", px + 420, y, 8.5, COPPER, J6, 0.25)
    for i, (l, r) in enumerate((("DOMOVA SAS", "M. et Mme Exemple"), ("12 rue de l’Exemple", "8 avenue de l’Exemple"),
                                ("75000 Paris", "92000 Ville"), ("contact@domova.fr", "Chantier : appartement T4"))):
        ts = J6 if i == 0 else J4
        b += T(l, px + m, y + 26 + i * 19, 10.5, INK, ts, 0.01)
        b += T(r, px + 420, y + 26 + i * 19, 10.5, INK, ts, 0.01)
    b += T("Date : 22/11/2026   ·   Validité : 30 jours", px + m, y + 128, 9.5, ANTHRACITE, J4, 0.03)
    # table
    ty = y + 166
    b += f'<rect x="{px + m}" y="{ty}" width="{pw - 2 * m}" height="30" fill="{INK}"/>'
    cols = (("DÉSIGNATION", px + m + 14, "start"), ("QTÉ", px + 470, "end"), ("PU HT", px + 560, "end"),
            ("TOTAL HT", px + pw - m - 14, "end"))
    for lab, x, a in cols:
        b += T(lab, x, ty + 19.5, 8.5, OFFWHITE, J6, 0.2, a)
    items = (("Démolition et évacuation des gravats", "1 ft", "2 400,00", "2 400,00"),
             ("Cloisons placo BA13 sur ossature", "64 m²", "48,00", "3 072,00"),
             ("Électricité — mise aux normes NF C 15-100", "1 ft", "5 850,00", "5 850,00"),
             ("Plomberie — salle d’eau complète", "1 ft", "4 200,00", "4 200,00"),
             ("Menuiserie — bureau sur mesure chêne", "1 u", "3 600,00", "3 600,00"),
             ("Peinture murs et plafonds", "182 m²", "24,00", "4 368,00"),
             ("Parquet contrecollé chêne, pose flottante", "58 m²", "72,00", "4 176,00"))
    for i, (d1, q, pu, tot) in enumerate(items):
        yy = ty + 30 + i * 42
        if i % 2 == 1:
            b += f'<rect x="{px + m}" y="{yy}" width="{pw - 2 * m}" height="42" fill="#F1EFEA"/>'
        b += T(f"{i + 1:02d}", px + m + 14, yy + 26, 9, COPPER, J6, 0.05)
        b += T(d1, px + m + 44, yy + 26, 10.5, INK, J4, 0.0)
        b += T(q, px + 470, yy + 26, 10.5, INK, J4, 0.0, "end")
        b += T(pu, px + 560, yy + 26, 10.5, INK, J4, 0.0, "end")
        b += T(tot, px + pw - m - 14, yy + 26, 10.5, INK, J5, 0.0, "end")
    yy = ty + 30 + len(items) * 42 + 30
    for i, (l, v) in enumerate((("Total HT", "27 666,00 €"), ("TVA 10 %", "2 766,60 €"))):
        b += T(l, px + 470, yy + i * 26, 10.5, ANTHRACITE, J4, 0.02)
        b += T(v, px + pw - m - 14, yy + i * 26, 10.5, INK, J5, 0.0, "end")
    b += f'<rect x="{px + 400}" y="{yy + 44}" width="{pw - m - 400}" height="44" fill="{INK}"/>'
    b += T("TOTAL TTC", px + 416, yy + 72, 11, OFFWHITE, J6, 0.2)
    b += T("30 432,60 €", px + pw - m - 14, yy + 73, 15, OFFWHITE, J6, 0.02, "end")
    b += f'<rect x="{px + 400}" y="{yy + 88}" width="{pw - m - 400}" height="3" fill="{COPPER}"/>'
    # signature area
    sy = yy + 140
    b += T("BON POUR ACCORD", px + m, sy, 8.5, COPPER, J6, 0.25)
    b += T("Date, signature et mention « bon pour accord »", px + m, sy + 22, 9.5, ANTHRACITE, J4, 0.02)
    b += f'<rect x="{px + m}" y="{sy + 36}" width="300" height="86" fill="none" stroke="{INK}" stroke-opacity="0.25"/>'
    # footer
    fy = py + ph - 46
    b += f'<rect x="{px + m}" y="{fy - 22}" width="{pw - 2 * m}" height="1" fill="{INK}" opacity="0.2"/>'
    b += T("DOMOVA SAS · SIRET 000 000 000 00000 · TVA FR00 000000000 · Assurance décennale n° 0000000",
           px + pw / 2, fy, 8, ANTHRACITE, J4, 0.04, "middle")
    b += g_symbol(px + pw / 2 - 9, fy + 12, 16, INK, COPPER)
    return svg_doc(W, H, b, "DOMOVA — devis", defs)


# =========================================================================
# 6. RÉSEAUX SOCIAUX — profils (style générique) + tailles d'avatar
# =========================================================================
def social():
    W, H = 1600, 1000
    defs = COMMON_DEFS + """
<clipPath id="av1"><circle cx="0" cy="0" r="62"/></clipPath>
<linearGradient id="bgS" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#E9E7E1"/><stop offset="1" stop-color="#D6D3CC"/></linearGradient>
"""
    b = '<rect width="1600" height="1000" fill="url(#bgS)"/>'

    def avatar(cx, cy, r, ring=None):
        s = ""
        if ring:
            s += f'<circle cx="{cx}" cy="{cy}" r="{r + 5}" fill="none" stroke="{ring}" stroke-width="2.5"/>'
        s += f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{INK}"/>'
        h = r * 0.80
        w = SYM_W * h / SYM_H
        s += g_symbol(cx - w / 2 + r * 0.015, cy - h / 2, h, OFFWHITE, COPPER)
        return s

    def phone(x, y, dark):
        bg = "#0B0B0B" if dark else "#FFFFFF"
        fg = OFFWHITE if dark else INK
        mut = "#8B8983" if dark else "#77756F"
        pw, ph = 380, 780
        s = f'<rect x="{x + 10}" y="{y + 24}" width="{pw}" height="{ph}" rx="56" fill="#000" opacity="0.35" filter="url(#soft)"/>'
        s += f'<rect x="{x}" y="{y}" width="{pw}" height="{ph}" rx="56" fill="#151515"/>'
        s += f'<rect x="{x + 12}" y="{y + 12}" width="{pw - 24}" height="{ph - 24}" rx="46" fill="{bg}"/>'
        s += f'<rect x="{x + pw / 2 - 52}" y="{y + 26}" width="104" height="28" rx="14" fill="#000"/>'
        s += T("domova.btp", x + 40, y + 104, 15, fg, J6, 0.0)
        s += avatar(x + 92, y + 190, 54, ring=COPPER)
        for i, (n, l) in enumerate((("128", "publications"), ("4 210", "abonnés"), ("312", "abonnements"))):
            xx = x + 200 + i * 64
            s += T(n, xx, y + 186, 13, fg, J6, 0.0, "middle")
            s += T(l, xx, y + 206, 8.5, mut, J4, 0.0, "middle")
        s += T("DOMOVA", x + 40, y + 280, 13, fg, J6, 0.15)
        s += T("Construction · Rénovation · Aménagement", x + 40, y + 302, 10.5, fg, J4, 0.0)
        s += T("Tous corps d’état · Bureaux sur mesure", x + 40, y + 320, 10.5, mut, J4, 0.0)
        s += T("domova.fr", x + 40, y + 340, 10.5, COPPER, J5, 0.0)
        s += f'<rect x="{x + 40}" y="{y + 358}" width="{pw - 80}" height="34" rx="8" fill="{COPPER if not dark else "#222"}"/>'
        s += T("Demander un devis", x + pw / 2, y + 380, 11, OFFWHITE, J5, 0.04, "middle")
        # post grid
        gx, gy = x + 12, y + 410
        cell = (pw - 24 - 4) / 3
        tiles = [INK, OFFWHITE, ANTHRACITE, COPPER, INK, "#3A3936", OFFWHITE, ANTHRACITE, INK]
        for i in range(9):
            cx_ = gx + (i % 3) * (cell + 2)
            cy_ = gy + (i // 3) * (cell + 2)
            if cy_ + cell > y + ph - 14:
                break
            col = tiles[i]
            s += f'<rect x="{cx_:.1f}" y="{cy_:.1f}" width="{cell:.1f}" height="{cell:.1f}" fill="{col}"/>'
            if i in (0, 4):
                hh = cell * 0.36
                ww = SYM_W * hh / SYM_H
                s += g_symbol(cx_ + (cell - ww) / 2, cy_ + (cell - hh) / 2, hh, OFFWHITE, COPPER)
            elif i == 1:
                s += T("AVANT", cx_ + 14, cy_ + 26, 9, INK, J6, 0.2)
                s += f'<rect x="{cx_ + 14:.1f}" y="{cy_ + 36:.1f}" width="{cell - 28:.1f}" height="{cell - 52:.1f}" fill="#D2CFC8"/>'
            elif i == 3:
                s += T("APRÈS", cx_ + 14, cy_ + 26, 9, INK, J6, 0.2)
            elif i in (2, 7):
                for k in range(4):
                    s += f'<rect x="{cx_ + 18 + k * 22:.1f}" y="{cy_ + 24:.1f}" width="10" height="{cell - 48:.1f}" fill="#4A4946"/>'
            elif i == 6:
                s += T("CHANTIER", cx_ + 14, cy_ + cell - 18, 9, INK, J6, 0.2)
                s += f'<rect x="{cx_ + 14:.1f}" y="{cy_ + cell - 14:.1f}" width="22" height="2" fill="{COPPER}"/>'
        return s

    b += phone(160, 110, False)
    b += phone(620, 110, True)
    # avatar sizes column
    x0 = 1150
    b += T("PHOTO DE PROFIL", x0, 200, 13, COPPER, J6, 0.3)
    b += T("Recadrage circulaire — lisible", x0, 232, 18, INK, J5, 0.0)
    b += T("de 180 px à 32 px", x0, 258, 18, INK, J5, 0.0)
    y = 330
    for r in (90, 56, 32, 20, 14):
        b += avatar(x0 + 90, y + r, r)
        b += T(f"{r * 2} px", x0 + 220, y + r + 6, 13, ANTHRACITE, J5, 0.05)
        y += 2 * r + 34
    return svg_doc(W, H, b, "DOMOVA — réseaux sociaux", defs)


SCENES = {
    "01_camionnette": van,
    "02_textile-polo-sweat": textile,
    "03_cartes-de-visite": cards,
    "04_panneau-de-chantier": site_panel,
    "05_devis": quote,
    "06_reseaux-sociaux": social,
}


def build(only=None):
    os.makedirs(OUT, exist_ok=True)
    pairs = []
    for name, fn in SCENES.items():
        if only and only not in name:
            continue
        svg = fn()
        open(os.path.join(OUT, f"domova_mockup_{name}.svg"), "w").write(svg)
        pairs += [os.path.join(OUT, f"domova_mockup_{name}.svg"), os.path.join(OUT, f"domova_mockup_{name}.png")]
        print("ok", name)
    import subprocess
    subprocess.run(["node", os.path.join(os.path.dirname(__file__), "render_svg.js"), "2400"] + pairs, check=True)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else None)
