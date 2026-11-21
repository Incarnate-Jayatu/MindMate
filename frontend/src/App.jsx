import { useState } from "react";
import { api } from "./api";
import KnowledgeMap from "./KnowledgeMap";

const BADGE = {
  unseen: "bg-slate-200 text-slate-700",
  weak: "bg-red-100 text-red-700",
  learning: "bg-amber-100 text-amber-800",
  mastered: "bg-green-100 text-green-700",
};

const Card = ({ children }) => (
  <div className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">{children}</div>
);
const Btn = (p) => (
  <button
    {...p}
    className="rounded-xl bg-indigo-600 px-5 py-2.5 font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
  />
);

export default function App() {
  const [stage, setStage] = useState("start");
  const [name, setName] = useState("");
  const [user, setUser] = useState(null);
  const [qs, setQs] = useState([]);
  const [i, setI] = useState(0);
  const [choice, setChoice] = useState(null);
  const [res, setRes] = useState(null);
  const [expl, setExpl] = useState(null);
  const [map, setMap] = useState([]);
  const [busy, setBusy] = useState(false);
  const [mode, setMode] = useState("diag");
  const [focus, setFocus] = useState(null);
  const [allDone, setAllDone] = useState(false);
  const [target, setTarget] = useState(null);
  const [insights, setInsights] = useState(null);
  const [lastStage, setLastStage] = useState("start");
  const [err, setErr] = useState("");

  const run = async (fn) => {
    setBusy(true);
    setErr("");
    try {
      await fn();
    } catch {
      setErr("Can't reach the server. Is the backend running on port 8000?");
    }
    setBusy(false);
  };

  const start = () =>
    run(async () => {
      const u = await api.createUser(name.trim() || "Student");
      setUser(u);
      setMode("diag");
      setAllDone(false);
      setQs(await api.diagnostic());
      setStage("quiz");
    });

  const q = qs[i];

  const submit = () =>
    run(async () => {
      const r = await api.attempt(user.id, q.id, choice);
      setRes(r);
      if (!r.correct) setExpl(await api.explain(user.id, q.id, choice));
    });

  const reset = () => {
    setChoice(null);
    setRes(null);
    setExpl(null);
  };

  const showResults = async (finished = false) => {
    setMap(await api.map(user.id));
    setAllDone(finished);
    setStage("done");
  };

  const loadPractice = async (conceptId = target) => {
    const r = await api.next(user.id, conceptId);
    if (r.done) return showResults(true);
    setFocus(r);
    setQs([r.question]);
    setI(0);
    setStage("quiz");
  };

  const next = () =>
    run(async () => {
      reset();
      if (mode === "practice") return loadPractice();
      if (i + 1 < qs.length) return setI(i + 1);
      await showResults();
    });

  const startPractice = (conceptId = null) =>
    run(async () => {
      reset();
      setMode("practice");
      setTarget(conceptId);
      await loadPractice(conceptId);
    });

  const openMap = () =>
    run(async () => {
      setLastStage(stage);
      setMap(await api.map(user.id));
      setInsights(await api.insights(user.id));
      setStage("map");
    });

  const finish = () => run(() => showResults());

  const restart = () => {
    setStage("start");
    setI(0);
    setChoice(null);
    setRes(null);
    setExpl(null);
  };

  return (
    <main className="mx-auto max-w-2xl space-y-4 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-indigo-700">MindMate</h1>
        {user && stage !== "start" && stage !== "map" && (
          <button className="text-sm text-indigo-700 underline" onClick={openMap} disabled={busy}>Knowledge map</button>
        )}
      </div>
      {err && <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{err}</p>}

      {stage === "start" && (
        <Card>
          <p className="mb-4 text-slate-600">
            A quick 3-question check of your C++ basics. Wrong answers get a personal explanation.
          </p>
          <input
            className="mb-4 w-full rounded-xl border border-slate-300 px-4 py-2"
            placeholder="Your name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <Btn onClick={start} disabled={busy}>Start diagnostic</Btn>
        </Card>
      )}

      {stage === "quiz" && q && (
        <Card>
          <p className="mb-1 text-sm text-slate-500">
            {mode === "practice"
              ? `Practice · ${focus?.concept_name} (${focus?.status})`
              : `Question ${i + 1} of ${qs.length} · ${q.concept_id}`}
          </p>
          <pre className="mb-4 whitespace-pre-wrap rounded-xl bg-slate-900 p-4 text-sm text-slate-100">{q.prompt}</pre>
          <div className="space-y-2">
            {q.options.map((o) => {
              const picked = choice === o.key;
              const done = !!res;
              const isAnswer = done && o.key === res.answer_key;
              const cls = isAnswer
                ? "border-green-500 bg-green-50"
                : done && picked
                ? "border-red-500 bg-red-50"
                : picked
                ? "border-indigo-500 bg-indigo-50"
                : "border-slate-300 hover:bg-slate-50";
              return (
                <button
                  key={o.key}
                  disabled={done}
                  onClick={() => setChoice(o.key)}
                  className={`w-full rounded-xl border px-4 py-2 text-left ${cls}`}
                >
                  <b>{o.key}.</b> {o.text}
                </button>
              );
            })}
          </div>

          {res && (
            <div className="mt-4 space-y-2">
              <p className={res.correct ? "font-medium text-green-700" : "font-medium text-red-700"}>
                {res.correct ? "Correct!" : "Not quite."}
              </p>
              <p className="text-sm text-slate-500">
                {res.mastery.concept_id}: {res.mastery.status} ({Math.round(res.mastery.score * 100)}%)
              </p>
              {res.misconception && (
                <p className="text-sm text-slate-600">
                  <b>Likely misunderstanding:</b> {res.misconception.description}
                </p>
              )}
              {expl && (
                <div className="rounded-xl bg-indigo-50 p-4 text-sm text-slate-800">
                  <p className="whitespace-pre-wrap">{expl.explanation}</p>
                  <p className="mt-2 text-xs text-slate-500">
                    {expl.source === "ai" ? "AI tutor" : "Basic explanation (add an API key for the AI tutor)"}
                  </p>
                </div>
              )}
            </div>
          )}

          <div className="mt-4">
            {!res ? (
              <Btn onClick={submit} disabled={!choice || busy}>Check answer</Btn>
            ) : (
              <>
                <Btn onClick={next} disabled={busy}>
                  {mode === "practice" ? "Next question" : i + 1 < qs.length ? "Next" : "See results"}
                </Btn>
                {mode === "practice" && (
                  <button className="ml-3 text-sm text-slate-600 underline" onClick={finish}>Finish</button>
                )}
              </>
            )}
          </div>
        </Card>
      )}

      {stage === "map" && insights && (
        <KnowledgeMap map={map} insights={insights} busy={busy}
          onPractice={(id) => startPractice(id)} onBack={() => setStage(lastStage)} />
      )}

      {stage === "done" && (
        <Card>
          <h2 className="mb-3 text-lg font-semibold">Your results</h2>
          <div className="space-y-3">
            {map.map((c) => (
              <div key={c.concept_id} className="rounded-xl border border-slate-200 p-3">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{c.name}</span>
                  <span className={`rounded-full px-2.5 py-0.5 text-xs ${BADGE[c.status]}`}>{c.status}</span>
                </div>
                <div className="mt-2 h-2 rounded-full bg-slate-200">
                  <div className="h-2 rounded-full bg-indigo-500" style={{ width: `${Math.round(c.score * 100)}%` }} />
                </div>
                {Object.keys(c.misconceptions).length > 0 && (
                  <p className="mt-2 text-xs text-slate-500">Needs work: {Object.keys(c.misconceptions).join(", ")}</p>
                )}
              </div>
            ))}
          </div>
          <div className="mt-4 flex items-center gap-4">
            {allDone ? (
              <p className="font-medium text-green-700">All concepts mastered 🎉</p>
            ) : (
              <Btn onClick={() => startPractice()} disabled={busy}>
                {mode === "practice" ? "Continue practice" : "Start practice"}
              </Btn>
            )}
            <button className="text-sm text-slate-600 underline" onClick={restart}>Start over</button>
          </div>
        </Card>
      )}
    </main>
  );
}
