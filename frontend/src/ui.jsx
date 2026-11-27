export const TOPICS = [
  ["arrays", "Arrays"], ["loops", "Loops"], ["recursion", "Recursion"], ["strings", "Strings"],
  ["stacks", "Stacks"], ["queues", "Queues"], ["linkedlist", "Linked lists"],
];
export const NAMES = Object.fromEntries(TOPICS);
export const STICKER_BG = ["#d6e4ff", "#ffe45c", "#ffd6d3", "#c7f0da", "#e6dcff", "#ffe9a8", "#d4f1f4"];
export const STICKER_ROT = ["-2.5deg", "1.5deg", "-1deg", "2.5deg", "-2deg", "1deg", "-1.5deg"];

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

export const Check = () => (
  <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true"><path d="M2 7.5 5.5 11 12 3" stroke="#fff" strokeWidth="2.4" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg>
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
