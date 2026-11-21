import os, tempfile
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/t3.db"
from fastapi.testclient import TestClient
from app.main import app
from app.seed import QUESTIONS

KEY = {q["prompt"]: q["answer_key"] for q in QUESTIONS}

def _wrong_diagnostic(c):
    uid = c.post("/users", json={"name": "J"}).json()["id"]
    diag = c.get("/diagnostic").json()
    for q in diag:
        c.post("/attempts", json={"user_id": uid, "question_id": q["id"], "choice": "A"})
    return uid, diag

def test_bank_size_and_keys():
    assert len(QUESTIONS) == 27
    assert all(q["answer_key"] in [o["key"] for o in q["options"]] for q in QUESTIONS)
    assert len({q["answer_key"] for q in QUESTIONS}) > 1

def test_practice_reaches_mastery():
    with TestClient(app) as c:
        uid, _ = _wrong_diagnostic(c)
        first = c.get(f"/practice/next?user_id={uid}").json()
        assert not first["done"] and first["question"]["difficulty"] == 1
        seen = set()
        for _ in range(40):
            r = c.get(f"/practice/next?user_id={uid}").json()
            if r["done"]:
                break
            q = r["question"]
            assert q["id"] not in seen
            seen.add(q["id"])
            c.post("/attempts", json={"user_id": uid, "question_id": q["id"], "choice": KEY[q["prompt"]]})
        else:
            raise AssertionError("never finished")
        assert all(m["status"] == "mastered" for m in c.get(f"/map/{uid}").json())

def test_repeating_one_question_is_not_mastery():
    with TestClient(app) as c:
        uid = c.post("/users", json={"name": "K"}).json()["id"]
        q = c.get("/diagnostic").json()[0]
        for _ in range(6):
            r = c.post("/attempts", json={"user_id": uid, "question_id": q["id"], "choice": KEY[q["prompt"]]}).json()
        assert r["mastery"]["score"] > 0.75 and r["mastery"]["status"] == "learning"

def test_insights_and_targeted_practice():
    with TestClient(app) as c:
        uid, _ = _wrong_diagnostic(c)
        ins = c.get(f"/insights/{uid}").json()
        assert ins["recommended"]["concept_id"] == "arrays" and ins["recommended"]["reason"] == "Your weakest area"
        assert len(ins["misconceptions"]) == 3 and all(m["count"] == 1 for m in ins["misconceptions"])
        r = c.get(f"/practice/next?user_id={uid}&concept_id=recursion").json()
        assert r["concept_id"] == "recursion"
        assert c.get("/insights/9999").status_code == 404
