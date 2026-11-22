import React from "react";
import { AbsoluteFill, Sequence, useCurrentFrame } from "remotion";
import { Media } from "../components/Media";
import { ParisMap } from "../components/Drawings";
import { Subtitles } from "../components/Subtitles";
import { content, has, sec, tw } from "../lib";
import { C, F, SAFE, SAFE_W } from "../theme";

const S = content.scenes.s1;

/** SCÈNE 1 — Paris : vue aérienne verticale → plongée vers le 14e → rue haussmannienne. */
export const S1Paris: React.FC = () => {
  const frame = useCurrentFrame();
  const [a, b] = S.shots;
  const aF = sec(a.durationSec);
  const mapP = tw(frame, [0, aF], [0, 1], (t) => t);
  const footage = has(a.src);
  const titleO = tw(frame, [8, 26], [0, 1]) * tw(frame, [sec(2.8), sec(3.3)], [1, 0]);
  const placeO = tw(frame, [sec(3.0), sec(3.5)], [0, 1]) * tw(frame, [sec(7.2), sec(7.8)], [1, 0]);

  return (
    <AbsoluteFill>
      <Sequence durationInFrames={aF + 10}>
        <Media
          src={a.src}
          push={[1.0, 1.35]}
          placeholder={{ id: a.id, title: a.title, source: a.source }}
          fallback={<ParisMap progress={mapP} />}
        />
        {footage ? (
          <AbsoluteFill style={{ opacity: 0.35, mixBlendMode: "screen" }}>
            <ParisMap progress={mapP} transparent />
          </AbsoluteFill>
        ) : null}
      </Sequence>
      <Sequence from={aF} durationInFrames={sec(b.durationSec)}>
        <AbsoluteFill style={{ opacity: tw(frame - aF, [0, 10], [0, 1]) }}>
          <Media src={b.src} push={[1.12, 1.0]} drift={[40, 0]} placeholder={{ id: b.id, title: b.title, source: b.source, tone: "warm" }} />
        </AbsoluteFill>
      </Sequence>

      {/* Titre PARIS */}
      <div style={{ position: "absolute", left: SAFE.left, width: SAFE_W, top: 520, textAlign: "center", opacity: titleO }}>
        <div
          style={{
            fontFamily: F.serif,
            fontSize: 170,
            fontWeight: 500,
            letterSpacing: "0.28em",
            marginRight: "-0.28em",
            color: C.blanc,
            transform: `scale(${tw(frame, [0, sec(3.3)], [1.08, 1])})`,
            textShadow: "0 6px 40px rgba(0,0,0,0.6)",
          }}
        >
          PARIS
        </div>
      </div>

      {/* Repère 14e */}
      <div style={{ position: "absolute", left: SAFE.left, width: SAFE_W, top: 820, textAlign: "center", opacity: placeO }}>
        <div style={{ fontFamily: F.serif, fontSize: 96, color: C.blanc, textShadow: "0 4px 30px rgba(0,0,0,0.7)" }}>{S.place}</div>
        <div style={{ width: tw(frame, [sec(3.1), sec(3.9)], [0, 420]), height: 2, background: C.led, margin: "18px auto" }} />
        <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 26, letterSpacing: 4, color: C.beige }}>{S.coordinates}</div>
      </div>

      <Subtitles lines={S.subtitles} />
    </AbsoluteFill>
  );
};
