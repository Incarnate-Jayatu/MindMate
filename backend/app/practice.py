from .models import Concept, Question, Attempt, Mastery
from . import variants, topics

def _target_difficulty(score: float) -> int:
    return 1 if score < 0.4 else 2 if score < 0.65 else 3

def choose_concept(db, user_id: int):
    """Returns (concept, status_by_id, score_by_id, open_concepts) or None if every chosen topic is mastered."""
    all_concepts = db.query(Concept).order_by(Concept.id).all()
    sel = topics.selected_ids(db, user_id)
    chosen = [c for c in all_concepts if sel is None or c.id in sel]
    chosen_ids = {c.id for c in chosen}
    ms = {m.concept_id: m for m in db.query(Mastery).filter_by(user_id=user_id)}
    st = {c.id: (ms[c.id].status if c.id in ms else "unseen") for c in all_concepts}
    sc = {c.id: (ms[c.id].score if c.id in ms else 0.5) for c in all_concepts}
    open_ = [c for c in chosen if st[c.id] != "mastered"]
    if not open_:
        return None
    # fix weak prerequisites first, but only ones the learner chose to practice
    ready = [c for c in open_ if not any(st.get(p) == "weak" for p in c.prereqs if p in chosen_ids)]
    return min(ready or open_, key=lambda c: sc[c.id]), st, sc, open_

def pick(db, user_id: int, concept_id: str | None = None):
    """Returns (concept, status, score, question) or None when every concept is mastered."""
    chosen = choose_concept(db, user_id)
    if chosen is None:
        return None
    c, st, sc, open_ = chosen
    if concept_id:  # learner picked a concept on the map (ignored if already mastered)
        c = next((x for x in open_ if x.id == concept_id), c)

    qs = db.query(Question).filter_by(concept_id=c.id).all()
    last = {}
    for a in db.query(Attempt).filter(Attempt.user_id == user_id, Attempt.question_id.in_([q.id for q in qs])):
        if a.question_id not in last or a.ts > last[a.question_id]:
            last[a.question_id] = a.ts
    fresh = [q for q in qs if q.id not in last]
    target = _target_difficulty(sc[c.id])
    if not fresh:  # question bank used up: create a brand-new variant instead of repeating
        v = variants.generate(db, c.id, target)
        if v:
            return c, st[c.id], sc[c.id], v
    pool = fresh or (sorted(qs, key=lambda q: last[q.id])[:-1] or qs)  # skip the one just answered
    q = min(pool, key=lambda q: (abs(q.difficulty - target), last[q.id].timestamp() if q.id in last else 0, q.id))
    return c, st[c.id], sc[c.id], q
