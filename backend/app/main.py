import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
from . import mastery as ms
from .db import Base, engine, get_db, SessionLocal
from .models import User, Concept, Misconception, Question, Attempt, Mastery
from .seed import seed
from . import tutor, practice

@asynccontextmanager
async def lifespan(_):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)
    yield

app = FastAPI(title="MindMate", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", *filter(None, os.getenv("CORS_ORIGINS", "").split(","))], allow_methods=["*"], allow_headers=["*"])

class UserIn(BaseModel):
    name: str

class AttemptIn(BaseModel):
    user_id: int
    question_id: int
    choice: str

def _public(q: Question):
    return {"id": q.id, "concept_id": q.concept_id, "difficulty": q.difficulty, "prompt": q.prompt,
            "options": [{"key": o["key"], "text": o["text"]} for o in q.options]}

@app.post("/users")
def create_user(body: UserIn, db: Session = Depends(get_db)):
    u = User(name=body.name)
    db.add(u); db.commit()
    return {"id": u.id, "name": u.name}

@app.get("/concepts")
def concepts(db: Session = Depends(get_db)):
    return [{"id": c.id, "name": c.name, "prereqs": c.prereqs} for c in db.query(Concept)]

@app.get("/diagnostic")
def diagnostic(db: Session = Depends(get_db)):
    """One medium-difficulty question per concept (difficulty 2)."""
    first = {}
    for q in db.query(Question).filter(Question.difficulty == 2).order_by(Question.id):
        first.setdefault(q.concept_id, q)
    return [_public(q) for q in first.values()]

@app.get("/questions")
def questions(concept_id: str, db: Session = Depends(get_db)):
    return [_public(q) for q in db.query(Question).filter_by(concept_id=concept_id).order_by(Question.difficulty)]

@app.post("/attempts")
def attempt(body: AttemptIn, db: Session = Depends(get_db)):
    q = db.get(Question, body.question_id)
    if not q or not db.get(User, body.user_id):
        raise HTTPException(404, "user or question not found")
    opt = next((o for o in q.options if o["key"] == body.choice), None)
    if not opt:
        raise HTTPException(422, "invalid choice")
    correct = body.choice == q.answer_key
    mid = None if correct else opt["misconception_id"]
    db.add(Attempt(user_id=body.user_id, question_id=q.id, choice=body.choice, correct=correct, misconception_id=mid))
    m = db.query(Mastery).filter_by(user_id=body.user_id, concept_id=q.concept_id).first()
    if not m:
        m = Mastery(user_id=body.user_id, concept_id=q.concept_id, score=0.5, attempts=0, status="unseen")
        db.add(m)
    db.flush()
    dc = (db.query(func.count(func.distinct(Attempt.question_id)))
          .join(Question, Question.id == Attempt.question_id)
          .filter(Attempt.user_id == body.user_id, Question.concept_id == q.concept_id, Attempt.correct.is_(True))
          .scalar())
    ms.update(m, correct, dc)
    db.commit()
    misc = db.get(Misconception, mid) if mid else None
    return {"correct": correct, "answer_key": q.answer_key,
            "misconception": {"id": misc.id, "description": misc.description} if misc else None,
            "mastery": {"concept_id": m.concept_id, "score": m.score, "status": m.status}}

@app.get("/map/{user_id}")
def knowledge_map(user_id: int, db: Session = Depends(get_db)):
    rows = {m.concept_id: m for m in db.query(Mastery).filter_by(user_id=user_id)}
    counts = dict(db.query(Attempt.misconception_id, func.count()).filter(
        Attempt.user_id == user_id, Attempt.misconception_id.isnot(None)).group_by(Attempt.misconception_id).all())
    out = []
    for c in db.query(Concept):
        m = rows.get(c.id)
        mids = [x.id for x in db.query(Misconception).filter_by(concept_id=c.id) if x.id in counts]
        out.append({"concept_id": c.id, "name": c.name, "prereqs": c.prereqs,
                    "score": m.score if m else 0.5, "attempts": m.attempts if m else 0,
                    "status": m.status if m else "unseen",
                    "misconceptions": {i: counts[i] for i in mids}})
    return out

class ExplainIn(BaseModel):
    user_id: int
    question_id: int
    choice: str

@app.post("/tutor/explain")
def tutor_explain(body: ExplainIn, db: Session = Depends(get_db)):
    q = db.get(Question, body.question_id)
    if not q:
        raise HTTPException(404, "question not found")
    opt = next((o for o in q.options if o["key"] == body.choice), None)
    if not opt:
        raise HTTPException(422, "invalid choice")
    correct = next(o for o in q.options if o["key"] == q.answer_key)
    misc = db.get(Misconception, opt["misconception_id"]) if opt["misconception_id"] else None
    m = db.query(Mastery).filter_by(user_id=body.user_id, concept_id=q.concept_id).first()
    level = "beginner" if (not m or m.score < 0.5) else "intermediate"
    concept = db.get(Concept, q.concept_id)
    text, source, note = tutor.explain(concept.name, q.prompt, opt["text"], correct["text"],
                                 misc.description if misc else None, level)
    return {"explanation": text, "source": source, "note": note}

@app.get("/tutor/status")
def tutor_status():
    return tutor.status()

@app.get("/practice/next")
def practice_next(user_id: int, concept_id: str | None = None, db: Session = Depends(get_db)):
    if not db.get(User, user_id):
        raise HTTPException(404, "user not found")
    r = practice.pick(db, user_id, concept_id)
    if r is None:
        return {"done": True}
    c, status, score, q = r
    return {"done": False, "concept_id": c.id, "concept_name": c.name, "status": status,
            "score": score, "question": _public(q)}

REASONS = {"weak": "Your weakest area", "unseen": "Not started yet", "learning": "Keep building it"}

@app.get("/insights/{user_id}")
def insights(user_id: int, db: Session = Depends(get_db)):
    if not db.get(User, user_id):
        raise HTTPException(404, "user not found")
    rec = None
    chosen = practice.choose_concept(db, user_id)
    if chosen:
        c, st, sc, open_ = chosen
        lowest = min(open_, key=lambda x: sc[x.id])
        reason = f"Prerequisite for {lowest.name}" if lowest.id != c.id else REASONS[st[c.id]]
        rec = {"concept_id": c.id, "name": c.name, "reason": reason}
    rows = (db.query(Attempt.misconception_id, func.count(), func.max(Attempt.ts))
            .filter(Attempt.user_id == user_id, Attempt.misconception_id.isnot(None))
            .group_by(Attempt.misconception_id).all())
    info = {x.id: x for x in db.query(Misconception)}
    items = [{"id": mid, "concept_id": info[mid].concept_id, "description": info[mid].description,
              "count": n, "last_seen": str(ts)} for mid, n, ts in rows]
    items.sort(key=lambda x: -x["count"])
    return {"recommended": rec, "misconceptions": items}

@app.get("/health")
def health():
    return {"ok": True}
