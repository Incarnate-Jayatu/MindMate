import os, tempfile
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/t2.db"
from fastapi.testclient import TestClient
from app.main import app
from app import tutor

def _setup(c):
    uid = c.post("/users", json={"name": "J"}).json()["id"]
    q = c.get("/diagnostic").json()[0]
    return uid, q

def test_fallback(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with TestClient(app) as c:
        uid, q = _setup(c)
        r = c.post("/tutor/explain", json={"user_id": uid, "question_id": q["id"], "choice": "A"}).json()
        assert r["source"] == "fallback" and "correct answer" in r["explanation"]

def test_ai(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setattr(tutor, "_call_llm", lambda s, u: "AI says hi")
    with TestClient(app) as c:
        uid, q = _setup(c)
        r = c.post("/tutor/explain", json={"user_id": uid, "question_id": q["id"], "choice": "A"}).json()
        assert r == {"explanation": "AI says hi", "source": "ai"}
