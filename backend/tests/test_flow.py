import os, tempfile
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/t.db"
from fastapi.testclient import TestClient
from app.main import app

def test_flow():
    with TestClient(app) as c:
        uid = c.post("/users", json={"name": "Jay"}).json()["id"]
        diag = c.get("/diagnostic").json()
        assert len(diag) == 3 and "answer_key" not in diag[0]
        q = next(x for x in diag if x["concept_id"] == "arrays")
        r = c.post("/attempts", json={"user_id": uid, "question_id": q["id"], "choice": "A"}).json()
        assert not r["correct"] and r["misconception"]["id"] == "arr-partial-init"
        assert r["mastery"]["score"] == 0.35
        r = c.post("/attempts", json={"user_id": uid, "question_id": q["id"], "choice": "A"}).json()
        assert r["mastery"]["status"] == "weak"
        m = {x["concept_id"]: x for x in c.get(f"/map/{uid}").json()}
        assert m["arrays"]["misconceptions"] == {"arr-partial-init": 2}
        assert m["loops"]["status"] == "unseen"
        assert c.post("/attempts", json={"user_id": uid, "question_id": q["id"], "choice": "Z"}).status_code == 422
