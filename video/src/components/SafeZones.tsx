import React from "react";
import { AbsoluteFill } from "remotion";
import { F, H, SAFE, SUB, W } from "../theme";

/** Calque de contrôle (composition DOMOVA-ZonesSecurite) : zones à éviter en rouge. */
export const SafeZones: React.FC = () => {
  const red = "rgba(255,40,40,0.28)";
  const lab: React.CSSProperties = { position: "absolute", color: "#fff", fontFamily: F.sans, fontSize: 22, fontWeight: 600 };
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div style={{ position: "absolute", left: 0, top: 0, width: W, height: SAFE.top, background: red }} />
      <div style={{ position: "absolute", left: 0, top: SAFE.bottom, width: W, height: H - SAFE.bottom, background: red }} />
      <div style={{ position: "absolute", left: SAFE.right, top: SAFE.top, width: W - SAFE.right, height: SAFE.bottom - SAFE.top, background: red }} />
      <div style={{ position: "absolute", left: 0, top: SAFE.top, width: SAFE.left, height: SAFE.bottom - SAFE.top, background: "rgba(255,160,40,0.2)" }} />
      <div style={{ position: "absolute", left: SAFE.left, top: SUB.bottom - 200, width: SUB.maxWidth, height: 200, border: "3px dashed #4cf" }} />
      <div style={{ ...lab, left: 20, top: 20 }}>HAUT : onglets / compte</div>
      <div style={{ ...lab, left: 20, top: SAFE.bottom + 20 }}>BAS : légende, son, barre de progression</div>
      <div style={{ ...lab, left: SAFE.right + 8, top: 900, width: 150 }}>Boutons plateforme</div>
      <div style={{ ...lab, left: SAFE.left + 10, top: SUB.bottom - 236, color: "#4cf" }}>Bande sous-titres</div>
    </AbsoluteFill>
  );
};
