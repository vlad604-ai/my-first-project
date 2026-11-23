import React from "react";
import { AbsoluteFill, interpolate, Sequence, Series, useCurrentFrame } from "remotion";
import { ArchFrame, archClip, BrandBug } from "../components/Brand";
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
        fontSize: 104,
        fontWeight: 400,
        letterSpacing: "0.32em",
        marginRight: "-0.32em",
        color: C.blanc,
        textShadow: "0 4px 30px rgba(0,0,0,0.9), 0 0 60px rgba(0,0,0,0.5)",
      }}
    >
      {text}
    </div>
    <div style={{ fontFamily: F.sans, fontSize: 22, letterSpacing: 4, color: C.beige, marginTop: 6, textShadow: "0 1px 8px rgba(0,0,0,0.8)" }}>
      {S.realLabel.toUpperCase()}
    </div>
  </div>
);

type Detail = { atSec: number; x: number; y: number; zoom: number; label: string };
type Clip = { startSec: number; durationSec: number; push?: number[]; details?: Detail[] };

/** Rapprochements successifs sur un plan APRÈS (simple recadrage, aucune retouche de l'image). */
const detailZoom = (f: number, details: Detail[]) => {
  const times: number[] = [0];
  const zs: number[] = [1];
  const xs: number[] = [0.5];
  const ys: number[] = [0.5];
  for (const d of details) {
    const t = sec(d.atSec);
    if (t <= times[times.length - 1]) continue;
    // centre borné pour ne jamais faire apparaître le bord de l'image
    const lim = 1 / (2 * d.zoom);
    times.push(t, t + 12);
    zs.push(zs[zs.length - 1], d.zoom);
    xs.push(xs[xs.length - 1], Math.min(1 - lim, Math.max(lim, d.x)));
    ys.push(ys[ys.length - 1], Math.min(1 - lim, Math.max(lim, d.y)));
  }
  if (times.length < 2) return { z: 1, x: 0.5, y: 0.5, active: undefined, since: 0 };
  const o = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const, easing: easeInOut };
  const active = [...details].reverse().find((d) => f >= sec(d.atSec) + 6);
  return {
    z: interpolate(f, times, zs, o),
    x: interpolate(f, times, xs, o),
    y: interpolate(f, times, ys, o),
    active,
    since: active ? f - sec(active.atSec) - 6 : 0,
  };
};

const ApresClip: React.FC<{ clip: Clip }> = ({ clip }) => {
  const f = useCurrentFrame();
  const zoom = detailZoom(f, clip.details ?? []);
  return (
    <AbsoluteFill>
      <AbsoluteFill
        style={{
          transform: `scale(${zoom.z}) translate(${(0.5 - zoom.x) * 100}%, ${(0.5 - zoom.y) * 100}%)`,
          transformOrigin: "50% 50%",
        }}
      >
        <Media
          src={BA.apres.src}
          startSec={clip.startSec}
          fit={BA.apres.fit as Fit}
          focusX={BA.apres.focusX}
          focusY={BA.apres.focusY}
          push={(clip.push as [number, number]) ?? [1, 1]}
          placeholder={{ id: "APRÈS", title: "Déposez la vidéo APRÈS (bureau réalisé)", source: "Vidéo réelle — elle ne sera ni remplacée ni retouchée.", tone: "alert" }}
        />
      </AbsoluteFill>
      {zoom.active ? (
        <div style={{ position: "absolute", left: SAFE.left, width: SAFE_W, top: 1060, display: "flex", justifyContent: "center", opacity: tw(zoom.since, [0, 8], [0, 1]) }}>
          <div style={{ fontFamily: F.sans, fontSize: 30, fontWeight: 500, letterSpacing: 4, color: C.blanc, padding: "12px 26px", borderLeft: `4px solid ${C.led}`, background: "rgba(43,12,19,0.6)" }}>
            {zoom.active.label.toUpperCase()}
          </div>
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

/** SCÈNE 6 — Avant / Après avec les vidéos réelles du client. */
export const S6AvantApres: React.FC = () => {
  const frame = useCurrentFrame();
  const avantF = sec(4.0);
  const transF = sec(1.2);
  const apresFrom = avantF - 4;
  const fa = frame - apresFrom;
  const archT = tw(frame, [apresFrom, avantF + transF + 4], [0, 1], easeInOut);
  const archW = 10 + archT * 2800;
  const archBottom = 1240 + archT * 1400;
  const inTrans = frame >= avantF - 4 && frame <= avantF + transF + 6;

  return (
    <AbsoluteFill style={{ backgroundColor: C.noir }}>
      {/* AVANT (dessus), effacé par un balayage architectural */}
      <Sequence durationInFrames={avantF + transF + 4}>
        <AbsoluteFill>
          <Media
            src={BA.avant.src}
            startSec={BA.avant.startSec}
            fit={BA.avant.fit as Fit}
            focusX={BA.avant.focusX}
            focusY={BA.avant.focusY}
            push={[1.0, 1.06]}
            playbackRate={BA.avant.playbackRate ?? 1}
            placeholder={{ id: "AVANT", title: "Déposez la vidéo AVANT (pièce vide)", source: "Vidéo réelle — elle ne sera ni remplacée ni retouchée.", tone: "alert" }}
          />
        </AbsoluteFill>
      </Sequence>

      {/* APRÈS (dessous) : plans successifs de votre vidéo */}
      <Sequence from={apresFrom}>
        <AbsoluteFill style={{ clipPath: archW < 2700 ? archClip(540, archBottom, archW, archW * 1.3) : undefined }}>
        <Series>
          {(BA.apresClips as Clip[]).map((clip, i, all) => (
            <Series.Sequence
              key={i}
              durationInFrames={i === all.length - 1 ? Math.max(1, sec(S.durationSec) - apresFrom - all.slice(0, -1).reduce((t, c) => t + sec(c.durationSec), 0)) : sec(clip.durationSec)}
            >
              <ApresClip clip={clip} />
            </Series.Sequence>
          ))}
        </Series>
        </AbsoluteFill>
      </Sequence>

      {/* révélation en arche : contour or qui suit l'ouverture */}
      {inTrans && archW < 2700 ? <ArchFrame x={540 - archW / 2} y={archBottom - archW * 1.3} w={archW} h={archW * 1.3} color={C.or} width={5} /> : null}

      <BigLabel text="AVANT" o={tw(frame, [6, 18], [0, 1]) * tw(frame, [avantF - 10, avantF], [1, 0])} />
      <BigLabel text="APRÈS" o={tw(frame, [avantF + transF - 4, avantF + transF + 10], [0, 1]) * tw(fa, [sec(2.0), sec(2.4)], [1, 0])} />

      <BrandBug chapter={S.chapter} />
      <Subtitles lines={S.subtitles} />
    </AbsoluteFill>
  );
};
