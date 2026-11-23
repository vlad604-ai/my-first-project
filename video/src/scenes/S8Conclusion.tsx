import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { ArchFrame, ArchIcon, Logo } from "../components/Brand";
import { Media } from "../components/Media";
import { content, easeInOut, has, sec, tw } from "../lib";
import { C, F, SAFE, SAFE_W } from "../theme";

const S = content.scenes.s8;
const B = content.brand;
const apres = content.beforeAfter.apres;

/** Pictogrammes génériques fins (pas de logos de marques tierces). */
const Icon: React.FC<{ type: string }> = ({ type }) => {
  const s = { stroke: C.or, strokeWidth: 2, fill: "none" };
  return (
    <svg width={30} height={30} viewBox="0 0 40 40">
      {type === "instagram" ? (
        <>
          <rect x={6} y={6} width={28} height={28} rx={8} {...s} />
          <circle cx={20} cy={20} r={6.5} {...s} />
          <circle cx={28.5} cy={11.5} r={1.6} fill={C.or} />
        </>
      ) : type === "tiktok" ? (
        <path d="M22 7 v18 a6 6 0 1 1 -6 -6 M22 7 c1 4 4 7 8 7" {...s} strokeLinecap="round" />
      ) : type === "whatsapp" ? (
        <>
          <path d="M20 6 a14 14 0 1 1 -11.5 22 L6 34 l6.2 -2.3 A14 14 0 0 1 20 6 z" {...s} strokeLinejoin="round" />
          <path d="M15 14 c0 6 5 11 11 11 l1.5 -2.5 -3.5 -1.8 -1.6 1.6 c-2 -0.8 -3.6 -2.4 -4.4 -4.4 l1.6 -1.6 -1.8 -3.5 z" fill={C.or} />
        </>
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

/**
 * SCÈNE 8 — Promesse sur la réalisation, puis « affiche » DOMOVA :
 * fond bordeaux, arche fine, icône qui se dessine, logotype, appel à l'action.
 */
export const S8Conclusion: React.FC = () => {
  const f = useCurrentFrame();
  const t0 = sec(2.7);
  const promiseO = tw(f, [6, 20], [0, 1]) * tw(f, [t0 - 14, t0], [1, 0]);
  const poster = tw(f, [t0 - 10, t0 + 12], [0, 1], easeInOut);
  const lf = f - t0;
  const bg = has(S.background) ? S.background : has(apres.src) ? apres.src : undefined;
  const [p1, p2] = B.promise.split(". ");
  const ap = (a: number, b: number) => tw(lf, [a, b], [0, 1]);

  return (
    <AbsoluteFill style={{ backgroundColor: C.bordeaux }}>
      {/* 1. promesse sur votre réalisation */}
      <AbsoluteFill style={{ opacity: 1 - poster }}>
        {bg ? <Media src={bg} startSec={bg === apres.src ? apres.startSec + 5 : 0} push={[1.12, 1.02]} placeholder={{ id: "FINAL", title: "" }} /> : null}
        <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(28,7,12,0.2) 0%, rgba(28,7,12,0.75) 60%, rgba(28,7,12,0.85) 100%)" }} />
        <div style={{ position: "absolute", left: SAFE.left, width: SAFE_W, top: 820, textAlign: "center", opacity: promiseO, color: C.creme }}>
          <div style={{ fontFamily: F.sans, fontWeight: 300, fontSize: 70, lineHeight: 1.12 }}>{p1}.</div>
          <div style={{ width: tw(f, [16, 34], [0, 120]), height: 2, background: C.or, margin: "30px auto" }} />
          <div style={{ fontFamily: F.sans, fontWeight: 400, fontSize: 52, lineHeight: 1.2, color: C.or, opacity: tw(f, [22, 36], [0, 1]) }}>{p2}</div>
        </div>
      </AbsoluteFill>

      {/* 2. affiche DOMOVA */}
      <AbsoluteFill style={{ opacity: poster }}>
        <ArchFrame x={175} y={300} w={730} h={1180} color={C.arche} width={2.5} draw={ap(0, 40)} />
        <div style={{ position: "absolute", left: SAFE.left, width: SAFE_W, top: 470, display: "flex", flexDirection: "column", alignItems: "center", color: C.creme }}>
          <ArchIcon size={150} draw={ap(4, 34)} />
          <div style={{ marginTop: 44, opacity: ap(20, 36), transform: `translateY(${(1 - ap(20, 36)) * 14}px)` }}>
            <Logo height={84} />
          </div>
          <div style={{ marginTop: 24, fontFamily: F.sans, fontWeight: 500, fontSize: 19, letterSpacing: "0.26em", marginRight: "-0.26em", opacity: ap(28, 42), whiteSpace: "nowrap" }}>
            {B.metier}
          </div>
          <div style={{ width: ap(34, 52) * 90, height: 2, background: C.or, margin: "42px 0 34px" }} />
          <div style={{ fontFamily: F.sans, fontWeight: 400, fontSize: 40, letterSpacing: "0.3em", marginRight: "-0.3em", color: C.or, opacity: ap(38, 52) }}>{B.tagline}</div>
          <div style={{ fontFamily: F.sans, fontWeight: 300, fontSize: 36, marginTop: 26, opacity: ap(44, 58) }}>{B.signature}</div>
          <div style={{ fontFamily: F.sans, fontWeight: 300, fontSize: 30, lineHeight: 1.35, textAlign: "center", maxWidth: 680, marginTop: 44, color: "#E3D5C3", opacity: ap(52, 66) }}>{B.cta}</div>
          <div
            style={{
              marginTop: 32,
              padding: "18px 54px",
              background: C.or,
              color: C.bordeaux,
              borderRadius: 6,
              fontFamily: F.sans,
              fontWeight: 500,
              fontSize: 30,
              letterSpacing: "0.06em",
              opacity: ap(58, 70),
              transform: `scale(${0.94 + 0.06 * ap(58, 74)})`,
            }}
          >
            {B.button}
          </div>
          <div style={{ marginTop: 44, display: "grid", gridTemplateColumns: "1fr 1fr", gap: "18px 26px", width: SAFE_W - 40 }}>
            {content.contacts.map((c, i) => (
              <div key={c.type} style={{ display: "flex", alignItems: "center", gap: 12, opacity: ap(64 + i * 5, 76 + i * 5) }}>
                <Icon type={c.type} />
                <div style={{ fontFamily: F.sans }}>
                  <div style={{ fontSize: 15, letterSpacing: 3, color: C.or }}>{c.label.toUpperCase()}</div>
                  <div style={{ fontSize: 26, color: C.creme }}>{c.value}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
