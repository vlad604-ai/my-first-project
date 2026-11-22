import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { C, F, SAFE, SAFE_W } from "../theme";

/**
 * Écran de repère affiché tant qu'un média n'est pas fourni.
 * Il indique précisément quel plan déposer et où.
 */
export const Placeholder: React.FC<{
  id: string;
  title: string;
  source?: string;
  path?: string;
  tone?: "dark" | "warm" | "alert";
  children?: React.ReactNode;
}> = ({ id, title, source, path, tone = "dark", children }) => {
  const frame = useCurrentFrame();
  const sweep = (frame * 6) % 2600;
  const bg =
    tone === "warm"
      ? `linear-gradient(170deg, #3b3127 0%, ${C.anthracite} 55%, #141415 100%)`
      : tone === "alert"
        ? `linear-gradient(170deg, #3a2a20 0%, #1b1716 100%)`
        : `linear-gradient(170deg, ${C.anthraciteClair} 0%, ${C.anthracite} 45%, ${C.noir} 100%)`;
  return (
    <AbsoluteFill style={{ background: bg, overflow: "hidden" }}>
      {children}
      <div
        style={{
          position: "absolute",
          left: -600 + sweep,
          top: -400,
          width: 260,
          height: 2800,
          transform: "rotate(18deg)",
          background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.05), transparent)",
        }}
      />
      <div
        style={{
          position: "absolute",
          left: SAFE.left,
          width: SAFE_W,
          top: 560,
          border: `1px solid rgba(216,201,177,0.45)`,
          padding: "34px 38px",
          background: "rgba(13,13,14,0.55)",
          color: C.blanc,
          fontFamily: F.sans,
        }}
      >
        <div style={{ fontSize: 24, letterSpacing: 6, color: C.beige, fontWeight: 500 }}>
          {tone === "alert" ? "VOTRE VIDÉO" : "PLAN À INSÉRER"} · {id}
        </div>
        <div style={{ fontFamily: F.serif, fontSize: 52, lineHeight: 1.1, marginTop: 18 }}>{title}</div>
        {source ? <div style={{ fontSize: 24, marginTop: 20, color: "#bdb8b0" }}>{source}</div> : null}
        {path ? (
          <div style={{ fontSize: 22, marginTop: 14, color: C.beige, fontFamily: "'JetBrains Mono', monospace" }}>
            /assets/{path}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
