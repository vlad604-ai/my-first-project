import React from "react";
import { AbsoluteFill, Img, useCurrentFrame } from "remotion";
import { file, has } from "../lib";

/**
 * Texture de matériau plein cadre. Utilise la photo /assets/materials/<id>.jpg si elle existe
 * (recommandé : vos vraies photos macro ou les visuels de vos fournisseurs), sinon une texture procédurale.
 */
export const Swatch: React.FC<{ id: string; kind: string; colors: string[]; texture?: string; pan?: number }> = ({
  id,
  kind,
  colors,
  texture,
  pan = 0,
}) => {
  const frame = useCurrentFrame();
  if (has(texture)) {
    return (
      <AbsoluteFill style={{ overflow: "hidden" }}>
        <Img src={file(texture!)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(1.15) translateX(${pan}px)` }} />
      </AbsoluteFill>
    );
  }
  const [a, b] = colors;
  const fid = `f-${id}`;
  const wood = kind === "wood" || kind === "veneer" || kind === "combo";
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: a }}>
      <svg width="140%" height="100%" style={{ position: "absolute", left: -150 + pan }}>
        <defs>
          <filter id={fid} x="0" y="0" width="100%" height="100%">
            {wood ? (
              <feTurbulence type="fractalNoise" baseFrequency="0.0025 0.06" numOctaves={4} seed={id.length * 7} />
            ) : kind === "stone" ? (
              <feTurbulence type="fractalNoise" baseFrequency="0.006" numOctaves={5} seed={9} />
            ) : (
              <feTurbulence type="fractalNoise" baseFrequency={kind === "fine" ? 1.4 : 0.9} numOctaves={2} seed={3} />
            )}
            <feColorMatrix type="saturate" values="0" />
            <feComponentTransfer>
              <feFuncA type="table" tableValues={wood ? "0 0.75" : kind === "stone" ? "0 0.5" : "0 0.12"} />
            </feComponentTransfer>
          </filter>
          <linearGradient id={`g-${id}`} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor={a} />
            <stop offset="1" stopColor={b} />
          </linearGradient>
        </defs>
        <rect width="100%" height="100%" fill={`url(#g-${id})`} />
        <rect width="100%" height="100%" filter={`url(#${fid})`} style={{ mixBlendMode: "multiply" }} />
        {kind === "veneer"
          ? [0.22, 0.47, 0.71].map((x) => <rect key={x} x={`${x * 100}%`} y={0} width={2} height="100%" fill="rgba(0,0,0,0.18)" />)
          : null}
        {kind === "combo" ? <polygon points="0,1100 1600,620 1600,2000 0,2000" fill="#141414" /> : null}
        {kind === "combo" ? <polygon points="0,1100 1600,620 1600,628 0,1108" fill="#FFD9A0" /> : null}
      </svg>
      {kind === "gloss" || kind === "stone" ? (
        <AbsoluteFill
          style={{
            background: `linear-gradient(115deg, transparent ${30 + (frame % 90) / 3}%, rgba(255,255,255,0.45) ${36 + (frame % 90) / 3}%, transparent ${44 + (frame % 90) / 3}%)`,
            mixBlendMode: "screen",
          }}
        />
      ) : null}
    </AbsoluteFill>
  );
};
