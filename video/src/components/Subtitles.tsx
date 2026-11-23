import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { sec, tw } from "../lib";
import { C, F, SAFE, SAFE_CX, SUB } from "../theme";

/**
 * Sous-titres intégrés, découpés en segments courts.
 * Le timing est réparti selon la longueur de chaque segment
 * (calé sur un débit de voix off publicitaire). Pour un calage exact
 * sur la voix enregistrée, renseignez "subtitleTimes" (en secondes) dans le JSON.
 */
export const Subtitles: React.FC<{ lines: string[]; times?: number[]; lead?: number; tail?: number }> = ({
  lines,
  times,
  lead = 0.25,
  tail = 0.35,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  if (!lines.length) return null;

  const start = sec(lead);
  const end = durationInFrames - sec(tail);
  const weights = lines.map((l) => l.length + 12);
  const total = weights.reduce((a, b) => a + b, 0);
  let acc = start;
  const slots = lines.map((l, i) => {
    const a = times?.[i] !== undefined ? sec(times[i]) : acc;
    const len = ((end - start) * weights[i]) / total;
    const b = times?.[i + 1] !== undefined ? sec(times[i + 1]) : a + len;
    acc = a + len;
    return { l, a, b };
  });
  const cur = slots.find((s) => frame >= s.a && frame < s.b);
  if (!cur) return null;
  const local = frame - cur.a;
  const o = tw(local, [0, 5], [0, 1]) * tw(frame, [cur.b - 4, cur.b], [1, 0]);
  const y = tw(local, [0, 8], [14, 0]);

  return (
    <div
      style={{
        position: "absolute",
        left: SAFE.left,
        width: SUB.maxWidth,
        top: SUB.bottom - 200,
        height: 200,
        display: "flex",
        alignItems: "flex-end",
        justifyContent: "center",
        opacity: o,
        transform: `translateY(${y}px)`,
      }}
    >
      <div
        style={{
          maxWidth: SUB.maxWidth,
          textAlign: "center",
          fontFamily: F.sans,
          fontWeight: 500,
          fontSize: 46,
          letterSpacing: "0.01em",
          lineHeight: 1.22,
          color: C.blanc,
          padding: "14px 26px 16px",
          borderRadius: 14,
          background: "rgba(43,12,19,0.74)",
          textShadow: "0 2px 10px rgba(0,0,0,0.5)",
        }}
      >
        {cur.l}
      </div>
      {/* repère invisible pour garder le centre de la bande */}
      <div style={{ position: "absolute", left: SAFE_CX - SAFE.left, top: 0 }} />
    </div>
  );
};
