export const GROUPS = [
  ["Basics", ["arrays", "loops", "recursion", "strings"]],
  ["Data structures", ["stacks", "queues", "linkedlist", "dll", "bst"]],
  ["Algorithms", ["searching", "sorting", "bits"]],
];
export const NAMES = {
  arrays: "Arrays", loops: "Loops", recursion: "Recursion", strings: "Strings",
  stacks: "Stacks", queues: "Queues", linkedlist: "Linked lists", dll: "Doubly linked lists", bst: "Binary search trees",
  searching: "Searching", sorting: "Sorting", bits: "Bit manipulation",
};
export const TOPIC_IDS = GROUPS.flatMap(([, ids]) => ids);
export const STICKER_BG = ["#d6e4ff", "#ffe45c", "#ffd6d3", "#c7f0da", "#e6dcff", "#ffe9a8", "#d4f1f4", "#ffd9ec", "#dff3b7", "#ffe0c2", "#cfe7ff", "#e9e1ff"];
export const STICKER_ROT = ["-2.5deg", "1.5deg", "-1deg", "2.5deg", "-2deg", "1deg", "-1.5deg", "2deg", "-1deg", "1.5deg", "-2deg", "1deg"];

const CHIP = { unseen: "chip-unseen", weak: "chip-weak", learning: "chip-learning", mastered: "chip-mastered" };
const LABEL = { unseen: "Not started", weak: "Needs work", learning: "Getting there", mastered: "Mastered" };
const FILL = { unseen: "#c9d1ee", weak: "#ff8f8a", learning: "#ffd34d", mastered: "#4cc38a" };

export function Logo() {
  return (
    <svg width="34" height="34" viewBox="0 0 34 34" aria-hidden="true">
      <rect x="1" y="1" width="32" height="32" rx="9" fill="#17204d" />
      <path d="M10 22 17 11 24 22" stroke="#fff" strokeWidth="2" fill="none" />
      <circle cx="10" cy="22" r="3.2" fill="#ffe45c" />
      <circle cx="17" cy="11" r="3.2" fill="#ffe45c" />
      <circle cx="24" cy="22" r="3.2" fill="#ffe45c" />
    </svg>
  );
}

export function Btn({ ghost, small, className = "", type = "button", ...p }) {
  return <button type={type} {...p} className={`btn ${ghost ? "btn-ghost" : ""} ${small ? "btn-sm" : ""} ${className}`} />;
}

export function StatusChip({ status }) {
  return <span className={`chip ${CHIP[status] ?? "chip-unseen"}`}>{LABEL[status] ?? status}</span>;
}

export function Meter({ score, status }) {
  const pct = Math.round(score * 100);
  return (
    <div className="meter" role="img" aria-label={`${pct}% score`}>
      <div className="meter-fill" style={{ width: `${pct}%`, background: FILL[status] ?? FILL.unseen }} />
    </div>
  );
}

export const Check = ({ color = "#fff" }) => (
  <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true"><path d="M2 7.5 5.5 11 12 3" stroke={color} strokeWidth="2.4" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg>
);
export const Cross = () => (
  <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true"><path d="M3 3 11 11M11 3 3 11" stroke="#fff" strokeWidth="2.4" strokeLinecap="round" /></svg>
);

const KW = new Set(["int", "char", "string", "void", "for", "while", "if", "else", "return", "new", "nullptr", "struct", "stack", "queue", "Node", "cout", "bool", "true", "false", "const", "auto"]);

function Highlight({ code }) {
  return code.split(/("[^"]*"|'[^']*'|\b\d+\b|\b[A-Za-z_]\w*\b)/g).map((t, i) => {
    if (!t) return null;
    if (/^["']/.test(t)) return <span key={i} style={{ color: "#ffe45c" }}>{t}</span>;
    if (/^\d+$/.test(t)) return <span key={i} style={{ color: "#ff9ea0" }}>{t}</span>;
    if (KW.has(t)) return <span key={i} style={{ color: "#9db8ff" }}>{t}</span>;
    return t;
  });
}

export function CodeBlock({ code }) {
  return (
    <pre className="code" aria-label="C++ code"><code><Highlight code={code} /></code></pre>
  );
}

/** Splits "code;  more code;  Prints?" into a code block and a plain-language question. */
export function splitPrompt(prompt) {
  const parts = prompt.split(/\s{2,}/).map((s) => s.trim()).filter(Boolean);
  let question = null;
  if (parts.length && parts[parts.length - 1].endsWith("?")) {
    question = parts.pop();
    let m;
    if (question === "Prints?") question = "What does this print?";
    else if ((m = question.match(/^(.+?)\s+prints\?$/i))) { parts.push(m[1]); question = "What does this print?"; }
    else if ((m = question.match(/^(.+?)\s*=\s*\?$/))) question = `What does ${m[1]} return?`;
  }
  return { code: parts.join("\n"), question };
}

/** Sticker-style topic chooser. `concepts` (from the API) is only used for the "builds on" tip. */
export function TopicPicker({ selected, onChange, concepts = [] }) {
  const toggle = (id) => onChange(selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id]);
  const missing = concepts.filter((c) => selected.includes(c.id) && c.prereqs.some((p) => !selected.includes(p)));
  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
        <span className="font-semibold">{selected.length} of {TOPIC_IDS.length} topics selected</span>
        <button type="button" className="font-medium text-pencil underline underline-offset-4" onClick={() => onChange(TOPIC_IDS)}>Select all</button>
        <button type="button" className="font-medium text-pencil underline underline-offset-4" onClick={() => onChange([])}>Clear</button>
      </div>
      {GROUPS.map(([label, ids]) => (
        <div key={label} className="mb-3">
          <p className="mb-1.5 text-sm text-pencil">{label}</p>
          <div className="flex flex-wrap gap-2.5">
            {ids.map((id) => {
              const on = selected.includes(id);
              const k = TOPIC_IDS.indexOf(id);
              return (
                <button key={id} type="button" role="checkbox" aria-checked={on} onClick={() => toggle(id)}
                  className={`sticker topic ${on ? "" : "topic-off"}`}
                  style={{ "--r": STICKER_ROT[k], background: on ? STICKER_BG[k] : "#fff", animationDelay: `${k * 45}ms` }}>
                  {on && <Check color="#17204d" />}
                  {NAMES[id]}
                </button>
              );
            })}
          </div>
        </div>
      ))}
      {missing.length > 0 && (
        <p className="mt-2 text-sm text-pencil">
          Tip: {missing.slice(0, 3).map((c) => `${NAMES[c.id]} builds on ${c.prereqs.filter((p) => !selected.includes(p)).map((p) => NAMES[p]).join(" and ")}`).join("; ")}. You can still pick it.
        </p>
      )}
    </div>
  );
}
