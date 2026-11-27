import os, random, tempfile
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/t4.db"
from fastapi.testclient import TestClient
from app.main import app
from app.seed import MISCONCEPTIONS
from app.db import SessionLocal
from app.models import Question
from app import variants

IDS = {m[0] for m in MISCONCEPTIONS}

def wrong(qid):
    with SessionLocal() as db:
        q = db.get(Question, qid)
        return next(o["key"] for o in q.options if o["key"] != q.answer_key)

def test_every_template_is_well_formed():
    assert len(variants.TEMPLATES) == 21
    for (concept, diff) in variants.TEMPLATES:
        for seed in range(200):
            q, cpp, correct = variants.make(concept, diff, random.Random(seed))
            texts = [o["text"] for o in q["options"]]
            assert len(texts) == 4 and len(set(texts)) == 4
            assert next(o for o in q["options"] if o["key"] == q["answer_key"])["text"] == correct
            assert all(o["misconception_id"] in IDS | {None} for o in q["options"])
            assert [o["misconception_id"] for o in q["options"] if o["text"] == correct] == [None]

def test_exhausted_bank_yields_new_variants():
    with TestClient(app) as c:
        uid = c.post("/users", json={"name": "V"}).json()["id"]
        bank = c.get("/questions?concept_id=arrays").json()
        assert len(bank) == 9
        for q in bank:
            c.post("/attempts", json={"user_id": uid, "question_id": q["id"], "choice": wrong(q["id"])})
        ids, prompts = {q["id"] for q in bank}, {q["prompt"] for q in bank}
        for _ in range(3):
            r = c.get(f"/practice/next?user_id={uid}").json()
            q = r["question"]
            assert r["concept_id"] == "arrays" and q["id"] not in ids and q["prompt"] not in prompts
            ids.add(q["id"]); prompts.add(q["prompt"])
            assert c.post("/attempts", json={"user_id": uid, "question_id": q["id"], "choice": wrong(q["id"])}).status_code == 200
