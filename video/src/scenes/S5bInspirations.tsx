import React from "react";
import { AbsoluteFill, Img, useCurrentFrame } from "remotion";
import { ArchFrame, BrandBug } from "../components/Brand";
import { CutoutDesk, layout } from "../components/Showcase";
import { Subtitles } from "../components/Subtitles";
import { content, easeInOut, file, has, tw } from "../lib";
import { C, F, SAFE, SAFE_W, W } from "../theme";

const S = content.scenes.s5b;
const DESK = content.bureaux.arrondi as CutoutDesk;

/** Position finale des cartes « inspiration » (tableau façon Pinterest, en colonnes décalées). */
const PINS = [
  { x: 150, y: 640, w: 360, h: 300, r: -4 },
  { x: 570, y: 600, w: 360, h: 250, r: 3 },
  { x: 150, y: 960, w: 360, h: 220, r: 2 },
  { x: 570, y: 870, w: 360, h: 310, r: -3 },
];

/**
 * SCÈNE 5b — Pas encore d'idée précise ?
 * 01 : DOMOVA imagine le projet. 02 : le client envoie ses inspirations
 * (Pinterest, Instagram, photos), qui se transforment en plan sur mesure.
 */
export const S5bInspirations: React.FC = () => {
  const f = useCurrentFrame();
  const qIn = tw(f, [4, 18], [0, 1]);
  const qUp = tw(f, [34, 52], [0, 1], easeInOut);
  const optO = tw(f, [100, 112], [1, 0]);
  const pinsIn = (i: number) => tw(f, [104 + i * 6, 120 + i * 6], [0, 1], easeInOut);
  const merge = tw(f, [150, 172], [0, 1], easeInOut);
  const draw = tw(f, [166, 206], [0, 1], (t) => t);
  const L = layout(DESK);

  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse 85% 60% at 50% 42%, #5C1B29 0%, ${C.bordeaux} 50%, ${C.bordeauxNuit} 100%)` }}>
      <ArchFrame x={175} y={330} w={730} h={1080} color={C.arche} width={2.5} draw={tw(f, [0, 34], [0, 1])} />

      {/* la question */}
      <div
        style={{
          position: "absolute",
          left: SAFE.left,
          width: SAFE_W,
          top: 760 - qUp * 340,
          textAlign: "center",
          opacity: qIn,
          transform: `scale(${1 - qUp * 0.22})`,
        }}
      >
        <div style={{ fontFamily: F.sans, fontWeight: 300, fontSize: 64, lineHeight: 1.12, color: C.creme }}>{S.question}</div>
        <div style={{ width: tw(f, [10, 28], [0, 90]), height: 2, background: C.or, margin: "26px auto 0" }} />
      </div>

      {/* les deux possibilités */}
      <div style={{ position: "absolute", left: SAFE.left + 20, width: SAFE_W - 40, top: 640, opacity: optO }}>
        {S.options.map((o, i) => {
          const a = tw(f, [50 + i * 22, 66 + i * 22], [0, 1]);
          return (
            <div
              key={o.n}
              style={{
                display: "flex",
                gap: 26,
                alignItems: "baseline",
                padding: "30px 0",
                borderBottom: `1px solid rgba(201,164,106,${0.4 * a})`,
                opacity: a,
                transform: `translateX(${(1 - a) * -24}px)`,
              }}
            >
              <div style={{ fontFamily: F.sans, fontSize: 30, letterSpacing: 4, color: C.or }}>{o.n}</div>
              <div>
                <div style={{ fontFamily: F.sans, fontWeight: 400, fontSize: 42, lineHeight: 1.15, color: C.creme }}>{o.title}</div>
                <div style={{ fontFamily: F.sans, fontWeight: 300, fontSize: 28, marginTop: 8, letterSpacing: "0.04em", color: C.or }}>{o.detail}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* tableau d'inspirations qui se rassemble puis devient un plan */}
      {S.inspirations.map((src, i) => {
        const p = PINS[i % PINS.length];
        const a = pinsIn(i);
        if (a <= 0 || merge >= 1) return null;
        const cx = W / 2 - p.w / 2;
        const cy = 880 - p.h / 2;
        const x = p.x + (cx - p.x) * merge;
        const y = p.y + 60 * (1 - a) + (cy - p.y) * merge;
        return (
          <div
            key={src}
            style={{
              position: "absolute",
              left: x,
              top: y,
              width: p.w,
              height: p.h,
              borderRadius: 22,
              overflow: "hidden",
              opacity: a * (1 - merge),
              transform: `rotate(${p.r * (1 - merge)}deg) scale(${1 - merge * 0.5})`,
              boxShadow: "0 18px 40px rgba(0,0,0,0.45)",
              border: `2px solid rgba(243,233,220,0.9)`,
              background: C.bordeauxFonce,
            }}
          >
            {has(src) ? <Img src={file(src)} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : null}
          </div>
        );
      })}
      {f >= 104 && f < 172 ? (
        <div
          style={{
            position: "absolute",
            left: SAFE.left,
            width: SAFE_W,
            top: 535,
            textAlign: "center",
            fontFamily: F.sans,
            fontSize: 22,
            letterSpacing: 6,
            color: C.or,
            opacity: tw(f, [104, 116], [0, 1]) * (1 - merge),
          }}
        >
          VOS INSPIRATIONS
        </div>
      ) : null}

      {/* le plan sur mesure, tracé en or */}
      {f >= 160 && DESK.lines && has(DESK.lines) ? (
        <>
          <AbsoluteFill style={{ clipPath: `inset(0 ${(1 - draw) * 100}% 0 0)` }}>
            <Img src={file(DESK.lines)} style={{ position: "absolute", left: L.left, top: L.top, width: L.width, height: L.height }} />
          </AbsoluteFill>
          {draw < 1 ? (
            <div style={{ position: "absolute", top: L.box.y - 50, height: L.box.h + 100, left: L.box.x + L.box.w * draw, width: 3, background: C.or, boxShadow: `0 0 22px ${C.or}` }} />
          ) : null}
          <div style={{ position: "absolute", left: SAFE.left, width: SAFE_W, top: 548, textAlign: "center", opacity: tw(f, [176, 190], [0, 1]) }}>
            <div style={{ fontFamily: F.sans, fontSize: 22, letterSpacing: 6, color: C.or }}>NOUS EN FAISONS</div>
            <div style={{ fontFamily: F.sans, fontWeight: 300, fontSize: 46, color: C.creme, marginTop: 4 }}>{S.result}</div>
          </div>
        </>
      ) : null}

      <BrandBug chapter={S.chapter} />
      <Subtitles lines={S.subtitles} />
    </AbsoluteFill>
  );
};
