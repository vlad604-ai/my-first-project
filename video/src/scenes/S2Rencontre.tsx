import React from "react";
import { AbsoluteFill, Series } from "remotion";
import { BrandBug } from "../components/Brand";
import { Media } from "../components/Media";
import { Subtitles } from "../components/Subtitles";
import { content, sec } from "../lib";

const S = content.scenes.s2;

/** SCÈNE 2 — La rencontre : marche du dirigeant (plan vertical en pied), puis poignée de main (plan taille, deux personnages empilés dans le cadre). */
export const S2Rencontre: React.FC = () => {
  const [a, b] = S.shots;
  return (
    <AbsoluteFill>
      <Series>
        <Series.Sequence durationInFrames={sec(a.durationSec)}>
          <Media src={a.src} push={[1.0, 1.08]} placeholder={{ id: a.id, title: a.title, source: a.source, tone: "warm" }} />
        </Series.Sequence>
        <Series.Sequence durationInFrames={sec(b.durationSec)}>
          <Media src={b.src} push={[1.08, 1.0]} placeholder={{ id: b.id, title: b.title, source: b.source, tone: "warm" }} />
        </Series.Sequence>
      </Series>
      <BrandBug chapter={S.chapter} />
      <Subtitles lines={S.subtitles} />
    </AbsoluteFill>
  );
};
