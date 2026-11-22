import React, { useMemo } from "react";
import { ThreeCanvas } from "@remotion/three";
import { useThree } from "@react-three/fiber";
import * as THREE from "three";
import { random } from "remotion";
import { H, W } from "../theme";

export type Finish = "chene" | "noyer" | "blanc" | "noir" | "anthracite" | "laque";
export type DeskSpec = {
  length: number; // m
  depth?: number;
  height?: number;
  shape: "straight" | "L" | "floating";
  legs: "panel" | "metal" | "none";
  finish: Finish | string;
  drawers: number;
  drawersBoth?: boolean;
  shelves: number;
  led: number; // 0..1
  /** animations 0..1 */
  lAmount?: number;
  drawerOpen?: number;
  shelfGrow?: number;
};

/* ---------- textures procédurales (remplaçables par de vraies photos) ---------- */
const woodTexture = (base: string, grain: string, seed: string) => {
  const c = document.createElement("canvas");
  c.width = 1024;
  c.height = 512;
  const g = c.getContext("2d")!;
  g.fillStyle = base;
  g.fillRect(0, 0, c.width, c.height);
  for (let i = 0; i < 140; i++) {
    const y0 = random(`${seed}y${i}`) * c.height;
    const amp = 2 + random(`${seed}a${i}`) * 9;
    const freq = 0.004 + random(`${seed}f${i}`) * 0.01;
    g.strokeStyle = grain;
    g.globalAlpha = 0.08 + random(`${seed}o${i}`) * 0.28;
    g.lineWidth = 0.6 + random(`${seed}w${i}`) * 2.6;
    g.beginPath();
    for (let x = 0; x <= c.width; x += 8) {
      const y = y0 + Math.sin(x * freq + i) * amp + Math.sin(x * freq * 3.1) * amp * 0.3;
      if (x === 0) g.moveTo(x, y);
      else g.lineTo(x, y);
    }
    g.stroke();
  }
  g.globalAlpha = 1;
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
};

const useFinish = (finish: string) =>
  useMemo(() => {
    switch (finish) {
      case "chene":
        return new THREE.MeshStandardMaterial({ map: woodTexture("#CDA472", "#8C6438", "chene"), roughness: 0.55 });
      case "noyer":
        return new THREE.MeshStandardMaterial({ map: woodTexture("#6A4428", "#2E1C0F", "noyer"), roughness: 0.5 });
      case "blanc":
        return new THREE.MeshStandardMaterial({ color: "#EDEBE7", roughness: 0.65 });
      case "noir":
        return new THREE.MeshStandardMaterial({ color: "#1A1A1B", roughness: 0.75 });
      case "laque":
        return new THREE.MeshStandardMaterial({ color: "#F3F1ED", roughness: 0.12, metalness: 0.05 });
      default:
        return new THREE.MeshStandardMaterial({ color: "#393A3D", roughness: 0.7 });
    }
  }, [finish]);

const black = new THREE.MeshStandardMaterial({ color: "#121212", roughness: 0.4, metalness: 0.6 });

const Box: React.FC<{ size: [number, number, number]; pos: [number, number, number]; mat: THREE.Material }> = ({ size, pos, mat }) => (
  <mesh position={pos} material={mat}>
    <boxGeometry args={size} />
  </mesh>
);

const Rig: React.FC<{ pos: [number, number, number]; target: [number, number, number]; fov: number }> = ({ pos, target, fov }) => {
  const camera = useThree((s) => s.camera) as THREE.PerspectiveCamera;
  camera.position.set(...pos);
  camera.fov = fov;
  camera.updateProjectionMatrix();
  camera.lookAt(...target);
  return null;
};

export const Desk: React.FC<{ spec: DeskSpec }> = ({ spec }) => {
  const L = spec.length;
  const D = spec.depth ?? 0.7;
  const Ht = spec.height ?? 0.75;
  const T = spec.shape === "floating" ? 0.05 : 0.032;
  const mat = useFinish(spec.finish);
  const front = useFinish(spec.finish === "noyer" ? "noir" : spec.finish);
  const led = spec.led;
  const ledMat = useMemo(() => new THREE.MeshStandardMaterial({ color: "#FFD9A0", emissive: "#FFC98A", toneMapped: false }), []);
  ledMat.emissiveIntensity = 0.2 + led * 4;
  const zBack = -D / 2;
  const topY = Ht - T / 2;
  const lA = spec.shape === "L" ? spec.lAmount ?? 1 : 0;
  const ret = 1.1 * lA;
  const open = spec.drawerOpen ?? 0;
  const grow = spec.shelfGrow ?? 1;
  const nShelves = spec.shelves;
  const caissonW = 0.45;
  const legH = Ht - T;

  const caisson = (side: 1 | -1) => {
    const cx = side * (L / 2 - caissonW / 2 - (spec.legs === "panel" ? 0.025 : 0.04));
    const h = spec.shape === "floating" ? 0.16 : legH - 0.06;
    const n = spec.shape === "floating" ? 1 : Math.max(1, spec.drawers);
    const fh = h / n;
    const y0 = Ht - T - h;
    return (
      <group key={side}>
        <Box size={[caissonW, h, D - 0.06]} pos={[cx, y0 + h / 2, 0]} mat={mat} />
        {Array.from({ length: n }, (_, i) => {
          const z = D / 2 - 0.03 + 0.01 + open * (0.32 - i * 0.06);
          const y = y0 + fh * (n - i - 0.5);
          return (
            <group key={i}>
              <Box size={[caissonW - 0.01, fh - 0.008, 0.018]} pos={[cx, y, z]} mat={front} />
              <Box size={[0.22, 0.012, 0.02]} pos={[cx, y + fh / 2 - 0.05, z + 0.018]} mat={black} />
            </group>
          );
        })}
      </group>
    );
  };

  return (
    <group>
      {/* plateau */}
      <Box size={[L, T, D]} pos={[0, topY, 0]} mat={mat} />
      {/* retour en L */}
      {ret > 0.01 ? <Box size={[D, T, ret]} pos={[L / 2 - D / 2, topY, D / 2 + ret / 2]} mat={mat} /> : null}
      {/* piétement */}
      {spec.legs === "panel" ? (
        <>
          <Box size={[0.025, legH, D]} pos={[-L / 2 + 0.0125, legH / 2, 0]} mat={mat} />
          {ret > 0.01 ? (
            <Box size={[D, legH, 0.025]} pos={[L / 2 - D / 2, legH / 2, D / 2 + ret - 0.0125]} mat={mat} />
          ) : (
            <Box size={[0.025, legH, D]} pos={[L / 2 - 0.0125, legH / 2, 0]} mat={mat} />
          )}
          <Box size={[L - 0.05, 0.3, 0.018]} pos={[0, Ht - T - 0.17, zBack + 0.05]} mat={mat} />
        </>
      ) : null}
      {spec.legs === "metal"
        ? ([[-1, -1], [-1, 1], [1, -1], [1, 1]] as const).map(([sx, sz], i) => (
            <Box key={i} size={[0.035, legH, 0.035]} pos={[sx * (L / 2 - 0.06), legH / 2, sz * (D / 2 - 0.06)]} mat={black} />
          ))
        : null}
      {/* tiroirs */}
      {spec.drawers > 0 ? caisson(1) : null}
      {spec.drawers > 0 && spec.drawersBoth ? caisson(-1) : null}
      {/* LED sous plateau suspendu */}
      {spec.shape === "floating" ? <Box size={[L - 0.1, 0.008, 0.01]} pos={[0, Ht - T - 0.005, D / 2 - 0.08]} mat={ledMat} /> : null}
      {/* étagères / bibliothèque */}
      {nShelves > 0 ? (
        <group>
          {Array.from({ length: nShelves }, (_, i) => {
            const k = Math.min(1, Math.max(0, grow * nShelves - i));
            const y = Ht + 0.42 + i * 0.36;
            return (
              <group key={i} scale={[k, 1, 1]}>
                <Box size={[L, 0.025, 0.28]} pos={[0, y, zBack + 0.14]} mat={mat} />
                <Box size={[L - 0.1, 0.008, 0.01]} pos={[0, y - 0.016, zBack + 0.26]} mat={ledMat} />
                {/* livres */}
                {k > 0.95
                  ? Array.from({ length: 7 }, (_, b) => (
                      <Box
                        key={b}
                        size={[0.035, 0.2 + random(`b${i}${b}`) * 0.08, 0.2]}
                        pos={[-L / 2 + 0.25 + b * 0.045 + (i % 2) * (L * 0.45), y + 0.12, zBack + 0.13]}
                        mat={b % 3 === 0 ? black : front}
                      />
                    ))
                  : null}
              </group>
            );
          })}
          {nShelves >= 3 ? (
            <group scale={[1, Math.max(0.001, grow), 1]} position={[0, Ht * (1 - grow), 0]}>
              <Box size={[0.025, nShelves * 0.36 + 0.1, 0.3]} pos={[-L / 2, Ht + 0.36 + (nShelves * 0.36) / 2, zBack + 0.15]} mat={mat} />
              <Box size={[0.025, nShelves * 0.36 + 0.1, 0.3]} pos={[L / 2, Ht + 0.36 + (nShelves * 0.36) / 2, zBack + 0.15]} mat={mat} />
            </group>
          ) : null}
        </group>
      ) : null}
      {/* éclairage LED réel */}
      {led > 0 ? <pointLight position={[0, Ht + 0.3, zBack + 0.4]} intensity={led * 2.5} distance={3} color="#FFCF94" /> : null}
      {/* objets de bureau */}
      <Box size={[0.5, 0.3, 0.02]} pos={[-0.1, Ht + 0.28, zBack + 0.18]} mat={black} />
      <Box size={[0.03, 0.12, 0.03]} pos={[-0.1, Ht + 0.06, zBack + 0.18]} mat={black} />
    </group>
  );
};

/** Scène 3D complète (mur, sol, lumière, caméra) pour un bureau paramétrique. */
export const DeskScene: React.FC<{
  spec: DeskSpec;
  cam: { pos: [number, number, number]; target: [number, number, number]; fov?: number };
  mood?: "day" | "evening";
  wall?: string;
}> = ({ spec, cam, mood = "day", wall = "#E6E1D9" }) => {
  const day = mood === "day";
  return (
    <ThreeCanvas width={W} height={H} style={{ position: "absolute", inset: 0 }} gl={{ antialias: true, preserveDrawingBuffer: true }}>
      <Rig pos={cam.pos} target={cam.target} fov={cam.fov ?? 42} />
      <color attach="background" args={[day ? "#ddd7ce" : "#1a1918"]} />
      <ambientLight intensity={day ? 0.75 : 0.18} />
      <hemisphereLight args={["#fff6ea", "#5b4a3a", day ? 0.6 : 0.15]} />
      <directionalLight position={[-2.5, 4, 3]} intensity={day ? 2.0 : 0.35} color="#fff3e2" />
      <directionalLight position={[3, 2, 2]} intensity={day ? 0.5 : 0.1} color="#dfe8ff" />
      {/* mur et sol */}
      <mesh position={[0, 2, -0.36 - 0.01]}>
        <planeGeometry args={[12, 6]} />
        <meshStandardMaterial color={day ? wall : "#3a3633"} roughness={0.95} />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 2]}>
        <planeGeometry args={[12, 8]} />
        <meshStandardMaterial color={day ? "#B49573" : "#3b2e24"} roughness={0.8} />
      </mesh>
      <Desk spec={spec} />
    </ThreeCanvas>
  );
};
