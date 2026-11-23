import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { tw } from "../lib";
import { C } from "../theme";

/** Enveloppe de scène : fondu d'entrée/sortie et dégradés de lisibilité haut/bas. */
export const Shell: React.FC<{ children: React.ReactNode; fadeIn?: number; fadeOut?: number; grade?: boolean }> = ({
  children,
  fadeIn = 8,
  fadeOut = 8,
  grade = true,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const o = Math.min(
    fadeIn > 0 ? tw(frame, [0, fadeIn], [0, 1]) : 1,
    fadeOut > 0 ? tw(frame, [durationInFrames - fadeOut, durationInFrames], [1, 0]) : 1,
  );
  return (
    <AbsoluteFill style={{ backgroundColor: C.noir }}>
      <AbsoluteFill style={{ opacity: o }}>
        {children}
        {grade ? (
          <AbsoluteFill
            style={{
              pointerEvents: "none",
              background:
                "linear-gradient(180deg, rgba(28,7,12,0.5) 0%, rgba(28,7,12,0) 22%, rgba(28,7,12,0) 58%, rgba(28,7,12,0.6) 100%)",
            }}
          />
        ) : null}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/** Grain filmique léger pour unifier images IA, 3D et vidéos réelles. */
export const Grain: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "overlay", opacity: 0.16 }}>
      <svg width="100%" height="100%">
        <filter id="g">
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed={frame % 12} />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#g)" />
      </svg>
    </AbsoluteFill>
  );
};
