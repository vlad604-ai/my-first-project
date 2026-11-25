import { useState } from "react";

/** Single-series vertical bar chart: thin rounded bars, recessive grid, hover tooltip, table view. */
export function DailyBars({ data, title }: { data: { day: string; count: number }[]; title: string }) {
  const [hover, setHover] = useState<number | null>(null);
  const [asTable, setAsTable] = useState(false);
  const W = 640, H = 220, padL = 32, padB = 24, padT = 12;
  const max = Math.max(1, ...data.map((d) => d.count));
  const niceMax = max <= 4 ? 4 : Math.ceil(max / 20) * 20; // divisible by 4 -> integer ticks
  const step = data.length ? (W - padL) / data.length : 0;
  const barW = Math.max(2, Math.min(18, step - 2)); // 2px surface gap between neighbours
  const y = (v: number) => padT + (H - padT - padB) * (1 - v / niceMax);
  const ticks = [0, niceMax / 4, niceMax / 2, (3 * niceMax) / 4, niceMax];
  const label = (d: string) => new Date(`${d}T12:00:00Z`).toLocaleDateString("fr-FR", { day: "numeric", month: "short" });

  return (
    <figure className="card">
      <div className="mb-2 flex items-center justify-between">
        <figcaption className="text-sm font-semibold">{title}</figcaption>
        <button className="text-xs muted underline" onClick={() => setAsTable((v) => !v)}>
          {asTable ? "Voir le graphique" : "Voir le tableau"}
        </button>
      </div>
      {!data.length && <p className="text-sm muted">Aucune donnée sur la période.</p>}
      {data.length > 0 && asTable && (
        <table className="w-full text-sm">
          <thead><tr className="muted"><th className="text-left">Jour</th><th className="text-right">Réservations</th></tr></thead>
          <tbody>{data.map((d) => <tr key={d.day}><td>{label(d.day)}</td><td className="text-right">{d.count}</td></tr>)}</tbody>
        </table>
      )}
      {data.length > 0 && !asTable && (
        <div className="relative">
          <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label={title}>
            {ticks.map((t) => (
              <g key={t}>
                <line x1={padL} x2={W} y1={y(t)} y2={y(t)} stroke="var(--grid)" strokeWidth={1} />
                <text x={padL - 6} y={y(t) + 4} textAnchor="end" fontSize={10} fill="var(--text-secondary)">{t}</text>
              </g>
            ))}
            {data.map((d, i) => {
              const x = padL + i * step + (step - barW) / 2;
              const top = y(d.count), base = y(0);
              const h = Math.max(0, base - top);
              const r = Math.min(4, barW / 2, h);
              const path = h > 0
                ? `M${x},${base} V${top + r} Q${x},${top} ${x + r},${top} H${x + barW - r} Q${x + barW},${top} ${x + barW},${top + r} V${base} Z`
                : "";
              return (
                <g key={d.day} onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}>
                  <rect x={padL + i * step} y={padT} width={step} height={H - padT - padB} fill="transparent" />
                  {path && <path d={path} fill="var(--series-1)" opacity={hover === null || hover === i ? 1 : 0.55} />}
                </g>
              );
            })}
            {data.map((d, i) => (i % Math.ceil(data.length / 6) === 0 ? (
              <text key={d.day} x={padL + i * step + step / 2} y={H - 6} fontSize={10}
                    textAnchor={i === 0 ? "start" : i >= data.length - Math.ceil(data.length / 6) ? "end" : "middle"}
                    fill="var(--text-secondary)">{label(d.day)}</text>
            ) : null))}
          </svg>
          {hover !== null && (
            <div className="pointer-events-none absolute -top-2 rounded-lg px-2 py-1 text-xs shadow"
                 style={{ left: `${Math.min(88, Math.max(12, ((padL + hover * step + step / 2) / W) * 100))}%`,
                          transform: "translate(-50%, -100%)", whiteSpace: "nowrap",
                          background: "var(--surface-1)", color: "var(--text-primary)", border: "1px solid var(--grid)" }}>
              <b>{data[hover].count}</b> réservation(s) · {label(data[hover].day)}
            </div>
          )}
        </div>
      )}
    </figure>
  );
}
