import React from "react";
import { AbsoluteFill, Sequence, useCurrentFrame } from "remotion";
import { BrandBug } from "../components/Brand";
import { DeskScene, DeskSpec } from "../components/Desk3D";
import { EmptyRoom, Plan2D } from "../components/Drawings";
import { Media } from "../components/Media";
import { Subtitles } from "../components/Subtitles";
import { content, easeInOut, sec, tw } from "../lib";
import { C, F, SAFE, SAFE_W } from "../theme";

const S = content.scenes.s4;

/** Carte d'option façon configurateur, placée haut-centre dans la zone sûre. */
const OptionChip: React.FC<{ index: number; total: number; k: string; from: string; to: string; p: number; appear: number }> = ({
  index,
  total,
  k,
  from,
  to,
  p,
  appear,
}) => (
  <div style={{ position: "absolute", left: SAFE.left, width: SAFE_W, top: 380, display: "flex", justifyContent: "center", opacity: appear }}>
    <div
      style={{
        background: "rgba(13,13,14,0.78)",
        border: "1px solid rgba(255,217,160,0.45)",
        borderRadius: 18,
        padding: "22px 34px",
        minWidth: 640,
        fontFamily: F.sans,
        color: C.blanc,
        transform: `translateY(${(1 - appear) * 20}px)`,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 22, letterSpacing: 5, color: C.beige, fontWeight: 500 }}>
        <span>{k}</span>
        <span>
          {String(index + 1).padStart(2, "0")} / {String(total).padStart(2, "0")}
        </span>
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 22, marginTop: 10 }}>
        <span style={{ fontSize: 40, color: "#9b968e", textDecoration: p > 0.5 ? "line-through" : "none" }}>{from}</span>
        <span style={{ fontSize: 34, color: C.led }}>→</span>
        <span style={{ fontFamily: F.serif, fontSize: 66, fontWeight: 600, opacity: 0.25 + p * 0.75 }}>{to}</span>
      </div>
      <div style={{ height: 4, background: "rgba(255,255,255,0.12)", marginTop: 14, borderRadius: 2 }}>
        <div style={{ height: 4, width: `${p * 100}%`, background: C.led, borderRadius: 2 }} />
      </div>
    </div>
  </div>
);

/** SCÈNE 4 — Conception : concepteur → la pièce devient plan 2D → configurateur 3D. */
export const S4Conception: React.FC = () => {
  const frame = useCurrentFrame();
  const shot = S.shots[0];
  const aF = sec(shot.durationSec);
  const planF = sec(3.0);
  const d3 = aF + planF;
  const f3 = frame - d3;

  // calendrier des options (en images, relatif au début de la 3D)
  const slot = 36;
  const step = (i: number) => tw(f3, [i * slot + 4, i * slot + 26], [0, 1], easeInOut);
  const spec: DeskSpec = {
    length: 1.6 + 0.8 * step(0),
    shape: "L",
    lAmount: step(1),
    legs: "panel",
    finish: step(5) > 0.5 ? "noyer" : "chene",
    drawers: 3,
    drawerOpen: step(2) * (1 - tw(f3, [3 * slot + 10, 3 * slot + 30], [0, 1])),
    shelves: 3,
    shelfGrow: step(3),
    led: step(4),
  };
  const evening = step(4) > 0.5;
  const angle = tw(f3, [0, sec(7.5)], [0.95, 0.55], (t) => t); // vue 3/4 : profondeur plutôt que largeur
  const dist = tw(f3, [0, sec(7.5)], [6.6, 5.6], (t) => t);
  const cam = {
    pos: [Math.sin(angle) * dist + 0.4, 1.7, Math.cos(angle) * dist + 0.4] as [number, number, number],
    target: [0.4, 0.8, 0.35] as [number, number, number],
    fov: 44,
  };
  const optIndex = Math.min(S.options.length - 1, Math.max(0, Math.floor((f3 - 2) / slot)));
  const opt = S.options[optIndex];

  // transition pièce → plan
  const pf = frame - aF;
  const scan = tw(pf, [0, 22], [0, 1920], easeInOut);

  return (
    <AbsoluteFill style={{ backgroundColor: C.noir }}>
      <Sequence durationInFrames={aF}>
        <Media src={shot.src} push={[1.05, 1.15]} placeholder={{ id: shot.id, title: shot.title, source: shot.source }} />
      </Sequence>

      <Sequence from={aF} durationInFrames={planF + 12}>
        <AbsoluteFill>
          <Plan2D p={tw(pf, [6, planF], [0, 1], (t) => t)} />
          {/* la pièce s'efface sous un balayage façon calque d'architecte */}
          <AbsoluteFill style={{ clipPath: `inset(${scan}px 0 0 0)` }}>
            <EmptyRoom />
          </AbsoluteFill>
          <div style={{ position: "absolute", left: 0, right: 0, top: scan - 2, height: 4, background: C.led, boxShadow: `0 0 30px ${C.led}`, opacity: scan < 1910 ? 1 : 0 }} />
        </AbsoluteFill>
      </Sequence>

      <Sequence from={d3}>
        <AbsoluteFill style={{ opacity: tw(f3, [0, 12], [0, 1]) }}>
          <DeskScene spec={spec} cam={cam} mood={evening ? "evening" : "day"} />
          <OptionChip index={optIndex} total={S.options.length} k={opt.key} from={opt.from} to={opt.to} p={step(optIndex)} appear={tw(f3, [0, 14], [0, 1])} />
        </AbsoluteFill>
      </Sequence>

      <BrandBug chapter={S.chapter} />
      <Subtitles lines={S.subtitles} />
    </AbsoluteFill>
  );
};
