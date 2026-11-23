import React from "react";
import { AbsoluteFill, Audio, Composition, interpolate, Sequence, useVideoConfig } from "remotion";
import { Shell } from "./components/Shell";
import { SafeZones } from "./components/SafeZones";
import { content, file, has, sceneFrames, SceneId, totalFrames } from "./lib";
import { S1Paris } from "./scenes/S1Paris";
import { S2Rencontre } from "./scenes/S2Rencontre";
import { S3Decouverte } from "./scenes/S3Decouverte";
import { S4Conception } from "./scenes/S4Conception";
import { S5Materiaux } from "./scenes/S5Materiaux";
import { S5bInspirations } from "./scenes/S5bInspirations";
import { S6AvantApres } from "./scenes/S6AvantApres";
import { S7Decouverte } from "./scenes/S7Decouverte";
import { S8Conclusion } from "./scenes/S8Conclusion";
import { FPS, H, W } from "./theme";

const SCENES: { id: SceneId; name: string; C: React.FC; fadeIn?: number; fadeOut?: number }[] = [
  { id: "s1", name: "S1-Paris", C: S1Paris, fadeIn: 18 },
  { id: "s2", name: "S2-Rencontre", C: S2Rencontre },
  { id: "s3", name: "S3-Decouverte", C: S3Decouverte },
  { id: "s4", name: "S4-Conception", C: S4Conception },
  { id: "s5", name: "S5-Materiaux", C: S5Materiaux },
  { id: "s5b", name: "S5b-Inspirations", C: S5bInspirations },
  { id: "s6", name: "S6-AvantApres", C: S6AvantApres },
  { id: "s7", name: "S7-LeClientDecouvre", C: S7Decouverte },
  { id: "s8", name: "S8-Conclusion", C: S8Conclusion, fadeOut: 0 },
];

const Voice: React.FC<{ id: SceneId }> = ({ id }) => {
  const v = content.scenes[id].voice;
  return has(v) ? (
    <Sequence from={6}>
      <Audio src={file(v)} volume={content.audio.voiceVolume} />
    </Sequence>
  ) : null;
};

const Music: React.FC = () => {
  const { durationInFrames } = useVideoConfig();
  const a = content.audio;
  if (!has(a.music)) return null;
  const anyVoice = SCENES.some((s) => has(content.scenes[s.id].voice));
  const base = anyVoice ? a.musicVolumeUnderVoice : a.musicVolume;
  return (
    <Audio
      src={file(a.music)}
      volume={(f) =>
        interpolate(f, [0, 20, durationInFrames - 60, durationInFrames], [0, base, base, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        })
      }
    />
  );
};

export const Main: React.FC<{ showSafeZones?: boolean }> = ({ showSafeZones }) => {
  let from = 0;
  return (
    <AbsoluteFill style={{ backgroundColor: "#0D0D0E" }}>
      {SCENES.map(({ id, C, fadeIn, fadeOut }) => {
        const d = sceneFrames(id);
        const el = (
          <Sequence key={id} from={from} durationInFrames={d} name={id}>
            <Shell fadeIn={fadeIn} fadeOut={fadeOut}>
              <C />
            </Shell>
            <Voice id={id} />
          </Sequence>
        );
        from += d;
        return el;
      })}
      <Music />
      {showSafeZones ? <SafeZones /> : null}
    </AbsoluteFill>
  );
};

const Single: React.FC<{ id: SceneId; showSafeZones?: boolean }> = ({ id, showSafeZones }) => {
  const s = SCENES.find((x) => x.id === id)!;
  return (
    <AbsoluteFill>
      <Shell fadeIn={s.fadeIn} fadeOut={s.fadeOut}>
        <s.C />
      </Shell>
      <Voice id={id} />
      {showSafeZones ? <SafeZones /> : null}
    </AbsoluteFill>
  );
};

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="DOMOVA" component={Main} durationInFrames={totalFrames()} fps={FPS} width={W} height={H} defaultProps={{ showSafeZones: false }} />
    <Composition id="DOMOVA-ZonesSecurite" component={Main} durationInFrames={totalFrames()} fps={FPS} width={W} height={H} defaultProps={{ showSafeZones: true }} />
    {SCENES.map((s) => (
      <Composition
        key={s.id}
        id={s.name}
        component={Single}
        durationInFrames={sceneFrames(s.id)}
        fps={FPS}
        width={W}
        height={H}
        defaultProps={{ id: s.id, showSafeZones: false }}
      />
    ))}
  </>
);

