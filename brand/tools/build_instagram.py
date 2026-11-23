"""DOMOVA — direction artistique Instagram (identité L'Arche, bordeaux & champagne).

Sorties : ../identite-arche/instagram/
  posts/   12 publications 1080 x 1350 (SVG + PNG) et 2 stories 1080 x 1920
  index.html  page de présentation (profil, modèles, règles)
"""
import os
import re
import subprocess
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import brand_arche as B  # noqa: E402
from marks import Typesetter, FONT_DIR  # noqa: E402

OUT = os.path.join(B.ROOT, "instagram")
P = os.path.join(OUT, "posts")
J3 = Typesetter(os.path.join(FONT_DIR, "jost-latin-400-normal.woff"))
J5 = Typesetter(os.path.join(FONT_DIR, "jost-latin-500-normal.woff"))
J6 = Typesetter(os.path.join(FONT_DIR, "jost-latin-600-normal.woff"))

BX, BXP, CR, CH, CHF = B.BORDEAUX, B.BORDEAUX_PROFOND, B.CREME, B.CHAMPAGNE, B.CHAMPAGNE_FONCE
W, H = 1080, 1350

DEFS = """
<filter id="blur" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="22"/></filter>
<filter id="blur2" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="8"/></filter>
<filter id="grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="7"/>
<feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.09 0"/></filter>
<linearGradient id="wall" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#EFE6DA"/><stop offset="1" stop-color="#E0D2C0"/></linearGradient>
<linearGradient id="wallg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#BDB8B1"/><stop offset="1" stop-color="#A7A29B"/></linearGradient>
<linearGradient id="beyond" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#F7EFE3"/><stop offset="1" stop-color="#D9C6AE"/></linearGradient>
<linearGradient id="oak" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#C39A70"/><stop offset="1" stop-color="#9E764F"/></linearGradient>
<linearGradient id="concrete" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#97928B"/><stop offset="1" stop-color="#7C7770"/></linearGradient>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#C9D3D8"/><stop offset="1" stop-color="#ECE6DC"/></linearGradient>
<linearGradient id="stone" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#E9DFCF"/><stop offset="1" stop-color="#DCCFBB"/></linearGradient>
<linearGradient id="glass" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#5D6A70"/><stop offset="1" stop-color="#2E3539"/></linearGradient>
<linearGradient id="velvet" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6E2433"/><stop offset="1" stop-color="#3E0F1A"/></linearGradient>
<linearGradient id="brass" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#E6CC95"/><stop offset=".5" stop-color="#B8925A"/><stop offset="1" stop-color="#E9D3A2"/></linearGradient>
<linearGradient id="shade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2E0B14" stop-opacity="0"/><stop offset=".45" stop-color="#2E0B14" stop-opacity=".7"/><stop offset="1" stop-color="#2E0B14" stop-opacity=".94"/></linearGradient>
"""


def T(ts, s, cap, x, y, fill, tr=0.0, anchor="start"):
    d, w = ts.text(s, cap, tr)
    if anchor == "middle":
        x -= w / 2
    elif anchor == "end":
        x -= w
    return f'<path fill="{fill}" transform="translate({x:.2f} {y:.2f})" d="{d}"/>'


def pill(ts, s_, cap, x, y, bg, fg, tr=0.3, padx=30, h=62, anchor="start"):
    w = ts.text(s_, cap, tr)[1]
    bw = w + 2 * padx
    if anchor == "end":
        x -= bw
    elif anchor == "middle":
        x -= bw / 2
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{h}" fill="{bg}"/>'
            + T(ts, s_, cap, x + padx, y + h / 2 + cap / 2, fg, tr))


def lines(ts, rows, cap, x, y, lh, fill, tr=0.0, anchor="start"):
    return "".join(T(ts, r, cap, x, y + i * lh, fill, tr, anchor) for i, r in enumerate(rows))


def arch_path(x, w, top, bottom):
    r = w / 2
    return f"M{x} {bottom}V{top + r}A{r} {r} 0 0 1 {x + w} {top + r}V{bottom}Z"


def mini_logo(x, y, h, col, acc):
    return B.g_symbol(x, y, h, col, acc, "renforce" if h < 90 else "fin")


def doc(body, w=W, h=H, title="DOMOVA — Instagram"):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            f'<title>{title}</title><defs>{DEFS}</defs>{body}'
            f'<rect width="{w}" height="{h}" filter="url(#grain)"/></svg>')


# ------------------------------------------------------------------ scenes
def interior(after=True, w=W, h=H):
    s = f'<rect width="{w}" height="{h}" fill="url(#{"wall" if after else "wallg"})"/>'
    fy = 980
    ax, aw, at = 360, 360, 250
    if after:
        s += f'<path d="{arch_path(ax, aw, at, fy)}" fill="url(#beyond)"/>'
        s += f'<path d="{arch_path(ax - 14, aw + 28, at - 14, fy)}" fill="none" stroke="#F6EEE2" stroke-width="12"/>'
        s += f'<polygon points="{ax + 40},{fy} {ax + aw - 20},{fy} {ax + aw + 140},{h} {ax - 60},{h}" fill="#FFF8EC" opacity=".35" filter="url(#blur2)"/>'
    else:
        s += f'<path d="{arch_path(ax, aw, at, fy)}" fill="#6E6963"/>'
        for (px, py, pw, ph) in ((90, 180, 160, 120), (760, 420, 200, 160), (140, 640, 120, 90)):
            s += f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" fill="#8F8A84" opacity=".55"/>'
    # floor
    if after:
        s += f'<rect y="{fy}" width="{w}" height="{h - fy}" fill="url(#oak)"/>'
        for i in range(-8, 19):
            x0 = i * 70
            s += f'<line x1="{540 + (x0 - 540) * 0.42:.1f}" y1="{fy}" x2="{x0}" y2="{h}" stroke="#7E5B3B" stroke-opacity=".35" stroke-width="2"/>'
        s += f'<rect y="{fy - 18}" width="{w}" height="18" fill="#F6EEE2"/>'
    else:
        s += f'<rect y="{fy}" width="{w}" height="{h - fy}" fill="url(#concrete)"/>'
        s += f'<rect y="{fy - 4}" width="{w}" height="4" fill="#6E6963"/>'
    if after:
        # console + vase (left)
        s += f'<ellipse cx="230" cy="{fy + 10}" rx="200" ry="22" fill="#000" opacity=".25" filter="url(#blur2)"/>'
        s += f'<rect x="80" y="{fy - 170}" width="300" height="150" rx="6" fill="#5B3B28"/>'
        s += f'<rect x="80" y="{fy - 170}" width="300" height="14" fill="#6E4A33"/>'
        s += f'<line x1="230" y1="{fy - 156}" x2="230" y2="{fy - 20}" stroke="#3E2618" stroke-width="2"/>'
        s += f'<path d="M180 {fy - 170} Q170 {fy - 250} 196 {fy - 280} L214 {fy - 280} Q240 {fy - 250} 230 {fy - 170} Z" fill="{CR}"/>'
        s += f'<path d="M205 {fy - 280} Q200 {fy - 360} 160 {fy - 400} M205 {fy - 280} Q215 {fy - 350} 250 {fy - 390}" stroke="#5E6B4E" stroke-width="5" fill="none"/>'
        # armchair (right, bordeaux velvet)
        s += f'<ellipse cx="880" cy="{fy + 120}" rx="190" ry="26" fill="#000" opacity=".28" filter="url(#blur2)"/>'
        s += f'<path d="M760 {fy - 120} Q760 {fy - 260} 880 {fy - 260} Q1000 {fy - 260} 1000 {fy - 120} Z" fill="url(#velvet)"/>'
        s += f'<rect x="730" y="{fy - 130}" width="300" height="190" rx="40" fill="url(#velvet)"/>'
        s += f'<rect x="770" y="{fy - 110}" width="220" height="70" rx="24" fill="#7A2B3A" opacity=".6"/>'
        for lx in (760, 990):
            s += f'<rect x="{lx}" y="{fy + 60}" width="12" height="60" fill="#3A2416"/>'
        # pendant light
        s += f'<line x1="540" y1="0" x2="540" y2="150" stroke="#2E2420" stroke-width="3"/>'
        s += f'<path d="M480 200 Q540 120 600 200 Z" fill="url(#brass)"/>'
        s += f'<ellipse cx="540" cy="206" rx="40" ry="10" fill="#FFF3D6" opacity=".9"/>'
    else:
        # cables, ladder, bucket
        s += '<path d="M300 0 Q310 140 280 220 M760 0 Q750 90 790 160" stroke="#3B3936" stroke-width="4" fill="none"/>'
        s += f'<path d="M820 {fy + 140} L880 {fy - 330} L940 {fy + 140} M836 {fy + 20} L924 {fy + 20} M850 {fy - 90} L910 {fy - 90} M864 {fy - 200} L896 {fy - 200}" stroke="#C9C4BC" stroke-width="12" fill="none"/>'
        s += f'<path d="M150 {fy + 150} L170 {fy + 40} L300 {fy + 40} L320 {fy + 150} Z" fill="#E8E3DA"/>'
        s += f'<ellipse cx="235" cy="{fy + 40}" rx="65" ry="12" fill="#D2CDC4"/>'
    return s


def facade(scaffold=True, w=W, h=H):
    s = f'<rect width="{w}" height="{h}" fill="url(#sky)"/>'
    bx, bw, by = 120, 840, 170
    s += f'<rect x="{bx}" y="{by}" width="{bw}" height="{h - by}" fill="url(#stone)"/>'
    s += f'<rect x="{bx - 20}" y="{by - 24}" width="{bw + 40}" height="30" fill="#D3C5AF"/>'
    for r in range(4):
        y = by + 70 + r * 230
        s += f'<rect x="{bx}" y="{y + 180}" width="{bw}" height="10" fill="#D6C9B4"/>'
        for c in range(4):
            x = bx + 70 + c * 190
            if r == 3 and c in (1, 2):
                continue
            s += f'<path d="{arch_path(x, 110, y, y + 170)}" fill="url(#glass)"/>'
            s += f'<path d="{arch_path(x - 8, 126, y - 8, y + 170)}" fill="none" stroke="#F3EBDD" stroke-width="6"/>'
            s += f'<rect x="{x - 14}" y="{y + 168}" width="138" height="10" fill="#EFE5D5"/>'
    dy = by + 70 + 3 * 230
    s += f'<path d="{arch_path(bx + 330, 180, dy - 30, h)}" fill="{BX}"/>'
    s += f'<path d="{arch_path(bx + 318, 204, dy - 42, h)}" fill="none" stroke="#F3EBDD" stroke-width="8"/>'
    s += f'<line x1="{bx + 420}" y1="{dy + 60}" x2="{bx + 420}" y2="{h}" stroke="{BXP}" stroke-width="3"/>'
    if scaffold:
        for x in range(bx - 30, bx + bw + 60, 150):
            s += f'<rect x="{x}" y="{by - 60}" width="10" height="{h}" fill="#7D7872"/>'
        for y in range(by + 40, h, 230):
            s += f'<rect x="{bx - 40}" y="{y}" width="{bw + 80}" height="16" fill="#9C8A6E"/>'
            s += f'<rect x="{bx - 40}" y="{y - 70}" width="{bw + 80}" height="5" fill="#7D7872"/>'
        s += f'<rect x="{bx - 40}" y="{by - 60}" width="{bw + 80}" height="{h}" fill="#FFFFFF" opacity=".18"/>'
    else:
        for tx in (60, 1020):
            s += f'<ellipse cx="{tx}" cy="{h - 260}" rx="110" ry="150" fill="#59684D"/><ellipse cx="{tx + 20}" cy="{h - 300}" rx="80" ry="110" fill="#6C7C5D"/>'
    return s


def desk(w=W, h=H):
    s = f'<rect width="{w}" height="{h}" fill="url(#wall)"/>'
    fy = 1080
    s += f'<rect y="{fy}" width="{w}" height="{h - fy}" fill="#CDBBA3"/>'
    # shelves
    for i, y in enumerate((300, 470)):
        s += f'<rect x="200" y="{y}" width="680" height="16" fill="#9E764F"/>'
        x = 230
        for j, (bw, bh, c) in enumerate(((34, 120, BX), (28, 110, CR), (40, 128, "#6B5444"), (30, 100, CH), (36, 118, BXP))):
            s += f'<rect x="{x}" y="{y - bh}" width="{bw}" height="{bh}" fill="{c}"/>'
            x += bw + 4
        s += f'<path d="{arch_path(700 - i * 120, 70, y - 120, y)}" fill="none" stroke="{CHF}" stroke-width="6"/>'
    # desk
    s += f'<ellipse cx="540" cy="{fy + 10}" rx="420" ry="26" fill="#000" opacity=".25" filter="url(#blur2)"/>'
    s += f'<rect x="150" y="760" width="780" height="40" fill="url(#oak)"/>'
    s += f'<rect x="150" y="800" width="780" height="8" fill="#7E5B3B"/>'
    s += f'<rect x="170" y="808" width="36" height="{fy - 808}" fill="#9E764F"/>'
    s += f'<rect x="640" y="808" width="270" height="{fy - 808}" fill="#A87F57"/>'
    for k in range(3):
        s += f'<rect x="652" y="{822 + k * 88}" width="246" height="76" fill="none" stroke="#7E5B3B" stroke-width="2"/>'
        s += f'<rect x="745" y="{856 + k * 88}" width="60" height="6" rx="3" fill="url(#brass)"/>'
    # lamp + objects
    s += '<path d="M300 760 L310 600 L380 560" stroke="#2E2420" stroke-width="6" fill="none"/>'
    s += '<path d="M360 540 L430 560 L400 610 Z" fill="url(#brass)"/>'
    s += f'<rect x="460" y="700" width="140" height="60" fill="{CR}"/><rect x="470" y="690" width="120" height="12" fill="{BX}"/>'
    return s


def materials(w=W, h=H):
    s = f'<rect width="{w}" height="{h}" fill="#E9DFD1"/>'
    # marble
    s += '<rect x="90" y="120" width="460" height="580" fill="#F3F0EB"/>'
    for d in ("M90 260 Q260 220 330 330 T550 380", "M140 120 Q200 400 90 520", "M300 700 Q360 520 550 470"):
        s += f'<path d="{d}" stroke="#BDB6AC" stroke-width="3" fill="none" opacity=".8"/>'
    # oak
    s += '<rect x="590" y="120" width="400" height="360" fill="url(#oak)"/>'
    for i in range(14):
        y = 140 + i * 24
        s += f'<path d="M590 {y} Q760 {y + 12} 990 {y - 4}" stroke="#7E5B3B" stroke-opacity=".4" stroke-width="2" fill="none"/>'
    # velvet
    s += '<circle cx="790" cy="700" r="190" fill="url(#velvet)"/>'
    # brass bar
    s += '<rect x="90" y="760" width="460" height="60" fill="url(#brass)"/>'
    # plaster / tadelakt
    s += f'<rect x="90" y="860" width="460" height="390" fill="#D9C2A8"/>'
    s += '<path d="M90 980 Q300 930 550 1020" stroke="#C7AE92" stroke-width="30" fill="none" opacity=".5" filter="url(#blur2)"/>'
    # terracotta tiles
    for r in range(3):
        for c in range(3):
            s += f'<rect x="{620 + c * 125}" y="{940 + r * 105}" width="115" height="95" fill="{["#B4532A", "#A84B26", "#BE5E33"][(r + c) % 3]}"/>'
    s += '<ellipse cx="790" cy="900" rx="170" ry="18" fill="#000" opacity=".15" filter="url(#blur2)"/>'
    return s


# ------------------------------------------------------------------ posts
def caption_band(eyebrow, title, sub, h=H):
    s = f'<rect y="{h - 520}" width="{W}" height="520" fill="url(#shade)"/>'
    s += T(J5, eyebrow, 18, 80, h - 222, CH, 0.3)
    s += T(J5, title, 42, 80, h - 156, CR, 0.02)
    s += T(J3, sub, 21, 80, h - 102, CR, 0.03)
    s += mini_logo(W - 80 - 66, h - 196, 64, CR, CH)
    return s


def post_bienvenue():
    s = f'<rect width="{W}" height="{H}" fill="{BX}"/>'
    s += f'<path d="{arch_path(240, 600, 200, 1150)}" fill="none" stroke="{CH}" stroke-opacity=".18" stroke-width="3"/>'
    body, w, h = B.LOCKUPS["principal"]("couleur-fond-sombre")
    k = 700 / w
    s += f'<g transform="translate({(W - w * k) / 2:.1f} {430:.1f}) scale({k:.4f})">{body}</g>'
    s += T(J3, "Bienvenue chez DOMOVA.", 28, W / 2, 1120, CR, 0.04, "middle")
    s += f'<rect x="{W / 2 - 30}" y="1160" width="60" height="3" fill="{CH}"/>'
    return s


def post_realisation():
    return interior(True) + caption_band("RÉALISATION", "Appartement haussmannien", "Rénovation complète · 120 m² · Paris 16e")


def post_citation():
    s = f'<rect width="{W}" height="{H}" fill="{CR}"/>'
    s += T(J6, "«", 150, 90, 400, CHF)
    s += lines(J3, ["Une belle rénovation,", "c’est celle qu’on ne", "remarque pas : tout", "semble avoir toujours", "été là."], 52, 90, 520, 90, BX, 0.0)
    s += f'<rect x="90" y="1060" width="60" height="3" fill="{CHF}"/>'
    s += T(J5, "L’ÉQUIPE DOMOVA", 18, 90, 1120, BX, 0.3)
    s += mini_logo(W - 90 - 64, 1060, 76, BX, CHF)
    return s


def post_avant_apres():
    s = '<defs><clipPath id="L"><rect width="540" height="1350"/></clipPath><clipPath id="R"><rect x="540" width="540" height="1350"/></clipPath></defs>'
    s += f'<g clip-path="url(#L)">{interior(False)}</g><g clip-path="url(#R)">{interior(True)}</g>'
    s += f'<rect x="537" width="6" height="{H}" fill="{CR}"/>'
    s += f'<circle cx="540" cy="675" r="42" fill="{CR}"/>'
    s += f'<path d="M520 660 L505 675 L520 690 M560 660 L575 675 L560 690" stroke="{BX}" stroke-width="5" fill="none"/>'
    s += pill(J5, "AVANT", 18, 60, 70, CR, BX)
    s += pill(J5, "APRÈS", 18, W - 60, 70, BX, CR, anchor="end")
    s += f'<rect y="{H - 150}" width="{W}" height="150" fill="{BX}"/>'
    s += T(J3, "Salon · dépose, électricité, sols, peinture", 24, 80, H - 64, CR, 0.02)
    return s


def post_chantier():
    s = facade(True)
    s += pill(J5, "SUR LE CHANTIER", 18, 70, 70, BX, CR)
    s += caption_band("RAVALEMENT DE FAÇADE", "Semaine 3 sur 8", "Échafaudage posé, piquetage des enduits en cours")
    return s


def post_metiers():
    s = f'<rect width="{W}" height="{H}" fill="{BX}"/>'
    s += f'<path d="{arch_path(520, 720, 260, 1500)}" fill="none" stroke="{CH}" stroke-opacity=".16" stroke-width="3"/>'
    s += T(J5, "NOS MÉTIERS", 18, 90, 210, CH, 0.32)
    s += T(J3, "Un seul interlocuteur,", 48, 90, 300, CR)
    s += T(J3, "tous les corps d’état.", 48, 90, 370, CR)
    items = ["Gros œuvre", "Rénovation intérieure & extérieure", "Électricité · Plomberie", "Menuiserie",
             "Bureaux sur mesure", "Aménagement intérieur", "Rénovation de façades"]
    for i, it in enumerate(items):
        y = 520 + i * 98
        s += f'<rect x="90" y="{y - 22}" width="14" height="14" fill="{CH}"/>'
        s += T(J3, it, 30, 130, y, CR, 0.01)
        s += f'<rect x="90" y="{y + 32}" width="900" height="1" fill="{CR}" opacity=".18"/>'
    s += mini_logo(W - 90 - 60, 1200, 70, CR, CH)
    return s


def post_sur_mesure():
    s = desk()
    s += caption_band("SUR MESURE", "Bureau en chêne massif", "Dessiné et fabriqué pour un cabinet d’avocats")
    return s


def post_conseil():
    s = f'<rect width="{W}" height="{H}" fill="{CR}"/>'
    s += T(J5, "CONSEIL DOMOVA", 18, 90, 200, CHF, 0.32)
    s += T(J3, "3", 420, 70, 720, BX)
    s += lines(J3, ["erreurs à éviter", "avant de rénover", "votre appartement"], 50, 90, 860, 84, BX)
    s += f'<rect x="90" y="1130" width="60" height="3" fill="{CHF}"/>'
    s += T(J5, "GLISSEZ", 18, 90, 1200, BX, 0.3)
    s += f'<path d="M248 1192 H310 M296 1180 L310 1192 L296 1204" stroke="{BX}" stroke-width="3" fill="none"/>'
    for i in range(5):
        s += f'<circle cx="{W - 230 + i * 30}" cy="1192" r="7" fill="{BX if i == 0 else CHF}" opacity="{1 if i == 0 else .45}"/>'
    s += f'<path d="{arch_path(700, 260, 300, 700)}" fill="none" stroke="{BX}" stroke-width="5"/>'
    s += f'<path d="{arch_path(742, 176, 342, 690)}" fill="none" stroke="{CHF}" stroke-width="2.5"/>'
    s += f'<rect x="630" y="697" width="400" height="6" fill="{BX}"/>'
    return s


def post_matiere():
    s = materials()
    s += f'<rect x="0" y="{H - 120}" width="{W}" height="120" fill="{BX}"/>'
    s += T(J5, "LA MATIÈRE", 18, 90, H - 52, CH, 0.32)
    s += T(J3, "Marbre · chêne · laiton · velours · terre cuite", 20, W - 90, H - 52, CR, 0.02, "end")
    return s


def post_facade():
    return facade(False) + caption_band("RÉALISATION", "Façade rénovée", "Ravalement pierre de taille · Immeuble de 1890")


def post_engagements():
    s = f'<rect width="{W}" height="{H}" fill="{BXP}"/>'
    s += T(J5, "NOS ENGAGEMENTS", 18, 90, 210, CH, 0.32)
    s += lines(J3, ["Un seul interlocuteur,", "du devis à la remise", "des clés."], 50, 90, 330, 80, CR)
    rows = [("01", "Devis détaillé, poste par poste"), ("02", "Suivi de chantier chaque semaine"),
            ("03", "Chantier propre, délais tenus"), ("04", "Garantie décennale")]
    for i, (n, t) in enumerate(rows):
        y = 700 + i * 120
        s += T(J5, n, 20, 90, y, CH, 0.1)
        s += T(J3, t, 30, 160, y, CR, 0.01)
        s += f'<rect x="90" y="{y + 40}" width="900" height="1" fill="{CR}" opacity=".18"/>'
    s += mini_logo(W - 90 - 60, 1200, 70, CR, CH)
    return s


def post_devis():
    s = f'<rect width="{W}" height="{H}" fill="{CH}"/>'
    s += f'<path d="{arch_path(290, 500, 170, 820)}" fill="none" stroke="{BX}" stroke-width="7"/>'
    s += f'<path d="{arch_path(370, 340, 250, 812)}" fill="none" stroke="{BXP}" stroke-width="3"/>'
    s += f'<rect x="150" y="816" width="780" height="9" fill="{BX}"/>'
    s += T(J3, "Votre projet", 58, W / 2, 960, BX, 0.0, "middle")
    s += T(J3, "commence ici.", 58, W / 2, 1046, BX, 0.0, "middle")
    s += pill(J5, "DEVIS GRATUIT · LIEN EN BIO", 18, W / 2, 1120, BX, CR, 0.22, 44, 86, "middle")
    return s


POSTS = [  # grid order: newest first (row by row)
    ("12_devis", "Appel à l’action", "Fond champagne, l’arche en grand, un seul message.", post_devis),
    ("11_facade", "Réalisation · photo", "La photo plein cadre, un bandeau dégradé bordeaux en bas avec titre et lieu.", post_facade),
    ("10_citation", "Citation", "Fond crème, une phrase de l’équipe en grand, signée.", post_citation),
    ("09_avant-apres", "Avant / Après", "Deux photos prises du même point de vue, séparées par un filet crème.", post_avant_apres),
    ("08_metiers", "Nos métiers", "Fond bordeaux, liste des corps d’état. À épingler en haut du profil.", post_metiers),
    ("07_sur-mesure", "Sur mesure · photo", "Les bureaux et la menuiserie, avec le même bandeau titre.", post_sur_mesure),
    ("06_engagements", "Nos engagements", "Fond bordeaux profond, quatre engagements numérotés. À épingler.", post_engagements),
    ("05_realisation", "Réalisation · photo", "Intérieur fini, lumière naturelle, cadrage frontal.", post_realisation),
    ("04_conseil", "Conseil (carrousel)", "Couverture crème avec un grand chiffre ; les pages suivantes détaillent chaque point.", post_conseil),
    ("03_chantier", "Sur le chantier", "L’avancement semaine par semaine, avec l’étiquette « Sur le chantier ».", post_chantier),
    ("02_matiere", "La matière", "Planche de matériaux : marbre, chêne, laiton, velours, terre cuite.", post_matiere),
    ("01_bienvenue", "Bienvenue", "Le premier post : le logo sur bordeaux.", post_bienvenue),
]


# ------------------------------------------------------------------ stories & highlights
def story_chantier():
    w, h = 1080, 1920
    s = f'<g transform="translate(0 285)">{facade(True, w, 1350)}</g>'
    s += f'<rect width="{w}" height="300" fill="{BX}"/><rect y="1620" width="{w}" height="300" fill="{BX}"/>'
    s += mini_logo(80, 120, 90, CR, CH)
    s += T(J5, "DOMOVA", 22, 210, 180, CR, 0.4)
    s += T(J5, "SUR LE CHANTIER AUJOURD’HUI", 20, 80, 1720, CH, 0.3)
    s += T(J3, "Pose de l’échafaudage", 30, 80, 1785, CR)
    s += f'<rect x="{w - 330}" y="1690" width="250" height="110" rx="20" fill="{CR}"/>'
    s += T(J5, "SEMAINE", 18, w - 205, 1735, BX, 0.3, "middle")
    s += T(J6, "3 / 8", 40, w - 205, 1785, BX, 0.05, "middle")
    return doc(s, w, h, "DOMOVA — story chantier")


def story_devis():
    w, h = 1080, 1920
    s = f'<rect width="{w}" height="{h}" fill="{BX}"/>'
    s += f'<path d="{arch_path(120, 840, 260, 1150)}" fill="none" stroke="{CH}" stroke-opacity=".35" stroke-width="4"/>'
    s += f'<rect x="40" y="1146" width="1000" height="8" fill="{CH}" opacity=".5"/>'
    s += T(J5, "UNE QUESTION SUR VOTRE PROJET ?", 20, w / 2, 640, CH, 0.3, "middle")
    s += lines(J3, ["Rénovation, extension,", "bureaux sur mesure…"], 50, w / 2, 780, 80, CR, 0.0, "middle")
    s += f'<rect x="190" y="1300" width="700" height="210" rx="28" fill="{CR}"/>'
    s += T(J5, "POSEZ-NOUS VOTRE QUESTION", 18, w / 2, 1370, CHF, 0.25, "middle")
    s += f'<rect x="240" y="1410" width="600" height="60" rx="14" fill="#EADDCB"/>'
    s += T(J3, "Tapez quelque chose…", 20, w / 2, 1450, "#9C8676", 0.0, "middle")
    s += T(J5, "DEVIS GRATUIT · LIEN EN BIO", 20, w / 2, 1700, CR, 0.25, "middle")
    return doc(s, w, h, "DOMOVA — story question")


HIGHLIGHTS = [
    ("Réalisations", '<path d="M30 74V40a20 20 0 0 1 40 0v34" /><path d="M20 74h60"/>'),
    ("Chantiers", '<path d="M24 76V30M76 76V30M18 44h64M18 62h64"/>'),
    ("Avant/Après", '<rect x="22" y="28" width="56" height="46"/><path d="M50 28v46"/>'),
    ("Sur mesure", '<path d="M18 46h64M24 46v30M76 46v30M54 46v30M54 60h22"/>'),
    ("Matières", '<circle cx="38" cy="44" r="14"/><rect x="52" y="46" width="24" height="24"/>'),
    ("Devis", '<path d="M30 22h28l14 14v42H30z"/><path d="M38 50h24M38 62h18"/>'),
]


def highlight_svg(paths):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" role="img"><circle cx="50" cy="50" r="50" fill="{BX}"/>'
            f'<g fill="none" stroke="{CH}" stroke-width="3" stroke-linejoin="round">{paths}</g></svg>')


# ------------------------------------------------------------------ page
def page():
    from content import INSTAGRAM_BIOS
    carou = "".join(f'<img src="posts/{n}.jpg" alt="Carrousel, page {k}" loading="lazy">' for k, n in enumerate(["04_conseil"] + [c[0] for c in CAROUSEL], 1))
    bio = INSTAGRAM_BIOS[0]["texte"].replace("\n", "<br>")
    bios = "".join(
        f'<div class="cap" style="color:var(--ink)"><span class="tag">{b["nom"]}</span>{b["texte"]}'
        f'<span class="note">{len(b["texte"])} / 150 caractères</span></div>' for b in INSTAGRAM_BIOS)
    avatar = open(os.path.join(B.ROOT, "icons", "reseaux-sociaux", "domova_cercle-symbole-bordeaux.svg")).read()
    avatar = re.sub(r' width="[^"]+" height="[^"]+"', ' role="img"', avatar, count=1)
    hl = "".join(f'<li><span class="hl">{highlight_svg(p)}</span><span>{n}</span></li>' for n, p in HIGHLIGHTS)
    grid = "".join(f'<img src="posts/{slug}.jpg" alt="Publication : {name}" loading="lazy">' for slug, name, _, _ in POSTS)
    tmpl = "".join(f'<figure><img src="posts/{slug}.jpg" alt="{name}" loading="lazy"><figcaption><b>{name}</b>{desc}</figcaption></figure>' for slug, name, desc, _ in reversed(POSTS))
    return f"""<title>DOMOVA Instagram</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Jost:wght@400;500;600&family=JetBrains+Mono:wght@400&display=swap">
<style>
/* Layout: hero with the phone profile beside the strategy, then templates grid, rules, captions, weekly rhythm */
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
.screen{{background:#fff;border-radius:38px;overflow:hidden;color:#141414;font-size:13px;line-height:1.35}}
.bar{{display:flex;justify-content:space-between;align-items:center;padding:18px 20px 8px;font-weight:600;font-size:16px}}
.bar small{{font-weight:400;color:#888}}
.top{{display:grid;grid-template-columns:86px 1fr;gap:18px;align-items:center;padding:8px 18px}}
.top svg{{width:86px;height:86px;display:block;border-radius:50%;outline:2px solid var(--chf);outline-offset:3px}}
.stats{{display:flex;justify-content:space-around;text-align:center}}
.stats b{{display:block;font-size:16px}} .stats span{{color:#555;font-size:12px}}
.bio{{padding:10px 18px 4px;display:grid;gap:2px}} .bio b{{font-size:14px}} .bio .cat{{color:#888}} .bio a{{color:#2b4a7a;text-decoration:none}}
.btns{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;padding:10px 18px}}
.btns span{{background:#EFEFEF;border-radius:8px;text-align:center;padding:7px 0;font-weight:600}}
.btns span:first-child{{background:var(--bx);color:var(--cr)}}
.hls{{display:flex;gap:14px;list-style:none;margin:0;padding:6px 16px 12px;overflow-x:auto}}
.hls li{{display:grid;justify-items:center;gap:4px;font-size:11px;flex:0 0 auto}}
.hl{{width:58px;height:58px;border-radius:50%;padding:2px;border:1px solid #ddd;display:block}} .hl svg{{width:100%;height:100%;display:block}}
.tabs{{display:flex;justify-content:space-around;border-top:1px solid #eee;padding:8px 0;color:#999;font-size:12px;letter-spacing:.08em}}
.tabs span:first-child{{color:#141414;border-bottom:2px solid #141414;padding-bottom:6px}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:2px}}
.grid img{{width:100%;aspect-ratio:3/4;object-fit:cover;display:block}}
.strat{{display:grid;gap:28px}}
.pillars{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:2px;background:var(--line)}}
.pillars div{{background:var(--cr);padding:20px;display:grid;gap:6px}}
.pillars b{{font-family:var(--m);font-size:12px;letter-spacing:.14em;color:var(--chf);text-transform:uppercase;font-weight:400}}
.tmpl{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:24px}}
.tmpl figure{{margin:0;display:grid;gap:10px}} .tmpl img{{width:100%;display:block;box-shadow:0 10px 30px rgba(0,0,0,.25)}}
.tmpl figcaption{{font-size:14.5px;color:#E3CFC2}} .tmpl b{{display:block;color:var(--cr);font-weight:500;font-size:16px}}
.rules{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:32px}}
.rule{{display:grid;gap:10px;align-content:start;padding-top:18px;border-top:2px solid var(--bx)}}
.rule ul{{margin:0;padding-left:18px;color:var(--muted)}}
.stories{{display:grid;grid-template-columns:repeat(2,minmax(0,260px)) minmax(0,1fr);gap:32px;align-items:start}}
.stories img{{width:100%;display:block;border-radius:22px;box-shadow:0 14px 34px rgba(46,11,20,.3)}}
.caps{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:24px}}
.cap{{background:#fff;padding:22px;display:grid;gap:10px;align-content:start;border:1px solid var(--line);font-size:15px;white-space:pre-line}}
.cap .tag{{font-family:var(--m);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--chf)}}
.cap .ht{{color:#2b4a7a}}
.carou{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:16px}} .carou img{{width:100%;display:block;box-shadow:0 10px 30px rgba(0,0,0,.3)}}
@media (max-width:900px){{.carou{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}
.bios4{{grid-template-columns:repeat(4,minmax(0,1fr))}} .bios4 .cap{{font-size:16px}}
@media (max-width:1000px){{.bios4{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}
.week{{width:100%;border-collapse:collapse;font-size:15px;min-width:640px}}
.week th,.week td{{text-align:left;padding:14px 12px;border-bottom:1px solid var(--line);vertical-align:top}}
.week th{{font-family:var(--m);font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--chf);font-weight:400}}
.scroll{{overflow-x:auto}}
.note{{font-size:14px;color:var(--muted)}}
@media (max-width:900px){{.hero,.stories{{grid-template-columns:minmax(0,1fr)}}.tmpl{{grid-template-columns:repeat(2,minmax(0,1fr))}}.rules,.caps{{grid-template-columns:minmax(0,1fr)}}.phone{{margin:0 auto}}}}
</style>

<section class="band"><div class="wrap">
 <div class="hero">
  <div class="phone"><div class="screen">
   <div class="bar">domova.btp <small>•••</small></div>
   <div class="top">{avatar}<div class="stats"><div><b>12</b><span>publications</span></div><div><b>0</b><span>abonnés</span></div><div><b>48</b><span>suivi(e)s</span></div></div></div>
   <div class="bio"><b>DOMOVA</b><span class="cat">Entreprise générale du bâtiment</span>
    <span>{bio}</span><a>domova.fr</a></div>
   <div class="btns"><span>Suivre</span><span>Message</span><span>Devis</span></div>
   <ul class="hls">{hl}</ul>
   <div class="tabs"><span>PUBLICATIONS</span><span>REELS</span><span>IDENTIFIÉ</span></div>
   <div class="grid">{grid}</div>
  </div></div>
  <div class="strat">
   <span class="eyebrow">DOMOVA · Direction artistique Instagram</span>
   <h1>Un profil qui ressemble à une maison d’architecture</h1>
   <p class="lede">Le fil alterne trois familles de visuels : les photos de vos réalisations, les visuels bordeaux qui portent la marque, et les visuels crème ou champagne qui donnent de l’air. Ainsi la grille reste élégante, même vue de loin.</p>
   <div class="pillars">
    <div><b>Montrer</b><span>Réalisations finies, plein cadre, lumière naturelle. 40 % des posts.</span></div>
    <div><b>Raconter</b><span>Le chantier semaine après semaine, l’avant et l’après. 30 %.</span></div>
    <div><b>Conseiller</b><span>Carrousels utiles : budget, étapes, erreurs à éviter. 20 %.</span></div>
    <div><b>Rassurer</b><span>Métiers, engagements, avis clients, appel au devis. 10 %.</span></div>
   </div>
   <p class="note">Les illustrations tiennent la place de vos futures photos de chantier. Le nom du compte, la ville, les chiffres et les projets sont des exemples à adapter.</p>
  </div>
 </div>
</div></section>

<section class="band dark"><div class="wrap">
 <div><span class="eyebrow">Les 12 premières publications</span><h2>Des modèles réutilisables, du premier post au plus récent</h2></div>
 <p class="lede">Format portrait 1080 × 1350 px (4:5). Chaque visuel et sa légende sont prêts dans le dossier « a-publier ». Tous les textes restent dans la zone centrale, pour survivre au recadrage 3:4 de la grille du profil.</p>
 <div class="tmpl">{tmpl}</div>
</div></section>

<section class="band dark" style="padding-top:0"><div class="wrap">
 <div><span class="eyebrow">Carrousel</span><h2>« 3 erreurs à éviter » en cinq pages</h2></div>
 <p class="lede">Couverture, une page par erreur avec la bonne pratique dans un encadré bordeaux, puis une page de résumé avec l’appel au devis. Les points en bas indiquent la progression.</p>
 <div class="carou">{carou}</div>
</div></section>

<section class="band"><div class="wrap">
 <div><span class="eyebrow">Stories</span><h2>Stories et couvertures « à la une »</h2></div>
 <div class="stories">
  <img src="posts/story_chantier.jpg" alt="Story : sur le chantier aujourd’hui">
  <img src="posts/story_question.jpg" alt="Story : une question sur votre projet">
  <div class="strat">
   <p>Les stories reprennent les bandeaux bordeaux en haut et en bas : la photo du jour au centre, une ligne de texte, et un sticker crème pour l’info clé (semaine, prix, délai). Une story par jour de chantier suffit.</p>
   <p>Les six couvertures à la une sont des pictogrammes au trait champagne sur bordeaux, dessinés dans l’esprit de l’arche : Réalisations, Chantiers, Avant/Après, Sur mesure, Matières, Devis.</p>
  </div>
 </div>
</div></section>

<section class="band" style="padding-top:0"><div class="wrap">
 <div><span class="eyebrow">Les règles</span><h2>Ce qui fait tenir la grille</h2></div>
 <div class="rules">
  <div class="rule"><h3>Photo</h3><ul><li>Lumière du jour, jamais de flash</li><li>Cadrage frontal, verticales bien droites (mode grille du téléphone)</li><li>Pièce rangée, chantier propre, pas de personnes de dos</li><li>Avant et après pris du même point exact</li><li>Filtre léger et chaud, toujours le même</li></ul></div>
  <div class="rule"><h3>Texte sur visuel</h3><ul><li>Jost uniquement : surtitre en capitales espacées, titre en Regular</li><li>Un titre de 6 mots maximum</li><li>Bordeaux sur crème, crème sur bordeaux, champagne pour les surtitres</li><li>Le logo arche en petit, toujours en bas à droite</li></ul></div>
  <div class="rule"><h3>Rythme de la grille</h3><ul><li>Jamais deux visuels bordeaux côte à côte</li><li>Une photo sur deux environ</li><li>Épinglez trois posts : Nos métiers, Nos engagements, un Avant/Après fort</li><li>Reels : visites de chantier verticales, 15 à 30 s</li></ul></div>
 </div>
</div></section>

<section class="band"><div class="wrap">
 <div><span class="eyebrow">Bio Instagram</span><h2>Quatre bios au choix (150 caractères maximum)</h2></div>
 <p class="lede">La première est celle affichée dans le profil ci-dessus. Le nom « DOMOVA » et la catégorie « Entreprise générale du bâtiment » se règlent à part, dans « Modifier le profil ».</p>
 <div class="caps bios4">{bios}</div>
</div></section>

<section class="band dark"><div class="wrap">
 <div><span class="eyebrow">Légendes</span><h2>Trois exemples de légendes</h2></div>
 <div class="caps">
  <div class="cap" style="color:var(--ink)"><span class="tag">Réalisation</span>Appartement haussmannien, Paris 16e.
Rénovation complète en 14 semaines : dépose, électricité, plomberie, parquet en chêne, moulures restaurées.

Le détail dont nous sommes fiers : l’arche entre le salon et la salle à manger, retrouvée sous un doublage des années 80.

📩 Un projet similaire ? Devis gratuit, lien en bio.
<span class="ht">#renovationappartement #haussmannien #architectureinterieure #paris16 #domova</span></div>
  <div class="cap" style="color:var(--ink)"><span class="tag">Sur le chantier</span>Semaine 3 sur 8 : l’échafaudage est en place, le piquetage des enduits a commencé.

La semaine prochaine : reprise des pierres abîmées et premiers enduits à la chaux.

Suivez l’avancement dans nos stories « Chantiers ».
<span class="ht">#ravalementdefacade #pierredetaille #chantier #batiment #domova</span></div>
  <div class="cap" style="color:var(--ink)"><span class="tag">Conseil</span>3 erreurs à éviter avant de rénover 👇

1. Choisir les finitions avant d’avoir validé l’électricité
2. Oublier la ventilation de la salle de bains
3. Multiplier les artisans sans coordinateur

Enregistrez ce post pour votre futur projet.
<span class="ht">#conseilrenovation #travauxmaison #renovation #amenagementinterieur #domova</span></div>
 </div>
</div></section>

<section class="band"><div class="wrap">
 <div><span class="eyebrow">Planning</span><h2>Une semaine type</h2></div>
 <div class="scroll"><table class="week">
  <thead><tr><th>Jour</th><th>Publication</th><th>Stories</th></tr></thead>
  <tbody>
   <tr><td>Lundi</td><td>Sur le chantier : avancement de la semaine</td><td>Arrivée sur un chantier</td></tr>
   <tr><td>Mercredi</td><td>Conseil (carrousel) ou Avant / Après</td><td>Sondage ou question</td></tr>
   <tr><td>Vendredi</td><td>Réalisation (photo) ou Reel de visite</td><td>Fin de semaine sur le chantier</td></tr>
   <tr><td>Dimanche</td><td>Facultatif : citation, matière, engagement</td><td>Repartage d’un avis client</td></tr>
  </tbody>
 </table></div>
 <p class="note">Trois publications par semaine, tenues dans la durée, valent mieux que dix la première semaine puis plus rien.</p>
</div></section>
"""


# ------------------------------------------------------------------ carrousel « 3 erreurs » : pages intérieures
ERREURS = [
    ("01", ["Choisir les finitions", "avant l’électricité"],
     ["Carrelage, cuisine, luminaires : tout", "dépend de l’emplacement des prises,", "des circuits et des points lumineux.",
      "Décidés après coup, ils obligent", "à casser ce qui est neuf."],
     ["Validez d’abord le plan électrique,", "pièce par pièce. Les finitions ensuite."]),
    ("02", ["Oublier la ventilation", "de la salle de bains"],
     ["Sans extraction efficace, l’humidité", "s’installe : moisissures, peinture qui", "cloque, joints noircis en quelques mois."],
     ["Prévoyez la VMC dès la conception,", "et une peinture pour pièces humides."]),
    ("03", ["Multiplier les artisans", "sans coordinateur"],
     ["Le plombier attend l’électricien, qui", "attend le plaquiste… Les retards", "s’additionnent et personne n’est", "responsable de l’ensemble."],
     ["Un seul interlocuteur tous corps", "d’état : un planning, un responsable."]),
]


def dots(active, total=5, y=1250, dark=False):
    s = ""
    x0 = W / 2 - (total - 1) * 15
    for i in range(total):
        on = i == active
        col = (CR if dark else BX) if on else (CH if dark else CHF)
        s += f'<circle cx="{x0 + i * 30:.1f}" cy="{y}" r="7" fill="{col}" opacity="{1 if on else .45}"/>'
    return s


def carousel_page(i):
    num, title, body, sol = ERREURS[i]
    s = f'<rect width="{W}" height="{H}" fill="{CR}"/>'
    s += T(J5, f"ERREUR {num} / 03", 18, 90, 170, CHF, 0.32)
    s += T(J3, num, 230, W - 90, 330, CH, 0.0, "end")
    s += lines(J3, title, 54, 90, 470, 76, BX)
    s += f'<rect x="90" y="580" width="60" height="3" fill="{CHF}"/>'
    s += lines(J3, body, 32, 90, 680, 50, "#5A3A3A")
    top = 680 + len(body) * 50 + 40
    s += f'<rect x="90" y="{top}" width="{W - 180}" height="{110 + len(sol) * 46}" fill="{BX}"/>'
    s += T(J5, "LA BONNE PRATIQUE", 17, 130, top + 56, CH, 0.3)
    s += lines(J3, sol, 30, 130, top + 112, 46, CR)
    s += dots(i + 1)
    s += mini_logo(W - 90 - 50, 1215, 60, BX, CHF)
    return s


def carousel_fin():
    s = f'<rect width="{W}" height="{H}" fill="{BX}"/>'
    s += f'<path d="{arch_path(340, 400, 170, 640)}" fill="none" stroke="{CH}" stroke-width="5"/>'
    s += f'<path d="{arch_path(400, 280, 230, 636)}" fill="none" stroke="{CH}" stroke-opacity=".5" stroke-width="2.5"/>'
    s += f'<rect x="230" y="637" width="620" height="6" fill="{CH}"/>'
    s += T(J5, "EN RÉSUMÉ", 18, W / 2, 760, CH, 0.32, "middle")
    s += lines(J3, ["Électricité d’abord,", "ventilation prévue,", "un seul coordinateur."], 50, W / 2, 850, 72, CR, 0.0, "middle")
    s += pill(J5, "DEVIS GRATUIT · LIEN EN BIO", 18, W / 2, 1080, CH, BX, 0.22, 44, 80, "middle")
    s += T(J3, "Enregistrez ce post pour votre projet", 24, W / 2, 1210, CR, 0.02, "middle")
    s += dots(4, dark=True, y=1270)
    return s


CAROUSEL = [("04_conseil_page-2", lambda: carousel_page(0)), ("04_conseil_page-3", lambda: carousel_page(1)),
            ("04_conseil_page-4", lambda: carousel_page(2)), ("04_conseil_page-5", carousel_fin)]


def build():
    os.makedirs(P, exist_ok=True)
    pairs = []
    for slug, name, desc, fn in POSTS:
        f = os.path.join(P, slug)
        open(f + ".svg", "w").write(doc(fn(), title=f"DOMOVA — Instagram — {name}"))
        pairs += [f + ".svg", f + ".png"]
    for slug, fn in CAROUSEL:
        f = os.path.join(P, slug)
        open(f + ".svg", "w").write(doc(fn(), title="DOMOVA — Instagram — carrousel 3 erreurs"))
        pairs += [f + ".svg", f + ".png"]
    for slug, fn in (("story_chantier", story_chantier), ("story_question", story_devis)):
        f = os.path.join(P, slug)
        open(f + ".svg", "w").write(fn())
        pairs += [f + ".svg", f + ".png"]
    subprocess.run(["node", os.path.join(os.path.dirname(__file__), "render_svg.js"), "1080"] + pairs, check=True)
    for k in range(1, len(pairs), 2):
        im = Image.open(pairs[k]).convert("RGB")
        im.save(pairs[k][:-4] + ".jpg", quality=86, optimize=True, progressive=True)
    open(os.path.join(OUT, "index.html"), "w").write(page())
    print("instagram ok")


if __name__ == "__main__":
    build()
