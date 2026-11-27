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
        assert r["source"] == "fallback" and "correct answer" in r["explanation"] and "key" in r["note"]

def test_ai(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setattr(tutor, "_call_llm", lambda s, u: "AI says hi")
    with TestClient(app) as c:
        uid, q = _setup(c)
        r = c.post("/tutor/explain", json={"user_id": uid, "question_id": q["id"], "choice": "A"}).json()
        assert r == {"explanation": "AI says hi", "source": "ai", "note": None}

def _ok(url, text="  groq says hi  "):
    return httpx.Response(200, json={"choices": [{"message": {"content": text}}]}, request=httpx.Request("POST", url))

def _run(monkeypatch, fake_post):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_MODEL", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    monkeypatch.setattr(httpx, "post", fake_post)
    with TestClient(app) as c:
        uid, q = _setup(c)
        return c.post("/tutor/explain", json={"user_id": uid, "question_id": q["id"], "choice": "A"}).json()

def test_groq_request_shape(monkeypatch):
    seen = {}
    def fake_post(url, headers, json, timeout):
        seen.update(url=url, headers=headers, json=json)
        return _ok(url)
    r = _run(monkeypatch, fake_post)
    assert r == {"explanation": "groq says hi", "source": "ai", "note": None}
    assert seen["url"] == "https://api.groq.com/openai/v1/chat/completions"
    assert seen["headers"]["Authorization"] == "Bearer gsk_test"
    assert seen["json"]["model"] == "openai/gpt-oss-120b" and seen["json"]["reasoning_effort"] == "low"

def test_retired_model_tries_backup(monkeypatch):
    tried = []
    def fake_post(url, headers, json, timeout):
        tried.append(json["model"])
        if json["model"] == "openai/gpt-oss-120b":
            return httpx.Response(404, request=httpx.Request("POST", url))
        return _ok(url, "from backup")
    r = _run(monkeypatch, fake_post)
    assert tried == ["openai/gpt-oss-120b", "openai/gpt-oss-20b"] and r["explanation"] == "from backup"

def test_all_models_404_is_explained(monkeypatch):
    r = _run(monkeypatch, lambda url, headers, json, timeout: httpx.Response(404, request=httpx.Request("POST", url)))
    assert r["source"] == "fallback" and r["note"] == "AI service returned HTTP 404"

def test_groq_failure_falls_back(monkeypatch):
    def boom(*a, **k): raise httpx.ConnectError("down")
    r = _run(monkeypatch, boom)
    assert r["source"] == "fallback" and "ConnectError" in r["note"]

def test_http_error_is_explained(monkeypatch):
    r = _run(monkeypatch, lambda url, headers, json, timeout: httpx.Response(401, request=httpx.Request("POST", url)))
    assert r["source"] == "fallback" and r["note"] == "AI service returned HTTP 401"

def test_empty_reply_falls_back(monkeypatch):
    r = _run(monkeypatch, lambda url, headers, json, timeout: _ok(url, "   "))
    assert r["source"] == "fallback" and "ValueError" in r["note"]

def test_status_endpoint(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with TestClient(app) as c:
        assert c.get("/tutor/status").json() == {"provider": None}
        monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
        assert c.get("/tutor/status").json() == {"provider": "groq"}
