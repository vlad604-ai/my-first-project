import React from "react";
import { AbsoluteFill, Series, useCurrentFrame, useVideoConfig } from "remotion";
import { BrandBug } from "../components/Brand";
import { Media } from "../components/Media";
import { Subtitles } from "../components/Subtitles";
import { content, has, sec, tw } from "../lib";
import { C, F, SAFE } from "../theme";

const S = content.scenes.s7;
const apres = content.beforeAfter.apres;
const FOCI = [
  [0.3, 0.7],
  [0.65, 0.6],
  [0.45, 0.4],
  [0.7, 0.3],
  [0.5, 0.55],
];

const DetailLabel: React.FC<{ label: string }> = ({ label }) => {
  const f = useCurrentFrame();
  const o = tw(f, [3, 12], [0, 1]);
  return (
    <div style={{ position: "absolute", left: SAFE.left, top: 1040, opacity: o, display: "flex", alignItems: "center", gap: 18 }}>
      <div style={{ width: tw(f, [0, 14], [0, 70]), height: 2, background: C.led }} />
      <div style={{ fontFamily: F.serif, fontWeight: 300, fontSize: 48, color: C.blanc, padding: "4px 24px 10px", borderRadius: 12, background: "rgba(43,12,19,0.62)" }}>{label}</div>
    </div>
  );
};

/**
 * SCÈNE 7 — Le client découvre son bureau.
 * Détails : vos photos /assets/images/details/*. À défaut, recadrages serrés dans votre vidéo APRÈS
 * (le bureau reste donc toujours le vôtre, jamais une image générée).
 */
export const S7Decouverte: React.FC = () => {
  const { durationInFrames } = useVideoConfig();
  const shot = S.shots[0];
  const aF = sec(shot.durationSec);
  const each = Math.floor((durationInFrames - aF) / S.details.length);
  return (
    <AbsoluteFill style={{ backgroundColor: C.noir }}>
      <Series>
        <Series.Sequence durationInFrames={aF}>
          <Media src={shot.src} startSec={(shot as { startSec?: number }).startSec ?? 0} push={((shot as { push?: number[] }).push as [number, number]) ?? [1.0, 1.1]} placeholder={{ id: shot.id, title: shot.title, source: shot.source, tone: "warm" }} />
        </Series.Sequence>
        {S.details.map((det, i) => {
          const d = det as typeof det & { focusX?: number; focusY?: number; push?: number[] };
          const useApres = !has(d.src) && has(apres.src);
          return (
            <Series.Sequence key={d.id} durationInFrames={i === S.details.length - 1 ? durationInFrames - aF - each * (S.details.length - 1) : each}>
              <Media
                src={useApres ? apres.src : d.src}
                startSec={useApres ? apres.startSec + 1 + i * 1.3 : 0}
                focusX={useApres ? FOCI[i % FOCI.length][0] : d.focusX ?? 0.5}
                focusY={useApres ? FOCI[i % FOCI.length][1] : d.focusY ?? 0.5}
                push={useApres ? [1.9, 2.1] : ((d.push as [number, number]) ?? [1.08, 1.2])}
                placeholder={{ id: d.id, title: `Gros plan : ${d.label}`, source: "Photo/vidéo réelle de votre bureau", tone: "warm" }}
              />
              <DetailLabel label={d.label} />
            </Series.Sequence>
          );
        })}
      </Series>
      <BrandBug chapter={S.chapter} />
      <Subtitles lines={S.subtitles} />
    </AbsoluteFill>
  );
};
