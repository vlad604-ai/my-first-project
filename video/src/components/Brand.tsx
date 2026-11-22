import React from "react";
import { Img, useCurrentFrame } from "remotion";
import { content, file, firstExisting, tw } from "../lib";
import { C, F, SAFE } from "../theme";

/** Logo DOMOVA : utilise /assets/logo/logo.png (ou .svg) s'il existe, sinon un logotype typographique. */
export const Logo: React.FC<{ height: number; color?: string; tracking?: number }> = ({
  height,
  color = C.blanc,
  tracking = 0.32,
}) => {
  const src = firstExisting(content.brand.logo, ...content.brand.logoAlternatives);
  if (src) return <Img src={file(src)} style={{ height, width: "auto", objectFit: "contain" }} />;
  return (
    <div
      style={{
        fontFamily: F.serif,
        fontWeight: 500,
        fontSize: height,
        lineHeight: 1,
        letterSpacing: `${tracking}em`,
        marginRight: `-${tracking}em`,
        color,
      }}
    >
      {content.brand.name}
    </div>
  );
};

/** Signature discrète en haut à gauche de la zone sûre + titre de chapitre. */
export const BrandBug: React.FC<{ chapter?: string; delay?: number }> = ({ chapter, delay = 6 }) => {
  const frame = useCurrentFrame();
  const o = tw(frame, [delay, delay + 14], [0, 1]);
  return (
    <div style={{ position: "absolute", left: SAFE.left, top: SAFE.top + 20, opacity: o, filter: "drop-shadow(0 1px 6px rgba(0,0,0,0.55))" }}>
      <div style={{ opacity: 0.82 }}>
        <Logo height={34} />
      </div>
      {chapter ? (
        <div
          style={{
            marginTop: 14,
            fontFamily: F.sans,
            fontSize: 21,
            fontWeight: 500,
            letterSpacing: 5,
            color: C.beige,
            transform: `translateX(${tw(frame, [delay + 4, delay + 22], [-16, 0])}px)`,
            opacity: tw(frame, [delay + 4, delay + 22], [0, 1]),
            textShadow: "0 1px 8px rgba(0,0,0,0.6)",
          }}
        >
          {chapter}
        </div>
      ) : null}
    </div>
  );
};
