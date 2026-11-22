import React from "react";
import { useCurrentFrame } from "remotion";
import { sec, tw } from "../lib";
import { C, F } from "../theme";

/** Cote architecturale animée (trait qui se dessine + étiquette). x1=x2 et y1=y2 → repère d'angle. */
export const Dimension: React.FC<{
  x1: number; y1: number; x2: number; y2: number;
  value: string; label?: string; atSec: number; color?: string;
}> = ({ x1, y1, x2, y2, value, label, atSec, color = C.blanc }) => {
  const frame = useCurrentFrame() - sec(atSec);
  if (frame < 0) return null;
  const p = tw(frame, [0, 18], [0, 1]);
  const textO = tw(frame, [10, 22], [0, 1]);
  const isAngle = x1 === x2 && y1 === y2;
  const vertical = Math.abs(x2 - x1) < Math.abs(y2 - y1);
  const mx = (x1 + x2) / 2;
  const my = (y1 + y2) / 2;
  const tick = 18;

  if (isAngle) {
    const r = 46 * p;
    return (
      <g>
        <path d={`M ${x1 - r} ${y1} A ${r} ${r} 0 0 1 ${x1} ${y1 - r}`} stroke={C.led} strokeWidth={3} fill="none" />
        <circle cx={x1} cy={y1} r={6} fill={C.led} opacity={p} />
        <text x={x1 - 70} y={y1 - 60} fill={C.led} opacity={textO} fontFamily={F.sans} fontSize={34} fontWeight={600} textAnchor="end">
          {value}
        </text>
        {label ? (
          <text x={x1 - 70} y={y1 - 104} fill={C.blanc} opacity={textO * 0.8} fontFamily={F.sans} fontSize={20} letterSpacing={3} textAnchor="end">
            {label.toUpperCase()}
          </text>
        ) : null}
      </g>
    );
  }

  const ex = x1 + (x2 - x1) * p;
  const ey = y1 + (y2 - y1) * p;
  const tx = vertical ? mx - 22 : mx;
  const ty = vertical ? my : my - 22;
  return (
    <g style={{ filter: "drop-shadow(0 2px 6px rgba(0,0,0,0.6))" }}>
      <line x1={x1} y1={y1} x2={ex} y2={ey} stroke={color} strokeWidth={3} />
      {vertical ? (
        <>
          <line x1={x1 - tick} y1={y1} x2={x1 + tick} y2={y1} stroke={color} strokeWidth={3} />
          <line x1={x2 - tick} y1={ey} x2={x2 + tick} y2={ey} stroke={color} strokeWidth={3} opacity={p} />
        </>
      ) : (
        <>
          <line x1={x1} y1={y1 - tick} x2={x1} y2={y1 + tick} stroke={color} strokeWidth={3} />
          <line x1={ex} y1={y2 - tick} x2={ex} y2={y2 + tick} stroke={color} strokeWidth={3} opacity={p} />
        </>
      )}
      <g opacity={textO} transform={vertical ? `rotate(-90 ${tx} ${ty})` : undefined}>
        <rect x={tx - 95} y={ty - 40} width={190} height={50} rx={8} fill="rgba(13,13,14,0.75)" />
        <text x={tx} y={ty - 4} fill={C.led} fontFamily={F.sans} fontSize={34} fontWeight={600} textAnchor="middle">
          {value}
        </text>
      </g>
      {label ? (
        <text
          x={vertical ? tx - 66 : tx}
          y={vertical ? ty : ty + 50}
          fill={C.blanc}
          opacity={textO * 0.85}
          fontFamily={F.sans}
          fontSize={20}
          letterSpacing={3}
          textAnchor="middle"
          transform={vertical ? `rotate(-90 ${tx - 66} ${ty})` : undefined}
        >
          {label.toUpperCase()}
        </text>
      ) : null}
    </g>
  );
};
