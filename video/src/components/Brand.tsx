import React from "react";
import { useCurrentFrame } from "remotion";
import { content, tw } from "../lib";
import { C, F, SAFE } from "../theme";

/**
 * Icône DOMOVA redessinée en vectoriel d'après le logo fourni :
 * arche crème, arche intérieure or, ligne de sol, monogramme D (optionnel).
 * `draw` (0→1) anime le tracé des traits.
 */
export const ArchIcon: React.FC<{ size: number; draw?: number; withD?: boolean; cream?: string; gold?: string }> = ({
  size,
  draw = 1,
  withD = false,
  cream = C.creme,
  gold = C.or,
}) => {
  const outer = "M 396 750 L 396 482 A 144 144 0 0 1 684 482 L 684 750";
  const inner = "M 448.5 750 L 448.5 482 A 91.5 91.5 0 0 1 631.5 482 L 631.5 750";
  const L1 = 1000;
  const L2 = 700;
  return (
    <svg width={size} height={(size * 480) / 520} viewBox="280 310 520 480" style={{ overflow: "visible" }}>
      <path d={outer} fill="none" stroke={cream} strokeWidth={26} strokeDasharray={L1} strokeDashoffset={L1 * (1 - draw)} />
      <path d={inner} fill="none" stroke={gold} strokeWidth={11} strokeDasharray={L2} strokeDashoffset={L2 * (1 - tw(draw, [0.2, 1], [0, 1]))} />
      <rect x={295} y={750} width={490 * tw(draw, [0.4, 1], [0, 1])} height={27} fill={cream} />
      {withD ? (
        <text x={540} y={652} textAnchor="middle" fontFamily={F.sans} fontWeight={500} fontSize={150} fill={cream} opacity={tw(draw, [0.7, 1], [0, 1])}>
          D
        </text>
      ) : null}
    </svg>
  );
};

/** Logotype « DOMOVA » : capitales Jost très espacées, comme sur la charte. */
export const Logo: React.FC<{ height: number; color?: string; tracking?: number }> = ({ height, color = C.creme, tracking = 0.42 }) => (
  <div
    style={{
      fontFamily: F.sans,
      fontWeight: 400,
      fontSize: height,
      lineHeight: 1,
      letterSpacing: `${tracking}em`,
      marginRight: `-${tracking}em`,
      color,
      whiteSpace: "nowrap",
    }}
  >
    {content.brand.name}
  </div>
);

/** Bloc logo complet : icône, logotype, signature métier. */
export const LogoLockup: React.FC<{ scale?: number; draw?: number; tagline?: string; textO?: number }> = ({
  scale = 1,
  draw = 1,
  tagline = "CONSTRUCTION · RÉNOVATION · AMÉNAGEMENT",
  textO = 1,
}) => (
  <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
    <ArchIcon size={150 * scale} draw={draw} />
    <div style={{ marginTop: 46 * scale, opacity: textO }}>
      <Logo height={86 * scale} />
    </div>
    <div
      style={{
        marginTop: 26 * scale,
        fontFamily: F.sans,
        fontWeight: 500,
        fontSize: 21 * scale,
        letterSpacing: "0.28em",
        marginRight: "-0.28em",
        color: C.creme,
        opacity: textO,
        whiteSpace: "nowrap",
      }}
    >
      {tagline}
    </div>
  </div>
);

/** Signature discrète en haut à gauche de la zone sûre (icône + logotype) et titre de chapitre. */
export const BrandBug: React.FC<{ chapter?: string; delay?: number }> = ({ chapter, delay = 6 }) => {
  const frame = useCurrentFrame();
  const o = tw(frame, [delay, delay + 14], [0, 1]);
  return (
    <div style={{ position: "absolute", left: SAFE.left, top: SAFE.top + 18, opacity: o, filter: "drop-shadow(0 1px 6px rgba(0,0,0,0.5))" }}>
      <div style={{ display: "flex", alignItems: "flex-end", gap: 14, opacity: 0.9 }}>
        <ArchIcon size={34} />
        <Logo height={27} />
      </div>
      {chapter ? (
        <div
          style={{
            marginTop: 14,
            fontFamily: F.sans,
            fontSize: 20,
            fontWeight: 500,
            letterSpacing: 5,
            color: C.or,
            transform: `translateX(${tw(frame, [delay + 4, delay + 22], [-16, 0])}px)`,
            opacity: tw(frame, [delay + 4, delay + 22], [0, 1]),
          }}
        >
          {chapter}
        </div>
      ) : null}
    </div>
  );
};

/** Arche fine décorative (motif de l'affiche DOMOVA). */
export const ArchFrame: React.FC<{ x: number; y: number; w: number; h: number; color?: string; width?: number; draw?: number }> = ({
  x,
  y,
  w,
  h,
  color = C.arche,
  width = 2,
  draw = 1,
}) => {
  const r = w / 2;
  const d = `M ${x} ${y + h} L ${x} ${y + r} A ${r} ${r} 0 0 1 ${x + w} ${y + r} L ${x + w} ${y + h}`;
  const len = 2 * (h - r) + Math.PI * r;
  return (
    <svg width={1080} height={1920} style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
      <path d={d} fill="none" stroke={color} strokeWidth={width} strokeDasharray={len} strokeDashoffset={len * (1 - draw)} />
    </svg>
  );
};

/** clip-path CSS en forme d'arche (pour les révélations façon « porte »). */
export const archClip = (cx: number, bottom: number, w: number, h: number) => {
  const r = w / 2;
  const x0 = cx - r;
  const x1 = cx + r;
  const top = bottom - h;
  return `path('M ${x0} ${bottom} L ${x0} ${top + r} A ${r} ${r} 0 0 1 ${x1} ${top + r} L ${x1} ${bottom} Z')`;
};
