import React from "react";
import { AbsoluteFill, interpolate, Sequence, useCurrentFrame } from "remotion";
import { BrandBug } from "../components/Brand";
import { Fit, Media } from "../components/Media";
import { Subtitles } from "../components/Subtitles";
import { content, easeInOut, sec, tw } from "../lib";
import { C, F, H, SAFE, SAFE_W, W } from "../theme";

const S = content.scenes.s6;
const BA = content.beforeAfter;

const BigLabel: React.FC<{ text: string; o: number }> = ({ text, o }) => (
  <div style={{ position: "absolute", left: SAFE.left, width: SAFE_W, top: 360, textAlign: "center", opacity: o }}>
    <div
      style={{
        display: "inline-block",
        fontFamily: F.serif,
        fontSize: 120,
        fontWeight: 500,
        letterSpacing: "0.22em",
        marginRight: "-0.22em",
        color: C.blanc,
        textShadow: "0 6px 34px rgba(0,0,0,0.7)",
      }}
    >
      {text}
    </div>
    <div style={{ fontFamily: F.sans, fontSize: 22, letterSpacing: 4, color: C.beige, marginTop: 6, textShadow: "0 1px 8px rgba(0,0,0,0.8)" }}>
      {S.realLabel.toUpperCase()}
    </div>
  </div>
);

/** Rapprochements successifs sur la vidéo APRÈS (sans retoucher l'image : simple recadrage). */
const useDetailZoom = (f: number) => {
  const times: number[] = [0];
  const zs: number[] = [1];
  const xs: number[] = [0.5];
  const ys: number[] = [0.5];
  for (const d of BA.details) {
    const t = sec(d.atSec);
    if (t <= times[times.length - 1]) continue;
    times.push(t, t + 14);
    zs.push(zs[zs.length - 1], d.zoom);
    xs.push(xs[xs.length - 1], d.x);
    ys.push(ys[ys.length - 1], d.y);
  }
  const o = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const, easing: easeInOut };
  const z = interpolate(f, times, zs, o);
  const x = interpolate(f, times, xs, o);
  const y = interpolate(f, times, ys, o);
  const active = [...BA.details].reverse().find((d) => f >= sec(d.atSec) + 8);
  return { z, x, y, active, since: active ? f - sec(active.atSec) - 8 : 0 };
};

/** SCÈNE 6 — Avant / Après avec les vidéos réelles du client. */
export const S6AvantApres: React.FC = () => {
  const frame = useCurrentFrame();
  const avantF = sec(4.0);
  const transF = sec(1.2);
  const apresFrom = avantF + transF - 10;
  const fa = frame - apresFrom;
  const zoom = useDetailZoom(fa);
  const wipe = tw(frame, [avantF - 4, avantF + transF], [0, H + 40], easeInOut);
  const inTrans = frame >= avantF - 4 && frame <= avantF + transF + 6;

  return (
    <AbsoluteFill style={{ backgroundColor: C.noir }}>
      {/* APRÈS (dessous) */}
      <Sequence from={apresFrom}>
        <AbsoluteFill
          style={{
            transform: `scale(${zoom.z}) translate(${(0.5 - zoom.x) * 100}%, ${(0.5 - zoom.y) * 100}%)`,
            transformOrigin: "50% 50%",
          }}
        >
          <Media
            src={BA.apres.src}
            startSec={BA.apres.startSec}
            fit={BA.apres.fit as Fit}
            focusX={BA.apres.focusX}
            focusY={BA.apres.focusY}
            push={[1, 1]}
            placeholder={{ id: "APRÈS", title: "Déposez la vidéo APRÈS (bureau réalisé)", source: "Vidéo réelle — elle ne sera ni remplacée ni retouchée.", tone: "alert" }}
          />
        </AbsoluteFill>
      </Sequence>

      {/* AVANT (dessus), effacé par un balayage architectural */}
      <Sequence durationInFrames={avantF + transF + 4}>
        <AbsoluteFill style={{ clipPath: `inset(${wipe}px 0 0 0)` }}>
          <Media
            src={BA.avant.src}
            startSec={BA.avant.startSec}
            fit={BA.avant.fit as Fit}
            focusX={BA.avant.focusX}
            focusY={BA.avant.focusY}
            push={[1.0, 1.06]}
            placeholder={{ id: "AVANT", title: "Déposez la vidéo AVANT (pièce vide)", source: "Vidéo réelle — elle ne sera ni remplacée ni retouchée.", tone: "alert" }}
          />
        </AbsoluteFill>
      </Sequence>

      {/* trame d'architecte pendant la transition */}
      {inTrans ? (
        <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
          {Array.from({ length: 13 }, (_, i) => (
            <line key={`v${i}`} x1={i * 90} y1={0} x2={i * 90} y2={wipe} stroke={C.led} strokeOpacity={0.22} strokeWidth={1.5} />
          ))}
          {Array.from({ length: 22 }, (_, i) =>
            i * 90 < wipe ? <line key={`h${i}`} x1={0} y1={i * 90} x2={W} y2={i * 90} stroke={C.led} strokeOpacity={0.12} strokeWidth={1} /> : null,
          )}
          <rect x={0} y={wipe - 3} width={W} height={6} fill={C.led} style={{ filter: `drop-shadow(0 0 18px ${C.led})` }} />
        </svg>
      ) : null}

      <BigLabel text="AVANT" o={tw(frame, [6, 18], [0, 1]) * tw(frame, [avantF - 10, avantF], [1, 0])} />
      <BigLabel text="APRÈS" o={tw(frame, [avantF + transF - 4, avantF + transF + 10], [0, 1]) * tw(fa, [sec(2.0), sec(2.4)], [1, 0])} />

      {zoom.active ? (
        <div style={{ position: "absolute", left: SAFE.left, width: SAFE_W, top: 1060, display: "flex", justifyContent: "center", opacity: tw(zoom.since, [0, 8], [0, 1]) }}>
          <div style={{ fontFamily: F.sans, fontSize: 30, fontWeight: 500, letterSpacing: 4, color: C.blanc, padding: "12px 26px", borderLeft: `4px solid ${C.led}`, background: "rgba(13,13,14,0.6)" }}>
            {zoom.active.label.toUpperCase()}
          </div>
        </div>
      ) : null}

      <BrandBug chapter={S.chapter} />
      <Subtitles lines={S.subtitles} />
    </AbsoluteFill>
  );
};
