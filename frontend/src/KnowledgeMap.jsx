import { useState } from "react";
import { Btn, NAMES, StatusChip, Meter } from "./ui";

const FILL = { unseen: "#ffffff", weak: "#ffd6d3", learning: "#ffe9a8", mastered: "#c7f0da" };
const W = 170, H = 76, GX = 90, GY = 30, PAD = 22;
const INK = "#17204d";

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
    list.forEach((c, r) => (pos[c.concept_id] = { x: PAD + col * (W + GX), y: PAD + 8 + r * (H + GY) }))
  );
  const nCols = Object.keys(cols).length;
  const nRows = Math.max(...Object.values(cols).map((l) => l.length));
  return {
    pos,
    width: PAD * 2 + nCols * W + (nCols - 1) * GX + 6,
    height: PAD * 2 + 8 + nRows * H + (nRows - 1) * GY + 6,
  };
}

export default function KnowledgeMap({ map, insights, busy, onPractice, onAddTopic, onBack }) {
  const rec = insights.recommended;
  const [sel, setSel] = useState(rec?.concept_id ?? map[0]?.concept_id);
  const { pos, width, height } = layout(map);
  const names = Object.fromEntries(map.map((c) => [c.concept_id, c.name]));
  const cur = map.find((c) => c.concept_id === sel);
  const curMis = insights.misconceptions.filter((m) => m.concept_id === sel);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <h2 className="font-display text-3xl font-extrabold tracking-tight">Your knowledge map</h2>
        <Btn ghost small onClick={onBack}>Back</Btn>
      </div>

      <section className="sheet">
        {rec ? (
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-sm text-pencil">Learn next</p>
              <p className="font-display text-2xl font-bold"><mark className="hl">{rec.name}</mark></p>
              <p className="mt-1 text-sm text-pencil">{rec.reason}</p>
            </div>
            <Btn disabled={busy} onClick={() => onPractice(rec.concept_id)}>Practice {rec.name}</Btn>
          </div>
        ) : (
          <p className="font-display text-xl font-bold text-pass">Every topic is mastered. Nice work.</p>
        )}
      </section>

      <section className="sheet p-3 sm:p-4">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full" role="group" aria-label="Topic map. Arrows point from a prerequisite to the topic that builds on it.">
          <defs>
            <pattern id="mm-grid" width="20" height="20" patternUnits="userSpaceOnUse">
              <path d="M20 0H0V20" fill="none" stroke="#e3e9f6" strokeWidth="1" />
            </pattern>
            <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
              <path d="M0 0L10 5L0 10z" fill={INK} />
            </marker>
          </defs>
          <rect width="100%" height="100%" fill="url(#mm-grid)" />
          {map.flatMap((c) =>
            c.prereqs.filter((p) => pos[p]).map((p) => {
              const a = pos[p], b = pos[c.concept_id];
              const x1 = a.x + W + 3, y1 = a.y + H / 2, x2 = b.x, y2 = b.y + H / 2;
              return (
                <path key={`${p}-${c.concept_id}`} d={`M${x1} ${y1} C${x1 + 40} ${y1}, ${x2 - 40} ${y2}, ${x2 - 3} ${y2}`}
                  fill="none" stroke={INK} strokeWidth="2" markerEnd="url(#arrow)" />
              );
            })
          )}
          {map.map((c) => {
            const { x, y } = pos[c.concept_id];
            const isRec = rec?.concept_id === c.concept_id;
            const isSel = sel === c.concept_id;
            return (
              <g key={c.concept_id} opacity={c.selected === false ? 0.45 : 1} role="button" tabIndex={0} aria-pressed={isSel} aria-label={`${c.name}, ${c.status}`}
                style={{ cursor: "pointer" }} onClick={() => setSel(c.concept_id)} onKeyDown={(e) => e.key === "Enter" && setSel(c.concept_id)}>
                <rect x={x + 4} y={y + 4} width={W} height={H} rx="14" fill={isSel ? "#ffe45c" : INK} stroke={INK} strokeWidth="2" />
                <rect x={x} y={y} width={W} height={H} rx="14" fill={FILL[c.status] ?? FILL.unseen} stroke={INK} strokeWidth="2" />
                <text x={x + 14} y={y + 31} fill={INK} style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 16 }}>{c.name}</text>
                <text x={x + 14} y={y + 55} fill="#5a6590" style={{ fontFamily: "var(--font-sans)", fontSize: 13 }}>{Math.round(c.score * 100)}%</text>
                {isRec && (
                  <g transform={`translate(${x + W - 66}, ${y - 13}) rotate(3)`}>
                    <rect width="76" height="24" rx="7" fill="#ffe45c" stroke={INK} strokeWidth="2" />
                    <text x="38" y="16.5" textAnchor="middle" fill={INK} style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 12 }}>learn next</text>
                  </g>
                )}
              </g>
            );
          })}
        </svg>
        <div className="mt-3 flex flex-wrap items-center gap-2 px-1">
          {["unseen", "weak", "learning", "mastered"].map((s) => <StatusChip key={s} status={s} />)}
        </div>
        <p className="mt-2 px-1 text-sm text-pencil">
          Arrows point from a prerequisite to the topic that builds on it.
          {map.some((c) => c.selected === false) && " Faded topics are not in your selection. Click one to add it."}
        </p>
      </section>

      {cur && (
        <section className="sheet">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="min-w-0">
              <div className="flex items-center gap-3">
                <p className="font-display text-xl font-bold">{cur.name}</p>
                <StatusChip status={cur.status} />
              </div>
              <p className="mt-1 text-sm text-pencil">
                {cur.attempts} attempt{cur.attempts === 1 ? "" : "s"}
                {cur.prereqs.length > 0 && ` · builds on ${cur.prereqs.map((p) => names[p] ?? NAMES[p] ?? p).join(", ")}`}
              </p>
            </div>
            {cur.selected === false ? (
              <Btn small disabled={busy} onClick={() => onAddTopic(cur.concept_id)}>Add to my topics</Btn>
            ) : (
              cur.status !== "mastered" && <Btn small disabled={busy} onClick={() => onPractice(cur.concept_id)}>Practice</Btn>
            )}
          </div>
          <div className="mt-3"><Meter score={cur.score} status={cur.status} /></div>
          {curMis.length > 0 && (
            <ul className="mt-4 space-y-1.5 text-sm leading-relaxed">
              {curMis.map((m) => (
                <li key={m.id}><mark className="hl">{m.description}</mark> <span className="text-pencil">×{m.count}</span></li>
              ))}
            </ul>
          )}
        </section>
      )}

      <section className="sheet">
        <h3 className="font-display text-xl font-bold">Mistakes to fix</h3>
        {insights.misconceptions.length === 0 ? (
          <p className="mt-2 text-sm text-pencil">Nothing yet. Answer a few questions and your misunderstandings will show up here.</p>
        ) : (
          <ul className="mt-3 space-y-2.5 text-sm leading-relaxed">
            {insights.misconceptions.map((m) => (
              <li key={m.id} className="flex items-start justify-between gap-3">
                <span><b>{names[m.concept_id]}:</b> <mark className="hl">{m.description}</mark></span>
                <span className="chip chip-weak shrink-0">×{m.count}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
