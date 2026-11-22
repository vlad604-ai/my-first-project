import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Logo } from "../components/Brand";
import { Media } from "../components/Media";
import { Swatch } from "../components/Swatch";
import { content, has, sec, tw } from "../lib";
import { C, F, SAFE, SAFE_W } from "../theme";

const S = content.scenes.s8;
const B = content.brand;
const apres = content.beforeAfter.apres;

/** Pictogrammes génériques (pas de logos de marques tierces). */
const Icon: React.FC<{ type: string }> = ({ type }) => {
  const s = { stroke: C.led, strokeWidth: 2.4, fill: "none" };
  return (
    <svg width={40} height={40} viewBox="0 0 40 40">
      {type === "instagram" ? (
        <>
          <rect x={6} y={6} width={28} height={28} rx={8} {...s} />
          <circle cx={20} cy={20} r={6.5} {...s} />
          <circle cx={28.5} cy={11.5} r={1.6} fill={C.led} />
        </>
      ) : type === "tiktok" ? (
        <path d="M22 7 v18 a6 6 0 1 1 -6 -6 M22 7 c1 4 4 7 8 7" {...s} strokeLinecap="round" />
      ) : type === "phone" ? (
        <path d="M12 7 l5 0 l2 7 l-3 2 a14 14 0 0 0 8 8 l2 -3 l7 2 l0 5 a3 3 0 0 1 -3 3 A23 23 0 0 1 9 10 a3 3 0 0 1 3 -3 z" {...s} strokeLinejoin="round" />
      ) : (
        <>
          <circle cx={20} cy={20} r={13} {...s} />
          <ellipse cx={20} cy={20} rx={5.5} ry={13} {...s} />
          <line x1={7} y1={20} x2={33} y2={20} {...s} />
        </>
      )}
    </svg>
  );
};

/** SCÈNE 8 — Promesse, logo DOMOVA, appel à l'action et coordonnées, centrés dans la zone sûre. */
export const S8Conclusion: React.FC = () => {
  const f = useCurrentFrame();
  const promiseO = tw(f, [6, 20], [0, 1]) * tw(f, [sec(2.4), sec(2.9)], [1, 0]);
  const t0 = sec(2.7);
  const logoO = tw(f, [t0, t0 + 20], [0, 1]);
  const bg = has(S.background) ? S.background : has(apres.src) ? apres.src : undefined;
  const [p1, p2] = B.promise.split(". ");

  return (
    <AbsoluteFill style={{ backgroundColor: C.noir }}>
      <AbsoluteFill style={{ filter: `brightness(${tw(f, [t0 - 10, t0 + 20], [0.75, 0.32])})` }}>
        {bg ? (
          <Media src={bg} startSec={bg === apres.src ? apres.startSec + 5 : 0} push={[1.12, 1.0]} placeholder={{ id: "FINAL", title: "" }} />
        ) : (
          <Swatch id="final-bg" kind="combo" colors={["#5A3A22", "#151515"]} pan={-f} />
        )}
      </AbsoluteFill>

      {/* Promesse principale */}
      <div style={{ position: "absolute", left: SAFE.left, width: SAFE_W, top: 640, textAlign: "center", opacity: promiseO, color: C.blanc }}>
        <div style={{ fontFamily: F.serif, fontSize: 82, lineHeight: 1.08, textShadow: "0 4px 30px rgba(0,0,0,0.6)" }}>{p1}.</div>
        <div style={{ fontFamily: F.serif, fontStyle: "italic", fontSize: 70, lineHeight: 1.1, color: C.led, marginTop: 26, opacity: tw(f, [22, 36], [0, 1]) }}>
          {p2}
        </div>
      </div>

      {/* Bloc logo */}
      <div style={{ position: "absolute", left: SAFE.left, width: SAFE_W, top: 470, display: "flex", flexDirection: "column", alignItems: "center", color: C.blanc, opacity: logoO }}>
        <div style={{ transform: `scale(${tw(f, [t0, t0 + 40], [1.08, 1])})` }}>
          <Logo height={124} tracking={0.26} />
        </div>
        <div style={{ width: tw(f, [t0 + 10, t0 + 34], [0, 360]), height: 2, background: C.led, margin: "34px 0 26px" }} />
        <div style={{ fontFamily: F.sans, fontSize: 32, fontWeight: 500, letterSpacing: "0.34em", marginRight: "-0.34em", opacity: tw(f, [t0 + 14, t0 + 28], [0, 1]) }}>
          {B.tagline}
        </div>
        <div style={{ fontFamily: F.serif, fontStyle: "italic", fontSize: 46, color: C.beige, marginTop: 26, opacity: tw(f, [t0 + 22, t0 + 36], [0, 1]) }}>
          {B.signature}
        </div>
        <div
          style={{
            marginTop: 50,
            padding: "26px 34px",
            border: `1.5px solid ${C.led}`,
            borderRadius: 14,
            fontFamily: F.sans,
            fontSize: 34,
            lineHeight: 1.3,
            textAlign: "center",
            maxWidth: 760,
            opacity: tw(f, [t0 + 32, t0 + 46], [0, 1]),
            transform: `translateY(${tw(f, [t0 + 32, t0 + 46], [16, 0])}px)`,
          }}
        >
          {B.cta}
        </div>
        <div style={{ marginTop: 44, display: "grid", gridTemplateColumns: "1fr 1fr", gap: "22px 30px", width: SAFE_W - 20 }}>
          {content.contacts.map((c, i) => (
            <div key={c.type} style={{ display: "flex", alignItems: "center", gap: 14, opacity: tw(f, [t0 + 44 + i * 5, t0 + 56 + i * 5], [0, 1]) }}>
              <Icon type={c.type} />
              <div style={{ fontFamily: F.sans }}>
                <div style={{ fontSize: 18, letterSpacing: 3, color: C.beige }}>{c.label.toUpperCase()}</div>
                <div style={{ fontSize: 25, color: C.blanc }}>{c.value}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};
