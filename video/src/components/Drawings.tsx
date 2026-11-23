import React, { useMemo } from "react";
import { random, useCurrentFrame } from "remotion";
import { tw } from "../lib";
import { C, F, H, W } from "../theme";

/* ------------------------------------------------------------------ */
/* Carte stylisée de Paris : sert d'animatique et de calque graphique  */
/* par-dessus le plan aérien réel/IA (ligne fine, fond transparent).   */
/* ------------------------------------------------------------------ */
export const PARIS_TARGET = { x: 500, y: 1150 }; // position du 14e dans le dessin

export const ParisMap: React.FC<{ progress: number; transparent?: boolean }> = ({ progress, transparent }) => {
  const streets = useMemo(() => {
    const out: string[] = [];
    // boulevards rayonnants
    for (let i = 0; i < 22; i++) {
      const a = (i / 22) * Math.PI * 2 + random(`a${i}`) * 0.12;
      out.push(`M540 960 L${540 + Math.cos(a) * 620} ${960 + Math.sin(a) * 620}`);
    }
    // tissu de rues (îlots haussmanniens)
    for (let i = 0; i < 520; i++) {
      const x = random(`x${i}`) * 1080;
      const y = 380 + random(`y${i}`) * 1160;
      // îlots : rues orthogonales dont l'orientation varie par quartier
      const a = (Math.floor(x / 270) * 0.5 + Math.floor(y / 290) * 0.35) + (random(`r${i}`) > 0.5 ? 0 : Math.PI / 2);
      const l = 30 + random(`l${i}`) * 110;
      out.push(`M${x} ${y} l${Math.cos(a) * l} ${Math.sin(a) * l}`);
    }
    return out;
  }, []);
  const line = transparent ? "rgba(245,243,239,0.55)" : "rgba(216,201,177,0.38)";
  const zoom = 1 + progress * progress * 7;
  const tilt = progress * 38;
  const pin = tw(progress, [0.55, 0.8], [0, 1]);

  return (
    <div style={{ position: "absolute", inset: 0, perspective: 1400, overflow: "hidden" }}>
      <div
        style={{
          position: "absolute",
          inset: 0,
          transformOrigin: `${PARIS_TARGET.x}px ${PARIS_TARGET.y}px`,
          transform: `rotateX(${tilt}deg) scale(${zoom})`,
          background: transparent ? "transparent" : `radial-gradient(circle at 50% 50%, #4A1420 0%, ${C.noir} 75%)`,
        }}
      >
        <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
          <defs>
            <clipPath id="paris">
              <ellipse cx={540} cy={960} rx={520} ry={430} />
            </clipPath>
          </defs>
          <g clipPath="url(#paris)" stroke={line} strokeWidth={1.2} fill="none">
            {streets.map((d, i) => (
              <path key={i} d={d} />
            ))}
          </g>
          {/* périphérique */}
          <ellipse cx={540} cy={960} rx={520} ry={430} stroke={C.beige} strokeOpacity={0.6} strokeWidth={3} fill="none" />
          {/* la Seine */}
          <path
            d="M20 820 C 200 760, 330 880, 470 860 S 700 760, 820 860 S 1000 1010, 1070 1060"
            stroke={C.or}
            strokeOpacity={0.55}
            strokeWidth={14}
            fill="none"
            strokeLinecap="round"
          />
          {/* 14e arrondissement */}
          <path
            d="M420 1060 L560 1050 L610 1150 L580 1300 L430 1320 L390 1200 Z"
            fill={C.or}
            fillOpacity={0.12 + pin * 0.25}
            stroke={C.led}
            strokeOpacity={0.4 + pin * 0.6}
            strokeWidth={3}
          />
          <circle cx={PARIS_TARGET.x} cy={PARIS_TARGET.y} r={10 + pin * 6} fill={C.led} opacity={pin} />
          <circle cx={PARIS_TARGET.x} cy={PARIS_TARGET.y} r={30 + ((progress * 600) % 40)} stroke={C.led} strokeWidth={2} fill="none" opacity={pin * 0.6} />
        </svg>
      </div>
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* Pièce vide en perspective centrale (animatique de la scène 3).      */
/* ------------------------------------------------------------------ */
export const EmptyRoom: React.FC<{ light?: number }> = ({ light = 1 }) => {
  const frame = useCurrentFrame();
  const bw = { x1: 300, y1: 600, x2: 780, y2: 1250 }; // mur du fond
  const planks = Array.from({ length: 14 }, (_, i) => -260 + i * 120);
  const sun = 0.5 + 0.08 * Math.sin(frame / 25);
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0 }}>
      <defs>
        <linearGradient id="wall" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#e9e2d6" />
          <stop offset="1" stopColor="#d5cbbb" />
        </linearGradient>
        <linearGradient id="side" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#c9bfae" />
          <stop offset="1" stopColor="#ddd4c6" />
        </linearGradient>
        <linearGradient id="floor" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#b89870" />
          <stop offset="1" stopColor="#8e6e4b" />
        </linearGradient>
        <radialGradient id="sun" cx="0.25" cy="0.55" r="0.6">
          <stop offset="0" stopColor="#fff4dc" stopOpacity={sun} />
          <stop offset="1" stopColor="#fff4dc" stopOpacity={0} />
        </radialGradient>
      </defs>
      {/* plafond */}
      <polygon points={`0,0 ${W},0 ${bw.x2},${bw.y1} ${bw.x1},${bw.y1}`} fill="#efeae2" />
      {/* murs latéraux */}
      <polygon points={`0,0 ${bw.x1},${bw.y1} ${bw.x1},${bw.y2} 0,${H}`} fill="url(#side)" />
      <polygon points={`${W},0 ${bw.x2},${bw.y1} ${bw.x2},${bw.y2} ${W},${H}`} fill="#cfc5b5" />
      {/* sol parquet */}
      <polygon points={`0,${H} ${bw.x1},${bw.y2} ${bw.x2},${bw.y2} ${W},${H}`} fill="url(#floor)" />
      {planks.map((x, i) => (
        <line key={i} x1={bw.x1 + ((x + 260) / 1560) * (bw.x2 - bw.x1)} y1={bw.y2} x2={x} y2={H} stroke="#6f5338" strokeOpacity={0.35} strokeWidth={2} />
      ))}
      {/* mur du fond */}
      <rect x={bw.x1} y={bw.y1} width={bw.x2 - bw.x1} height={bw.y2 - bw.y1} fill="url(#wall)" />
      {/* fenêtre sur mur gauche */}
      <polygon points="70,560 230,640 230,1080 70,1150" fill="#f6f2ea" stroke="#9c9183" strokeWidth={6} />
      <line x1={150} y1={600} x2={150} y2={1115} stroke="#9c9183" strokeWidth={5} />
      {/* plinthes, moulure haussmannienne */}
      <line x1={bw.x1} y1={bw.y2 - 14} x2={bw.x2} y2={bw.y2 - 14} stroke="#f4efe7" strokeWidth={10} />
      <rect x={bw.x1 + 40} y={bw.y1 + 60} width={bw.x2 - bw.x1 - 80} height={360} fill="none" stroke="#cbbfac" strokeWidth={3} />
      <rect x={0} y={0} width={W} height={H} fill="url(#sun)" opacity={light} />
    </svg>
  );
};

/* ------------------------------------------------------------------ */
/* Plan 2D façon architecte (vue de dessus) qui se dessine.            */
/* ------------------------------------------------------------------ */
export const Plan2D: React.FC<{ p: number }> = ({ p }) => {
  const draw = (start: number, end: number) => tw(p, [start, end], [0, 1]);
  const dash = (len: number, k: number) => ({ strokeDasharray: len, strokeDashoffset: len * (1 - k) });
  const room = { x: 170, y: 520, w: 740, h: 940 };
  const blue = C.creme;
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0 }}>
      <defs>
        <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
          <path d="M40 0 L0 0 0 40" fill="none" stroke="rgba(243,233,220,0.06)" strokeWidth="1" />
        </pattern>
      </defs>
      <rect width={W} height={H} fill={C.bordeauxNuit} />
      <rect width={W} height={H} fill="url(#grid)" />
      {/* murs */}
      <rect x={room.x} y={room.y} width={room.w} height={room.h} fill="none" stroke={blue} strokeWidth={14} style={dash(3400, draw(0, 0.35))} />
      {/* fenêtre */}
      <line x1={room.x} y1={700} x2={room.x} y2={940} stroke={C.bordeauxNuit} strokeWidth={16} opacity={draw(0.3, 0.35)} />
      <line x1={room.x - 8} y1={700} x2={room.x - 8} y2={940} stroke={C.creme} strokeWidth={3} opacity={draw(0.3, 0.4)} />
      <line x1={room.x + 8} y1={700} x2={room.x + 8} y2={940} stroke={C.creme} strokeWidth={3} opacity={draw(0.3, 0.4)} />
      {/* porte */}
      <path d={`M ${room.x + room.w - 220} ${room.y + room.h} A 180 180 0 0 1 ${room.x + room.w - 40} ${room.y + room.h - 180}`} stroke={blue} strokeOpacity={0.6} strokeWidth={3} fill="none" style={dash(300, draw(0.35, 0.45))} />
      {/* bureau en L */}
      <path
        d={`M ${room.x + 20} ${room.y + 20} H ${room.x + room.w - 20} V ${room.y + 620} H ${room.x + room.w - 200} V ${room.y + 200} H ${room.x + 20} Z`}
        fill={C.or}
        fillOpacity={0.18 * draw(0.55, 0.7)}
        stroke={C.led}
        strokeWidth={5}
        style={dash(3000, draw(0.4, 0.62))}
      />
      {/* tiroirs */}
      {[0, 1, 2].map((i) => (
        <rect key={i} x={room.x + room.w - 190} y={room.y + 300 + i * 100} width={160} height={86} fill="none" stroke={C.led} strokeOpacity={0.7} strokeWidth={2} opacity={draw(0.6 + i * 0.03, 0.7 + i * 0.03)} />
      ))}
      {/* fauteuil */}
      <circle cx={room.x + 360} cy={room.y + 300} r={60} fill="none" stroke={blue} strokeOpacity={0.6} strokeWidth={3} opacity={draw(0.65, 0.75)} />
      {/* cotes */}
      <g opacity={draw(0.7, 0.85)} fontFamily={F.sans} fill={C.led} fontSize={30} fontWeight={600}>
        <line x1={room.x + 20} y1={room.y - 50} x2={room.x + room.w - 20} y2={room.y - 50} stroke={C.led} strokeWidth={2} />
        <text x={room.x + room.w / 2} y={room.y - 66} textAnchor="middle">240 cm</text>
        <line x1={room.x + room.w + 40} y1={room.y + 20} x2={room.x + room.w + 40} y2={room.y + 620} stroke={C.led} strokeWidth={2} />
        <text x={room.x + room.w + 60} y={room.y + 330} textAnchor="middle" transform={`rotate(90 ${room.x + room.w + 60} ${room.y + 330})`}>160 cm</text>
        <text x={room.x + 40} y={room.y + 160} fontSize={24} fill={blue} fillOpacity={0.8}>P. 70 cm</text>
      </g>
      <g opacity={draw(0.8, 0.95)} fontFamily={F.sans} fill={blue} fontSize={20} letterSpacing={4}>
        <text x={room.x} y={room.y + room.h + 70}>PLAN — BUREAU SUR MESURE · ÉCH. 1:20</text>
      </g>
    </svg>
  );
};

/* ------------------------------------------------------------------ */
/* Plan 2D d'un comptoir arrondi (vue de dessus), qui se dessine.      */
/* ------------------------------------------------------------------ */
export const PlanCurved: React.FC<{ p: number }> = ({ p }) => {
  const draw = (start: number, end: number) => tw(p, [start, end], [0, 1]);
  const dash = (len: number, k: number) => ({ strokeDasharray: len, strokeDashoffset: len * (1 - k) });
  const room = { x: 170, y: 520, w: 740, h: 940 };
  const blue = C.creme;
  const cx = 540;
  const cy = 700;
  const ro = 400;
  const ri = 270;
  const pt = (r: number, deg: number) => [cx + r * Math.cos((deg * Math.PI) / 180), cy + r * Math.sin((deg * Math.PI) / 180)];
  const [o1x, o1y] = pt(ro, 12);
  const [o2x, o2y] = pt(ro, 168);
  const [i1x, i1y] = pt(ri, 12);
  const [i2x, i2y] = pt(ri, 168);
  const [l1x, l1y] = pt(ro + 16, 14);
  const [l2x, l2y] = pt(ro + 16, 166);
  const counter = `M ${o1x} ${o1y} A ${ro} ${ro} 0 0 1 ${o2x} ${o2y} L ${i2x} ${i2y} A ${ri} ${ri} 0 0 0 ${i1x} ${i1y} Z`;
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0 }}>
      <defs>
        <pattern id="gridc" width="40" height="40" patternUnits="userSpaceOnUse">
          <path d="M40 0 L0 0 0 40" fill="none" stroke="rgba(243,233,220,0.06)" strokeWidth="1" />
        </pattern>
      </defs>
      <rect width={W} height={H} fill={C.bordeauxNuit} />
      <rect width={W} height={H} fill="url(#gridc)" />
      <rect x={room.x} y={room.y} width={room.w} height={room.h} fill="none" stroke={blue} strokeWidth={14} style={dash(3400, draw(0, 0.3))} />
      {/* verrière sur le mur du fond */}
      <line x1={560} y1={room.y} x2={800} y2={room.y} stroke={C.creme} strokeWidth={6} opacity={draw(0.25, 0.35)} />
      {/* comptoir arrondi */}
      <path d={counter} fill={C.noyer} fillOpacity={0.35 * draw(0.55, 0.7)} stroke={C.led} strokeWidth={5} style={dash(2600, draw(0.3, 0.6))} />
      {/* ruban LED */}
      <path d={`M ${l1x} ${l1y} A ${ro + 16} ${ro + 16} 0 0 1 ${l2x} ${l2y}`} fill="none" stroke={C.led} strokeWidth={3} strokeDasharray="10 8" opacity={draw(0.6, 0.7)} />
      {/* fauteuils et passe-câbles */}
      {[470, 610].map((x, i) => (
        <circle key={x} cx={x} cy={830} r={46} fill="none" stroke={blue} strokeOpacity={0.6} strokeWidth={3} opacity={draw(0.65 + i * 0.03, 0.75 + i * 0.03)} />
      ))}
      {[[400, 980], [680, 980]].map(([x, y]) => (
        <circle key={x} cx={x} cy={y} r={10} fill="none" stroke={C.led} strokeWidth={2} opacity={draw(0.7, 0.78)} />
      ))}
      <g opacity={draw(0.72, 0.88)} fontFamily={F.sans} fill={C.led} fontSize={28} fontWeight={600}>
        <line x1={o2x} y1={o2y + 120} x2={o1x} y2={o1y + 120} stroke={C.led} strokeWidth={2} />
        <line x1={o2x} y1={o2y + 105} x2={o2x} y2={o2y + 135} stroke={C.led} strokeWidth={2} />
        <line x1={o1x} y1={o1y + 105} x2={o1x} y2={o1y + 135} stroke={C.led} strokeWidth={2} />
        <text x={cx} y={o1y + 108} textAnchor="middle">Cotes relevées sur site</text>
        <line x1={cx} y1={cy} x2={pt(ro, 60)[0]} y2={pt(ro, 60)[1]} stroke={C.led} strokeWidth={2} strokeDasharray="6 6" />
        <text x={pt(ro * 0.55, 60)[0] + 18} y={pt(ro * 0.55, 60)[1]} fontSize={24}>R. sur mesure</text>
      </g>
      <g opacity={draw(0.8, 0.95)} fontFamily={F.sans} fill={blue} fontSize={20} letterSpacing={4}>
        <text x={room.x} y={room.y + room.h + 70}>PLAN — COMPTOIR ARRONDI · ÉCH. 1:20</text>
      </g>
    </svg>
  );
};
