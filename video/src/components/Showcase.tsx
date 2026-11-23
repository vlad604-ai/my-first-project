import React from "react";
import { AbsoluteFill, Img } from "remotion";
import { file, has } from "../lib";
import { C, F, SAFE, SAFE_W, W } from "../theme";
import { ArchFrame } from "./Brand";

/** Bureau détouré : fichier, taille d'origine et cadre utile (bbox) du détourage. */
export type CutoutDesk = { cutout: string; lines?: string; size: number[]; bbox: number[]; led?: boolean };

/** Zone de présentation dans l'image 1080×1920 (entre le titre et les sous-titres). */
export const STAGE = { cx: W / 2, cy: 880, w: 900, h: 520 };

/** Calcule où se trouve le bureau à l'écran, pour placer annotations et zooms. */
export const layout = (d: CutoutDesk, stage = STAGE) => {
  const [x0, y0, x1, y1] = d.bbox;
  const bw = x1 - x0;
  const bh = y1 - y0;
  const k = Math.min(stage.w / bw, stage.h / bh);
  const left = stage.cx - (x0 + bw / 2) * k;
  const top = stage.cy - (y0 + bh / 2) * k;
  return {
    k,
    left,
    top,
    width: d.size[0] * k,
    height: d.size[1] * k,
    box: { x: stage.cx - (bw * k) / 2, y: stage.cy - (bh * k) / 2, w: bw * k, h: bh * k },
    /** point (0–1 dans le bbox) → pixels écran */
    pt: (u: number, v: number) => ({ x: stage.cx + (u - 0.5) * bw * k, y: stage.cy + (v - 0.5) * bh * k }),
  };
};

/** Fond studio aux couleurs DOMOVA : bordeaux profond, arche fine en fond, sol qui s'assombrit. */
export const StudioBackdrop: React.FC<{ horizon: number; warm?: number }> = ({ horizon, warm = 1 }) => (
  <AbsoluteFill>
    <AbsoluteFill style={{ background: `radial-gradient(ellipse 85% 55% at 50% 40%, rgba(110,38,52,${0.9 * warm}) 0%, ${C.bordeaux} 45%, ${C.bordeauxNuit} 100%)` }} />
    <ArchFrame x={200} y={330} w={680} h={horizon - 330} color="rgba(201,164,106,0.28)" width={2} />
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        top: horizon,
        bottom: 0,
        background: `linear-gradient(180deg, #3A101A 0%, ${C.bordeauxFonce} 45%, ${C.bordeauxNuit} 100%)`,
      }}
    />
    <div style={{ position: "absolute", left: 0, right: 0, top: horizon - 1, height: 2, background: "rgba(201,164,106,0.25)" }} />
  </AbsoluteFill>
);

/** Le bureau détouré posé dans le studio : ombre portée, reflet au sol, halo LED éventuel. */
export const CutoutOnStage: React.FC<{ desk: CutoutDesk; opacity?: number; ledGlow?: number }> = ({ desk, opacity = 1, ledGlow }) => {
  if (!has(desk.cutout)) {
    return (
      <div style={{ position: "absolute", left: SAFE.left, width: SAFE_W, top: 760, textAlign: "center", color: C.beige, fontFamily: F.sans, fontSize: 26 }}>
        Détourage manquant : /assets/{desk.cutout}
      </div>
    );
  }
  const L = layout(desk);
  const bottom = L.box.y + L.box.h;
  const glow = ledGlow ?? (desk.led ? 1 : 0);
  const img: React.CSSProperties = { position: "absolute", left: L.left, top: L.top, width: L.width, height: L.height };
  return (
    <AbsoluteFill style={{ opacity }}>
      {/* ombre de contact */}
      <div
        style={{
          position: "absolute",
          left: L.box.x - 30,
          width: L.box.w + 60,
          top: bottom - 30,
          height: 70,
          borderRadius: "50%",
          background: "radial-gradient(ellipse at center, rgba(0,0,0,0.75) 0%, rgba(0,0,0,0) 70%)",
          filter: "blur(6px)",
        }}
      />
      {/* halo LED au sol */}
      {glow > 0 ? (
        <div
          style={{
            position: "absolute",
            left: L.box.x - 60,
            width: L.box.w + 120,
            top: bottom - 50,
            height: 130,
            borderRadius: "50%",
            background: `radial-gradient(ellipse at center, rgba(255,205,140,${0.45 * glow}) 0%, rgba(255,205,140,0) 70%)`,
            mixBlendMode: "screen",
          }}
        />
      ) : null}
      {/* reflet */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          WebkitMaskImage: `linear-gradient(180deg, transparent ${bottom - 2}px, rgba(0,0,0,0.28) ${bottom}px, transparent ${bottom + L.box.h * 0.35}px)`,
        }}
      >
        <Img src={file(desk.cutout)} style={{ ...img, transform: `scaleY(-1)`, transformOrigin: `50% ${bottom - L.top}px` }} />
      </div>
      <Img src={file(desk.cutout)} style={{ ...img, filter: "drop-shadow(0 18px 30px rgba(0,0,0,0.55))" }} />
    </AbsoluteFill>
  );
};

/** Annotation : point lumineux sur le détail + trait coudé + libellé centré dans la zone sûre. */
export const Callout: React.FC<{ x: number; y: number; labelY: number; label: string; p: number }> = ({ x, y, labelY, label, p }) => {
  if (p <= 0) return null;
  const cx = SAFE.left + SAFE_W / 2;
  const vLen = (labelY - y) * Math.min(1, p * 2);
  const hp = Math.max(0, p * 2 - 1);
  return (
    <>
      <svg width={W} height={1920} style={{ position: "absolute", inset: 0 }}>
        <circle cx={x} cy={y} r={9} fill={C.led} opacity={Math.min(1, p * 3)} />
        <circle cx={x} cy={y} r={20} fill="none" stroke={C.led} strokeWidth={2} opacity={0.5 * Math.min(1, p * 3)} />
        <line x1={x} y1={y} x2={x} y2={y + vLen} stroke={C.led} strokeWidth={2.5} />
        <line x1={x} y1={labelY} x2={x + (cx - x) * hp} y2={labelY} stroke={C.led} strokeWidth={2.5} opacity={hp > 0 ? 1 : 0} />
      </svg>
      <div style={{ position: "absolute", left: SAFE.left, width: SAFE_W, top: labelY - 28, display: "flex", justifyContent: "center", opacity: hp }}>
        <div
          style={{
            fontFamily: F.sans,
            fontSize: 30,
            fontWeight: 500,
            color: C.blanc,
            whiteSpace: "nowrap",
            padding: "8px 20px",
            background: "rgba(43,12,19,0.9)",
            border: `1px solid rgba(255,217,160,0.5)`,
            borderRadius: 10,
          }}
        >
          {label}
        </div>
      </div>
    </>
  );
};
