"""DOMOVA — geometry helpers.

Shapes are built with shapely (exact boolean operations), then written as SVG
paths. Curves are re-fitted on export: every run of polygon vertices that lies
on one of the construction circles/ellipses is replaced by a true SVG arc
command, so the delivered vectors contain clean arcs and few nodes.
"""
import math
from shapely.geometry import Polygon, Point, box, MultiPolygon
from shapely.ops import unary_union
from shapely import affinity

QS = 96  # segments per quarter circle used during construction

# Registry of construction ellipses: (cx, cy, rx, ry)
_CURVES = []


def reset_curves():
    _CURVES.clear()


def ellipse(cx, cy, rx, ry=None):
    ry = rx if ry is None else ry
    _CURVES.append((cx, cy, rx, ry))
    g = Point(0, 0).buffer(1.0, quad_segs=QS)
    g = affinity.scale(g, rx, ry, origin=(0, 0))
    return affinity.translate(g, cx, cy)


def half_right(cx, cy, rx, ry=None):
    ry = rx if ry is None else ry
    return ellipse(cx, cy, rx, ry).intersection(box(cx, cy - ry - 1, cx + rx + 1, cy + ry + 1))


def poly(pts):
    return Polygon(pts)


def union(*gs):
    return unary_union(list(gs))


def halfplane_below(p, q, off=0.0, big=5000):
    """Half-plane below (screen y down) the line p-q, shifted down by perpendicular distance off."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    L = math.hypot(dx, dy)
    nx, ny = -dy / L, dx / L
    if ny < 0:
        nx, ny = -nx, -ny
    ux, uy = dx / L, dy / L
    p2 = (p[0] + nx * off, p[1] + ny * off)
    q2 = (q[0] + nx * off, q[1] + ny * off)
    a = (p2[0] - ux * big, p2[1] - uy * big)
    b = (q2[0] + ux * big, q2[1] + uy * big)
    return Polygon([a, b, (b[0], b[1] + 3 * big), (a[0], a[1] + 3 * big)])


def band(p, q, w):
    """Rectangle of width w centred on segment p-q."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    L = math.hypot(dx, dy)
    nx, ny = -dy / L * w / 2, dx / L * w / 2
    return Polygon([(p[0] + nx, p[1] + ny), (q[0] + nx, q[1] + ny),
                    (q[0] - nx, q[1] - ny), (p[0] - nx, p[1] - ny)])


def translate(g, dx, dy):
    return affinity.translate(g, dx, dy)


def scale(g, s, origin=(0, 0)):
    return affinity.scale(g, s, s, origin=origin)


# --------------------------------------------------------------------------
# SVG path writing with arc re-fitting
# --------------------------------------------------------------------------

def _on_curve(pt, c, tol):
    cx, cy, rx, ry = c
    v = ((pt[0] - cx) / rx) ** 2 + ((pt[1] - cy) / ry) ** 2
    return abs(math.sqrt(v) - 1.0) * min(rx, ry) < tol


def _fmt(v):
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _ring_to_d(coords, curves, tf, tol=0.02):
    pts = [tf(p) for p in coords[:-1]]
    n = len(pts)
    if n < 3:
        return ""
    # tag each segment i (pts[i] -> pts[i+1]) with a curve index if it is a short step on a curve
    seg_curve = []
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        tag = None
        for ci, c in enumerate(curves):
            cx, cy, rx, ry = c
            step = 2 * math.pi * max(rx, ry) / (4 * QS) * 1.6
            if math.hypot(b[0] - a[0], b[1] - a[1]) <= step and _on_curve(a, c, tol) and _on_curve(b, c, tol):
                tag = ci
                break
        seg_curve.append(tag)
    # rotate so we start at a segment boundary where the tag changes
    start = 0
    for i in range(n):
        if seg_curve[i] != seg_curve[i - 1]:
            start = i
            break
    order = [(start + k) % n for k in range(n)]
    out = [f"M{_fmt(pts[start][0])} {_fmt(pts[start][1])}"]
    k = 0
    while k < n:
        i = order[k]
        tag = seg_curve[i]
        if tag is None:
            b = pts[(i + 1) % n]
            out.append(f"L{_fmt(b[0])} {_fmt(b[1])}")
            k += 1
            continue
        # gather run on same curve
        run = [i]
        while k + len(run) < n and seg_curve[order[k + len(run)]] == tag:
            run.append(order[k + len(run)])
        cx, cy, rx, ry = curves[tag]
        # accumulate signed sweep in normalised space
        total = 0.0
        for j in run:
            a, b = pts[j], pts[(j + 1) % n]
            a0 = math.atan2((a[1] - cy) / ry, (a[0] - cx) / rx)
            b0 = math.atan2((b[1] - cy) / ry, (b[0] - cx) / rx)
            d = b0 - a0
            while d > math.pi:
                d -= 2 * math.pi
            while d < -math.pi:
                d += 2 * math.pi
            total += d
        # split into pieces of at most ~170 degrees
        pieces = max(1, math.ceil(abs(total) / math.radians(170)))
        chunk = math.ceil(len(run) / pieces)
        for p0 in range(0, len(run), chunk):
            sub = run[p0:p0 + chunk]
            end = pts[(sub[-1] + 1) % n]
            sw = 0.0
            for j in sub:
                a, b = pts[j], pts[(j + 1) % n]
                a0 = math.atan2((a[1] - cy) / ry, (a[0] - cx) / rx)
                b0 = math.atan2((b[1] - cy) / ry, (b[0] - cx) / rx)
                d = b0 - a0
                while d > math.pi:
                    d -= 2 * math.pi
                while d < -math.pi:
                    d += 2 * math.pi
                sw += d
            sweep = 1 if sw > 0 else 0
            large = 1 if abs(sw) > math.pi else 0
            out.append(f"A{_fmt(rx)} {_fmt(ry)} 0 {large} {sweep} {_fmt(end[0])} {_fmt(end[1])}")
        k += len(run)
    out.append("Z")
    return "".join(out)


def to_d(g, sx=1.0, dx=0.0, dy=0.0):
    """Shapely geometry -> SVG path data, with transform x' = x*sx+dx."""
    tf = lambda p: (p[0] * sx + dx, p[1] * sx + dy)
    curves = [(c[0] * sx + dx, c[1] * sx + dy, c[2] * sx, c[3] * sx) for c in _CURVES]
    geoms = g.geoms if hasattr(g, "geoms") else [g]
    d = []
    for p in geoms:
        if p.is_empty:
            continue
        p = p.simplify(0.0)  # drop duplicate vertices only
        d.append(_ring_to_d(list(p.exterior.coords), curves, tf))
        for r in p.interiors:
            d.append(_ring_to_d(list(r.coords), curves, tf))
    return "".join(d)
