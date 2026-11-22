import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { BrandBug } from "../components/Brand";
import { Dimension } from "../components/Dimension";
import { EmptyRoom } from "../components/Drawings";
import { Media } from "../components/Media";
import { Subtitles } from "../components/Subtitles";
import { content, tw } from "../lib";
import { H, W } from "../theme";

const S = content.scenes.s3;

/** SCÈNE 3 — Découverte de la pièce : cadrage en hauteur/profondeur + cotes animées. */
export const S3Decouverte: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const shot = S.shots[0];
  const push = tw(frame, [0, durationInFrames], [1.0, 1.06], (t) => t);
  return (
    <AbsoluteFill>
      <Media
        src={shot.src}
        push={[1.0, 1.1]}
        placeholder={{ id: shot.id, title: shot.title, source: shot.source }}
        fallback={
          <AbsoluteFill style={{ transform: `scale(${push})` }}>
            <EmptyRoom />
          </AbsoluteFill>
        }
      />
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0 }}>
        {S.dimensions.map((d, i) => (
          <Dimension key={i} {...d} />
        ))}
      </svg>
      <BrandBug chapter={S.chapter} />
      <Subtitles lines={S.subtitles} />
    </AbsoluteFill>
  );
};
