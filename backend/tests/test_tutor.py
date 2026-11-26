import os, tempfile
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/t2.db"
from fastapi.testclient import TestClient
from app.main import app
from app import tutor
import httpx

def _setup(c):
    uid = c.post("/users", json={"name": "J"}).json()["id"]
    q = c.get("/diagnostic").json()[0]
    return uid, q

def test_fallback(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
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

def test_groq_request_shape(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    seen = {}

    class FakeResp:
        def raise_for_status(self): pass
        def json(self): return {"choices": [{"message": {"content": "  groq says hi  "}}]}

    def fake_post(url, headers, json, timeout):
        seen.update(url=url, headers=headers, json=json)
        return FakeResp()

    monkeypatch.setattr(httpx, "post", fake_post)
    with TestClient(app) as c:
        uid, q = _setup(c)
        r = c.post("/tutor/explain", json={"user_id": uid, "question_id": q["id"], "choice": "A"}).json()
    assert r == {"explanation": "groq says hi", "source": "ai"}
    assert seen["url"] == "https://api.groq.com/openai/v1/chat/completions"
    assert seen["headers"]["Authorization"] == "Bearer gsk_test"
    assert seen["json"]["model"] == "llama-3.3-70b-versatile"

def test_groq_failure_falls_back(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    def boom(*a, **k): raise httpx.ConnectError("down")
    monkeypatch.setattr(httpx, "post", boom)
    with TestClient(app) as c:
        uid, q = _setup(c)
        r = c.post("/tutor/explain", json={"user_id": uid, "question_id": q["id"], "choice": "A"}).json()
    assert r["source"] == "fallback"
