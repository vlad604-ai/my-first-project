import React from "react";
import { AbsoluteFill, Series, useCurrentFrame } from "remotion";
import { BrandBug } from "../components/Brand";
import { Dimension } from "../components/Dimension";
import { EmptyRoom } from "../components/Drawings";
import { Media } from "../components/Media";
import { Subtitles } from "../components/Subtitles";
import { content, sec, tw } from "../lib";
import { C, F, H, SAFE, W } from "../theme";

const S = content.scenes.s3;
type Shot = (typeof S.shots)[number] & { caption?: string; startSec?: number; push?: number[] };

const Caption: React.FC<{ text: string }> = ({ text }) => {
  const f = useCurrentFrame();
  const o = tw(f, [4, 14], [0, 1]);
  return (
    <div style={{ position: "absolute", left: SAFE.left, top: 1080, opacity: o, display: "flex", alignItems: "center", gap: 16 }}>
      <div style={{ width: tw(f, [2, 16], [0, 60]), height: 2, background: C.led }} />
      <div style={{ fontFamily: F.sans, fontSize: 28, letterSpacing: 4, fontWeight: 500, color: C.blanc, textShadow: "0 2px 12px rgba(0,0,0,0.8)" }}>
        {text.toUpperCase()}
      </div>
    </div>
  );
};

/** SCÈNE 3 — L'étude : vos images réelles (visite, pièce vide, traçage au sol) + cotes animées. */
export const S3Decouverte: React.FC = () => (
  <AbsoluteFill>
    <Series>
      {(S.shots as Shot[]).map((shot) => (
        <Series.Sequence key={shot.id} durationInFrames={sec(shot.durationSec)}>
          <Media
            src={shot.src}
            startSec={shot.startSec ?? 0}
            push={(shot.push as [number, number]) ?? [1.0, 1.06]}
            placeholder={{ id: shot.id, title: shot.title, source: shot.source }}
            fallback={<EmptyRoom />}
          />
          <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0 }}>
            {shot.dimensions.map((d, i) => (
              <Dimension key={i} {...d} />
            ))}
          </svg>
          {shot.caption ? <Caption text={shot.caption} /> : null}
        </Series.Sequence>
      ))}
    </Series>
    <BrandBug chapter={S.chapter} />
    <Subtitles lines={S.subtitles} />
  </AbsoluteFill>
);
