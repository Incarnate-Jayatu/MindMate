import { useEffect, useState } from "react";
import { api } from "./api";
import KnowledgeMap from "./KnowledgeMap";
import { Btn, Check, CodeBlock, Cross, Logo, Meter, NAMES, StatusChip, TOPIC_IDS, TopicPicker, splitPrompt } from "./ui";

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
  const [selected, setSelected] = useState(TOPIC_IDS);
  const [concepts, setConcepts] = useState([]);

  useEffect(() => {
    api.concepts().then(setConcepts).catch(() => {});
  }, []);

  const run = async (fn) => {
    setBusy(true);
    setErr("");
    try {
      await fn();
    } catch {
      setErr("Can't reach the server. If the site was idle, give it a minute to wake up, then try again.");
    }
    setBusy(false);
  };

  const reset = () => {
    setChoice(null);
    setRes(null);
    setExpl(null);
  };

  const start = () =>
    run(async () => {
      const u = await api.createUser(name.trim() || "Student", selected);
      setUser(u);
      setMode("diag");
      setAllDone(false);
      setQs(await api.diagnostic(u.id));
      setI(0);
      setStage("quiz");
    });

  const q = qs[i];

  const submit = () =>
    run(async () => {
      const r = await api.attempt(user.id, q.id, choice);
      setRes(r);
      if (!r.correct) setExpl(await api.explain(user.id, q.id, choice));
    });

  const showResults = async (finished = false) => {
    const [m, ins] = await Promise.all([api.map(user.id), api.insights(user.id)]);
    setMap(m);
    setInsights(ins);
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
      const [m, ins] = await Promise.all([api.map(user.id), api.insights(user.id)]);
      setMap(m);
      setInsights(ins);
      setStage("map");
    });

  const finish = () => run(() => showResults());

  const openTopics = () =>
    run(async () => {
      setLastStage(stage);
      setSelected((await api.getTopics(user.id)).topics);
      setStage("topics");
    });

  const saveTopics = () =>
    run(async () => {
      await api.setTopics(user.id, selected);
      reset();
      setAllDone(false);
      await showResults();
    });

  const addTopic = (id) =>
    run(async () => {
      const current = map.filter((c) => c.selected !== false).map((c) => c.concept_id);
      const next = [...new Set([...current, id])];
      await api.setTopics(user.id, next);
      const [m, ins] = await Promise.all([api.map(user.id), api.insights(user.id)]);
      setMap(m);
      setInsights(ins);
      setSelected(next);
    });

  const restart = () => {
    reset();
    setI(0);
    setStage("start");
  };

  const parts = q ? splitPrompt(q.prompt) : null;
  const answered = i + (res ? 1 : 0);
  const waitingForTutor = res && !res.correct && !expl && busy;
  const shown = map.filter((c) => c.selected !== false);

  return (
    <div className="mx-auto max-w-5xl px-5 pb-20">
      <header className="flex items-center justify-between py-6">
        <div className="flex items-center gap-3">
          <Logo />
          <span className="font-display text-2xl font-extrabold tracking-tight">MindMate</span>
        </div>
        {user && stage !== "start" && stage !== "map" && stage !== "topics" && (
          <div className="flex gap-2">
            <Btn ghost small onClick={openTopics} disabled={busy}>My topics</Btn>
            <Btn ghost small onClick={openMap} disabled={busy}>Knowledge map</Btn>
          </div>
        )}
      </header>

      {err && (
        <p role="alert" className="mx-auto mb-5 max-w-2xl rounded-xl border-2 border-pen bg-[#ffe1df] px-4 py-3 text-sm font-medium text-[#8f1d24]">
          {err}
        </p>
      )}

      {stage === "start" && (
        <section className="grid items-start gap-12 pt-4 md:grid-cols-[1.1fr_0.9fr]">
          <div>
            <h1 className="font-display text-4xl font-extrabold leading-[1.05] tracking-tight sm:text-6xl">
              Learn DSA in C++ by fixing the mistakes you actually make.
            </h1>
            <p className="mt-6 max-w-md text-lg leading-relaxed text-pencil">
              Pick the topics you want to practice. The check has one question per topic, and each wrong answer shows what you probably misunderstood, then explains it.
            </p>
            <div className="mt-8 max-w-xl">
              <p className="font-hand mb-3 text-2xl text-pencil">pick your topics</p>
              <TopicPicker selected={selected} onChange={setSelected} concepts={concepts} />
            </div>
            <form
              className="mt-8 flex max-w-md flex-col gap-3 sm:flex-row"
              onSubmit={(e) => {
                e.preventDefault();
                if (!busy && selected.length > 0) start();
              }}
            >
              <label htmlFor="name" className="sr-only">Your name</label>
              <input id="name" className="field" placeholder="Your name" maxLength={40} value={name} onChange={(e) => setName(e.target.value)} />
              <Btn type="submit" disabled={busy || selected.length === 0} className="shrink-0">{busy ? "Starting…" : "Start the check"}</Btn>
            </form>
          </div>

          <div className="sheet md:rotate-[1.5deg]" aria-hidden="true">
            <p className="mb-3 text-sm text-pencil">Arrays</p>
            <CodeBlock code={"int a[5] = {1, 2};\ncout << a[4];"} />
            <p className="mb-3 mt-4 font-display text-lg font-bold">What does this print?</p>
            <div className="space-y-2">
              <div className="opt opt-wrong"><span className="badge"><Cross /></span>Garbage value</div>
              <div className="opt opt-right"><span className="badge"><Check /></span>0</div>
            </div>
            <p className="mt-4 text-[15px] leading-relaxed">
              <span className="font-semibold">Likely misunderstanding:</span>{" "}
              <mark className="hl">Thinks unfilled slots hold garbage</mark>
            </p>
          </div>
        </section>
      )}

      {stage === "quiz" && q && (
        <div className="mx-auto max-w-2xl">
          {mode === "diag" && (
            <div className="mb-5 flex gap-1.5" role="progressbar" aria-label="Progress" aria-valuemin={0} aria-valuemax={qs.length} aria-valuenow={answered}>
              {qs.map((_, k) => (
                <span key={k} className={`seg ${k < answered ? "seg-done" : k === i ? "seg-now" : ""}`} />
              ))}
            </div>
          )}

          <section className="sheet ruled">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="font-display text-lg font-bold">{NAMES[q.concept_id] ?? q.concept_id}</span>
                {mode === "practice" && focus && <StatusChip status={focus.status} />}
              </div>
              <p className="text-sm text-pencil">{mode === "diag" ? `Question ${i + 1} of ${qs.length}` : "Practice"}</p>
            </div>

            {parts.code && <CodeBlock code={parts.code} />}
            {parts.question && <p className={`font-display text-xl font-bold ${parts.code ? "mt-4" : ""}`}>{parts.question}</p>}

            <div className="mt-4 space-y-2.5" role="group" aria-label="Answer choices">
              {q.options.map((o) => {
                const done = !!res;
                const picked = choice === o.key;
                const isAnswer = done && o.key === res.answer_key;
                const isWrong = done && picked && !res.correct;
                const cls = isAnswer ? "opt-right" : isWrong ? "opt-wrong" : picked ? "opt-picked" : "";
                return (
                  <button key={o.key} type="button" disabled={done} onClick={() => setChoice(o.key)} className={`opt ${cls}`}>
                    <span className="badge">{isAnswer ? <Check /> : isWrong ? <Cross /> : o.key}</span>
                    <span>{o.text}</span>
                  </button>
                );
              })}
            </div>

            {res && (
              <div className="mt-6 space-y-4" aria-live="polite">
                <p className={`font-display text-3xl font-extrabold ${res.correct ? "text-pass" : "text-pen"}`}>
                  {res.correct ? "Correct" : "Not quite"}
                </p>
                <div className="flex items-center gap-3">
                  <StatusChip status={res.mastery.status} />
                  <div className="w-32"><Meter score={res.mastery.score} status={res.mastery.status} /></div>
                  <span className="text-sm text-pencil">{Math.round(res.mastery.score * 100)}%</span>
                </div>
                {res.misconception && (
                  <p className="text-[15px] leading-relaxed">
                    <span className="font-semibold">Likely misunderstanding:</span>{" "}
                    <mark className="hl">{res.misconception.description}</mark>
                  </p>
                )}
                {waitingForTutor && <div className="note text-sm text-pencil">Your tutor is writing an explanation…</div>}
                {expl && (
                  <div className="note">
                    <p className="whitespace-pre-wrap text-[15px] leading-relaxed">{expl.explanation}</p>
                    <p className="mt-2 text-xs text-pencil">
                      {expl.source === "ai" ? "AI tutor" : `Basic explanation${expl.note ? ` (${expl.note})` : ""}`}
                    </p>
                  </div>
                )}
              </div>
            )}

            <div className="mt-6 flex items-center gap-4">
              {!res ? (
                <Btn onClick={submit} disabled={!choice || busy}>{busy ? "Checking…" : "Check answer"}</Btn>
              ) : (
                <>
                  <Btn onClick={next} disabled={busy}>
                    {mode === "practice" ? "Next question" : i + 1 < qs.length ? "Next question" : "See results"}
                  </Btn>
                  {mode === "practice" && (
                    <button type="button" className="text-sm font-medium text-pencil underline underline-offset-4" onClick={finish} disabled={busy}>
                      Finish
                    </button>
                  )}
                </>
              )}
            </div>
          </section>
        </div>
      )}

      {stage === "map" && insights && (
        <div className="mx-auto max-w-2xl">
          <KnowledgeMap map={map} insights={insights} busy={busy} onPractice={(id) => startPractice(id)} onAddTopic={addTopic} onBack={() => setStage(lastStage)} />
        </div>
      )}

      {stage === "topics" && (
        <div className="mx-auto max-w-2xl">
          <h2 className="font-display text-3xl font-extrabold tracking-tight">Choose your topics</h2>
          <p className="mt-2 text-pencil">Practice only uses the topics you pick. Your progress on the others is kept.</p>
          <section className="sheet mt-5">
            <TopicPicker selected={selected} onChange={setSelected} concepts={concepts} />
          </section>
          <div className="mt-6 flex items-center gap-5">
            <Btn onClick={saveTopics} disabled={busy || selected.length === 0}>Save topics</Btn>
            <button type="button" className="text-sm font-medium text-pencil underline underline-offset-4" onClick={() => setStage(lastStage)}>
              Cancel
            </button>
          </div>
        </div>
      )}

      {stage === "done" && (
        <div className="mx-auto max-w-3xl">
          <h2 className="font-display text-4xl font-extrabold tracking-tight">Here's where you stand</h2>
          <p className="mt-2 text-pencil">
            {shown.filter((c) => c.status === "mastered").length} of {shown.length} topics mastered.
            {!allDone && " Practice a topic to move its bar."}
          </p>
          <div className="mt-6 grid gap-5 sm:grid-cols-2">
            {shown.map((c) => {
              const mis = (insights?.misconceptions ?? []).filter((m) => m.concept_id === c.concept_id);
              return (
                <div key={c.concept_id} className="sheet p-5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-display text-xl font-bold">{c.name}</span>
                    <StatusChip status={c.status} />
                  </div>
                  <div className="mt-3 flex items-center gap-3">
                    <div className="flex-1"><Meter score={c.score} status={c.status} /></div>
                    <span className="text-sm text-pencil">{Math.round(c.score * 100)}%</span>
                  </div>
                  {mis.length > 0 && (
                    <ul className="mt-3 space-y-1.5 text-sm leading-relaxed">
                      {mis.map((m) => <li key={m.id}><mark className="hl">{m.description}</mark></li>)}
                    </ul>
                  )}
                </div>
              );
            })}
          </div>
          <div className="mt-8 flex flex-wrap items-center gap-5">
            {allDone ? (
              <p className="font-display text-xl font-bold text-pass">Every topic is mastered. Nice work.</p>
            ) : (
              <Btn onClick={() => startPractice()} disabled={busy}>
                {mode === "practice" ? "Continue practice" : "Start practice"}
              </Btn>
            )}
            <button type="button" className="text-sm font-medium text-pencil underline underline-offset-4" onClick={openTopics} disabled={busy}>
              Change topics
            </button>
            <button type="button" className="text-sm font-medium text-pencil underline underline-offset-4" onClick={restart}>
              Start over
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
