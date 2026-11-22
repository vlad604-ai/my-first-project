"""DOMOVA — construction of the symbols, the custom wordmark and the tagline."""
import math
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from geom import (ellipse, half_right, poly, union, box, halfplane_below, band, translate)

# ==========================================================================
# DIRECTION A — "LE PLI" : monogramme D+M (direction retenue)
# ==========================================================================
# Grid: height 112 units. A D (stem + half round) whose top is folded by a V
# that descends to the base: the stem and the bowl become the two legs of an
# M. Two counters appear: a triangle (plan, structure) and a D segment
# (volume). Stroke 20 u, diagonals optically thinner (0.9).

SYM = dict(s=20.0, H=112.0, flat=64.0, nl=20.0, nr=100.0, sd=18.0)


def symbol_A(parts=False):
    s, H, flat, nl, nr, sd = (SYM[k] for k in ("s", "H", "flat", "nl", "nr", "sd"))
    R = H / 2
    # apex so that the lower edge of the V lands exactly on the inner base line
    ax = (nl + nr) / 2
    half = (nr - nl) / 2

    def lower_apex_y(ay):
        L = math.hypot(half, ay)
        return ay + sd * L / half  # vertical offset of a parallel line at distance sd

    lo, hi = 10.0, H
    for _ in range(60):
        mid = (lo + hi) / 2
        if lower_apex_y(mid) > H - s:
            hi = mid
        else:
            lo = mid
    ay = lo
    outer = union(box(0, 0, flat, H), half_right(flat, R, R))
    inner = union(box(s, s, flat, H - s), half_right(flat, R, R - s))
    notch = poly([(nl, -60), (nl, 0), (ax, ay), (nr, 0), (nr, -60)])
    counter = inner.intersection(union(halfplane_below((nl, 0), (ax, ay), sd),
                                       halfplane_below((ax, ay), (nr, 0), sd)))
    mark = outer.difference(notch).difference(counter)
    mark = mark.buffer(0)
    if not parts:
        return mark
    # copper accent: the second stroke of the M, from the apex to the bowl
    strip = halfplane_below((ax, ay), (nr, 0), 0.0).difference(halfplane_below((ax, ay), (nr, 0), sd))
    ring = outer.difference(inner)
    diag = mark.intersection(strip).difference(ring).intersection(box(ax - 30, 0, nr, H)).buffer(0)
    return mark, diag


# ==========================================================================
# DIRECTION B — "PERSPECTIVE" : M plié en volume (deux façades)
# ==========================================================================
def symbol_B():
    """Returns (dark_planes, light_planes, accent_planes) — an M read as two
    folded facades seen in perspective."""
    W, H = 120.0, 112.0
    d = 22.0  # facade depth in perspective
    # left facade (front) and its return, right facade and its return
    left_front = poly([(0, 14), (d, 0), (d, H - 14 + 0), (0, H)])
    left_diag = poly([(d, 0), (W / 2, 52), (W / 2, 52 + 30), (d, 30)])
    right_diag = poly([(W / 2, 52), (W - d, 0), (W - d, 30), (W / 2, 52 + 30)])
    right_front = poly([(W - d, 0), (W, 14), (W, H), (W - d, H - 14)])
    return [left_front, right_front], [left_diag], [right_diag]


# ==========================================================================
# DIRECTION C — "FONDATION" : D assemblé (pilier + demi-cylindre)
# ==========================================================================
def symbol_C():
    H = 112.0
    pillar = box(0, 0, 26, H)
    bowl_outer = half_right(40, H / 2, H / 2)
    bowl_inner = half_right(40, H / 2, H / 2 - 22)
    bowl = union(bowl_outer.difference(bowl_inner), box(36, 0, 40, 22), box(36, H - 22, 40, H))
    bowl = union(bowl, box(36, 0, 40.01, 22))
    key = box(36, H / 2 - 11, 54, H / 2 + 11)  # copper key stone in the counter
    return pillar, bowl, key


# ==========================================================================
# WORDMARK — DOMOVA, custom geometric capitals (cap height 100)
# ==========================================================================
CAP = 100.0
STEM = 21.0          # vertical stems
HAIR = 18.5          # horizontals
ROUND = 22.5         # horizontal thickness of rounds
DIAG = 20.5          # perpendicular thickness of diagonals
OVER = 1.6           # optical overshoot of rounds


def _diag_width(dx_total, height, d):
    """Horizontal width t of a diagonal stroke of perpendicular thickness d
    whose outer edge spans dx_total horizontally over height."""
    t = d
    for _ in range(40):
        run = dx_total - t / 2
        ang = math.atan2(run, height)
        t = d / math.cos(ang)
    return t


def L_D(x0):
    W = 82.0
    flat = W - CAP / 2
    outer = union(box(x0, 0, x0 + flat, CAP), half_right(x0 + flat, CAP / 2, CAP / 2, CAP / 2))
    inner = union(box(x0 + STEM, HAIR, x0 + flat, CAP - HAIR),
                  half_right(x0 + flat, CAP / 2, CAP / 2 - ROUND, CAP / 2 - HAIR))
    return outer.difference(inner), W


def L_O(x0):
    r = CAP / 2 + OVER
    W = 2 * r
    cx = x0 + r
    g = ellipse(cx, CAP / 2, r, r).difference(ellipse(cx, CAP / 2, r - ROUND, r - HAIR - 0.6))
    return g, W


def L_M(x0):
    W = 108.0
    mid = x0 + W / 2
    t = _diag_width(W / 2, CAP, DIAG)
    left = poly([(x0, 0), (x0 + t, 0), (mid + t / 2, CAP), (mid - t / 2, CAP)])
    right = poly([(x0 + W - t, 0), (x0 + W, 0), (mid + t / 2, CAP), (mid - t / 2, CAP)])
    g = union(box(x0, 0, x0 + STEM, CAP), box(x0 + W - STEM, 0, x0 + W, CAP), left, right)
    return g.intersection(box(x0 - 1, 0, x0 + W + 1, CAP)), W


def L_V(x0):
    W = 96.0
    mid = x0 + W / 2
    t = _diag_width(W / 2, CAP, DIAG)
    left = poly([(x0, 0), (x0 + t, 0), (mid + t / 2, CAP), (mid - t / 2, CAP)])
    right = poly([(x0 + W - t, 0), (x0 + W, 0), (mid + t / 2, CAP), (mid - t / 2, CAP)])
    return union(left, right).intersection(box(x0 - 1, 0, x0 + W + 1, CAP)), W


def L_A(x0):
    W = 96.0
    mid = x0 + W / 2
    t = _diag_width(W / 2, CAP, DIAG)
    left = poly([(mid - t / 2, 0), (mid + t / 2, 0), (x0 + t, CAP), (x0, CAP)])
    right = poly([(mid - t / 2, 0), (mid + t / 2, 0), (x0 + W, CAP), (x0 + W - t, CAP)])
    legs = union(left, right)
    bar_y = 66.0
    bar = box(x0, bar_y, x0 + W, bar_y + HAIR).intersection(
        union(poly([(mid, 0), (x0 + W + 40, CAP + 80), (x0 - 40, CAP + 80)])))
    # keep the bar only between the legs
    hull = poly([(mid - t / 2, 0), (mid + t / 2, 0), (x0 + W, CAP), (x0, CAP)])
    bar = bar.intersection(hull)
    return union(legs, bar).intersection(box(x0 - 1, 0, x0 + W + 1, CAP)), W


# Spacing (units between letter bounding boxes), set optically.
TRACK = 27.0
PAIRS = {"DO": -3.0, "OM": -1.0, "MO": -1.0, "OV": -4.0, "VA": -20.0}
BUILDERS = {"D": L_D, "O": L_O, "M": L_M, "V": L_V, "A": L_A}


def wordmark(word="DOMOVA", track=TRACK):
    x = 0.0
    shapes = []
    prev = None
    for ch in word:
        if prev is not None:
            x += track + PAIRS.get(prev + ch, 0.0)
        g, w = BUILDERS[ch](x)
        shapes.append(g)
        x += w
        prev = ch
    return union(*shapes), x


# ==========================================================================
# TAGLINE — Jost Medium (SIL OFL 1.1), converted to outlines
# ==========================================================================
import os
FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")


class Typesetter:
    def __init__(self, path):
        self.f = TTFont(path)
        self.gs = self.f.getGlyphSet()
        self.cmap = self.f.getBestCmap()
        self.upm = self.f["head"].unitsPerEm
        self.cap = self.f["OS/2"].sCapHeight
        self.hmtx = self.f["hmtx"]

    def text(self, s, cap_height, tracking_em=0.0, x0=0.0, baseline=0.0, glyph_gap=None):
        """Return (path_d, width). cap_height in output units. Tracking in em."""
        k = cap_height / self.cap
        size = self.upm * k
        x = x0
        parts = []
        for i, ch in enumerate(s):
            gname = self.cmap[ord(ch)]
            pen = SVGPathPen(self.gs)
            tp = TransformPen(pen, (k, 0, 0, -k, x, baseline))
            self.gs[gname].draw(tp)
            parts.append(pen.getCommands())
            adv = self.hmtx[gname][0] * k
            x += adv + (tracking_em * size if i < len(s) - 1 else 0)
        return "".join(parts), x - x0

    def advance(self, s, cap_height, tracking_em=0.0):
        return self.text(s, cap_height, tracking_em)[1]


def tagline(ts, cap_h, total_width=None, words=("CONSTRUCTION", "RÉNOVATION", "AMÉNAGEMENT"),
            tracking_em=0.30, sep_gap_em=1.05, dot=None):
    """Lay out the tagline. Returns dict(text=d, dots=[(cx,cy,r)], width).
    If total_width is given, tracking is solved so the line matches it."""
    dot = dot if dot is not None else cap_h * 0.17

    def layout(tr):
        size = ts.upm * cap_h / ts.cap
        x = 0.0
        d = ""
        dots = []
        for i, w in enumerate(words):
            pd, wd = ts.text(w, cap_h, tr, x0=x, baseline=0.0)
            d += pd
            x += wd
            if i < len(words) - 1:
                gap = sep_gap_em * size + tr * size
                dots.append((x + gap / 2 + tr * size * 0.5 * 0, -cap_h / 2, dot))
                x += gap
        return d, dots, x

    tr = tracking_em
    if total_width:
        lo, hi = 0.0, 1.5
        for _ in range(50):
            tr = (lo + hi) / 2
            if layout(tr)[2] > total_width:
                hi = tr
            else:
                lo = tr
        tr = lo
    d, dots, w = layout(tr)
    # centre dots precisely between words: recompute using glyph bounds would be
    # overkill; the dot sits in the middle of the separator gap.
    return dict(text=d, dots=dots, width=w, tracking=tr)
