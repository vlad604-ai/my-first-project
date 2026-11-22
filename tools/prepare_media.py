"""Prépare les médias réels DOMOVA pour le montage vertical.

- Convertit les vidéos iPhone HDR (HLG) en SDR Rec.709, 30 i/s, H.264.
- Supprime le logo de l'enseigne cliente (Fresh Ride) : suivi image par image
  (tracker CSRT) puis reconstruction du mur (inpainting) avec bord adouci.
- Retire aussi le logo de la photo IMG_7771.

Usage : python3 tools/prepare_media.py   (depuis la racine du dépôt, originaux dans sources/)
Dépendances : ffmpeg, opencv-contrib-python-headless, numpy.
"""
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "sources"
TMP = ROOT / "sources" / "_tmp"
A = ROOT / "assets"
TMP.mkdir(parents=True, exist_ok=True)

SDR = "fps=30,eq=saturation=1.08:contrast=1.03,format=yuv420p"
TAGS = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709"]


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def soft_mask(shape, box, pad, sigma):
    x, y, w, h = box
    m = np.zeros(shape[:2], np.float32)
    cv2.ellipse(m, (int(x + w / 2), int(y + h / 2)), (int(w * (0.5 + pad)), int(h * (0.5 + pad))), 0, 0, 360, 1, -1)
    return cv2.GaussianBlur(m, (0, 0), sigma) if sigma else m


def remove(frame, box, pad=0.38, scale=None):
    """Efface le logo posé sur le mur bordeaux.

    Le mur est reconstruit par un dégradé (plan de couleur ajusté sur les pixels
    bordeaux autour du logo). Le mur blanc voisin, détecté ligne par ligne,
    n'est jamais modifié : aucune traînée grise.
    """
    H, W = frame.shape[:2]
    x, y, w, h = box
    ax, ay = w * (0.5 + pad), h * (0.5 + pad)
    cx, cy = x + w / 2, y + h / 2
    x0, x1 = int(max(0, cx - ax * 1.5)), int(min(W, cx + ax * 1.5))
    y0, y1 = int(max(0, cy - ay * 1.4)), int(min(H, cy + ay * 1.4))
    if x1 - x0 < 8 or y1 - y0 < 8:
        return frame
    roi = frame[y0:y1, x0:x1].astype(np.float32)
    b, g, r = roi[..., 0], roi[..., 1], roi[..., 2]
    red = (r > g * 1.15 + 4) & (r > b * 1.05) & (r < 235)
    mx, mn = roi.max(-1), roi.min(-1)
    whiteish = (mn > 140) & (mx - mn < 40)
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    ell = ((xx - cx) / ax) ** 2 + ((yy - cy) / ay) ** 2
    inside = ell <= 1.0
    # bord gauche du mur bordeaux : droite ajustée sur le premier pixel bordeaux de chaque ligne.
    # Tout ce qui est à gauche (mur blanc, porte) reste intact.
    cols = np.arange(red.shape[1])[None, :]
    rows = np.where(red.sum(1) > 6)[0]
    if len(rows) < 10:
        return frame
    fr = red[rows].argmax(1).astype(np.float32)
    med = np.median(fr)
    ok = np.abs(fr - med) < 60
    a, c = np.polyfit(rows[ok], fr[ok], 1) if ok.sum() > 5 else (0.0, med)
    edge = a * np.arange(red.shape[0]) + c
    white_wall = cols < (edge[:, None] + 2)
    # plan de couleur ajusté sur l'anneau bordeaux autour du logo
    ring = (ell > 1.05) & (ell < 2.2) & red
    if ring.sum() < 50:
        return frame
    A_ = np.stack([xx[ring], yy[ring], np.ones(ring.sum())], 1)
    fill = np.zeros_like(roi)
    for c in range(3):
        coef, *_ = np.linalg.lstsq(A_, roi[..., c][ring], rcond=None)
        fill[..., c] = coef[0] * xx + coef[1] * yy + coef[2]
    rng = np.random.default_rng(0)
    fill += rng.normal(0, 1.2, fill.shape[:2])[..., None]
    m = inside.astype(np.float32)
    m = cv2.GaussianBlur(m, (0, 0), max(4, min(ax, ay) * 0.12))
    keep = cv2.GaussianBlur(white_wall.astype(np.float32), (0, 0), 2.5)
    m = m * (1 - keep)
    out = frame.copy()
    out[y0:y1, x0:x1] = np.clip(roi * (1 - m[..., None]) + fill * m[..., None], 0, 255).astype(np.uint8)
    return out


def track_logo(path, init_box, last_tracked, last_frame):
    cap = cv2.VideoCapture(str(path))
    ok, f = cap.read()
    tr = cv2.TrackerCSRT_create()
    tr.init(f, init_box)
    boxes = [list(init_box)]
    for _ in range(1, last_tracked + 1):
        ok, f = cap.read()
        ok2, b = tr.update(f)
        boxes.append([float(v) for v in b] if ok2 else boxes[-1])
    arr = np.array(boxes)
    # lissage temporel (évite le tremblement du masque)
    k = 5
    sm = np.array([arr[max(0, i - k): i + k + 1].mean(0) for i in range(len(arr))])
    # extrapolation jusqu'à la sortie du cadre
    v = (arr[-1] - arr[-9]) / 8  # vitesse réelle (non lissée) des dernières images
    v[2:] = 0
    ext = [arr[-1] + v * (j + 1) for j in range(last_frame - last_tracked)]
    return np.vstack([sm, ext]) if ext else sm


def process_video(src, dst, logo=None):
    sdr = TMP / (src.stem + "_sdr.mp4")
    ffmpeg("-i", str(src), "-vf", SDR, *TAGS, "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-an", str(sdr))
    if not logo:
        ffmpeg("-i", str(sdr), "-c:v", "libx264", "-crf", "17", "-preset", "slow", *TAGS, "-movflags", "+faststart", str(dst))
        return
    boxes = track_logo(sdr, **logo)
    json.dump(boxes.tolist(), open(TMP / (src.stem + "_logo_boxes.json"), "w"))
    cap = cv2.VideoCapture(str(sdr))
    w, h = int(cap.get(3)), int(cap.get(4))
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", "30", "-i", "-",
         "-c:v", "libx264", "-crf", "17", "-preset", "slow", "-pix_fmt", "yuv420p", *TAGS, "-movflags", "+faststart", str(dst)],
        stdin=subprocess.PIPE,
    )
    i = 0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        if i < len(boxes):
            x, y, bw, bh = boxes[i]
            if x < w:  # logo encore (partiellement) dans le cadre
                f = remove(f, (x, y, bw, bh))
        enc.stdin.write(f.tobytes())
        i += 1
    enc.stdin.close()
    enc.wait()


def process_photo(src, dst, logo_box=None, max_side=2400):
    img = cv2.imread(str(src))
    if logo_box:
        img = remove(img, logo_box, pad=0.22)
    s = max_side / max(img.shape[:2])
    if s < 1:
        img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(dst), img, [cv2.IMWRITE_JPEG_QUALITY, 92])


if __name__ == "__main__":
    process_video(SRC / "avant_video-447.mov", A / "videos/avant/avant.mp4")
    process_video(
        SRC / "apres_video-610.mov",
        A / "videos/apres/apres.mp4",
        logo=dict(init_box=(1070, 680, 160, 260), last_tracked=60, last_frame=72),
    )
    (A / "images/photos").mkdir(parents=True, exist_ok=True)
    process_photo(SRC / "IMG_7681_avant.jpg", A / "images/photos/avant-piece-vide.jpg")
    process_photo(SRC / "IMG_7696_tracage.jpg", A / "images/photos/pendant-tracage-au-sol.jpg")
    process_photo(SRC / "IMG_7769_face_led.jpg", A / "images/bureau-final.jpg")
    process_photo(SRC / "IMG_7770_vue_dessus.jpg", A / "images/photos/apres-vue-dessus.jpg")
    process_photo(SRC / "IMG_7771_interieur.jpg", A / "images/photos/apres-interieur.jpg", logo_box=(430, 185, 435, 400))
    print("médias prêts")
