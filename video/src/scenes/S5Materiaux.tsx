import React from "react";
import { AbsoluteFill, Sequence, useCurrentFrame } from "remotion";
import { BrandBug } from "../components/Brand";
import { DeskScene, DeskSpec } from "../components/Desk3D";
import { Subtitles } from "../components/Subtitles";
import { Swatch } from "../components/Swatch";
import { content, easeInOut, sec, tw } from "../lib";
import { C, F, SAFE, SAFE_W } from "../theme";

const S = content.scenes.s5;
const MAT_F = 31; // ≈ 1 s par matériau
const STYLE_F = 21; // ≈ 0,7 s par style de bureau

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
        <div style={{ fontFamily: F.serif, fontSize: 84, lineHeight: 1.02, marginTop: 10, fontWeight: 500 }}>{m.name}</div>
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

const StylesShowcase: React.FC = () => {
  const frame = useCurrentFrame();
  const n = content.deskStyles.length;
  const i = Math.min(n - 1, Math.floor(frame / STYLE_F));
  const style = content.deskStyles[i];
  const local = frame - i * STYLE_F;
  const angle = 0.75 + Math.sin(frame / 40) * 0.12 + (i % 2 ? -1.5 : 0); // alterne gauche/droite pour dynamiser
  const spec = { ...style.spec, drawerOpen: 0, shelfGrow: 1, lAmount: 1 } as DeskSpec;
  const L = spec.shape === "L" ? 2.6 : spec.length;
  const dist = 3.6 + L * 1.1;
  const flash = tw(local, [0, 4], [0.5, 0]);
  return (
    <AbsoluteFill>
      <DeskScene
        spec={spec}
        mood={spec.led > 0.5 ? "evening" : "day"}
        cam={{ pos: [Math.sin(angle) * dist, 1.6, Math.cos(angle) * dist + 0.3], target: [spec.shape === "L" ? 0.4 : 0, 0.62, 0.3], fov: 44 }}
      />
      <AbsoluteFill style={{ background: "#fff", opacity: flash }} />
      <div style={{ position: "absolute", left: SAFE.left, width: SAFE_W, top: 390, textAlign: "center" }}>
        <div style={{ fontFamily: F.sans, fontSize: 22, letterSpacing: 6, color: C.beige, textShadow: "0 1px 6px rgba(0,0,0,0.9)" }}>
          STYLE {String(i + 1).padStart(2, "0")} / {String(n).padStart(2, "0")}
        </div>
        <div style={{ display: "inline-block", fontFamily: F.serif, fontSize: 74, color: C.blanc, marginTop: 10, padding: "6px 30px 12px", borderRadius: 14, background: "rgba(13,13,14,0.72)" }}>{style.name}</div>
      </div>
    </AbsoluteFill>
  );
};

const PriceCard: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ filter: "blur(6px) brightness(0.45)", transform: "scale(1.1)" }}>
        <Swatch id="noyer-bg" kind="wood" colors={["#6B4529", "#3A2414"]} pan={-frame} />
      </AbsoluteFill>
      <div style={{ position: "absolute", left: SAFE.left, width: SAFE_W, top: 560, textAlign: "center", color: C.blanc }}>
        <div style={{ fontFamily: F.sans, fontSize: 24, letterSpacing: 7, color: C.beige, opacity: tw(frame, [0, 10], [0, 1]) }}>
          UN BUREAU · UN BUDGET
        </div>
        <div style={{ fontFamily: F.serif, fontSize: 78, lineHeight: 1.05, marginTop: 18, opacity: tw(frame, [4, 16], [0, 1]) }}>{S.priceNote}</div>
        <div style={{ marginTop: 44, display: "flex", flexDirection: "column", gap: 18, alignItems: "center" }}>
          {S.priceFactors.map((f, i) => {
            const o = tw(frame, [12 + i * 7, 22 + i * 7], [0, 1]);
            return (
              <div
                key={f}
                style={{
                  opacity: o,
                  transform: `translateY(${(1 - o) * 16}px)`,
                  fontFamily: F.sans,
                  fontSize: 40,
                  fontWeight: 500,
                  width: 520,
                  padding: "14px 0",
                  borderBottom: "1px solid rgba(255,217,160,0.35)",
                  display: "flex",
                  justifyContent: "space-between",
                }}
              >
                <span>{f}</span>
                <span style={{ color: C.led }}>+</span>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** SCÈNE 5 — Matériaux (macros verticales) → 9 styles de bureaux → le prix dépend du projet. */
export const S5Materiaux: React.FC = () => {
  const nM = content.materials.length;
  const aF = nM * MAT_F;
  const bF = content.deskStyles.length * STYLE_F;
  return (
    <AbsoluteFill style={{ backgroundColor: C.noir }}>
      {content.materials.map((_, i) => (
        <Sequence key={i} from={i * MAT_F} durationInFrames={MAT_F + 10}>
          <MaterialCard i={i} />
        </Sequence>
      ))}
      <Sequence from={aF} durationInFrames={bF}>
        <StylesShowcase />
      </Sequence>
      <Sequence from={aF + bF}>
        <PriceCard />
      </Sequence>
      <BrandBug chapter={S.chapter} />
      <Subtitles lines={S.subtitles} />
    </AbsoluteFill>
  );
};

export const S5_MIN_FRAMES = content.materials.length * MAT_F + content.deskStyles.length * STYLE_F + sec(2.5);
