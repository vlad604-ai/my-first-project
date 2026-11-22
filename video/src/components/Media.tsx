import React from "react";
import { AbsoluteFill, Img, OffthreadVideo, useCurrentFrame, useVideoConfig } from "remotion";
import { file, has, isVideo, sec, tw } from "../lib";
import { Placeholder } from "./Placeholder";

export type Fit = "cover" | "contain-blur";

type Props = {
  src?: string;
  startSec?: number;
  fit?: Fit;
  focusX?: number;
  focusY?: number;
  /** zoom lent sur la durée du plan (Ken Burns) : [échelle début, échelle fin] */
  push?: [number, number];
  /** décalage vertical en px sur la durée, pour un mouvement de grue */
  drift?: [number, number];
  placeholder: { id: string; title: string; source?: string; tone?: "dark" | "warm" | "alert" };
  fallback?: React.ReactNode;
  style?: React.CSSProperties;
  volume?: number;
  playbackRate?: number;
};

const Raw: React.FC<{ src: string; startSec: number; style: React.CSSProperties; volume: number; playbackRate?: number }> = ({
  src,
  startSec,
  style,
  volume,
  playbackRate = 1,
}) =>
  isVideo(src) ? (
    <OffthreadVideo src={file(src)} startFrom={sec(startSec)} volume={volume} playbackRate={playbackRate} style={style} />
  ) : (
    <Img src={file(src)} style={style} />
  );

/** Affiche une vidéo/une image plein cadre 9:16, ou un écran de repère si le fichier manque. */
export const Media: React.FC<Props> = ({
  src,
  startSec = 0,
  fit = "cover",
  focusX = 0.5,
  focusY = 0.5,
  push = [1.04, 1.12],
  drift = [0, 0],
  placeholder,
  fallback,
  style,
  volume = 0,
  playbackRate = 1,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const s = tw(frame, [0, durationInFrames], push, (t) => t);
  const dy = tw(frame, [0, durationInFrames], drift, (t) => t);
  const motion: React.CSSProperties = { transform: `translateY(${dy}px) scale(${s})`, transformOrigin: `${focusX * 100}% ${focusY * 100}%` };

  if (!has(src)) {
    return fallback ? (
      <AbsoluteFill style={style}>{fallback}</AbsoluteFill>
    ) : (
      <AbsoluteFill style={style}>
        <Placeholder {...placeholder} path={src} />
      </AbsoluteFill>
    );
  }

  const cover: React.CSSProperties = {
    position: "absolute",
    width: "100%",
    height: "100%",
    objectFit: "cover",
    objectPosition: `${focusX * 100}% ${focusY * 100}%`,
  };

  if (fit === "contain-blur") {
    return (
      <AbsoluteFill style={{ overflow: "hidden", backgroundColor: "#111", ...style }}>
        <AbsoluteFill style={{ filter: "blur(40px) brightness(0.55)", transform: "scale(1.2)" }}>
          <Raw src={src} startSec={startSec} style={cover} volume={0} playbackRate={playbackRate} />
        </AbsoluteFill>
        <AbsoluteFill style={motion}>
          <Raw src={src} startSec={startSec} style={{ ...cover, objectFit: "contain" }} volume={volume} playbackRate={playbackRate} />
        </AbsoluteFill>
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: "#111", ...style }}>
      <AbsoluteFill style={motion}>
        <Raw src={src} startSec={startSec} style={cover} volume={volume} playbackRate={playbackRate} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
