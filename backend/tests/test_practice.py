import os, tempfile
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/t3.db"
from fastapi.testclient import TestClient
from app.main import app
from app.db import SessionLocal
from app.models import Question
from app.seed import QUESTIONS, MISCONCEPTIONS, CONCEPTS

def _choice(qid, correct):
    with SessionLocal() as db:
        q = db.get(Question, qid)
        return q.answer_key if correct else next(o["key"] for o in q.options if o["key"] != q.answer_key)

def _answer(c, uid, qid, correct):
    return c.post("/attempts", json={"user_id": uid, "question_id": qid, "choice": _choice(qid, correct)}).json()

def _wrong_diagnostic(c):
    uid = c.post("/users", json={"name": "J"}).json()["id"]
    diag = c.get("/diagnostic").json()
    for q in diag:
        _answer(c, uid, q["id"], False)
    return uid, diag

def test_bank_is_consistent():
    prompts = [q["prompt"] for q in QUESTIONS]
    assert len(QUESTIONS) >= 51 and len(prompts) == len(set(prompts))
    concepts = {c[0] for c in CONCEPTS}
    misc = {m[0] for m in MISCONCEPTIONS}
    assert all(p in concepts for c in CONCEPTS for p in c[2])
    for q in QUESTIONS:
        assert q["concept_id"] in concepts
        assert q["answer_key"] in [o["key"] for o in q["options"]]
        assert all(o["misconception_id"] in misc | {None} for o in q["options"])
    assert len({q["answer_key"] for q in QUESTIONS}) > 1
    assert {q["concept_id"] for q in QUESTIONS} == concepts

def test_practice_reaches_mastery():
    with TestClient(app) as c:
        uid, _ = _wrong_diagnostic(c)
        first = c.get(f"/practice/next?user_id={uid}").json()
        assert not first["done"] and first["question"]["difficulty"] == 1
        seen = set()
        for _ in range(150):
            r = c.get(f"/practice/next?user_id={uid}").json()
            if r["done"]:
                break
            q = r["question"]
            assert q["id"] not in seen
            seen.add(q["id"])
            _answer(c, uid, q["id"], True)
        else:
            raise AssertionError("never finished")
        statuses = {m["concept_id"]: m["status"] for m in c.get(f"/map/{uid}").json()}
        assert len(statuses) == 7 and set(statuses.values()) == {"mastered"}

def test_repeating_one_question_is_not_mastery():
    with TestClient(app) as c:
        uid = c.post("/users", json={"name": "K"}).json()["id"]
        q = c.get("/diagnostic").json()[0]
        for _ in range(6):
            r = _answer(c, uid, q["id"], True)
        assert r["mastery"]["score"] > 0.75 and r["mastery"]["status"] == "learning"

def test_insights_and_targeted_practice():
    with TestClient(app) as c:
        uid, _ = _wrong_diagnostic(c)
        ins = c.get(f"/insights/{uid}").json()
        assert ins["recommended"]["concept_id"] == "arrays" and ins["recommended"]["reason"] == "Your weakest area"
        assert len(ins["misconceptions"]) >= 3
        r = c.get(f"/practice/next?user_id={uid}&concept_id=queues").json()
        assert r["concept_id"] == "queues"
        assert c.get("/insights/9999").status_code == 404

def test_prerequisite_gating():
    with TestClient(app) as c:
        uid, _ = _wrong_diagnostic(c)
        # arrays and loops are weak, so dependent topics must not be recommended yet
        for _ in range(3):
            r = c.get(f"/practice/next?user_id={uid}").json()
            assert r["concept_id"] in {"arrays", "loops"}
            _answer(c, uid, r["question"]["id"], False)
