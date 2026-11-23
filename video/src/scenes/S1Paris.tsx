import React from "react";
import { AbsoluteFill, Sequence, useCurrentFrame } from "remotion";
import { Media } from "../components/Media";
import { ParisMap } from "../components/Drawings";
import { Subtitles } from "../components/Subtitles";
import { content, easeInOut, has, sec, tw } from "../lib";
import { ArchIcon, archClip } from "../components/Brand";
import { C, F, SAFE, SAFE_W } from "../theme";

const S = content.scenes.s1;

/** SCÈNE 1 — Paris : vue aérienne verticale → plongée vers le 14e → rue haussmannienne. */
export const S1Paris: React.FC = () => {
  const frame = useCurrentFrame();
  const [a, b] = S.shots;
  const aF = sec(a.durationSec);
  const mapP = tw(frame, [0, aF], [0, 1], (t) => t);
  const footage = has(a.src);
  // ouverture : l'arche DOMOVA se dessine puis s'ouvre comme une porte sur Paris
  const iconDraw = tw(frame, [4, 30], [0, 1], easeInOut);
  const open = tw(frame, [30, 52], [0, 1], easeInOut);
  const aw = 300 + open * 2700;
  const clip = open >= 1 ? undefined : archClip(540, 1010 + open * 1500, aw, aw * 1.25);
  const titleO = tw(frame, [46, 62], [0, 1]) * tw(frame, [sec(2.8), sec(3.3)], [1, 0]);
  const placeO = tw(frame, [sec(3.0), sec(3.5)], [0, 1]) * tw(frame, [sec(7.2), sec(7.8)], [1, 0]);

  return (
    <AbsoluteFill style={{ backgroundColor: C.bordeaux }}>
      <AbsoluteFill style={{ clipPath: frame < 30 ? archClip(540, 1010, 1, 1) : clip }}>
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
            fontSize: 150,
            fontWeight: 300,
            letterSpacing: "0.34em",
            marginRight: "-0.34em",
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
        <div style={{ fontFamily: F.serif, fontWeight: 300, fontSize: 77, color: C.blanc, textShadow: "0 4px 30px rgba(0,0,0,0.7)" }}>{S.place}</div>
        <div style={{ width: tw(frame, [sec(3.1), sec(3.9)], [0, 420]), height: 2, background: C.led, margin: "18px auto" }} />
        <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 26, letterSpacing: 4, color: C.beige }}>{S.coordinates}</div>
      </div>

      <Subtitles lines={S.subtitles} />
      </AbsoluteFill>
      {open < 1 ? (
        <div style={{ position: "absolute", left: 0, right: 0, top: 760, display: "flex", justifyContent: "center", opacity: 1 - open, transform: `scale(${1 + open * 2})` }}>
          <ArchIcon size={230} draw={iconDraw} />
        </div>
      ) : null}
      {open < 1 ? (
        <div
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            top: 1010,
            textAlign: "center",
            fontFamily: F.sans,
            fontWeight: 400,
            fontSize: 26,
            letterSpacing: "0.42em",
            marginRight: "-0.42em",
            color: C.or,
            opacity: tw(frame, [16, 28], [0, 1]) * (1 - open * 2),
          }}
        >
          {content.brand.devise.toUpperCase()}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
