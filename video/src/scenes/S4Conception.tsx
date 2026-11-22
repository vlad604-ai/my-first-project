import React from "react";
import { AbsoluteFill, Img, Sequence, useCurrentFrame } from "remotion";
import { BrandBug } from "../components/Brand";
import { EmptyRoom, PlanCurved } from "../components/Drawings";
import { Media } from "../components/Media";
import { Callout, CutoutDesk, CutoutOnStage, layout, StudioBackdrop } from "../components/Showcase";
import { Subtitles } from "../components/Subtitles";
import { content, easeInOut, file, has, sec, tw } from "../lib";
import { C, F, SAFE, SAFE_W } from "../theme";

const S = content.scenes.s4;
const DESK = content.bureaux.arrondi as CutoutDesk;

/** Titre de l'option en cours, haut-centre de la zone sûre. */
const OptionTitle: React.FC<{ index: number; total: number; k: string; appear: number }> = ({ index, total, k, appear }) => (
  <div style={{ position: "absolute", left: SAFE.left, width: SAFE_W, top: 390, textAlign: "center", opacity: appear }}>
    <div style={{ fontFamily: F.sans, fontSize: 22, letterSpacing: 6, color: C.beige }}>
      PERSONNALISATION · {String(index + 1).padStart(2, "0")} / {String(total).padStart(2, "0")}
    </div>
    <div style={{ fontFamily: F.serif, fontSize: 76, color: C.blanc, marginTop: 4 }}>{k.charAt(0) + k.slice(1).toLowerCase()}</div>
  </div>
);

/** SCÈNE 4 — Conception : concepteur → plan du comptoir → du tracé à la réalisation réelle. */
export const S4Conception: React.FC = () => {
  const frame = useCurrentFrame();
  const shot = S.shots[0];
  const aF = sec(shot.durationSec);
  const planF = sec(3.0);
  const d3 = aF + planF;
  const f3 = frame - d3;
  const pf = frame - aF;
  const scan = tw(pf, [0, 22], [0, 1920], easeInOut);

  // du tracé doré à la photo
  const draw = tw(f3, [0, 60], [0, 1], (t) => t);
  const real = tw(f3, [50, 85], [0, 1]);
  const push = tw(f3, [0, sec(7.5)], [1.0, 1.06], (t) => t);
  const L = layout(DESK);
  const slot = 32;
  const o0 = 92;
  const optIndex = Math.min(S.options.length - 1, Math.max(0, Math.floor((f3 - o0) / slot)));
  const opt = S.options[optIndex];
  const local = f3 - o0 - optIndex * slot;
  const pt = L.pt(opt.x, opt.y);
  const labelY = L.box.y + L.box.h + 60;

  return (
    <AbsoluteFill style={{ backgroundColor: C.noir }}>
      <Sequence durationInFrames={aF}>
        <Media src={shot.src} push={[1.05, 1.15]} placeholder={{ id: shot.id, title: shot.title, source: shot.source }} />
      </Sequence>

      <Sequence from={aF} durationInFrames={planF + 12}>
        <AbsoluteFill>
          <PlanCurved p={tw(pf, [6, planF], [0, 1], (t) => t)} />
          <AbsoluteFill style={{ clipPath: `inset(${scan}px 0 0 0)` }}>
            <EmptyRoom />
          </AbsoluteFill>
          <div style={{ position: "absolute", left: 0, right: 0, top: scan - 2, height: 4, background: C.led, boxShadow: `0 0 30px ${C.led}`, opacity: scan < 1910 ? 1 : 0 }} />
        </AbsoluteFill>
      </Sequence>

      <Sequence from={d3}>
        <AbsoluteFill style={{ opacity: tw(f3, [0, 10], [0, 1]) }}>
          <StudioBackdrop horizon={L.box.y + L.box.h - 10} warm={0.4 + 0.6 * real} />
          <AbsoluteFill style={{ transform: `scale(${push})`, transformOrigin: "50% 46%" }}>
            {/* tracé d'architecte qui se dessine de gauche à droite */}
            {DESK.lines && has(DESK.lines) ? (
              <AbsoluteFill style={{ clipPath: `inset(0 ${(1 - draw) * 100}% 0 0)`, opacity: 1 - real * 0.85 }}>
                <Img src={file(DESK.lines)} style={{ position: "absolute", left: L.left, top: L.top, width: L.width, height: L.height }} />
              </AbsoluteFill>
            ) : null}
            {draw < 1 ? (
              <div style={{ position: "absolute", top: L.box.y - 60, height: L.box.h + 120, left: L.box.x + L.box.w * draw - 2 + (L.box.x - L.box.x), width: 3, background: C.led, boxShadow: `0 0 24px ${C.led}`, opacity: 0.9 }} />
            ) : null}
            <CutoutOnStage desk={DESK} opacity={real} ledGlow={real} />
            {f3 >= o0 ? <Callout x={pt.x} y={pt.y} labelY={labelY} label={opt.value} p={tw(local, [0, 16], [0, 1])} /> : null}
          </AbsoluteFill>
          {f3 < o0 ? (
            <div style={{ position: "absolute", left: SAFE.left, width: SAFE_W, top: 390, textAlign: "center", opacity: tw(f3, [8, 20], [0, 1]) * tw(f3, [o0 - 10, o0], [1, 0]) }}>
              <div style={{ fontFamily: F.sans, fontSize: 22, letterSpacing: 6, color: C.beige }}>DU PLAN À LA RÉALISATION</div>
              <div style={{ fontFamily: F.serif, fontSize: 72, color: C.blanc, marginTop: 4 }}>{content.bureaux.arrondi.name}</div>
            </div>
          ) : (
            <OptionTitle index={optIndex} total={S.options.length} k={opt.key} appear={tw(local, [0, 8], [0, 1])} />
          )}
        </AbsoluteFill>
      </Sequence>

      <BrandBug chapter={S.chapter} />
      <Subtitles lines={S.subtitles} />
    </AbsoluteFill>
  );
};
