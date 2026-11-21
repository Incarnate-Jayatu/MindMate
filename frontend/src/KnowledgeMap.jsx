import { useState } from "react";

const NODE = {
  unseen: "fill-slate-100 stroke-slate-400",
  weak: "fill-red-100 stroke-red-400",
  learning: "fill-amber-100 stroke-amber-400",
  mastered: "fill-green-100 stroke-green-500",
};
const CHIP = {
  unseen: "bg-slate-200 text-slate-700",
  weak: "bg-red-100 text-red-700",
  learning: "bg-amber-100 text-amber-800",
  mastered: "bg-green-100 text-green-700",
};
const W = 170, H = 76, GX = 90, GY = 28, PAD = 16;

function layout(map) {
  const byId = Object.fromEntries(map.map((c) => [c.concept_id, c]));
  const depth = {};
  const d = (id) => {
    if (depth[id] !== undefined) return depth[id];
    const pre = byId[id]?.prereqs ?? [];
    return (depth[id] = pre.length ? 1 + Math.max(...pre.map(d)) : 0);
  };
  map.forEach((c) => d(c.concept_id));
  const cols = {};
  map.forEach((c) => (cols[depth[c.concept_id]] ||= []).push(c));
  const pos = {};
  Object.entries(cols).forEach(([col, list]) =>
    list.forEach((c, r) => (pos[c.concept_id] = { x: PAD + col * (W + GX), y: PAD + r * (H + GY) }))
  );
  const nCols = Object.keys(cols).length;
  const nRows = Math.max(...Object.values(cols).map((l) => l.length));
  return {
    pos,
    width: PAD * 2 + nCols * W + (nCols - 1) * GX,
    height: PAD * 2 + nRows * H + (nRows - 1) * GY,
  };
}

const Card = ({ children, className = "" }) => (
  <div className={`rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200 ${className}`}>{children}</div>
);
const Primary = (p) => (
  <button {...p} className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50" />
);

export default function KnowledgeMap({ map, insights, busy, onPractice, onBack }) {
  const rec = insights.recommended;
  const [sel, setSel] = useState(rec?.concept_id ?? map[0]?.concept_id);
  const { pos, width, height } = layout(map);
  const names = Object.fromEntries(map.map((c) => [c.concept_id, c.name]));
  const cur = map.find((c) => c.concept_id === sel);
  const curMis = insights.misconceptions.filter((m) => m.concept_id === sel);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Knowledge map</h2>
        <button className="text-sm text-slate-600 underline" onClick={onBack}>Back</button>
      </div>

      <Card className="bg-indigo-50 ring-indigo-200">
        {rec ? (
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-wide text-indigo-600">Learn next</p>
              <p className="font-semibold">{rec.name}</p>
              <p className="text-sm text-slate-600">{rec.reason}</p>
            </div>
            <Primary disabled={busy} onClick={() => onPractice(rec.concept_id)}>Practice {rec.name}</Primary>
          </div>
        ) : (
          <p className="font-medium text-green-700">All concepts mastered 🎉</p>
        )}
      </Card>

      <Card>
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full" role="img" aria-label="Concept prerequisite map">
          <defs>
            <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
              <path d="M0 0L10 5L0 10z" className="fill-slate-400" />
            </marker>
          </defs>
          {map.flatMap((c) =>
            c.prereqs.filter((p) => pos[p]).map((p) => {
              const a = pos[p], b = pos[c.concept_id];
              const x1 = a.x + W, y1 = a.y + H / 2, x2 = b.x, y2 = b.y + H / 2;
              return (
                <path key={`${p}-${c.concept_id}`} d={`M${x1} ${y1} C${x1 + 40} ${y1}, ${x2 - 40} ${y2}, ${x2 - 2} ${y2}`}
                  className="fill-none stroke-slate-400" strokeWidth="2" markerEnd="url(#arrow)" />
              );
            })
          )}
          {map.map((c) => {
            const { x, y } = pos[c.concept_id];
            const isRec = rec?.concept_id === c.concept_id;
            const isSel = sel === c.concept_id;
            return (
              <g key={c.concept_id} role="button" tabIndex={0} className="cursor-pointer outline-none"
                onClick={() => setSel(c.concept_id)} onKeyDown={(e) => e.key === "Enter" && setSel(c.concept_id)}>
                <rect x={x} y={y} width={W} height={H} rx="14" strokeWidth={isSel ? 3 : 1.5} className={NODE[c.status]} />
                {isRec && <rect x={x - 4} y={y - 4} width={W + 8} height={H + 8} rx="17" strokeWidth="2"
                  strokeDasharray="6 4" className="fill-none stroke-indigo-500" />}
                <text x={x + 14} y={y + 30} className="fill-slate-900 text-sm font-semibold">{c.name}</text>
                <text x={x + 14} y={y + 54} className="fill-slate-600 text-xs">{c.status} · {Math.round(c.score * 100)}%</text>
              </g>
            );
          })}
        </svg>
        <div className="mt-3 flex flex-wrap gap-2 text-xs">
          {Object.keys(CHIP).map((s) => <span key={s} className={`rounded-full px-2.5 py-0.5 ${CHIP[s]}`}>{s}</span>)}
          <span className="rounded-full border border-dashed border-indigo-500 px-2.5 py-0.5 text-indigo-700">recommended</span>
        </div>
      </Card>

      {cur && (
        <Card>
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="font-semibold">{cur.name}</p>
              <p className="text-sm text-slate-600">
                {cur.status} · {Math.round(cur.score * 100)}% · {cur.attempts} attempt{cur.attempts === 1 ? "" : "s"}
                {cur.prereqs.length > 0 && ` · needs ${cur.prereqs.map((p) => names[p] ?? p).join(", ")}`}
              </p>
            </div>
            {cur.status !== "mastered" && (
              <Primary disabled={busy} onClick={() => onPractice(cur.concept_id)}>Practice</Primary>
            )}
          </div>
          {curMis.length > 0 && (
            <ul className="mt-3 space-y-1 text-sm text-slate-700">
              {curMis.map((m) => <li key={m.id}>• {m.description} <span className="text-slate-400">(×{m.count})</span></li>)}
            </ul>
          )}
        </Card>
      )}

      <Card>
        <h3 className="mb-2 font-semibold">Misconception history</h3>
        {insights.misconceptions.length === 0 ? (
          <p className="text-sm text-slate-500">None detected yet. Answer a few questions first.</p>
        ) : (
          <ul className="space-y-2 text-sm">
            {insights.misconceptions.map((m) => (
              <li key={m.id} className="flex justify-between gap-3">
                <span><b>{names[m.concept_id]}:</b> {m.description}</span>
                <span className="shrink-0 rounded-full bg-red-50 px-2 text-red-700">×{m.count}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
