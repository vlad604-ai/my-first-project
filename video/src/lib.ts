import { Easing, interpolate, staticFile } from "remotion";
import content from "./content/domova.json";
import assets from "./generated/assets.json";
import { FPS } from "./theme";

export { content };
export type SceneId = keyof typeof content.scenes;

const present = new Set<string>(assets.files);
export const has = (p?: string | null): p is string => !!p && present.has(p);
export const file = (p: string) => staticFile(p);
export const firstExisting = (...paths: (string | undefined)[]) => paths.find((p) => has(p));
export const isVideo = (p: string) => /\.(mp4|mov|webm|m4v)$/i.test(p);

export const sec = (s: number) => Math.round(s * FPS);
export const sceneFrames = (id: SceneId) => sec(content.scenes[id].durationSec);
export const totalFrames = () =>
  (Object.keys(content.scenes) as SceneId[]).reduce((a, id) => a + sceneFrames(id), 0);

export const ease = Easing.bezier(0.22, 1, 0.36, 1); // sortie douce « luxe »
export const easeInOut = Easing.bezier(0.65, 0, 0.35, 1);

/** Interpolation bornée avec easing par défaut. */
export const tw = (
  frame: number,
  [a, b]: [number, number],
  [from, to]: [number, number],
  easing = ease,
) => interpolate(frame, [a, b], [from, to], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing });
