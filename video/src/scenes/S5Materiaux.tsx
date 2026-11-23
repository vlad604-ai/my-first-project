import React from "react";
import { AbsoluteFill, Sequence, useCurrentFrame } from "remotion";
import { ArchFrame, BrandBug } from "../components/Brand";
import { Callout, CutoutDesk, CutoutOnStage, layout, STAGE, StudioBackdrop } from "../components/Showcase";
import { Subtitles } from "../components/Subtitles";
import { Swatch } from "../components/Swatch";
import { content, easeInOut, sec, tw } from "../lib";
import { C, F, SAFE, SAFE_W } from "../theme";

const S = content.scenes.s5;
const MAT_F = 26; // ≈ 0,9 s par matériau
const REAL_F = 80; // ≈ 2,7 s par réalisation

const Price: React.FC<{ level: number }> = ({ level }) => (
  <span style={{ letterSpacing: 6 }}>
    {[1, 2, 3, 4].map((i) => (
      <span key={i} style={{ color: i <= level ? C.led : "rgba(255,255,255,0.25)" }}>
        €
      </span>
    ))}
  </span>
);

const MaterialCard: React.FC<{ i: number }> = ({ i }) => {
  const frame = useCurrentFrame();
  const m = content.materials[i];
  const reveal = tw(frame, [0, 9], [100, 0], easeInOut);
  const textO = tw(frame, [4, 12], [0, 1]);
  return (
    <AbsoluteFill style={{ clipPath: `inset(${reveal}% 0 0 0)` }}>
      <AbsoluteFill style={{ transform: `scale(${tw(frame, [0, MAT_F + 8], [1.25, 1.1], (t) => t)})` }}>
        <Swatch id={m.id} kind={m.kind} colors={m.colors} texture={m.texture} pan={-frame * 3} />
      </AbsoluteFill>
      {/* chant du panneau : rappel de l'épaisseur et de la finition */}
      <div style={{ position: "absolute", left: 0, right: 0, top: 1500, height: 34, background: "rgba(0,0,0,0.25)", borderTop: "2px solid rgba(255,255,255,0.35)" }} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,0) 35%, rgba(0,0,0,0.55) 62%, rgba(0,0,0,0.1) 85%)" }} />
      <div style={{ position: "absolute", left: SAFE.left, width: SAFE_W, top: 860, opacity: textO, transform: `translateY(${(1 - textO) * 18}px)`, color: C.blanc }}>
        <div style={{ fontFamily: F.sans, fontSize: 24, letterSpacing: 6, color: C.beige }}>
          {String(i + 1).padStart(2, "0")} / {String(content.materials.length).padStart(2, "0")}
        </div>
        <div style={{ fontFamily: F.serif, fontWeight: 300, fontSize: 67, lineHeight: 1.02, marginTop: 10 }}>{m.name}</div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 16, fontFamily: F.sans, fontSize: 30 }}>
          <span style={{ color: "#e6e1d8" }}>{m.detail}</span>
          <span style={{ fontSize: 34, fontWeight: 600 }}>
            <Price level={m.price} />
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

type Realisation = (typeof content.bureaux.realisations)[number];

/** Une réalisation : détourée sur fond studio, annotations, puis zoom sur son détail signature. */
const RealisationCard: React.FC<{ r: Realisation; i: number; n: number }> = ({ r, i, n }) => {
  const f = useCurrentFrame();
  const desk = r as unknown as CutoutDesk;
  const L = layout(desk);
  const enter = tw(f, [0, 12], [0, 1]);
  const zt = tw(f, [42, 62], [0, 1], easeInOut);
  const P = L.pt(r.detail.x, r.detail.y);
  const z = 1 + (r.detail.zoom - 1) * zt;
  const dx = (STAGE.cx - P.x) * zt;
  const dy = (STAGE.cy - P.y) * zt;
  const calloutsO = tw(f, [36, 44], [1, 0]);
  return (
    <AbsoluteFill>
      <StudioBackdrop horizon={L.box.y + L.box.h - 10} />
      <AbsoluteFill style={{ transformOrigin: `${P.x}px ${P.y}px`, transform: `translate(${dx}px, ${dy + (1 - enter) * 40}px) scale(${z})`, opacity: enter }}>
        <CutoutOnStage desk={desk} />
      </AbsoluteFill>
      <AbsoluteFill style={{ opacity: calloutsO }}>
        {r.callouts.map((c, k) => {
          const pt = L.pt(c.x, c.y);
          const labelY = c.side === "top" ? L.box.y - 50 : L.box.y + L.box.h + 55;
          return <Callout key={k} x={pt.x} y={pt.y} labelY={labelY} label={c.label} p={tw(f, [8 + k * 12, 24 + k * 12], [0, 1])} />;
        })}
      </AbsoluteFill>
      <div style={{ position: "absolute", left: SAFE.left, width: SAFE_W, top: 370, textAlign: "center", opacity: enter }}>
        <div style={{ fontFamily: F.sans, fontSize: 22, letterSpacing: 6, color: C.beige }}>
          NOS RÉALISATIONS · {String(i + 1).padStart(2, "0")} / {String(n).padStart(2, "0")}
        </div>
        <div style={{ fontFamily: F.serif, fontWeight: 300, fontSize: 53, color: C.blanc, marginTop: 4, lineHeight: 1.05 }}>{r.name}</div>
        <div style={{ fontFamily: F.sans, fontSize: 26, color: "#cfc8bd", marginTop: 8 }}>{r.subtitle}</div>
      </div>
      {zt > 0 ? (
        <div style={{ position: "absolute", left: SAFE.left, top: 1120, opacity: tw(f, [52, 62], [0, 1]), display: "flex", alignItems: "center", gap: 18 }}>
          <div style={{ width: tw(f, [52, 66], [0, 70]), height: 2, background: C.led }} />
          <div style={{ fontFamily: F.serif, fontWeight: 300, fontSize: 46, color: C.blanc, padding: "2px 20px 8px", borderRadius: 12, background: "rgba(43,12,19,0.7)" }}>{r.detail.label}</div>
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

const Realisations: React.FC = () => {
  const list = content.bureaux.realisations;
  return (
    <>
      {list.map((r, i) => (
        <Sequence key={r.id} from={i * REAL_F} durationInFrames={REAL_F}>
          <RealisationCard r={r} i={i} n={list.length} />
        </Sequence>
      ))}
    </>
  );
};

const PriceCard: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse 80% 60% at 50% 45%, #5C1B29 0%, ${C.bordeaux} 50%, ${C.bordeauxNuit} 100%)` }}>
      <ArchFrame x={175} y={380} w={730} h={1060} color={C.arche} width={2.5} draw={tw(frame, [0, 30], [0, 1])} />
      <div style={{ position: "absolute", left: SAFE.left, width: SAFE_W, top: 600, textAlign: "center", color: C.blanc }}>
        <div style={{ fontFamily: F.sans, fontSize: 22, letterSpacing: 7, color: C.or, opacity: tw(frame, [0, 10], [0, 1]) }}>UN BUREAU · UN BUDGET</div>
        <div style={{ fontFamily: F.sans, fontWeight: 300, fontSize: 66, lineHeight: 1.12, marginTop: 20, opacity: tw(frame, [4, 16], [0, 1]) }}>{S.priceNote}</div>
        <div style={{ marginTop: 50, display: "flex", flexDirection: "column", gap: 10, alignItems: "center" }}>
          {S.priceFactors.map((f, i) => {
            const o = tw(frame, [12 + i * 7, 22 + i * 7], [0, 1]);
            return (
              <div
                key={f}
                style={{
                  opacity: o,
                  transform: `translateY(${(1 - o) * 16}px)`,
                  fontFamily: F.sans,
                  fontSize: 30,
                  fontWeight: 400,
                  letterSpacing: "0.22em",
                  width: 520,
                  padding: "16px 0",
                  borderBottom: "1px solid rgba(201,164,106,0.4)",
                  textTransform: "uppercase",
                }}
              >
                {f}
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** SCÈNE 5 — Matériaux (macros verticales) → vos réalisations, une par une → le prix dépend du projet. */
export const S5Materiaux: React.FC = () => {
  const nM = content.materials.length;
  const aF = nM * MAT_F;
  const bF = content.bureaux.realisations.length * REAL_F;
  return (
    <AbsoluteFill style={{ backgroundColor: C.noir }}>
      {content.materials.map((_, i) => (
        <Sequence key={i} from={i * MAT_F} durationInFrames={MAT_F + 10}>
          <MaterialCard i={i} />
        </Sequence>
      ))}
      <Sequence from={aF} durationInFrames={bF}>
        <Realisations />
      </Sequence>
      <Sequence from={aF + bF}>
        <PriceCard />
      </Sequence>
      <BrandBug chapter={S.chapter} />
      <Subtitles lines={S.subtitles} />
    </AbsoluteFill>
  );
};

export const S5_MIN_FRAMES = content.materials.length * MAT_F + content.bureaux.realisations.length * REAL_F + sec(2.5);
