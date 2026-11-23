import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { content, easeInOut, tw } from "../lib";
import { C, F, H, SAFE, SAFE_W, W } from "../theme";
import { ArchFrame, archClip } from "./Brand";

/**
 * Illustrations au trait (crème et or sur bordeaux) qui remplacent les plans
 * à tourner ou à générer. Si une vraie vidéo est déposée au même emplacement,
 * elle prend automatiquement la place de l'illustration.
 */

/** Trait qui se dessine : pathLength normalisé à 1. */
const Stroke: React.FC<{ d: string; p: number; color?: string; w?: number; fill?: string }> = ({ d, p, color = C.creme, w = 2.5, fill = "none" }) =>
  p <= 0 ? null : <path d={d} pathLength={1} strokeDasharray={1} strokeDashoffset={1 - Math.min(1, p)} stroke={color} strokeWidth={w} fill={fill} strokeLinecap="round" />;

const Backdrop: React.FC = () => (
  <AbsoluteFill style={{ background: `radial-gradient(ellipse 90% 60% at 50% 40%, #5C1B29 0%, ${C.bordeaux} 50%, ${C.bordeauxNuit} 100%)` }} />
);

/* ------------------------------------------------------------------ */
/* S1-B — Façade haussmannienne du 14e qui se dessine, descente vers   */
/* la porte cochère en arche (rappel du logo).                         */
/* ------------------------------------------------------------------ */
export const FacadeScene: React.FC = () => {
  const f = useCurrentFrame();
  const { durationInFrames: D } = useVideoConfig();
  const TOTAL = 2500;
  const dy = tw(f, [0, D], [0, -(TOTAL - H)], easeInOut);
  const p = (a: number, b: number) => tw(f, [a, b], [0, 1], (t) => t);
  const floors = [0, 1, 2, 3, 4];
  const cols = [290, 540, 790];
  const fTop = (i: number) => 380 + i * 300;
  return (
    <AbsoluteFill>
      <Backdrop />
      <svg width={W} height={TOTAL} viewBox={`0 0 ${W} ${TOTAL}`} style={{ position: "absolute", left: 0, top: dy }}>
        {/* toit en zinc et lucarnes */}
        <Stroke d="M 190 130 L 890 130 L 950 340 L 130 340 Z" p={p(0, 20)} />
        {cols.map((x, i) => (
          <Stroke key={`l${i}`} d={`M ${x - 40} 320 L ${x - 40} 230 A 40 40 0 0 1 ${x + 40} 230 L ${x + 40} 320`} p={p(4 + i * 2, 22 + i * 2)} color={C.or} />
        ))}
        <Stroke d="M 120 355 L 960 355 M 120 370 L 960 370" p={p(6, 24)} />
        {/* étages : fenêtres, moulures, balcons */}
        {floors.map((i) => (
          <g key={i}>
            <Stroke d={`M 140 ${fTop(i)} L 940 ${fTop(i)}`} p={p(8 + i * 3, 26 + i * 3)} w={1.5} />
            {cols.map((x, k) => (
              <g key={k}>
                <Stroke d={`M ${x - 62} ${fTop(i) + 250} L ${x - 62} ${fTop(i) + 60} L ${x + 62} ${fTop(i) + 60} L ${x + 62} ${fTop(i) + 250}`} p={p(10 + i * 3 + k, 30 + i * 3 + k)} />
                <Stroke d={`M ${x} ${fTop(i) + 60} L ${x} ${fTop(i) + 250}`} p={p(14 + i * 3 + k, 32 + i * 3 + k)} w={1.2} />
                <Stroke d={`M ${x - 78} ${fTop(i) + 48} L ${x + 78} ${fTop(i) + 48}`} p={p(12 + i * 3 + k, 30 + i * 3 + k)} w={1.5} />
              </g>
            ))}
            {/* balcon filant aux 2e et 5e étages, balconnets ailleurs */}
            {i === 1 || i === 4 ? (
              <>
                <Stroke d={`M 150 ${fTop(i) + 205} L 930 ${fTop(i) + 205} M 150 ${fTop(i) + 250} L 930 ${fTop(i) + 250}`} p={p(16 + i * 3, 36 + i * 3)} color={C.or} />
                <Stroke d={Array.from({ length: 40 }, (_, j) => `M ${158 + j * 19.5} ${fTop(i) + 205} L ${158 + j * 19.5} ${fTop(i) + 250}`).join(" ")} p={p(20 + i * 3, 40 + i * 3)} color={C.or} w={1.2} />
              </>
            ) : (
              cols.map((x, k) => (
                <Stroke key={`b${k}`} d={`M ${x - 72} ${fTop(i) + 215} L ${x + 72} ${fTop(i) + 215} M ${x - 72} ${fTop(i) + 250} L ${x + 72} ${fTop(i) + 250} ${Array.from({ length: 8 }, (_, j) => `M ${x - 72 + j * 20.5} ${fTop(i) + 215} L ${x - 72 + j * 20.5} ${fTop(i) + 250}`).join(" ")}`} p={p(18 + i * 3 + k, 38 + i * 3 + k)} color={C.or} w={1.4} />
              ))
            )}
          </g>
        ))}
        {/* murs */}
        <Stroke d="M 140 370 L 140 2400 M 940 370 L 940 2400" p={p(4, 40)} />
        {/* rez-de-chaussée : porte cochère en arche + arcades */}
        <Stroke d="M 140 1890 L 940 1890 M 140 1910 L 940 1910" p={p(30, 50)} />
        <Stroke d="M 430 2400 L 430 2090 A 110 110 0 0 1 650 2090 L 650 2400" p={p(34, 58)} w={4} />
        <Stroke d="M 460 2400 L 460 2100 A 80 80 0 0 1 620 2100 L 620 2400" p={p(40, 62)} color={C.or} w={2.5} />
        <Stroke d="M 540 2020 L 540 2400" p={p(46, 64)} w={1.5} />
        {[250, 830].map((x) => (
          <Stroke key={x} d={`M ${x - 80} 2400 L ${x - 80} 2080 A 80 80 0 0 1 ${x + 80} 2080 L ${x + 80} 2400`} p={p(38, 60)} />
        ))}
        {/* trottoir et réverbère */}
        <Stroke d="M 0 2400 L 1080 2400 M 0 2440 L 1080 2440" p={p(44, 64)} />
        <Stroke d="M 1010 2400 L 1010 2060 M 985 2060 L 1035 2060 L 1025 2010 L 995 2010 Z" p={p(48, 66)} color={C.or} />
      </svg>
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------------ */
/* S2-A — La porte s'ouvre : « Un projet. Une envie. Un espace ? »     */
/* ------------------------------------------------------------------ */
export const DoorScene: React.FC = () => {
  const f = useCurrentFrame();
  const open = tw(f, [8, 40], [0, 1], easeInOut);
  const cx = 540;
  const bottom = 1300;
  const w = 560;
  const h = 860;
  const words = ["Un projet.", "Une envie.", "Un espace à aménager ?"];
  return (
    <AbsoluteFill>
      <Backdrop />
      {/* lumière chaude derrière la porte */}
      <AbsoluteFill style={{ clipPath: archClip(cx, bottom, w, h), background: `radial-gradient(ellipse at 50% 70%, rgba(255,222,170,${0.55 * open}) 0%, rgba(201,164,106,${0.25 * open}) 40%, ${C.bordeauxFonce} 85%)` }} />
      {/* battants */}
      <AbsoluteFill style={{ clipPath: archClip(cx, bottom, w, h), perspective: 1400 }}>
        {[0, 1].map((k) => (
          <div
            key={k}
            style={{
              position: "absolute",
              left: k === 0 ? cx - w / 2 : cx,
              top: bottom - h,
              width: w / 2,
              height: h,
              background: `linear-gradient(180deg, #3D101A, ${C.bordeauxFonce})`,
              borderLeft: k === 1 ? `2px solid ${C.or}` : undefined,
              transformOrigin: k === 0 ? "left center" : "right center",
              transform: `rotateY(${(k === 0 ? -1 : 1) * open * 80}deg)`,
              boxShadow: "inset 0 0 0 2px rgba(201,164,106,0.35)",
            }}
          >
            <div style={{ position: "absolute", left: 40, right: 40, top: 360, height: 200, border: `1.5px solid rgba(201,164,106,0.5)` }} />
            <div style={{ position: "absolute", left: 40, right: 40, top: 600, height: 200, border: `1.5px solid rgba(201,164,106,0.5)` }} />
          </div>
        ))}
      </AbsoluteFill>
      <ArchFrame x={cx - w / 2 - 22} y={bottom - h - 22} w={w + 44} h={h + 22} color={C.creme} width={5} />
      <ArchFrame x={cx - w / 2 - 6} y={bottom - h - 6} w={w + 12} h={h + 6} color={C.or} width={2} />
      <div style={{ position: "absolute", left: 120, right: 120, top: bottom, height: 3, background: C.creme }} />
      {/* les mots */}
      <div style={{ position: "absolute", left: SAFE.left, width: SAFE_W, top: 760, textAlign: "center" }}>
        {words.map((t, i) => {
          const a = tw(f, [34 + i * 22, 48 + i * 22], [0, 1]);
          return (
            <div key={t} style={{ fontFamily: F.sans, fontWeight: 300, fontSize: i === 2 ? 46 : 58, lineHeight: 1.5, color: i === 2 ? C.creme : C.creme, opacity: a, transform: `translateY(${(1 - a) * 14}px)`, textShadow: "0 2px 18px rgba(43,12,19,0.6)" }}>
              {t}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------------ */
/* S2-B — Nous venons chez vous : épingle + 3 engagements              */
/* ------------------------------------------------------------------ */
export const VisitScene: React.FC = () => {
  const f = useCurrentFrame();
  const drop = tw(f, [0, 16], [0, 1], easeInOut);
  const items = content.scenes.s2.promises;
  return (
    <AbsoluteFill>
      <Backdrop />
      <ArchFrame x={175} y={330} w={730} h={1080} color={C.arche} width={2.5} draw={tw(f, [0, 30], [0, 1])} />
      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
        <g transform={`translate(540 ${430 + (1 - drop) * -120})`} opacity={drop}>
          <path d="M 0 90 C -40 40 -52 18 -52 -6 A 52 52 0 1 1 52 -6 C 52 18 40 40 0 90 Z" fill="none" stroke={C.or} strokeWidth={4} />
          <circle cx={0} cy={-8} r={18} fill="none" stroke={C.creme} strokeWidth={3} />
        </g>
        <ellipse cx={540} cy={540} rx={60 * drop} ry={10 * drop} fill="none" stroke={C.or} strokeOpacity={0.5} strokeWidth={2} />
      </svg>
      <div style={{ position: "absolute", left: SAFE.left, width: SAFE_W, top: 590, textAlign: "center", opacity: tw(f, [12, 24], [0, 1]) }}>
        <div style={{ fontFamily: F.sans, fontSize: 22, letterSpacing: 6, color: C.or }}>{content.scenes.s2.visitKicker}</div>
        <div style={{ fontFamily: F.sans, fontWeight: 300, fontSize: 60, color: C.creme, marginTop: 8 }}>{content.scenes.s2.visitTitle}</div>
      </div>
      <div style={{ position: "absolute", left: SAFE.left + 60, width: SAFE_W - 120, top: 790 }}>
        {items.map((t, i) => {
          const a = tw(f, [26 + i * 14, 40 + i * 14], [0, 1]);
          return (
            <div key={t} style={{ display: "flex", gap: 24, alignItems: "baseline", padding: "22px 0", borderBottom: `1px solid rgba(201,164,106,${0.4 * a})`, opacity: a, transform: `translateX(${(1 - a) * -20}px)` }}>
              <div style={{ fontFamily: F.sans, fontSize: 26, letterSpacing: 4, color: C.or }}>{String(i + 1).padStart(2, "0")}</div>
              <div style={{ fontFamily: F.sans, fontWeight: 400, fontSize: 38, color: C.creme }}>{t}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------------ */
/* S4-A — Bureau d'études : écran où le comptoir se dessine, puis      */
/* zoom dans l'écran (enchaîne sur le plan).                           */
/* ------------------------------------------------------------------ */
export const StudioScreenScene: React.FC = () => {
  const f = useCurrentFrame();
  const { durationInFrames: D } = useVideoConfig();
  const p = (a: number, b: number) => tw(f, [a, b], [0, 1], (t) => t);
  const zoom = tw(f, [D - 26, D], [1, 3.4], easeInOut);
  const scr = { x: 170, y: 600, w: 740, h: 450 };
  const cx = scr.x + scr.w / 2;
  const cy = scr.y + scr.h / 2 + 20;
  return (
    <AbsoluteFill>
      <Backdrop />
      <AbsoluteFill style={{ transformOrigin: `${cx}px ${scr.y + scr.h / 2}px`, transform: `scale(${zoom})` }}>
        <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
          {/* écran */}
          <Stroke d={`M ${scr.x + 18} ${scr.y} L ${scr.x + scr.w - 18} ${scr.y} Q ${scr.x + scr.w} ${scr.y} ${scr.x + scr.w} ${scr.y + 18} L ${scr.x + scr.w} ${scr.y + scr.h - 18} Q ${scr.x + scr.w} ${scr.y + scr.h} ${scr.x + scr.w - 18} ${scr.y + scr.h} L ${scr.x + 18} ${scr.y + scr.h} Q ${scr.x} ${scr.y + scr.h} ${scr.x} ${scr.y + scr.h - 18} L ${scr.x} ${scr.y + 18} Q ${scr.x} ${scr.y} ${scr.x + 18} ${scr.y} Z`} p={p(0, 16)} w={4} />
          <Stroke d={`M ${cx} ${scr.y + scr.h} L ${cx} ${scr.y + scr.h + 90} M ${cx - 120} ${scr.y + scr.h + 90} L ${cx + 120} ${scr.y + scr.h + 90}`} p={p(6, 18)} w={4} />
          {/* interface du logiciel */}
          <Stroke d={`M ${scr.x + 20} ${scr.y + 46} L ${scr.x + scr.w - 20} ${scr.y + 46} M ${scr.x + 120} ${scr.y + 46} L ${scr.x + 120} ${scr.y + scr.h - 20}`} p={p(10, 22)} w={1.5} color="rgba(243,233,220,0.5)" />
          {[0, 1, 2, 3, 4].map((i) => (
            <Stroke key={i} d={`M ${scr.x + 36} ${scr.y + 80 + i * 40} L ${scr.x + 100} ${scr.y + 80 + i * 40}`} p={p(14 + i, 24 + i)} w={6} color="rgba(201,164,106,0.45)" />
          ))}
          {/* comptoir arrondi qui se trace dans l'écran */}
          <Stroke d={`M ${cx - 190 + 60} ${cy - 40} A 230 230 0 0 0 ${cx + 190 + 60} ${cy - 40} L ${cx + 140 + 60} ${cy - 40} A 180 180 0 0 1 ${cx - 140 + 60} ${cy - 40} Z`} p={p(18, 46)} color={C.or} w={3} />
          <Stroke d={`M ${cx - 220 + 60} ${cy + 140} L ${cx + 220 + 60} ${cy + 140}`} p={p(38, 52)} color={C.or} w={1.5} />
          {/* bureau, clavier, souris, lampe */}
          <Stroke d={`M 80 ${scr.y + scr.h + 150} L 1000 ${scr.y + scr.h + 150}`} p={p(4, 20)} />
          <Stroke d={`M 330 ${scr.y + scr.h + 112} L 750 ${scr.y + scr.h + 112} L 760 ${scr.y + scr.h + 140} L 320 ${scr.y + scr.h + 140} Z`} p={p(12, 26)} w={2} />
          <Stroke d={`M 820 ${scr.y + scr.h + 140} a 22 14 0 1 1 44 0 Z`} p={p(16, 26)} w={2} />
          <Stroke d={`M 130 ${scr.y + scr.h + 150} L 130 ${scr.y + scr.h - 40} L 210 ${scr.y + scr.h - 130} M 180 ${scr.y + scr.h - 160} L 250 ${scr.y + scr.h - 100}`} p={p(20, 34)} color={C.or} w={2.5} />
        </svg>
      </AbsoluteFill>
      <div style={{ position: "absolute", left: SAFE.left, width: SAFE_W, top: 470, textAlign: "center", fontFamily: F.sans, fontSize: 22, letterSpacing: 6, color: C.or, opacity: tw(f, [8, 20], [0, 1]) * Math.max(0, 1 - (zoom - 1) * 2) }}>
        {content.scenes.s4.studioLabel}
      </div>
    </AbsoluteFill>
  );
};
